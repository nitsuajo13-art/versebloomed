# main.py — VerseBloomed Main Orchestrator

import pandas as pd
import sys
import os
from datetime import datetime
from extract_verse import extract_all_languages, find_random_extractable_verse
from generate_image import generate_carousel
from config import CSV_PATH, LANGUAGE_ORDER

os.makedirs("state", exist_ok=True)
os.makedirs("output", exist_ok=True)


def get_next_verse():
    """Get next unused verse from CSV."""
    df     = pd.read_csv(CSV_PATH)
    unused = df[df["used"] == False]
    if unused.empty:
        print("🎉 All curated verses used! Reset CSV or add more.")
        return None, None
    return unused.iloc[0], df


def mark_verse_used(df, verse_id, verse_texts):
    """Mark verse as used and save extracted text back to CSV."""
    df.loc[df["id"] == verse_id, "used"]      = True
    df.loc[df["id"] == verse_id, "used_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    # Save extracted verse texts for caption use
    for lang in LANGUAGE_ORDER:
        col = f"{lang}_verse"
        if col not in df.columns:
            df[col] = ""
        if verse_texts.get(lang):
            df.loc[df["id"] == verse_id, col] = verse_texts[lang]
    df.to_csv(CSV_PATH, index=False)
    print(f"  ✅ Verse ID {verse_id} marked as used.")


def run(session="morning"):
    print(f"\n🌸 VerseBloomed — {session.upper()} — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # Get next verse
    verse, df = get_next_verse()
    if verse is None:
        return False

    book    = verse["book"]
    chapter = verse["chapter"]
    v       = verse["verse"]
    vid     = verse["id"]

    print(f"📖 Selected verse: {book} {chapter}:{v} (ID: {vid})\n")

    # Extract verse text from all 4 PDFs
    print("📄 Extracting verse text from Bible PDFs...")
    verse_texts = extract_all_languages(book, chapter, v)

    # Handle any failed extractions — find random extractable verse
    unused = df[df["used"] == False]
    for lang in LANGUAGE_ORDER:
        if verse_texts[lang] is None:
            print(f"  ⚠️  {lang} extraction failed — finding alternate verse...")
            alt_row, alt_text = find_random_extractable_verse(lang, unused)
            if alt_text:
                verse_texts[lang] = alt_text
                print(f"  ✅ Using alternate: {alt_row['book']} {alt_row['chapter']}:{alt_row['verse']}")
            else:
                verse_texts[lang] = f"[{book} {chapter}:{v}]"

    # Build references dict
    references = {
        "english": verse["english_ref"],
        "hindi":   verse["hindi_ref"],
        "marathi": verse["marathi_ref"],
        "kannada": verse["kannada_ref"],
    }

    # Store english verse text for caption
    verse_texts["english_ref"] = verse["english_ref"]

    # Generate 4 slide images
    print("\n🎨 Generating carousel images...")
    slide_paths = generate_carousel(verse_texts, references, session)

    # Mark verse as used
    mark_verse_used(df, vid, verse_texts)

    print(f"\n✅ {len(slide_paths)} slides generated successfully!")
    print(f"📂 Saved to: output/{datetime.now().strftime('%Y-%m-%d')}_{session}/")
    print("\n📋 Review images in GitHub Actions Artifacts before they post.")

    return slide_paths, verse.to_dict()


if __name__ == "__main__":
    session = sys.argv[1] if len(sys.argv) > 1 else "morning"
    result  = run(session)
    if result:
        print("\n🌸 VerseBloomed run complete!")
    else:
        print("\n❌ Run failed — check logs above.")
