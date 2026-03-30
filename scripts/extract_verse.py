# extract_verse.py — VerseBloomed | Verse Extraction Engine (v3 — PDF Only)
#
# All 4 languages (English, Hindi, Marathi, Kannada) extracted from local PDFs.
# No external API required.
#
# EXTRACTION APPROACH (3 steps per verse):
#   1. Parse local book name from the *_ref CSV column
#   2. Find the book's heading page in the PDF (skips TOC pages)
#   3. Find the chapter within that book's pages, then isolate the exact verse
#
# RULE: Bible verse text is NEVER altered — returned verbatim from source PDF.

import os
import re
import fitz          # PyMuPDF
from config import BIBLE_PATHS


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def clean_text(text):
    """Remove OCR artefacts and normalise whitespace. No content changes."""
    text = text.replace('\ufffd', '').replace('\x00', '')
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'^[\s\.\:\-–—\)\(]+', '', text)
    return text.strip()


def is_clean_verse(text, language):
    """Check that extracted text is genuine verse content, not index/TOC."""
    if not text or len(text) < 15:
        return False
    # Too many digits = index or cross-reference section
    if sum(c.isdigit() for c in text) / len(text) > 0.12:
        return False
    # Decimal page-number patterns (e.g. "1.089") = TOC content
    if len(re.findall(r'\d+\.\d{2,3}', text)) > 2:
        return False
    # Script character checks
    if language in ("hindi", "marathi"):
        if sum(1 for c in text if '\u0900' <= c <= '\u097F') < 5:
            return False
    if language == "kannada":
        if sum(1 for c in text if '\u0C80' <= c <= '\u0CFF') < 5:
            return False
    if language == "english":
        if sum(1 for c in text if c.isalpha()) < 10:
            return False
    return True


def is_toc_page(text):
    """Detect Table of Contents pages by density of decimal page numbers."""
    return len(re.findall(r'\b\d+\.\d{2,3}\b', text)) > 8


def parse_local_ref(ref_string):
    """
    Extract local book name from a *_ref column value.

    Examples:
      'Hosea 11:4'           -> 'Hosea'
      'Song of Solomon 8:6'  -> 'Song of Solomon'
      'होशे 11:4'            -> 'होशे'
      'भजन संहिता 63:3'     -> 'भजन संहिता'
      'ಹೋಶೇಯ 11:4'          -> 'ಹೋಶೇಯ'
    """
    if not ref_string or not isinstance(ref_string, str):
        return None
    m = re.match(r'^(.+?)\s+\d+:\d+\s*$', ref_string.strip())
    return m.group(1).strip() if m else None


# ══════════════════════════════════════════════════════════════════════════════
#  CHAPTER HEADING KEYWORDS PER LANGUAGE
# ══════════════════════════════════════════════════════════════════════════════

# Words that appear before a chapter number in each language's Bible PDF.
# If none match, a standalone chapter number on its own line is also tried.
CHAPTER_KEYWORDS = {
    "english": ["Chapter"],
    "hindi":   ["अध्याय", "अध्‍याय"],
    "marathi": ["धडा", "प्रकरण", "अध्याय"],
    "kannada": ["ಅಧ್ಯಾಯ", "ಅಧ್ಯಾಯವು"],
}


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 1 — FIND BOOK HEADING PAGE
# ══════════════════════════════════════════════════════════════════════════════

def find_book_start_page(doc, local_book_name, total_pages):
    """
    Find the page where the book truly begins (its title/heading page),
    skipping TOC pages and stray cross-reference mentions.

    Prefers pages where the book name appears in the first 8 non-empty lines.
    Falls back to any non-TOC page containing the name.
    """
    headed = []
    fallback = []

    for page_num in range(total_pages):
        text = doc[page_num].get_text()
        if local_book_name not in text:
            continue
        if is_toc_page(text):
            continue

        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in lines[:8]:
            if local_book_name in line:
                headed.append(page_num)
                break
        else:
            fallback.append(page_num)

    for pool in (headed, fallback):
        if pool:
            return min(pool)
    return -1


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 2 — FIND CHAPTER START PAGE
# ══════════════════════════════════════════════════════════════════════════════

def find_chapter_page(doc, chapter, book_start, book_end, language):
    """
    Within the book's page range, find the page where chapter begins.

    Tries:
      A. Keyword + number:  "अध्याय 11" / "Chapter 11"
      B. Standalone number on its own line (common in Indian Bible PDFs)
    """
    chapter_str = str(chapter)
    keywords    = CHAPTER_KEYWORDS.get(language, [])

    for page_num in range(book_start, book_end):
        text = doc[page_num].get_text()

        # A — keyword match
        for kw in keywords:
            if f"{kw} {chapter_str}" in text or f"{kw}\n{chapter_str}" in text:
                return page_num

        # B — standalone chapter number line
        for line in text.split('\n'):
            if line.strip() == chapter_str:
                return page_num

    return book_start  # fallback: start of book


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — EXTRACT THE SPECIFIC VERSE
# ══════════════════════════════════════════════════════════════════════════════

