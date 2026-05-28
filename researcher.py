"""BBQ Grilling Researcher — CLI entry point.

Usage:
    python researcher.py "brisket bark"
    python researcher.py --weekly
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
from datetime import date

from dotenv import load_dotenv

from brief import synthesize
from config import WEEKLY_TOPICS
from tavily_client import BBQTavily


def run_topic(topic: str, tavily: BBQTavily, out_dir: pathlib.Path) -> pathlib.Path:
    print(f"[*] researching: {topic}", file=sys.stderr)
    hits = tavily.search(topic)
    print(f"    {len(hits)} hits across pitmaster sources", file=sys.stderr)
    brief = synthesize(topic, hits)

    slug = topic.lower().replace(" ", "-").replace("/", "-")
    path = out_dir / f"{date.today().isoformat()}-{slug}.md"
    path.write_text(f"# {topic}\n\n{brief.markdown}\n")
    print(f"    wrote {path}", file=sys.stderr)
    return path


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="BBQ grilling researcher")
    parser.add_argument("topic", nargs="?", help="research topic")
    parser.add_argument("--weekly", action="store_true",
                        help="run the default rotation of BBQ topics")
    parser.add_argument("--out", default="briefs", help="output directory")
    args = parser.parse_args()

    if not args.topic and not args.weekly:
        parser.error("provide a topic or pass --weekly")

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    tavily = BBQTavily()
    topics = WEEKLY_TOPICS if args.weekly else [args.topic]

    for t in topics:
        try:
            run_topic(t, tavily, out_dir)
        except Exception as e:
            print(f"    !! failed {t}: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
