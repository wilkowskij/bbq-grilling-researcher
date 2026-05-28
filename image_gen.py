"""OpenAI gpt-image-1 cover generator for IG posts.

Produces a 1080x1080 photoreal BBQ shot per topic. The prompt is tuned to
avoid text artifacts (IG flags AI-generated text), stock-photo lighting,
and the "perfect studio brisket" look that screams marketing.
"""

from __future__ import annotations

import base64
import os
import pathlib
from dataclasses import dataclass

from openai import OpenAI


MODEL = "gpt-image-1"
SIZE = "1024x1024"  # IG renders 1:1 cleanly; closest gpt-image-1 square size

PROMPT_TEMPLATE = """A close-up, gritty, photoreal hero shot for a backyard
BBQ Instagram post about: {topic}.

Style: natural daylight or warm pit-side lighting, shallow depth of field,
visible smoke, real-looking char and bark, slightly imperfect plating —
like a serious pitmaster's phone photo, not a stock food-styling shoot.
Composition: tight crop, the food fills the frame.

Hard constraints: no text, no logos, no watermarks, no overlay graphics,
no human faces, no hands holding utensils.
"""


@dataclass
class GeneratedImage:
    topic: str
    path: pathlib.Path
    bytes_len: int


def generate(topic: str, out_dir: pathlib.Path, api_key: str | None = None) -> GeneratedImage:
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=key)
    prompt = PROMPT_TEMPLATE.format(topic=topic)

    resp = client.images.generate(
        model=MODEL,
        prompt=prompt,
        size=SIZE,
        n=1,
    )

    b64 = resp.data[0].b64_json
    img_bytes = base64.b64decode(b64)

    out_dir.mkdir(parents=True, exist_ok=True)
    slug = topic.lower().replace(" ", "-").replace("/", "-")
    path = out_dir / f"{slug}.png"
    path.write_bytes(img_bytes)

    return GeneratedImage(topic=topic, path=path, bytes_len=len(img_bytes))
