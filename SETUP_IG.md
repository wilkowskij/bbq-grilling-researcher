# Instagram Setup for @jerseysmokebbq

Uses **Instagram Business Login** (the newer Meta auth flow) — NOT Facebook
Login + Page tokens. This path avoids the FB-Page-to-IG connection mess.

## 1. Account requirements
- IG account is **Business** or **Creator** (Settings → Account → Switch
  account type). Already confirmed.
- IG account does NOT need to be linked to a Facebook Page for this flow.

## 2. Meta app — already created
- App: **JerseySmokeBBQ** (App ID `1832946314333428`)
- Use case enabled: **Manage messaging & content on Instagram**

## 3. Enable Instagram Business Login + redirect URI
1. Go to https://developers.facebook.com/apps/1832946314333428/use_cases
2. Tap the pencil ✏️ next to **Manage messaging & content on Instagram**
3. Find section **"4. Set up Instagram business login"** → tap **Set up**
4. In the OAuth settings:
   - **Valid OAuth Redirect URIs**: add `https://localhost/`
   - (Optional) Deauthorize callback URL: leave blank
   - (Optional) Data deletion request URL: leave blank
5. Save

## 4. Grant permissions in the use case
In the same "Manage messaging & content on Instagram" customize page,
section 1 (Add required permissions) — verify these are added:
- `instagram_business_basic` ✓ (added automatically)
- `instagram_business_content_publish` ← add if missing
- `instagram_business_manage_comments` ← add if you want auto-comments
- `instagram_business_manage_messages` (optional)

## 5. Mint the long-lived Instagram User token
Run the helper script locally (not in a server) since it walks you through
a browser OAuth flow:

```bash
git pull
pip install -r requirements.txt
export META_APP_ID=1832946314333428
export META_APP_SECRET=...     # App settings → Basic → Show
python mint_ig_token.py
```

The script prints:
1. An authorization URL — open it in your browser
2. You log in to **@jerseysmokebbq** on Instagram
3. Approve the scopes
4. Instagram redirects to `https://localhost/?code=XXXX` (page won't load,
   that's fine — copy the `code` value from the URL bar)
5. Paste it back into the script
6. Script exchanges short-lived → long-lived token and prints:
   ```
   IG_ACCESS_TOKEN = IGAA...
   IG_USER_ID      = 17841...
   ```

## 6. Save to GitHub Actions secrets
Repo → Settings → Secrets and variables → Actions → update both:
- `IG_ACCESS_TOKEN` — the `IGAA…` token (long-lived, 60-day life)
- `IG_USER_ID` — the `17841…` number

## 7. Token refresh (every 60 days)
The long-lived IG token expires after 60 days but can be refreshed without
re-doing the OAuth flow:

```
GET https://graph.instagram.com/refresh_access_token
  ?grant_type=ig_refresh_token
  &access_token={current_token}
```

For now: re-run `mint_ig_token.py` whenever the token nears expiry.
(Future: add a `refresh_ig_token.py` script + a monthly cron.)

## 8. Supabase image hosting (already provisioned)
A `jerseysmokebbq` Supabase project (ref `tewmbnlldtavuqzaolve`,
us-east-1) with a public `bbq-covers` bucket already exists. The
service-role key is in `SUPABASE_SERVICE_ROLE_KEY`.

## 9. Verify with a preview run
Actions → Daily IG publish → Run workflow → leave Preview checked → Run.
The Publish step output ends with a preview URL — open it to see the post
mocked up.

## 10. First live publish
Actions → Daily IG publish → Run workflow → **uncheck Preview** → Run.
Watch for `[+] published media_id=…` in the logs.

## 11. Daily cron via cron-job.org
- cron-job.org POSTs to:
  `https://api.github.com/repos/wilkowskij/bbq-grilling-researcher/actions/workflows/daily-publish.yml/dispatches`
- Headers: `Authorization: Bearer {fine-grained-PAT}`,
  `Accept: application/vnd.github+json`,
  `X-GitHub-Api-Version: 2022-11-28`
- Body: `{"ref":"main","inputs":{"preview":"false"}}`
- Schedule: whenever you want it to fire daily
