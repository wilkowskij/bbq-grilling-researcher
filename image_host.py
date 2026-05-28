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
"""

from __future__ import annotations

import mimetypes
import os
import pathlib

import requests


BUCKET = "bbq-covers"


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
