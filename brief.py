"""Contrarian BBQ brief synthesis.

The prompt forces Claude to take a side. Neutral "consider both perspectives"
briefs are rejected — pitmasters argue, and so should the brief.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from anthropic import Anthropic

from config import CONTRARIAN_LENSES
from tavily_client import Hit


MODEL = "claude-sonnet-4-6"


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
<ONE sentence stating the conventional wisdom that is wrong, naming who
teaches it (a brand, a recipe blog, a tradition). Cite [n] if you can.>

Do This Instead:
1. <specific action with a number — temp in degrees, time in minutes/hours,
   quantity in tbsp/cups/oz/lbs, or distance in inches>
2. <specific action with a number>
3. <specific action with a number>
4. <optional fourth step, only if needed>

Why It Works:
<ONE sentence. Cite the credible pitmaster, lab test, or evidence as [n].>

Sources:
[1] <url>
[2] <url>
...

Hard rules:
- Total body excluding Sources MUST be UNDER 150 words. Count them.
- VERDICT must be a single sentence, MAX 180 characters.
- The VERDICT sentence must NOT be repeated anywhere else in the brief.
- Numbered steps must each contain a concrete number (e.g. 225F, 30 min,
  1 tbsp, 1.5 inches). A step without a number is rejected.
- No "it depends." Pick a side.
- No "consider both perspectives." Take a position.
- Cite credible sources inline with [n] matching the Sources list.
- Reject sponsored-content language. If a source is selling something, say so.
"""


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


def synthesize(topic: str, hits: list[Hit], api_key: str | None = None) -> Brief:
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    if not hits:
        raise RuntimeError(f"no search hits for topic: {topic}")

    client = Anthropic(api_key=key)

    lenses = "\n".join(f"- {l}" for l in CONTRARIAN_LENSES)
    sources = _format_sources(hits)

    user_msg = f"""Topic: {topic}

Apply these contrarian lenses while reading the sources:
{lenses}

Sources (numbered for inline citation):

{sources}

Write the brief now using the exact structure from the system prompt:
VERDICT line, then "The Lie:", then "Do This Instead:" with numbered steps
containing concrete numbers, then "Why It Works:", then "Sources:".
Total body under 150 words. The VERDICT sentence must not be repeated.
"""

    resp = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    text = "".join(block.text for block in resp.content if block.type == "text")
    return Brief(topic=topic, markdown=text)
