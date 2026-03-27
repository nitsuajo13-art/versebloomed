# post_instagram.py — Upload images to Cloudinary and post carousel to Instagram

import requests
import cloudinary
import cloudinary.uploader
import os
import sys
import glob
import pandas as pd
from datetime import datetime
from config import (
    INSTAGRAM_ACCOUNT_ID, INSTAGRAM_ACCESS_TOKEN,
    CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET,
    CAPTION_TEMPLATE, HASHTAG_SET_A, HASHTAG_SET_B,
    OUTPUT_DIR, CSV_PATH
)

# ── Configure Cloudinary ──────────────────────────────────────────────────────
cloudinary.config(
    cloud_name = CLOUDINARY_CLOUD_NAME,
    api_key    = CLOUDINARY_API_KEY,
    api_secret = CLOUDINARY_API_SECRET,
    secure     = True
)

BASE_URL = f"https://graph.facebook.com/v18.0/{INSTAGRAM_ACCOUNT_ID}"


# ── Upload to Cloudinary ──────────────────────────────────────────────────────

def upload_to_cloudinary(image_path, public_id):
    """Upload image to Cloudinary and return public URL."""
    try:
        result = cloudinary.uploader.upload(
            image_path,
            public_id=public_id,
            overwrite=True,
            resource_type="image"
        )
        url = result.get("secure_url")
        print(f"  ☁️  Uploaded to Cloudinary: {url}")
        return url
    except Exception as e:
        print(f"  ❌ Cloudinary upload failed: {e}")
        return None


# ── Instagram Carousel Upload ─────────────────────────────────────────────────

def upload_carousel_item(image_url):
    """Upload single image to Instagram as carousel item."""
    url    = f"{BASE_URL}/media"
    params = {
        "image_url":        image_url,
        "is_carousel_item": True,
        "access_token":     INSTAGRAM_ACCESS_TOKEN,
    }
    resp = requests.post(url, data=params)
    data = resp.json()
    if "id" in data:
        print(f"  📸 IG item uploaded: {data['id']}")
        return data["id"]
    else:
        print(f"  ❌ IG item upload failed: {data}")
        return None


def create_carousel_container(children_ids, caption):
    """Create Instagram carousel container."""
    url    = f"{BASE_URL}/media"
    params = {
        "media_type":   "CAROUSEL",
        "children":     ",".join(children_ids),
        "caption":      caption,
        "access_token": INSTAGRAM_ACCESS_TOKEN,
    }
    resp = requests.post(url, data=params)
    data = resp.json()
    if "id" in data:
        print(f"  📦 Carousel container: {data['id']}")
        return data["id"]
    else:
        print(f"  ❌ Carousel creation failed: {data}")
        return None


def publish_carousel(container_id):
    """Publish Instagram carousel."""
    url    = f"{BASE_URL}/media_publish"
    params = {
        "creation_id":  container_id,
        "access_token": INSTAGRAM_ACCESS_TOKEN,
    }
    resp = requests.post(url, data=params)
    data = resp.json()
    if "id" in data:
        print(f"  🎉 Published! Post ID: {data['id']}")
        return data["id"]
    else:
        print(f"  ❌ Publish failed: {data}")
        return None


# ── Build Caption ─────────────────────────────────────────────────────────────

def build_caption(english_verse, english_ref, run_number):
    """Build post caption with rotating hashtags."""
    hashtags = HASHTAG_SET_A if run_number % 2 == 0 else HASHTAG_SET_B
    return CAPTION_TEMPLATE.format(
        verse_text=english_verse,
        reference=english_ref,
        hashtags=hashtags
    )


# ── Main Post Function ────────────────────────────────────────────────────────

def post_carousel(session, verse_row):
    """Full pipeline: upload images → post carousel to Instagram."""
    date_str    = datetime.now().strftime("%Y-%m-%d")
    folder      = os.path.join(OUTPUT_DIR, f"{date_str}_{session}")
    lang_order  = ["english", "hindi", "marathi", "kannada"]

    print(f"\n📸 Uploading {session} carousel to Instagram...\n")

    # Step 1 — Upload each slide to Cloudinary
    public_urls = []
    for lang in lang_order:
        img_path  = os.path.join(folder, f"slide_{lang}.png")
        public_id = f"versebloomed/{date_str}_{session}_{lang}"
        url       = upload_to_cloudinary(img_path, public_id)
        if url:
            public_urls.append(url)
        else:
            print(f"❌ Failed to upload {lang} slide. Aborting post.")
            return False

    # Step 2 — Upload each image to Instagram as carousel item
    children_ids = []
    for url in public_urls:
        item_id = upload_carousel_item(url)
        if item_id:
            children_ids.append(item_id)
        else:
            print("❌ Failed to create Instagram carousel item. Aborting.")
            return False

    # Step 3 — Build caption
    run_number = int(datetime.now().strftime("%j"))  # Day of year for rotation
    caption    = build_caption(
        verse_row.get("english_verse", ""),
        verse_row.get("english_ref", ""),
        run_number
    )

    # Step 4 — Create carousel container
    container_id = create_carousel_container(children_ids, caption)
    if not container_id:
        return False

    # Step 5 — Publish
    post_id = publish_carousel(container_id)
    return post_id is not None


if __name__ == "__main__":
    session = sys.argv[1] if len(sys.argv) > 1 else "morning"

    # Get last used verse for caption
    try:
        df       = pd.read_csv(CSV_PATH)
        last_row = df[df["used"] == True].iloc[-1].to_dict()
    except:
        last_row = {"english_verse": "", "english_ref": ""}

    success = post_carousel(session, last_row)
    if success:
        print("\n✅ Instagram post published successfully!")
    else:
        print("\n❌ Instagram post failed — images saved locally for manual posting.")
