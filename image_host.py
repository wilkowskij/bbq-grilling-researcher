"""Upload generated BBQ covers to Supabase Storage and return a public URL.

Project: jerseysmokebbq (ref tewmbnlldtavuqzaolve, us-east-1)
Bucket:  bbq-covers (public, 5 MB cap, png/jpeg/webp)

The Instagram Graph API requires `image_url` to be a public HTTPS URL.
Supabase serves public-bucket objects at
`{SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}`, which is what
this module returns.

Uses the service-role key for writes (set `SUPABASE_SERVICE_ROLE_KEY` in
`.env` / GitHub Actions secrets). The service-role key bypasses RLS so we
don't need permissive insert policies on `storage.objects`.

When Supabase is unreachable (project paused, DNS down) we fall back to
catbox.moe so the daily IG post still ships. Catbox is a no-account
public file host — fine for the cover image, which is already meant for
public consumption. The fallback is logged to stderr so the next day's
diagnostic catches it.
"""

from __future__ import annotations

import mimetypes
import os
import pathlib
import sys

import requests


BUCKET = "bbq-covers"
CATBOX_API = "https://catbox.moe/user/api.php"


def _env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(f"{name} is not set")
    return v


def upload(image_path: pathlib.Path, dest_name: str | None = None) -> str:
    """Upload a local file to the bbq-covers bucket and return the public URL."""
    if not image_path.exists():
        raise FileNotFoundError(image_path)
    dest = dest_name or image_path.name
    mime, _ = mimetypes.guess_type(dest)
    mime = mime or "image/png"
    return _upload_bytes(image_path.read_bytes(), dest, mime)


def upload_html(html_text: str, dest_name: str) -> str:
    """Upload an HTML string to the bbq-covers bucket and return the public URL."""
    return _upload_bytes(html_text.encode("utf-8"), dest_name, "text/html")


def _upload_bytes(data: bytes, dest: str, mime: str) -> str:
    try:
        return _supabase_upload(data, dest, mime)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        # DNS failure usually means the Supabase project is paused. Don't
        # block the day's post on analytics infrastructure.
        if not mime.startswith("image/"):
            # Non-images (preview HTML) have no useful fallback. Surface
            # the original error so the workflow log makes the cause obvious.
            raise
        print(
            f"[!] Supabase upload failed ({type(e).__name__}: {e}); "
            f"falling back to catbox.moe. Likely cause: Supabase project paused.",
            file=sys.stderr,
        )
        return _catbox_upload(data, dest, mime)


def _supabase_upload(data: bytes, dest: str, mime: str) -> str:
    supabase_url = _env("SUPABASE_URL").rstrip("/")
    service_key = _env("SUPABASE_SERVICE_ROLE_KEY")
    endpoint = f"{supabase_url}/storage/v1/object/{BUCKET}/{dest}"
    headers = {
        "Authorization": f"Bearer {service_key}",
        "Content-Type": mime,
        "x-upsert": "true",
    }
    r = requests.post(endpoint, headers=headers, data=data, timeout=60)
    if not r.ok:
        raise RuntimeError(f"supabase upload failed [{r.status_code}]: {r.text}")
    return f"{supabase_url}/storage/v1/object/public/{BUCKET}/{dest}"


def _catbox_upload(data: bytes, dest: str, mime: str) -> str:
    filename = pathlib.PurePath(dest).name
    files = {"fileToUpload": (filename, data, mime)}
    r = requests.post(
        CATBOX_API,
        data={"reqtype": "fileupload"},
        files=files,
        timeout=60,
    )
    if not r.ok or not r.text.startswith("https://"):
        raise RuntimeError(f"catbox upload failed [{r.status_code}]: {r.text[:200]}")
    url = r.text.strip()
    print(f"[+] catbox fallback URL: {url}", file=sys.stderr)
    return url
