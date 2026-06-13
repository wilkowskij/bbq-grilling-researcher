"""Contrarian BBQ brief synthesis.

The prompt forces Claude to take a side. Neutral "consider both perspectives"
briefs are rejected — pitmasters argue, and so should the brief.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from anthropic import Anthropic

from config import CONTRARIAN_LENSES, KNOWN_PITMASTER_HANDLES
from tavily_client import Hit


MODEL = "claude-sonnet-4-6"


def _load_stop_slop() -> str:
    """Read the stop-slop SKILL.md so its prose rules apply to every brief.

    Returns the SKILL.md body with YAML frontmatter stripped, or "" if the
    skill isn't installed (e.g. someone cloned the repo without running
    `npx skills add ...`). Empty string means brief synthesis still works,
    just without the extra anti-slop guidance.
    """
    skill = Path(__file__).parent / ".agents" / "skills" / "stop-slop" / "SKILL.md"
    try:
        raw = skill.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    if raw.startswith("---\n"):
        _, _, body = raw[4:].partition("---\n")
        raw = body or raw
    return raw.strip()


_STOP_SLOP = _load_stop_slop()


SYSTEM_PROMPT = """You are a contrarian BBQ research analyst writing
SAVE-WORTHY Instagram briefs for serious backyard pitmasters.

You cover four beats: BBQ technique, grilling food, smoking meats, and
sauce/rub recipes.

Every brief must read like a recipe card or how-to that a pitmaster would
screenshot and save for next weekend. Specific temps, times, quantities,
and tools. No essays. No throat-clearing.

Output EXACTLY this structure, with these exact headers and nothing else:

VERDICT: <one punchy contrarian sentence, MAX 180 characters. This is the
hook Instagram shows above the "...more" fold. It must name the dogma being
rejected and the corrective stance in a single line.>

The Lie:
<ONE sentence stating the conventional wisdom that is wrong. Refer to it
generically ("most backyard tutorials say...", "the standard recipe blog
take is..."). Do NOT name a specific person, brand, or blog here.>

Do This Instead:
1. <specific action with a number — temp in degrees, time in minutes/hours,
   quantity in tbsp/cups/oz/lbs, or distance in inches>
2. <specific action with a number>
3. <specific action with a number>
4. <optional fourth step, only if needed>

Why It Works:
<ONE sentence. Name ONE primary credible pitmaster, blog, or source — the
single most authoritative voice on this take. Cite them as [n]. This is
the ONLY place a specific source/person is named in the body.>

Sources:
[1] <url>
[2] <url>
...

Featured: <pick the slug of the ONE source named in "Why It Works" from the
KNOWN_PITMASTER_HANDLES list provided by the user. Output exactly one slug,
no @ symbol, no brackets, no quotes. If none of the listed slugs fit, output
the literal word "none".>

Hard rules:
- Total body excluding Sources/Featured MUST be UNDER 150 words. Count them.
- VERDICT must be a single sentence, MAX 180 characters.
- The VERDICT sentence must NOT be repeated anywhere else in the brief.
- Numbered steps must each contain a concrete number (e.g. 225F, 30 min,
  1 tbsp, 1.5 inches). A step without a number is rejected.
- The body must name AT MOST ONE specific source/pitmaster/brand, and only
  in "Why It Works". The Lie must stay generic.
- No "it depends." Pick a side.
- No "consider both perspectives." Take a position.
- Cite credible sources inline with [n] matching the Sources list.
- Reject sponsored-content language. If a source is selling something, say so.
"""

if _STOP_SLOP:
    SYSTEM_PROMPT += (
        "\n\nAdditionally, the brief prose must follow the stop-slop "
        "writing rules below. Pitmasters can smell AI slop from across "
        "the cookout; these rules keep the caption sounding like a "
        "human who actually cooks.\n\n"
        + _STOP_SLOP
    )


@dataclass
class Brief:
    topic: str
    markdown: str


def _format_sources(hits: list[Hit]) -> str:
    lines = []
    for i, h in enumerate(hits, 1):
        snippet = h.content.strip().replace("\n", " ")[:600]
        lines.append(f"[{i}] ({h.lens}) {h.title}\n    {h.url}\n    {snippet}")
    return "\n\n".join(lines)


def synthesize(
    topic: str,
    hits: list[Hit],
    api_key: str | None = None,
    exclude_handles: list[str] | None = None,
) -> Brief:
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    if not hits:
        raise RuntimeError(f"no search hits for topic: {topic}")

    client = Anthropic(api_key=key)

    # Source-diversity: drop any slug whose @-tag was featured in the last
    # N posts. Multiple slugs can map to the same @-tag (e.g. `meathead`
    # and `amazingribs` both resolve to @amazingribs), so we filter by the
    # value, not the key, to make sure both spellings are blocked.
    exclude_set = {h.strip().lower() for h in (exclude_handles or []) if h}
    available_handles = {
        slug: handle
        for slug, handle in KNOWN_PITMASTER_HANDLES.items()
        if handle.lower() not in exclude_set
    } or KNOWN_PITMASTER_HANDLES

    lenses = "\n".join(f"- {l}" for l in CONTRARIAN_LENSES)
    sources = _format_sources(hits)
    handles = "\n".join(f"- {k}" for k in sorted(available_handles))

    exclusion_note = ""
    if exclude_set:
        recent_list = ", ".join(sorted(exclude_set))
        exclusion_note = (
            f"\n\nSource diversity rule (HARD): the following pitmaster "
            f"handles were featured in the last 7 posts and MUST NOT be "
            f"cited in this brief: {recent_list}. Pick a different voice "
            f"for 'Why It Works'. The slug list above already excludes "
            f"them; do not work around the exclusion.\n"
        )

    user_msg = f"""Topic: {topic}

Apply these contrarian lenses while reading the sources:
{lenses}

Sources (numbered for inline citation):

{sources}

KNOWN_PITMASTER_HANDLES (use ONE slug for the Featured line, or "none"):
{handles}
{exclusion_note}
Write the brief now using the exact structure from the system prompt:
VERDICT, "The Lie:" (generic, no names), "Do This Instead:" (numbered
steps with concrete numbers), "Why It Works:" (name ONE source/pitmaster,
cite [n]), "Sources:", then "Featured: <slug>".
Total body under 150 words. The VERDICT sentence must not be repeated.
At most one specific source/pitmaster named in the entire body.
"""

    resp = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    text = "".join(block.text for block in resp.content if block.type == "text")
    return Brief(topic=topic, markdown=text)
