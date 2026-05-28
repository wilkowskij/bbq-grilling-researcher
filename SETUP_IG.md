# Instagram Setup for @jerseysmokebbq

One-time manual setup before the daily publisher can run. The Graph API
side has to be done by hand in Meta's UI — there's no programmatic path
for app creation or token issuance.

## 1. Confirm account shape
- Instagram account is **Business** or **Creator** (Settings → Account →
  Switch account type). You confirmed this is already done.
- The IG account is linked to a Facebook Page you admin.

## 2. Create a Meta Developer App
1. Go to https://developers.facebook.com/apps and click **Create App**.
2. Use case: **Other** → App type: **Business**.
3. Name it `jerseysmokebbq-publisher`.

## 3. Add products
- Add **Instagram Graph API**.
- Add **Facebook Login for Business** (used to mint the page token).

## 4. Mint a long-lived Page access token
1. In the Graph API Explorer, select your app and your Page.
2. Request these scopes:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_show_list`
   - `pages_read_engagement`
3. Generate a short-lived user token, then exchange it for a long-lived
   token (60 days). Then exchange THAT for a long-lived **Page** token —
   page tokens minted from a long-lived user token don't expire as long as
   the user token stays valid.
4. Save the page token as `IG_ACCESS_TOKEN` in `.env`.

## 5. Find IG_USER_ID
Call:

```
GET /{page-id}?fields=instagram_business_account&access_token={token}
```

The returned `instagram_business_account.id` is your `IG_USER_ID`. Save it
in `.env`.

## 6. Image hosting (Supabase — already provisioned)
A dedicated Supabase project `jerseysmokebbq`
(ref `tewmbnlldtavuqzaolve`, us-east-1) and a public bucket `bbq-covers`
(5 MB cap, png/jpeg/webp) are already in place. The uploader lives at
`image_host.upload()` and is wired into `publish_brief.py`.

You only need to grab the **service-role key** and set two env vars:

1. In the Supabase dashboard, open the `jerseysmokebbq` project →
   **Project Settings → API → Project API keys → service_role**. Copy.
2. Locally, add to `.env`:
   ```
   SUPABASE_URL=https://tewmbnlldtavuqzaolve.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=<paste>
   ```
3. In GitHub: repo **Settings → Secrets and variables → Actions → New
   secret** for both `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.

> The service-role key bypasses RLS — never expose it to a browser or to
> the IG side. It only lives in `.env` (gitignored) and in the GitHub
> Actions secret store.

## 7. Verify with a preview run
```
python publish_brief.py --preview
```
Confirms the caption + image pipeline works without touching IG.

## 8. First live publish
```
PUBLISH_ENABLED=true python publish_brief.py
```
Watch the first run carefully. If anything misfires, set
`PUBLISH_ENABLED=false` and the cron will skip until you fix it.