def extract_verse_from_pages(doc, chapter, verse, start_page, end_page, language):
    """
    Scan pages [start_page, end_page) for verse `verse` and return its text.

    Looks for the verse number as:
      - A standalone line (most common in Indian PDFs)
      - Inline followed by space and non-digit text
    """
    verse_str      = str(verse)
    next_verse_str = str(verse + 1)

    patterns = [
        re.compile(rf'(?m)^\s*{re.escape(verse_str)}\s*$'),
        re.compile(rf'(?<!\d){re.escape(verse_str)}\s+(?=[^\d])'),
    ]

    for page_num in range(start_page, min(end_page, len(doc))):
        text = doc[page_num].get_text()

        for pat in patterns:
            for m in pat.finditer(text):
                pos = m.end()
                raw = text[pos: pos + 900]

                # Cut at next verse number
                nv = re.search(rf'(?<!\d){re.escape(next_verse_str)}(?!\d)', raw)
                if nv:
                    raw = raw[:nv.start()]

                # Cut at lone chapter-number line (chapter boundary signal)
                ch = re.search(r'\n\s*\d{1,3}\s*\n', raw)
                if ch and ch.start() > 30:
                    raw = raw[:ch.start()]

                cleaned = clean_text(raw)
                if is_clean_verse(cleaned, language):
                    return cleaned[:500]

    return None


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN PDF EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

def extract_from_pdf(language, book, chapter, verse, local_ref):
    """
    Full 3-step PDF extraction for any language.

    Parameters
    ----------
    language  : 'english' | 'hindi' | 'marathi' | 'kannada'
    book      : English book name (informational only)
    chapter   : int
    verse     : int
    local_ref : *_ref column value from CSV
                English  -> 'Hosea 11:4'
                Hindi    -> 'होशे 11:4'
                Marathi  -> 'होशे 11:4'
                Kannada  -> 'ಹೋಶೇಯ 11:4'
    """
    pdf_path = BIBLE_PATHS.get(language)
    if not pdf_path or not os.path.exists(pdf_path):
        print(f"  ❌ [{language.upper()}] PDF not found: {pdf_path}")
        return None

    local_book_name = parse_local_ref(local_ref)
    if not local_book_name:
        print(f"  ⚠️  [{language.upper()}] Cannot parse book name from ref: {local_ref!r}")
        return None

    print(f"  🔍 [{language.upper()}] '{local_book_name}' ch.{chapter} v.{verse}")

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"  ❌ [{language.upper()}] Cannot open PDF: {e}")
        return None

    total_pages = len(doc)

    # Step 1 — book heading page
    book_start = find_book_start_page(doc, local_book_name, total_pages)
    if book_start == -1:
        print(f"  ❌ [{language.upper()}] Book '{local_book_name}' not found in PDF")
        doc.close()
        return None
    print(f"     Book heading  → page {book_start + 1}")

    book_end = min(book_start + 200, total_pages)

    # Step 2 — chapter start page within the book
    chapter_page = find_chapter_page(doc, chapter, book_start, book_end, language)
    print(f"     Chapter {chapter:<4} → page {chapter_page + 1}")

    # Step 3 — extract the verse (scan up to 10 pages from chapter start)
    result = extract_verse_from_pages(
        doc, chapter, verse,
        start_page=chapter_page,
        end_page=min(chapter_page + 10, book_end),
        language=language,
    )

    doc.close()

    if result:
        print(f"  ✅ [{language.upper()}] {result[:70]}...")
    else:
        print(f"  ⚠️  [{language.upper()}] Not extracted "
              f"(book p.{book_start + 1}, ch p.{chapter_page + 1})")
    return result


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def extract_verse(language, book, chapter, verse, local_ref=None):
    """
    Extract a single verse from the appropriate Bible PDF.

    Parameters
    ----------
    language  : 'english' | 'hindi' | 'marathi' | 'kannada'
    book      : English book name
    chapter   : int
    verse     : int
    local_ref : *_ref column value from CSV (required for all languages)

    Returns verbatim verse text, or None if extraction fails.
    RULE: Text is NEVER altered or paraphrased.
    """
    return extract_from_pdf(language, book, chapter, verse, local_ref=local_ref)


def extract_all_languages(row):
    """
    Extract the same verse across all 4 languages using a CSV row dict.

    Expects keys: book, chapter, verse,
                  english_ref, hindi_ref, marathi_ref, kannada_ref

    Returns dict: {'english': '...', 'hindi': '...', 'marathi': '...', 'kannada': '...'}
    """
    book    = row['book']
    chapter = int(row['chapter'])
    verse   = int(row['verse'])

    results = {}
    for lang in ["english", "hindi", "marathi", "kannada"]:
        print(f"  📖 Extracting {lang}...")
        local_ref     = row.get(f"{lang}_ref", "")
        results[lang] = extract_verse(lang, book, chapter, verse, local_ref=local_ref)

    return results


def find_random_extractable_verse(language, df_unused):
    """Find an unused verse that can be cleanly extracted for a given language."""
    import random
    rows = df_unused.to_dict('records')
    random.shuffle(rows)

    for row in rows:
        local_ref = row.get(f"{language}_ref", "")
        text = extract_verse(
            language, row['book'],
            int(row['chapter']), int(row['verse']),
            local_ref=local_ref,
        )
        if text and is_clean_verse(text, language):
            return row, text

    return None, None
