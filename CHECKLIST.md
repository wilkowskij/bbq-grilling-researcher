# BBQ Researcher → Instagram Pipeline Checklist

Working checklist for wiring the researcher's contrarian briefs into a
specific Instagram page. Update statuses as items complete: `[ ]` open,
`[~]` in progress, `[x]` done, `[!]` blocked.

## 1. Research engine (foundation)
- [x] Curated pitmaster domain allowlist (`config.py`)
- [x] Fan-out Tavily query strategy (technique / recipe / gear / contrarian)
- [x] Contrarian synthesis prompt (`brief.py`)
- [x] CLI with `--weekly` topic rotation (`researcher.py`)
- [ ] Persist hits as JSON alongside the markdown brief (for replay/debug)
- [ ] Add a `--dry-run` flag that prints sources without calling Claude

## 2. Instagram target configuration
- [x] Target IG page handle: **@jerseysmokebbq**
- [x] Account is Business/Creator + linked to a Facebook Page (user-confirmed)
- [ ] Record `IG_USER_ID` (the business account's IG ID) in `.env` — pulled
      from the Meta app once §3 is done
- [x] Posting cadence: **daily**, 1 topic/day from `WEEKLY_TOPICS`

## 3. Auth & credentials — **PIVOTED to Instagram Business Login**
- [x] Old Facebook-Login + Page-token path abandoned (Meta UI permission
      wall couldn't be cleared)
- [x] Refactored to Instagram Business Login flow:
      - `instagram_publish.py` now hits `graph.instagram.com` (not `.facebook.com`)
      - Token is IG User token (`IGAA…`), not FB Page token (`EAA…`)
      - Permissions: `instagram_business_basic`, `instagram_business_content_publish`
- [x] `mint_ig_token.py` helper: walks the user through IG OAuth, prints
      long-lived token + IG user id ready to paste into GitHub secrets
- [x] `SETUP_IG.md` rewritten for the new flow
- [ ] **User TODO**: enable Instagram Business Login + add `https://localhost/`
      redirect URI in Meta app (use case section 4)
- [ ] **User TODO**: run `mint_ig_token.py` locally → save tokens to
      GitHub secrets
- [ ] Token-refresh helper (60-day rotation) — deferred until v2

## 4. Brief → Instagram caption adapter (`instagram_caption.py`)
- [x] Caption built and capped at 2,200 chars (`build_post`)
- [x] VERDICT line extracted as the opening hook (multi-line aware)
- [x] Curated brand + topic-aware hashtag block (≤ 30 tags)
- [x] Markdown headings/links/bold stripped
- [x] "Sources in the comments ↓" tail block
- [x] First-comment payload with source URLs
- [x] Smoke test passes (`test_caption.py`)

## 5. Image asset for the post (`image_gen.py`)
- [x] Strategy: AI-generated cover per topic via OpenAI `gpt-image-1`
- [x] `OPENAI_API_KEY` added to `.env.example`
- [x] `image_gen.generate()`: topic → 1024x1024 photoreal cover
- [x] Prompt tuned: no text/logos/faces, real pitmaster look (not stock)
- [x] Supabase project provisioned: **jerseysmokebbq**
      (`tewmbnlldtavuqzaolve`, us-east-1, free tier)
- [x] Public bucket **bbq-covers** created (5 MB cap, png/jpeg/webp)
- [x] `image_host.upload()` wired in via `publish_brief.upload_to_public_url`
- [x] GitHub Actions secrets set: `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`
- [ ] TTL bucket to auto-delete images > 30 days (cron via Edge Function)

## 6. Publish flow (`instagram_publish.py`)
- [x] `_create_container` → POST `/{ig-user-id}/media`
- [x] `_wait_finished` polls `status_code` until `FINISHED` (90s timeout)
- [x] `_publish` → POST `/{ig-user-id}/media_publish`
- [x] `_comment` posts the source block as first comment
- [ ] Live-fire test against the real IG account (blocked on §3 token)

## 7. Orchestration (`publish_brief.py`)
- [x] Single entry point: research → caption → image → publish
- [x] `--preview` flag: generates everything, skips IG publish
- [x] Deterministic daily topic rotation (`topic_for(date)`)
- [x] Failed-publish payloads saved to `briefs/failed/<date>-<topic>.json`

## 8. Scheduling
- [x] Host: GitHub Actions cron (`.github/workflows/daily-publish.yml`)
- [x] Daily run at 14:30 UTC (10:30 AM ET)
- [x] `workflow_dispatch` for manual runs
- [x] `PUBLISH_ENABLED` repo variable as kill-switch
- [x] Repo secrets: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- [ ] **User TODO**: remaining repo secrets — `TAVILY_API_KEY`,
      `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `IG_USER_ID`,
      `IG_ACCESS_TOKEN`

## 9. Safety & quality gates (auto-publish mode)
- [x] Decision: auto-publish on schedule (no manual approval gate)
- [x] Profanity / brand-safety wordlist check (`safety.check_caption`)
- [x] Hard cap on caption length (2,200) and hashtag count (30)
- [x] Rate-limit guard via local ledger (25 posts/24h)
- [x] On publish failure, payload written to `briefs/failed/`
- [x] `PUBLISH_ENABLED=false` emergency kill

## 10. Observability
- [x] Every publish recorded in `.publish_ledger.json` (media id, topic, ts)
- [ ] Weekly digest of what posted and what failed
- [ ] Pull engagement (likes / comments / saves) per topic via Graph API
      Insights and feed back into topic selection
