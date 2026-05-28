# BBQ Grilling Researcher

A focused research agent that produces weekly briefs on BBQ, grilling, smoking
meats, and sauce/rub recipes. It pulls from a curated set of pitmaster
newsletters and blogs, runs a BBQ-tuned Tavily search strategy, and
synthesizes findings into contrarian briefs that push back on common
backyard-grilling dogma.

## What makes it BBQ-specific

1. **Curated sources** (`config.py`) — restricted to pitmaster/BBQ outlets
   instead of generic food media. Tavily is forced to `include_domains` with
   these so the corpus stays on-topic.
2. **Query strategy** (`tavily_client.py`) — every topic is expanded into
   four sub-queries: technique, recipe, gear/fuel, and contrarian/myth-busting.
   Searches use `topic="news"`, `days=14`, and `search_depth="advanced"` so
   briefs reflect what pitmasters are actually arguing about right now.
3. **Contrarian synthesis** (`brief.py`) — the LLM prompt is opinionated. It
   must identify the conventional wisdom, name who is pushing back on it, and
   take a side with a one-line verdict. Neutral "both sides" briefs are
   rejected.

## Layout

- `researcher.py` — CLI entry point. `python researcher.py "brisket bark"`
- `config.py` — newsletter/blog allowlist and topic seeds
- `tavily_client.py` — BBQ-tuned Tavily wrapper
- `brief.py` — Anthropic Claude synthesis with contrarian prompt
- `requirements.txt` — `anthropic`, `tavily-python`, `python-dotenv`

## Environment

Set `TAVILY_API_KEY` and `ANTHROPIC_API_KEY` in `.env`. The synthesis model
is configured in `brief.py` and defaults to the latest Claude Sonnet.

## Running

```bash
pip install -r requirements.txt
python researcher.py "offset smoker fuel management"
python researcher.py --weekly   # runs the default topic rotation
```
