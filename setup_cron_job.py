"""Create (or replace) a cron-job.org daily trigger for the IG publish workflow.

Reads from env (all set by the setup-cron.yml workflow):
    CRON_JOB_ORG_API_KEY  -- cron-job.org API key (Settings -> API)
    GITHUB_DISPATCH_PAT   -- fine-grained GitHub PAT with Actions: Write
                             on wilkowskij/bbq-grilling-researcher
    CRON_HOUR_UTC         -- hour 0-23 UTC (default 14 = 10am ET)
    CRON_MINUTE           -- minute 0-59 (default 0)
    CRON_REF              -- git ref (branch) to dispatch on

The script lists existing jobs whose title starts with "BBQ daily IG publish"
and deletes them first so re-runs replace the schedule instead of stacking
duplicate cron jobs.
"""

from __future__ import annotations

import json
import os
import sys

import requests


REPO = "wilkowskij/bbq-grilling-researcher"
WORKFLOW = "daily-publish.yml"
JOB_TITLE = "BBQ daily IG publish"
CRON_API = "https://api.cron-job.org"


def _auth(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def _list_jobs(api_key: str) -> list[dict]:
    r = requests.get(f"{CRON_API}/jobs", headers=_auth(api_key), timeout=30)
    if not r.ok:
        raise RuntimeError(f"list jobs failed [{r.status_code}]: {r.text}")
    return r.json().get("jobs", [])


def _delete_job(api_key: str, job_id: int) -> None:
    r = requests.delete(f"{CRON_API}/jobs/{job_id}", headers=_auth(api_key), timeout=30)
    if not r.ok and r.status_code != 404:
        raise RuntimeError(f"delete job {job_id} failed [{r.status_code}]: {r.text}")


def _create_job(api_key: str, payload: dict) -> int:
    r = requests.put(f"{CRON_API}/jobs", headers=_auth(api_key), json=payload, timeout=30)
    if not r.ok:
        raise RuntimeError(f"create job failed [{r.status_code}]: {r.text}")
    return int(r.json().get("jobId"))


def main() -> int:
    api_key = os.environ["CRON_JOB_ORG_API_KEY"]
    gh_pat = os.environ["GITHUB_DISPATCH_PAT"]
    hour = int(os.environ.get("CRON_HOUR_UTC", "14"))
    minute = int(os.environ.get("CRON_MINUTE", "0"))
    ref = os.environ.get("CRON_REF", "main")

    body = json.dumps({"ref": ref, "inputs": {"preview": "false"}})

    payload = {
        "job": {
            "url": f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW}/dispatches",
            "title": JOB_TITLE,
            "enabled": True,
            "saveResponses": True,
            "requestMethod": 1,
            "extendedData": {
                "headers": {
                    "Authorization": f"Bearer {gh_pat}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "Content-Type": "application/json",
                },
                "body": body,
            },
            "schedule": {
                "timezone": "UTC",
                "expiresAt": 0,
                "hours": [hour],
                "mdays": [-1],
                "minutes": [minute],
                "months": [-1],
                "wdays": [-1],
            },
        }
    }

    print(f"Listing existing jobs to dedupe...")
    existing = _list_jobs(api_key)
    duplicates = [j for j in existing if (j.get("title") or "").startswith(JOB_TITLE)]
    for j in duplicates:
        jid = j.get("jobId")
        print(f"  deleting existing job {jid} (title: {j.get('title')!r})")
        _delete_job(api_key, jid)

    print(f"Creating new daily job at {hour:02d}:{minute:02d} UTC -> dispatch {WORKFLOW} on {ref}")
    job_id = _create_job(api_key, payload)
    print(f"  created job id={job_id}")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write("## cron-job.org daily trigger configured\n\n")
            f.write(f"- Job ID: `{job_id}`\n")
            f.write(f"- Title: `{JOB_TITLE}`\n")
            f.write(f"- Schedule: **{hour:02d}:{minute:02d} UTC** daily\n")
            f.write(f"- Target: `{REPO}` workflow `{WORKFLOW}` on branch `{ref}`\n")
            f.write(f"- Replaced {len(duplicates)} prior job(s) with the same title\n\n")
            f.write("Manage at https://cron-job.org/en/members/jobs/\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
