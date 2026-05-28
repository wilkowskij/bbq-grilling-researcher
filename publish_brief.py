"""End-to-end: pick today's topic -> research -> caption -> image -> publish.

Topic rotation is deterministic by date so the same date always picks the
same topic (cron-safe across retries).
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from dataclasses import asdict
from datetime import date

from dotenv import load_dotenv

from brief import synthesize
from config import WEEKLY_TOPICS
from image_gen import generate as generate_image
from instagram_caption import build_post
from instagram_publish import InstagramPublisher
from safety import (
    check_caption,
    check_publish_enabled,
    check_rate_limit,
    record_publish,
)
from tavily_client import BBQTavily


LEDGER = pathlib.Path(".publish_ledger.json")
BRIEFS_DIR = pathlib.Path("briefs")
IMAGES_DIR = pathlib.Path("generated_images")
FAILED_DIR = pathlib.Path("briefs/failed")


def topic_for(day: date) -> str:
    return WEEKLY_TOPICS[day.toordinal() % len(WEEKLY_TOPICS)]


def upload_to_public_url(image_path: pathlib.Path) -> str:
    """Upload the image to a public HTTPS URL.

    The Graph API can't read local files. Wire this to your bucket of
    choice (S3 / R2 / Supabase Storage) and return the public URL.
    """
    env_url = os.environ.get("IMAGE_PUBLIC_URL_TEMPLATE")
    if env_url:
        return env_url.format(filename=image_path.name)
    raise RuntimeError(
        "No image host configured. Set IMAGE_PUBLIC_URL_TEMPLATE "
        "(e.g. https://cdn.example.com/bbq/{filename}) and upload the "
        "file there, or replace upload_to_public_url() with a real "
        "uploader."
    )


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Publish today's BBQ brief to Instagram")
    parser.add_argument("--topic", help="override today's topic")
    parser.add_argument("--date", help="ISO date for topic rotation (default: today)")
    parser.add_argument("--preview", action="store_true",
                        help="generate everything but skip the IG publish")
    args = parser.parse_args()

    target_day = date.fromisoformat(args.date) if args.date else date.today()
    topic = args.topic or topic_for(target_day)
    print(f"[*] topic for {target_day.isoformat()}: {topic}", file=sys.stderr)

    if not args.preview:
        check_publish_enabled()
        check_rate_limit(LEDGER)

    tavily = BBQTavily()
    hits = tavily.search(topic)
    print(f"    {len(hits)} hits", file=sys.stderr)

    brief = synthesize(topic, hits)
    BRIEFS_DIR.mkdir(parents=True, exist_ok=True)
    brief_path = BRIEFS_DIR / f"{target_day.isoformat()}-{topic.replace(' ', '-')}.md"
    brief_path.write_text(brief.markdown)

    post = build_post(topic, brief.markdown)
    check_caption(post.caption)

    img = generate_image(topic, IMAGES_DIR)
    print(f"    image: {img.path} ({img.bytes_len} bytes)", file=sys.stderr)

    if args.preview:
        print("--- caption ---")
        print(post.caption)
        print("--- first comment ---")
        print(post.first_comment)
        return 0

    image_url = upload_to_public_url(img.path)
    publisher = InstagramPublisher()
    try:
        result = publisher.publish(image_url, post.caption, post.first_comment)
    except Exception as e:
        FAILED_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "topic": topic,
            "date": target_day.isoformat(),
            "caption": post.caption,
            "first_comment": post.first_comment,
            "image_url": image_url,
            "error": str(e),
        }
        (FAILED_DIR / f"{target_day.isoformat()}-{topic.replace(' ', '-')}.json").write_text(
            json.dumps(payload, indent=2)
        )
        raise

    record_publish(LEDGER, result.media_id, topic)
    print(f"[+] published media_id={result.media_id} comment_id={result.comment_id}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
