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
- [ ] Capture target IG page handle — **NEEDED FROM USER** (paste in chat)
- [x] Account is Business/Creator + linked to a Facebook Page (user-confirmed)
- [ ] Record `IG_USER_ID` (the business account's IG ID) in `.env`
- [x] Posting cadence: **daily**, 1 topic/day from `WEEKLY_TOPICS`

## 3. Auth & credentials
- [ ] Create / reuse a Meta Developer App (type: Business)
- [ ] Add Instagram Graph API + Facebook Login products to the app
- [ ] Generate a **long-lived** Page access token (60-day) with scopes:
      `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
      `pages_read_engagement`
- [ ] Store token in `.env` as `IG_ACCESS_TOKEN`
- [ ] Add token-refresh helper (or document the manual 60-day rotation)

## 4. Brief → Instagram caption adapter (`instagram_post.py`)
- [ ] Trim brief to ≤ 2,200 chars (IG caption limit)
- [ ] Extract a punchy hook from the `VERDICT:` line as the first line
- [ ] Append a curated hashtag block (e.g. `#bbq #pitmaster #smokedmeat`)
- [ ] Strip markdown headings/links the IG renderer won't honor
- [ ] Preserve source attribution as a tail block ("Sources in comments")
- [ ] Auto-generate a first-comment payload containing the source URLs
      (URLs in captions don't render as links on IG anyway)

## 5. Image asset for the post
- [x] Strategy: **AI-generated cover per topic** via **OpenAI `gpt-image-1`**
- [ ] Add `OPENAI_API_KEY` to `.env` and `.env.example`
- [ ] Implement `image_gen.py`: topic → photoreal BBQ cover (1:1, 1080px)
- [ ] Tune the image prompt to avoid text artifacts and stock-photo look
- [ ] Upload generated image to a public HTTPS URL (IG Graph API requires a
      public URL, not a local file) — likely S3 / R2 / Supabase Storage
- [ ] TTL the upload bucket to auto-delete images > 30 days old

## 6. Publish flow (`instagram_publish.py`)
- [ ] POST `/{ig-user-id}/media` to create a media container with the image
      URL + caption
- [ ] Poll the container's `status_code` until it returns `FINISHED`
- [ ] POST `/{ig-user-id}/media_publish` with the creation ID
- [ ] Capture the returned media ID and log it
- [ ] Post the source-attribution block as the first comment via
      `/{ig-media-id}/comments`

## 7. Orchestration
- [ ] Wire `researcher.py` → `instagram_post.py` → `instagram_publish.py`
      into a single `publish_brief.py` entry point
- [ ] Add a `--preview` mode that writes the caption + image to disk
      without hitting the IG API
- [ ] Add a confirmation prompt before the live publish call

## 8. Scheduling
- [ ] Decide host (GitHub Actions cron / Railway / fly.io / cron on a VM)
- [ ] Add a **daily** scheduled workflow (1 topic/day from `WEEKLY_TOPICS`,
      round-robin by `date.today().toordinal() % len(WEEKLY_TOPICS)`)
- [ ] Add a kill-switch env var (`PUBLISH_ENABLED=false`) so the schedule
      can be paused without editing cron

## 9. Safety & quality gates (auto-publish mode)
- [x] Decision: **auto-publish on schedule** (no manual approval gate)
- [ ] Pre-publish profanity / brand-safety check on the caption
- [ ] Hard cap: refuse to publish if caption > 2,200 chars or hashtag
      count > 30 (IG limits)
- [ ] Rate-limit guard (IG: 25 API-published posts per 24h per account)
- [ ] On publish failure, write the payload to `briefs/failed/` for retry
- [ ] Optional emergency kill via `PUBLISH_ENABLED=false`

## 10. Observability
- [ ] Log every publish with media ID, topic, timestamp
- [ ] Weekly digest of what posted and what failed
- [ ] Track engagement (likes / comments / saves) per topic to feed back
      into topic selection
