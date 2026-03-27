# extract_verse.py — Extract verse text from Bible PDFs

import fitz  # PyMuPDF
import re
from config import BIBLE_PATHS


def clean_text(text):
    """Clean extracted text — remove extra whitespace and artifacts."""
    text = " ".join(text.split())
    text = re.sub(r'^[\s\.\:\-–—]+', '', text)
    return text.strip()


def extract_verse(language, book, chapter, verse):
    """
    Extract verse text from a single-PDF Bible.
    IMPORTANT: Never alter the extracted text — use as-is from the Bible.
    """
    pdf_path = BIBLE_PATHS[language]

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"❌ Cannot open {pdf_path}: {e}")
        return f"[{book} {chapter}:{verse} — PDF not found]"

    search_patterns = [
        f"{chapter}:{verse}",
        f"{chapter}.{verse}",
        f"{chapter} :{verse}",
    ]

    result_text = ""

    for page_num in range(len(doc)):
        page_text = doc[page_num].get_text()

        for pattern in search_patterns:
            if pattern in page_text:
                idx = page_text.find(pattern)
                # Extract text after the reference marker
                raw = page_text[idx + len(pattern): idx + len(pattern) + 600]
                cleaned = clean_text(raw)
                # Remove leading verse numbers that sometimes appear
                cleaned = re.sub(r'^\d+\s*', '', cleaned)
                if len(cleaned) > 10:
                    result_text = cleaned[:500]
                    break

        if result_text:
            break

    doc.close()

    if not result_text:
        print(f"⚠️  [{language.upper()}] Not found: {book} {chapter}:{verse} — will use random available verse")
        return None  # Signal to main.py to pick a random verse

    print(f"  ✅ [{language.upper()}] Extracted: {result_text[:60]}...")
    return result_text


def extract_all_languages(book, chapter, verse):
    """Extract same verse from all 4 language PDFs."""
    results = {}
    for lang in ["english", "hindi", "marathi", "kannada"]:
        print(f"  📖 Extracting {lang}...")
        results[lang] = extract_verse(lang, book, chapter, verse)
    return results


def find_random_extractable_verse(language, df_unused):
    """
    If a verse can't be extracted, find another unused verse that CAN be extracted.
    This prevents placeholder text from appearing on slides.
    """
    import random
    unused_list = df_unused.to_dict('records')
    random.shuffle(unused_list)

    for row in unused_list:
        text = extract_verse(language, row['book'], row['chapter'], row['verse'])
        if text and len(text) > 15:
            return row, text

    return None, None
