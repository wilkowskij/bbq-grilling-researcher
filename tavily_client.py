"""BBQ-tuned Tavily search.

Each topic is fanned out into four sub-queries — technique, recipe, gear/fuel,
and contrarian — and every search is restricted to the curated pitmaster
domain allowlist defined in config.BBQ_DOMAINS.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from tavily import TavilyClient

from config import BBQ_DOMAINS


SUB_QUERY_TEMPLATES = {
    "technique": "{topic} smoking technique pitmaster method temperature time",
    "recipe":    "{topic} recipe rub sauce ingredients ratios",
    "gear":      "{topic} smoker grill wood pellet charcoal fuel comparison",
    "contrarian": "{topic} myth debunked overrated controversy disagree wrong",
}


@dataclass
class Hit:
    title: str
    url: str
    content: str
    score: float
    lens: str


class BBQTavily:
    def __init__(self, api_key: str | None = None):
        key = api_key or os.environ.get("TAVILY_API_KEY")
        if not key:
            raise RuntimeError("TAVILY_API_KEY is not set")
        self.client = TavilyClient(api_key=key)

    def search(
        self,
        topic: str,
        max_per_lens: int = 4,
        exclude_domains: list[str] | None = None,
    ) -> list[Hit]:
        # Filter the allowlist instead of passing exclude_domains alongside —
        # narrower allowlist is a stronger guarantee than relying on Tavily
        # to apply both filters cleanly.
        excluded = set(exclude_domains or [])
        allowed = [d for d in BBQ_DOMAINS if d not in excluded] or BBQ_DOMAINS

        hits: list[Hit] = []
        seen_urls: set[str] = set()
        for lens, template in SUB_QUERY_TEMPLATES.items():
            q = template.format(topic=topic)
            resp = self.client.search(
                query=q,
                search_depth="advanced",
                topic="news",
                days=14,
                max_results=max_per_lens,
                include_domains=allowed,
                include_answer=False,
            )
            for r in resp.get("results", []):
                url = r.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                hits.append(Hit(
                    title=r.get("title", ""),
                    url=url,
                    content=r.get("content", ""),
                    score=float(r.get("score", 0.0)),
                    lens=lens,
                ))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits
