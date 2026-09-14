#!/usr/bin/env python3
"""Publish the tail of a build log as a GitHub diagnostic.

Used by .github/workflows/android-apk.yml when a build step fails, so the
error output can be inspected even when raw job logs are unavailable.

Modes:
  publish_log.py <log-file> <name>
      Best-effort: PR comment (pull_request events) or check run (others).

  publish_log.py --annotate <log-file> <title>
      Print a GitHub Actions workflow command (::error::) carrying the log
      tail as base64.  The runner turns it into a check-run annotation that
      is readable via the API even with a read-only fork-PR token.

Env (for the first mode): DIAG_REPO (owner/repo), DIAG_PR (PR number),
      DIAG_SHA, GH_TOKEN.
"""
import base64
import json
import os
import re
import subprocess
import sys
import tempfile

# Patterns that usually indicate the real failure in a build log.
_ERR_RE = re.compile(
    r"(?i)\berror\b|error:|fatal|undefined reference|cannot (read|find|open)|"
    r"no such file|not found|failed|failure|make.*\[\d+,\d+\]\d+: |"
    r"Traceback|Exception|Killed|out of memory|ld\.lld|linker"
)


def _read_lines(log_file):
    if not os.path.isfile(log_file):
        return None
    with open(log_file, errors="replace") as f:
        return f.readlines()


def tail_of(log_file, lines=400):
    data = _read_lines(log_file)
    if data is None:
        return None
    return "".join(data[-lines:])


def diagnostic_of(log_file, budget=40000):
    """Build a compact diagnostic: every error-looking line plus the tail.

    Kept under ~budget raw chars so the base64'd workflow-command annotation
    stays under GitHub's 65535-byte limit.
    """
    data = _read_lines(log_file)
    if data is None:
        return "NO LOG FILE at %s" % log_file
    errs = [ln.rstrip("\n") for ln in data if _ERR_RE.search(ln)]
    # De-dupe while preserving order.
    seen = set()
    errs = [e for e in errs if not (e in seen or seen.add(e))]
    tail = [ln.rstrip("\n") for ln in data[-60:]]
    parts = []
    if errs:
        parts.append("===== %d error line(s) =====" % len(errs))
        parts.extend(errs)
    parts.append("===== last %d line(s) =====" % len(tail))
    parts.extend(tail)
    text = "\n".join(parts)
    if len(text) > budget:
        # Keep the tail (most recent state), drop the oldest error lines.
        text = "…(truncated)…\n" + text[-(budget - 20):]
    return text


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
    if len(sys.argv) >= 2 and sys.argv[1] == "--annotate":
        if len(sys.argv) != 4:
            print("usage: publish_log.py --annotate <log-file> <title>")
            return 2
        log_file, title = sys.argv[2], sys.argv[3]
        payload = diagnostic_of(log_file)
        # Workflow-command annotations are single-line; carry the log as
        # base64 so it can be decoded from the API.
        b64 = base64.b64encode(payload.encode("utf-8", "replace")).decode()
        print("::error title=%s (log tail, base64)::p3d-log-b64:%s" % (title, b64))
        return 0

    if len(sys.argv) != 3:
        print("usage: publish_log.py <log-file> <name> | --annotate <log-file> <title>")
        return 2
    log_file, name = sys.argv[1], sys.argv[2]
    repo = os.environ.get("DIAG_REPO", "")
    pr = os.environ.get("DIAG_PR", "").strip()
    sha = os.environ.get("DIAG_SHA", "").strip()

    tail = tail_of(log_file)
    body = ("(No log file found at `%s` — the step failed before it started "
            "writing the log.)" % log_file) if tail is None else "```bash\n" + tail + "```"

    # Prefer a PR comment (always works for pull_request events); fall
    # back to a check run for pushes/tags.
    if pr:
        post_pr_comment(repo, pr, name + " diagnostic", body)
    else:
        post_check_run(repo, sha, name, body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
