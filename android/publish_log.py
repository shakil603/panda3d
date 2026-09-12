#!/usr/bin/env python3
"""Post the tail of a build log to a GitHub check run (diagnostic helper).

Used by .github/workflows/android-apk.yml when a build step fails, so the
error output can be inspected even when raw job logs are unavailable.

Usage:  publish_log.py <log-file> <check-run-name>
Env:    DIAG_SHA, DIAG_REPO  (set by the workflow), GH_TOKEN (for gh api)
"""
import json
import os
import subprocess
import sys


def main():
    if len(sys.argv) != 3:
        print("usage: publish_log.py <log-file> <check-run-name>")
        return 2
    log_file, name = sys.argv[1], sys.argv[2]
    if not os.path.isfile(log_file):
        return 0

    with open(log_file, errors="replace") as f:
        tail = f.readlines()[-150:]

    body = "Build failed. Log tail:\n\n```\n" + "".join(tail) + "```"
    payload = {
        "name": name,
        "head_sha": os.environ["DIAG_SHA"],
        "status": "completed",
        "conclusion": "action_required",
        "completed_at": "2026-01-01T00:00:00Z",
        "output": {
            "title": name + " (tail)",
            "summary": "See output for the last 150 log lines",
            "text": body,
        },
    }
    subprocess.run(
        ["gh", "api", "-X", "POST",
         "repos/%s/check-runs" % os.environ["DIAG_REPO"],
         "--input", "-"],
        input=json.dumps(payload),
        check=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
