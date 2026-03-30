# extract_verse.py — Extract verse text from Bible PDFs + API fallback

import fitz  # PyMuPDF
import re
import requests
from config import BIBLE_PATHS


def clean_text(text):
    """Clean extracted text — remove numbers, junk, extra whitespace."""
    # Remove standalone numbers and verse reference numbers
    text = re.sub(r'^\d+\s*', '', text)
    text = re.sub(r'\s+\d+\.\d+', '', text)
    # Remove replacement characters
    text = text.replace('\ufffd', '').replace('?', '')
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    # Remove leading punctuation artifacts
    text = re.sub(r'^[\s\.\:\-–—\)\(]+', '', text)
    return text.strip()


def is_clean_verse(text, language):
    """Check if extracted text looks like a real verse."""
    if not text or len(text) < 15:
        return False
    # Too many numbers = likely index/metadata, not verse
    digit_count = sum(c.isdigit() for c in text)
    if digit_count > len(text) * 0.15:
        return False
    # For non-English: check has script characters
    if language == "hindi" or language == "marathi":
        devanagari = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        if devanagari < 5:
            return False
    if language == "kannada":
        kannada_chars = sum(1 for c in text if '\u0C80' <= c <= '\u0CFF')
        if kannada_chars < 5:
            return False
    return True


# ── ENGLISH: Use Bible API (free, reliable, NIV) ──────────────────────────────

BOOK_NAME_MAP = {
    "Genesis": "genesis", "Exodus": "exodus", "Leviticus": "leviticus",
    "Numbers": "numbers", "Deuteronomy": "deuteronomy", "Joshua": "joshua",
    "Judges": "judges", "Ruth": "ruth", "1 Samuel": "1+samuel",
    "2 Samuel": "2+samuel", "1 Kings": "1+kings", "2 Kings": "2+kings",
    "1 Chronicles": "1+chronicles", "2 Chronicles": "2+chronicles",
    "Ezra": "ezra", "Nehemiah": "nehemiah", "Esther": "esther",
    "Job": "job", "Psalm": "psalm", "Proverbs": "proverbs",
    "Ecclesiastes": "ecclesiastes", "Song of Solomon": "song+of+solomon",
    "Isaiah": "isaiah", "Jeremiah": "jeremiah", "Lamentations": "lamentations",
    "Ezekiel": "ezekiel", "Daniel": "daniel", "Hosea": "hosea",
    "Joel": "joel", "Amos": "amos", "Obadiah": "obadiah",
    "Jonah": "jonah", "Micah": "micah", "Nahum": "nahum",
    "Habakkuk": "habakkuk", "Zephaniah": "zephaniah", "Haggai": "haggai",
    "Zechariah": "zechariah", "Malachi": "malachi",
    "Matthew": "matthew", "Mark": "mark", "Luke": "luke", "John": "john",
    "Acts": "acts", "Romans": "romans", "1 Corinthians": "1+corinthians",
    "2 Corinthians": "2+corinthians", "Galatians": "galatians",
    "Ephesians": "ephesians", "Philippians": "philippians",
    "Colossians": "colossians", "1 Thessalonians": "1+thessalonians",
    "2 Thessalonians": "2+thessalonians", "1 Timothy": "1+timothy",
    "2 Timothy": "2+timothy", "Titus": "titus", "Philemon": "philemon",
    "Hebrews": "hebrews", "James": "james", "1 Peter": "1+peter",
    "2 Peter": "2+peter", "1 John": "1+john", "2 John": "2+john",
    "3 John": "3+john", "Jude": "jude", "Revelation": "revelation",
}


def extract_english_from_api(book, chapter, verse):
    """Fetch English NIV verse from bible-api.com — clean and reliable."""
    book_slug = BOOK_NAME_MAP.get(book, book.lower().replace(" ", "+"))
    url = f"https://bible-api.com/{book_slug}+{chapter}:{verse}?translation=kjv"
    try:
        resp = requests.get(url, timeout=15)
        data = resp.json()
        if "text" in data:
            text = data["text"].strip().replace("\n", " ")
            text = re.sub(r'\s+', ' ', text).strip()
            print(f"  ✅ [ENGLISH] API: {text[:60]}...")
            return text
        else:
            print(f"  ⚠️  [ENGLISH] API returned no text: {data}")
            return None
    except Exception as e:
        print(f"  ⚠️  [ENGLISH] API failed: {e} — trying PDF fallback")
        return None


# ── PDF EXTRACTION (Hindi, Marathi, Kannada) ──────────────────────────────────

def extract_from_pdf(language, book, chapter, verse):
    """Extract verse from PDF with improved cleaning."""
    pdf_path = BIBLE_PATHS[language]

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"  ❌ Cannot open {pdf_path}: {e}")
        return None

    search_patterns = [
        f"{chapter}:{verse}",
        f"{chapter}.{verse} ",
        f" {chapter}:{verse} ",
        f"\n{verse}\n",
    ]

    result_text = ""

    for page_num in range(len(doc)):
        page_text = doc[page_num].get_text()

        for pattern in search_patterns:
            if pattern in page_text:
                idx = page_text.find(pattern)
                raw = page_text[idx + len(pattern): idx + len(pattern) + 800]
                # Take only up to the next verse number
                next_verse = re.search(r'\n\d+\n', raw)
                if next_verse:
                    raw = raw[:next_verse.start()]
                cleaned = clean_text(raw)
                if is_clean_verse(cleaned, language):
                    result_text = cleaned[:500]
                    break

        if result_text:
            break

    doc.close()

    if not result_text:
        print(f"  ⚠️  [{language.upper()}] Not found: {book} {chapter}:{verse}")
        return None

    print(f"  ✅ [{language.upper()}] Extracted: {result_text[:60]}...")
    return result_text


def extract_verse(language, book, chapter, verse):
    """
    Extract verse text.
    English → Bible API (reliable)
    Hindi/Marathi/Kannada → PDF extraction
    RULE: Never alter verse text — use exactly as received.
    """
    if language == "english":
        # Try API first
        text = extract_english_from_api(book, chapter, verse)
        if text:
            return text
        # Fallback to PDF if API fails
        print(f"  ⚠️  [ENGLISH] Falling back to PDF...")
        return extract_from_pdf(language, book, chapter, verse)
    else:
        return extract_from_pdf(language, book, chapter, verse)


def extract_all_languages(book, chapter, verse):
    """Extract same verse from all 4 language sources."""
    results = {}
    for lang in ["english", "hindi", "marathi", "kannada"]:
        print(f"  📖 Extracting {lang}...")
        results[lang] = extract_verse(lang, book, chapter, verse)
    return results


def find_random_extractable_verse(language, df_unused):
    """Find an unused verse that can be cleanly extracted."""
    import random
    unused_list = df_unused.to_dict('records')
    random.shuffle(unused_list)

    for row in unused_list:
        text = extract_verse(language, row['book'], row['chapter'], row['verse'])
        if text and is_clean_verse(text, language):
            return row, text

    return None, None
