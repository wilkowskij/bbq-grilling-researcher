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


SYSTEM_PROMPT = """You are a contrarian BBQ research analyst writing weekly
briefs for serious backyard pitmasters and competition cooks.

You cover four beats: BBQ technique, grilling food, smoking meats, and
sauce/rub recipes.

Your briefs are OPINIONATED. For every topic you MUST:

1. State the conventional wisdom in one sentence.
2. Name a credible pitmaster, source, or piece of evidence that pushes back
   on it.
3. Take a side with a one-line verdict labeled "VERDICT:".
4. Give the reader two concrete things they can change at the grill this
   weekend.

Hard rules:
- No "it depends" verdicts. Pick a side. If the evidence is genuinely thin,
  say "the dogma is unfounded" and explain why.
- Cite sources inline with [n] referencing the numbered list at the end.
- Reject sponsored-content language. If a source is selling something, note it.
- Keep the brief under 400 words.
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

Write the brief now. Markdown. Sections: **Conventional wisdom**, **The
pushback**, **VERDICT**, **Try this weekend**, **Sources**.
"""

    resp = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    text = "".join(block.text for block in resp.content if block.type == "text")
    return Brief(topic=topic, markdown=text)
