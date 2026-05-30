"""Brief markdown -> Instagram caption + first-comment payload.

The caption opens with the VERDICT line as a hook (IG truncates after the
first ~125 chars in feed), drops markdown the IG renderer ignores, appends a
curated hashtag block, and emits the source attribution as a separate
first-comment payload (URLs in IG captions aren't clickable anyway).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from config import KNOWN_PITMASTER_HANDLES

CAPTION_MAX = 2200
HASHTAG_MAX = 30

BASE_HASHTAGS = [
    "#bbq", "#barbecue", "#pitmaster", "#smokedmeat", "#lowandslow",
    "#grilling", "#bbqlife", "#smokerporn", "#meatlover", "#bbqnation",
    "#jerseysmokebbq", "#njbbq",
]

TOPIC_HASHTAGS = {
    "brisket":   ["#brisket", "#texasbbq", "#bark"],
    "pork":      ["#pulledpork", "#porkshoulder", "#boston_butt"],
    "rib":       ["#ribs", "#porkribs", "#3-2-1"],
    "sauce":     ["#bbqsauce", "#saucerecipe"],
    "wood":      ["#woodfired", "#hickory", "#postoak"],
    "pellet":    ["#pelletsmoker", "#traeger"],
    "offset":    ["#offsetsmoker", "#stickburner"],
    "carolina":  ["#carolinabbq", "#vinegarsauce"],
    "alabama":   ["#alabamawhitesauce"],
    "texas":     ["#texasbbq", "#centraltexasbbq"],
    "tri-tip":   ["#tritip", "#santamaria"],
    "sausage":   ["#hotguts", "#sausage"],
    "steak":     ["#reversesear", "#steak"],
}


@dataclass
class IGPost:
    caption: str
    first_comment: str
    hashtags: list[str]


def _strip_markdown(text: str) -> str:
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"^\s*[-*]\s+", "• ", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_verdict(brief_md: str) -> str:
    # Match VERDICT label, then capture until a blank line or next heading.
    m = re.search(
        r"VERDICT[:\s]*\n*(.+?)(?:\n\s*\n|\n#{1,6}\s|\Z)",
        brief_md,
        flags=re.I | re.S,
    )
    if not m:
        return ""
    verdict = re.sub(r"\s+", " ", m.group(1)).strip()
    return verdict.rstrip(".") + "."


def _extract_source_urls(brief_md: str) -> list[str]:
    return re.findall(r"https?://\S+", brief_md)


def _pick_hashtags(topic: str) -> list[str]:
    tags = list(BASE_HASHTAGS)
    low = topic.lower()
    for key, extra in TOPIC_HASHTAGS.items():
        if key in low:
            for t in extra:
                if t not in tags:
                    tags.append(t)
    return tags[:HASHTAG_MAX]


SAVE_CTA = "Save this for your next cook ↓"


def _strip_verdict_block(body: str) -> str:
    return re.sub(
        r"(?im)^\s*VERDICT[:\s].*?(?:\n\s*\n|\Z)",
        "",
        body,
        count=1,
    ).strip()


def _extract_featured_handle(brief_md: str) -> str:
    m = re.search(r"(?im)^\s*Featured:\s*([@\w.-]+)\s*$", brief_md)
    if not m:
        return ""
    raw = m.group(1).strip().lower().lstrip("@")
    if not raw or raw == "none":
        return ""
    return KNOWN_PITMASTER_HANDLES.get(raw, "")


def _strip_featured_line(body: str) -> str:
    return re.sub(r"(?im)^\s*Featured:.*$\n?", "", body).strip()


def build_post(topic: str, brief_md: str) -> IGPost:
    verdict = _extract_verdict(brief_md)
    featured = _extract_featured_handle(brief_md)
    body = _strip_markdown(brief_md)
    body = re.split(r"\n\s*Sources:?\s*\n", body, maxsplit=1)[0].strip()
    body = _strip_verdict_block(body)
    body = _strip_featured_line(body)

    hashtags = _pick_hashtags(topic)
    tag_line = " ".join(hashtags)
    feature_line = f"Featuring {featured}\n\n" if featured else ""

    hook = verdict or f"Hot take on {topic}."
    caption = f"{hook}\n\n{body}\n\n{SAVE_CTA}\n\n{feature_line}{tag_line}"

    if len(caption) > CAPTION_MAX:
        budget = CAPTION_MAX - (len(hook) + len(SAVE_CTA) + len(feature_line) + len(tag_line) + 8)
        truncated = body[: max(0, budget)].rsplit(" ", 1)[0] + "…"
        caption = f"{hook}\n\n{truncated}\n\n{SAVE_CTA}\n\n{feature_line}{tag_line}"

    urls = _extract_source_urls(brief_md)
    if urls:
        first_comment = "Sources:\n" + "\n".join(f"• {u}" for u in urls[:10])
    else:
        first_comment = "Sources available on request."

    return IGPost(caption=caption, first_comment=first_comment, hashtags=hashtags)
