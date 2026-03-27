# config.py — VerseBloomed Central Configuration

import os

# ── Canvas ────────────────────────────────────────────────────────────────────
CANVAS_SIZE = (1080, 1080)
OUTPUT_DIR  = "output"

# ── File Paths ────────────────────────────────────────────────────────────────
CSV_PATH   = "verses/curated_verses.csv"
STATE_PATH = "state/progress.json"

# ── Bible PDF Paths ───────────────────────────────────────────────────────────
BIBLE_PATHS = {
    "english": "bibles/Holy_Bible_English_NIV.pdf",
    "hindi": "bibles/Holy_Bible_Hindi.pdf",
    "marathi": "bibles/Holy_Bible_Marathi.pdf",
    "kannada": "bibles/Holy_Bible_Kannada.pdf",
}

# ── Font Paths ────────────────────────────────────────────────────────────────
FONTS = {
    "playfair":        "fonts/PlayfairDisplay-Regular.ttf",
    "playfair_italic": "fonts/PlayfairDisplay-Italic.ttf",
    "playfair_bold":   "fonts/PlayfairDisplay-Bold.ttf",
    "devanagari":      "fonts/NotoSerifDevanagari-Regular.ttf",
    "devanagari_med":  "fonts/NotoSerifDevanagari-Medium.ttf",
    "kannada":         "fonts/NotoSerifKannada-Regular.ttf",
}

# ── Language Order ────────────────────────────────────────────────────────────
LANGUAGE_ORDER = ["english", "hindi", "marathi", "kannada"]

# ── Color Themes (Finalized v6) ───────────────────────────────────────────────
THEMES = {
    "english": {
        "gradient_type":    "golden",
        "text_color":       (58,  36,  16),
        "ref_color":        (122, 85,  48),
        "wm_color":         (58,  36,  16, 230),
        "wm_ul_color":      (58,  36,  16, 210),
        "frame_color":      (100, 70,  30,  56),
        "quote_color":      (100, 70,  30,  20),
        "font_verse":       "playfair",
        "font_ref":         "playfair_italic",
        "is_light":         True,
    },
    "hindi": {
        "gradient_type":    "vertical",
        "gradient_start":   (10,  92,  96),
        "gradient_end":     (26,  212, 192),
        "text_color":       (255, 255, 255),
        "ref_color":        (178, 240, 235),
        "wm_color":         (255, 255, 255, 242),
        "wm_ul_color":      (255, 255, 255, 225),
        "frame_color":      (255, 255, 255,  36),
        "quote_color":      (255, 255, 255,  18),
        "font_verse":       "devanagari",
        "font_ref":         "devanagari_med",
        "is_light":         False,
    },
    "marathi": {
        "gradient_type":    "diagonal",
        "stripe_colors":    ["#87C4E8","#B8D8EE","#F0D6E8","#F2A8C8","#E07AA8","#C95C9A","#A34888"],
        "stripe_stops":     [0.00, 0.20, 0.38, 0.52, 0.68, 0.82, 1.00],
        "text_color":       (61,  10,  48),
        "ref_color":        (107, 18,  85),
        "wm_color":         (61,  10,  48, 230),
        "wm_ul_color":      (61,  10,  48, 210),
        "frame_color":      (255, 255, 255,  71),
        "quote_color":      (255, 255, 255,  28),
        "font_verse":       "devanagari",
        "font_ref":         "devanagari_med",
        "is_light":         True,
    },
    "kannada": {
        "gradient_type":    "diagonal",
        "stripe_colors":    ["#F5C842","#F9D96A","#FAE0A0","#F5A878","#EF7090","#E84D80","#D43070"],
        "stripe_stops":     [0.00, 0.18, 0.35, 0.50, 0.65, 0.82, 1.00],
        "text_color":       (74,  10,  37),
        "ref_color":        (122, 16,  64),
        "wm_color":         (74,  10,  37, 230),
        "wm_ul_color":      (74,  10,  37, 210),
        "frame_color":      (255, 255, 255,  77),
        "quote_color":      (255, 255, 255,  28),
        "font_verse":       "kannada",
        "font_ref":         "kannada",
        "is_light":         True,
    },
}

# ── Instagram ─────────────────────────────────────────────────────────────────
INSTAGRAM_ACCOUNT_ID   = os.environ.get("INSTAGRAM_ACCOUNT_ID", "")
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")

# ── Cloudinary ────────────────────────────────────────────────────────────────
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY    = os.environ.get("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "")

# ── Caption Template ──────────────────────────────────────────────────────────
CAPTION_TEMPLATE = """{verse_text}

— {reference} —

🌸 VerseBloomed | Daily Bible Verses
📖 English · Hindi · Marathi · Kannada
Follow @versebloomed_daily for daily verses

💬 Which word in this verse speaks to you today? Comment below 👇

📖 Read more on YouVersion: https://www.bible.com

{hashtags}"""

HASHTAG_SET_A = """#BibleVerse #DailyVerse #VerseBloomed #WordOfGod #Scripture
#BibleStudy #Faith #Christian #Gospel #HolyBible
#KannadaBible #HindiBible #MarathiBible #BibleInIndianLanguages
#GodIsGood #Blessed #DailyDevotional #VerseOfTheDay #Jesus
#ChristianIndia #IndianChristian"""

HASHTAG_SET_B = """#VerseBloomed #DailyInspiration #BibleQuote #FaithOverFear
#GodsPlan #TrustGod #BibleVersesDaily #Kannada #Hindi #Marathi
#Multilingual #IndianBible #ChristianContent #Devotion
#Scripture #WordOfTheLord #SpiritualGrowth #PrayerWarrior
#DailyScripture #GodLovesYou"""
