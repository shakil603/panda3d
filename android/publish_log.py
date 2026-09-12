#!/usr/bin/env python3
"""Publish the tail of a build log as a GitHub diagnostic.

Used by .github/workflows/android-apk.yml when a build step fails, so the
error output can be inspected even when raw job logs are unavailable.

Usage:  publish_log.py <log-file> <check-run-name>
Env:    DIAG_REPO (owner/repo), DIAG_PR (pull request number, optional),
        DIAG_SHA (for the check-run fallback), GH_TOKEN (for gh api)
"""
import json
import os
import subprocess
import sys
import tempfile


def post_pr_comment(repo, pr, title, body):
    path = None
    try:
        f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
        f.write("## %s\n\n%s\n" % (title, body))
        f.close()
        path = f.name
        subprocess.run(
            ["gh", "api", "-X", "POST",
             "repos/%s/issues/%s/comments" % (repo, pr),
             "-f", "body=@%s" % path],
            check=True,
        )
    finally:
        if path:
            os.unlink(path)


def post_check_run(repo, sha, name, body):
    if not sha:
        return
    payload = {
        "name": name,
        "head_sha": sha,
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
         "repos/%s/check-runs" % repo,
         "--input", "-"],
        input=json.dumps(payload),
        text=True,
        check=True,
    )


def main():
    if len(sys.argv) != 3:
        print("usage: publish_log.py <log-file> <name>")
        return 2
    log_file, name = sys.argv[1], sys.argv[2]
    repo = os.environ.get("DIAG_REPO", "")
    pr = os.environ.get("DIAG_PR", "").strip()
    sha = os.environ.get("DIAG_SHA", "").strip()

    if not os.path.isfile(log_file):
        body = ("No log file found at `%s` — the step failed before it "
                "started writing the log." % log_file)
    else:
        with open(log_file, errors="replace") as f:
            tail = f.readlines()[-150:]
        body = "```bash\n" + "".join(tail) + "```"

    # Prefer a PR comment (always works for pull_request events); fall
    # back to a check run for pushes/tags.
    if pr:
        post_pr_comment(repo, pr, name + " diagnostic", body)
    else:
        post_check_run(repo, sha, name, body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
