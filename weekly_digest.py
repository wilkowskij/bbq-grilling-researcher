"""Weekly performance digest written to $GITHUB_STEP_SUMMARY.

For each post snapshotted in the last 30 days, computes save_rate
(saved / reach) — the metric to optimize when the goal is bookmark-worthy
content — and surfaces the top 5 and bottom 3 posts.

Phase 1 is read-only: it does not change the prompt or topic rotation.
You eyeball the digest and decide what to tweak.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

from insights_db import latest_insights_by_post


def _safe(num) -> int:
    return int(num) if num is not None else 0


def _save_rate(row: dict) -> float:
    reach = _safe(row.get("reach"))
    saved = _safe(row.get("saved"))
    return (saved / reach) if reach > 0 else 0.0


def _age_days(posted_at: str) -> float:
    dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0


def main() -> int:
    rows = latest_insights_by_post()
    if not rows:
        print("no insights yet — nothing to digest", file=sys.stderr)
        return 0

    annotated = []
    for r in rows:
        post = r.get("post") or {}
        if not post.get("posted_at"):
            continue
        annotated.append({
            "media_id": r["media_id"],
            "topic": post.get("topic", "?"),
            "style_tag": post.get("style_tag", "?"),
            "featured": post.get("featured_handle") or "—",
            "age_days": _age_days(post["posted_at"]),
            "reach": _safe(r.get("reach")),
            "saved": _safe(r.get("saved")),
            "likes": _safe(r.get("likes")),
            "comments": _safe(r.get("comments")),
            "shares": _safe(r.get("shares")),
            "save_rate": _save_rate(r),
        })

    if not annotated:
        print("no annotated rows", file=sys.stderr)
        return 0

    by_save_rate = sorted(annotated, key=lambda x: x["save_rate"], reverse=True)
    by_reach = sorted(annotated, key=lambda x: x["reach"], reverse=True)

    style_buckets: dict[str, list[float]] = {}
    for r in annotated:
        style_buckets.setdefault(r["style_tag"], []).append(r["save_rate"])
    style_summary = sorted(
        ((s, sum(rates) / len(rates), len(rates)) for s, rates in style_buckets.items()),
        key=lambda x: x[1],
        reverse=True,
    )

    lines = []
    lines.append("## BBQ post performance digest\n")
    lines.append(f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
                 f"Window: latest insights snapshot per post (up to 30 days back). "
                 f"Posts in window: **{len(annotated)}**.\n")

    lines.append("### Save rate by style\n")
    lines.append("| Style | Avg save rate | Posts |")
    lines.append("| --- | ---: | ---: |")
    for style, avg, n in style_summary:
        lines.append(f"| `{style}` | {avg:.2%} | {n} |")
    lines.append("")

    lines.append("### Top 5 by save rate\n")
    lines.append("| Topic | Style | Age | Reach | Saved | Save rate | Featured |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | --- |")
    for r in by_save_rate[:5]:
        lines.append(
            f"| {r['topic'][:48]} | `{r['style_tag']}` | {r['age_days']:.1f}d | "
            f"{r['reach']} | {r['saved']} | **{r['save_rate']:.2%}** | {r['featured']} |"
        )
    lines.append("")

    lines.append("### Top 5 by reach\n")
    lines.append("| Topic | Style | Age | Reach | Likes | Comments | Saved |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for r in by_reach[:5]:
        lines.append(
            f"| {r['topic'][:48]} | `{r['style_tag']}` | {r['age_days']:.1f}d | "
            f"**{r['reach']}** | {r['likes']} | {r['comments']} | {r['saved']} |"
        )
    lines.append("")

    if len(annotated) >= 5:
        lines.append("### Bottom 3 by save rate (worth re-thinking)\n")
        lines.append("| Topic | Style | Age | Reach | Saved | Save rate |")
        lines.append("| --- | --- | ---: | ---: | ---: | ---: |")
        for r in by_save_rate[-3:]:
            lines.append(
                f"| {r['topic'][:48]} | `{r['style_tag']}` | {r['age_days']:.1f}d | "
                f"{r['reach']} | {r['saved']} | {r['save_rate']:.2%} |"
            )
        lines.append("")

    summary = "\n".join(lines)
    print(summary)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
