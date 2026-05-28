"""Instagram Graph API publisher.

Flow:
    1. POST /{ig-user-id}/media        -> creation_id
    2. Poll /{creation_id}?fields=status_code until FINISHED
    3. POST /{ig-user-id}/media_publish -> media_id
    4. POST /{media_id}/comments       (first comment with source URLs)

The Graph API requires the image to live at a public HTTPS URL. The caller
is responsible for uploading the generated image to S3 / R2 / Supabase /
similar and passing the URL in.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

import requests


GRAPH_BASE = "https://graph.facebook.com/v21.0"


@dataclass
class PublishResult:
    media_id: str
    comment_id: str | None


class IGPublishError(RuntimeError):
    pass


class InstagramPublisher:
    def __init__(self, ig_user_id: str | None = None, access_token: str | None = None):
        self.ig_user_id = ig_user_id or os.environ.get("IG_USER_ID")
        self.token = access_token or os.environ.get("IG_ACCESS_TOKEN")
        if not self.ig_user_id or not self.token:
            raise RuntimeError("IG_USER_ID and IG_ACCESS_TOKEN must be set")

    def _create_container(self, image_url: str, caption: str) -> str:
        r = requests.post(
            f"{GRAPH_BASE}/{self.ig_user_id}/media",
            data={
                "image_url": image_url,
                "caption": caption,
                "access_token": self.token,
            },
            timeout=30,
        )
        if not r.ok:
            raise IGPublishError(f"create container failed [{r.status_code}]: {r.text}")
        cid = r.json().get("id")
        if not cid:
            raise IGPublishError(f"no container id returned: {r.text}")
        return cid

    def _wait_finished(self, creation_id: str, timeout_s: int = 90) -> None:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            r = requests.get(
                f"{GRAPH_BASE}/{creation_id}",
                params={"fields": "status_code", "access_token": self.token},
                timeout=30,
            )
            if not r.ok:
                raise IGPublishError(f"status check failed [{r.status_code}]: {r.text}")
            status = r.json().get("status_code")
            if status == "FINISHED":
                return
            if status == "ERROR":
                raise IGPublishError(f"container errored: {r.text}")
            time.sleep(3)
        raise IGPublishError(f"timeout waiting for container {creation_id}")

    def _publish(self, creation_id: str) -> str:
        r = requests.post(
            f"{GRAPH_BASE}/{self.ig_user_id}/media_publish",
            data={"creation_id": creation_id, "access_token": self.token},
            timeout=30,
        )
        if not r.ok:
            raise IGPublishError(f"publish failed [{r.status_code}]: {r.text}")
        mid = r.json().get("id")
        if not mid:
            raise IGPublishError(f"no media id returned: {r.text}")
        return mid

    def _comment(self, media_id: str, message: str) -> str | None:
        r = requests.post(
            f"{GRAPH_BASE}/{media_id}/comments",
            data={"message": message, "access_token": self.token},
            timeout=30,
        )
        if not r.ok:
            return None
        return r.json().get("id")

    def publish(self, image_url: str, caption: str, first_comment: str | None = None) -> PublishResult:
        cid = self._create_container(image_url, caption)
        self._wait_finished(cid)
        media_id = self._publish(cid)
        comment_id = self._comment(media_id, first_comment) if first_comment else None
        return PublishResult(media_id=media_id, comment_id=comment_id)
