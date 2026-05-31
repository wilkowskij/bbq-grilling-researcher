"""Dump the last few cron-job.org executions of the BBQ daily publish job
so we can see what GitHub returned when cron-job.org tried to dispatch.

Reads:
    CRON_JOB_ORG_API_KEY -- cron-job.org API key

Writes a markdown report to GITHUB_STEP_SUMMARY with: job id, schedule,
the last 10 executions (timestamp, HTTP status, duration), and for each
non-2xx execution the saved response body so we can read GitHub's error.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

import requests


CRON_API = "https://api.cron-job.org"
JOB_TITLE_PREFIX = "BBQ daily IG publish"


def _auth(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def _fmt_ts(epoch: int | float | None) -> str:
    if not epoch:
        return "—"
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def main() -> int:
    api_key = os.environ.get("CRON_JOB_ORG_API_KEY")
    if not api_key:
        print("CRON_JOB_ORG_API_KEY not set", file=sys.stderr)
        return 2

    r = requests.get(f"{CRON_API}/jobs", headers=_auth(api_key), timeout=30)
    r.raise_for_status()
    jobs = r.json().get("jobs", [])
    matching = [j for j in jobs if (j.get("title") or "").startswith(JOB_TITLE_PREFIX)]
    if not matching:
        print(f"No cron-job.org job with title prefix {JOB_TITLE_PREFIX!r}", file=sys.stderr)
        return 1

    out = ["## cron-job.org diagnostic\n"]
    for j in matching:
        jid = j["jobId"]
        out.append(f"### Job `{jid}` — {j.get('title')}\n")
        out.append(f"- Enabled: **{j.get('enabled')}**")
        out.append(f"- URL: `{j.get('url')}`")
        sched = j.get("schedule") or {}
        out.append(f"- Schedule: `hours={sched.get('hours')} minutes={sched.get('minutes')} "
                   f"tz={sched.get('timezone')}`")
        out.append(f"- Last status: `{j.get('lastStatus')}` "
                   f"(0=unknown, 1=ok, 2=failed-DNS, 3=failed-connect, 4=HTTP-error, "
                   f"5=timeout, 6=response-too-large)")
        out.append(f"- Last execution: {_fmt_ts(j.get('lastExecution'))}")
        out.append(f"- Last duration (ms): {j.get('lastDuration')}\n")

        hr = requests.get(f"{CRON_API}/jobs/{jid}/history", headers=_auth(api_key), timeout=30)
        if not hr.ok:
            out.append(f"_history fetch failed [{hr.status_code}]: {hr.text}_\n")
            continue
        history = hr.json().get("history", [])[:10]

        out.append("| # | When (UTC) | Status | HTTP | Duration ms |")
        out.append("| ---: | --- | ---: | ---: | ---: |")
        for i, h in enumerate(history, 1):
            out.append(f"| {i} | {_fmt_ts(h.get('date'))} | "
                       f"{h.get('status')} | {h.get('httpStatus')} | {h.get('duration')} |")
        out.append("")

        for i, h in enumerate(history, 1):
            if h.get("httpStatus") and 200 <= h["httpStatus"] < 300:
                continue
            ident = h.get("identifier")
            if not ident:
                continue
            dr = requests.get(f"{CRON_API}/jobs/{jid}/history/{ident}",
                              headers=_auth(api_key), timeout=30)
            if not dr.ok:
                out.append(f"_detail fetch for execution #{i} failed [{dr.status_code}]_\n")
                continue
            detail = dr.json().get("jobHistoryDetails") or {}
            body = (detail.get("body") or "")[:1500]
            headers = detail.get("headers") or ""
            out.append(f"#### Execution #{i} ({_fmt_ts(h.get('date'))}) — "
                       f"HTTP {h.get('httpStatus')}\n")
            out.append("Response headers:\n```\n" + headers[:600] + "\n```\n")
            out.append("Response body:\n```\n" + body + "\n```\n")

    summary = "\n".join(out)
    print(summary)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
