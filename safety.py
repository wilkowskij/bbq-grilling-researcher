"""Pre-publish safety gates.

Auto-publish mode means a bad brief reaches the page unfiltered, so every
caption runs through these checks before the Graph API is called.
"""

from __future__ import annotations

import json
import os
import pathlib
from datetime import datetime, timedelta, timezone

CAPTION_MAX = 2200
HASHTAG_MAX = 30
IG_DAILY_LIMIT = 25

# Conservative wordlist — expand as needed. These are not allowed to leak
# from a contrarian-but-classy BBQ page.
BLOCKED_TERMS = {
    "fuck", "shit", "bitch", "asshole", "cunt", "dick", "pussy",
    "nigger", "faggot", "retard",
}


class SafetyError(RuntimeError):
    pass


def check_caption(caption: str) -> None:
    if len(caption) > CAPTION_MAX:
        raise SafetyError(f"caption {len(caption)} chars > {CAPTION_MAX}")
    hashtag_count = caption.count("#")
    if hashtag_count > HASHTAG_MAX:
        raise SafetyError(f"hashtag count {hashtag_count} > {HASHTAG_MAX}")
    low = caption.lower()
    for term in BLOCKED_TERMS:
        if term in low.split() or f" {term} " in low:
            raise SafetyError(f"blocked term in caption: {term}")


def check_publish_enabled() -> None:
    if os.environ.get("PUBLISH_ENABLED", "true").lower() in ("false", "0", "no"):
        raise SafetyError("PUBLISH_ENABLED=false — publishing paused")


def check_rate_limit(ledger_path: pathlib.Path) -> None:
    if not ledger_path.exists():
        return
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    entries = json.loads(ledger_path.read_text() or "[]")
    recent = [e for e in entries if datetime.fromisoformat(e["ts"]) > cutoff]
    if len(recent) >= IG_DAILY_LIMIT:
        raise SafetyError(f"rate limit: {len(recent)} posts in last 24h >= {IG_DAILY_LIMIT}")


def record_publish(ledger_path: pathlib.Path, media_id: str, topic: str) -> None:
    entries = json.loads(ledger_path.read_text()) if ledger_path.exists() else []
    entries.append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "media_id": media_id,
        "topic": topic,
    })
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    entries = [e for e in entries if datetime.fromisoformat(e["ts"]) > cutoff]
    ledger_path.write_text(json.dumps(entries, indent=2))
