"""Render a single-file HTML mock of the IG post for visual review.

Outputs a self-contained page that references the already-uploaded
Supabase image URL and lays out the caption + first comment in a
phone-shaped IG-style frame. Uploaded to the same bucket so reviewing
is one click.
"""

from __future__ import annotations

import html


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>IG preview · {topic}</title>
<style>
  body {{ background:#0f1115; color:#e8e8e8; font:15px/1.45 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif; margin:0; padding:40px 20px; }}
  .meta {{ max-width:520px; margin:0 auto 16px; color:#9aa0a6; font-size:13px; }}
  .meta a {{ color:#7cb7ff; text-decoration:none; word-break:break-all; }}
  .post {{ max-width:520px; margin:0 auto; background:#16181d; border:1px solid #2a2d34; border-radius:14px; overflow:hidden; }}
  .head {{ display:flex; align-items:center; padding:12px 14px; gap:10px; border-bottom:1px solid #2a2d34; }}
  .avatar {{ width:34px; height:34px; border-radius:50%; background:linear-gradient(135deg,#ff7a18,#af002d 60%,#319197); }}
  .handle {{ font-weight:600; }}
  .img {{ display:block; width:100%; aspect-ratio:1/1; object-fit:cover; background:#000; }}
  .actions {{ padding:10px 14px 4px; font-size:18px; color:#e8e8e8; }}
  .caption {{ padding:8px 14px 14px; white-space:pre-wrap; word-wrap:break-word; }}
  .caption .handle {{ font-weight:600; margin-right:6px; }}
  .comment {{ padding:10px 14px 16px; border-top:1px solid #2a2d34; color:#cfd2d6; }}
  .comment .label {{ font-size:11px; letter-spacing:.06em; text-transform:uppercase; color:#9aa0a6; margin-bottom:6px; }}
  .comment pre {{ margin:0; white-space:pre-wrap; word-wrap:break-word; font:inherit; }}
  .stats {{ max-width:520px; margin:14px auto 0; color:#9aa0a6; font-size:12px; display:flex; gap:18px; }}
</style>
</head>
<body>
  <div class="meta">
    <div><strong>Preview</strong> · {topic} · generated {date}</div>
    <div>image: <a href="{image_url}">{image_url}</a></div>
  </div>
  <div class="post">
    <div class="head">
      <div class="avatar"></div>
      <div class="handle">jerseysmokebbq</div>
    </div>
    <img class="img" src="{image_url}" alt="">
    <div class="actions">♡  💬  ⤴</div>
    <div class="caption"><span class="handle">jerseysmokebbq</span>{caption}</div>
    <div class="comment">
      <div class="label">First comment (auto-posted)</div>
      <pre>{first_comment}</pre>
    </div>
  </div>
  <div class="stats">
    <span>caption length: {caption_len} / 2200</span>
    <span>hashtags: {hashtag_count} / 30</span>
  </div>
</body>
</html>
"""


def render(*, topic: str, date: str, image_url: str, caption: str, first_comment: str) -> str:
    return TEMPLATE.format(
        topic=html.escape(topic),
        date=html.escape(date),
        image_url=html.escape(image_url),
        caption=html.escape(caption),
        first_comment=html.escape(first_comment),
        caption_len=len(caption),
        hashtag_count=caption.count("#"),
    )
