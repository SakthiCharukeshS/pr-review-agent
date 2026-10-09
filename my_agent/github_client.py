"""Plain GitHub API helpers (no AI involved).

Posting a comment is a deterministic step, so it lives here as normal Python
and is NOT given to the agent as a tool. That way the AI can never decide to
write to GitHub by itself.
"""

import os

import requests

GITHUB_API = "https://api.github.com"
MAX_COMMENT_CHARS = 60000  # GitHub's hard limit is 65536
FOOTER = (
    "\n\n---\n"
    "*AI-generated review by pr-review-agent. It can make mistakes, "
    "so verify before acting.*"
)


def post_pr_comment(
    repo: str, pr_number: int, body: str, token: str | None = None
) -> dict:
    """Posts a comment on a pull request.

    Args:
        repo: Repository in "owner/name" format.
        pr_number: The pull request number.
        body: The comment text (markdown).
        token: GitHub token. Falls back to the GITHUB_TOKEN environment variable.

    Returns:
        {"status": "success", "url": ...} or {"status": "error", "message": ...}
    """
    token = token or os.environ.get("GITHUB_TOKEN")
    if not token:
        return {"status": "error", "message": "No GitHub token. Set GITHUB_TOKEN."}
    if not body or not body.strip():
        return {"status": "error", "message": "Refusing to post an empty comment."}

    text = body[:MAX_COMMENT_CHARS] + FOOTER
    # PR comments use the "issues" endpoint: every PR is also an issue.
    url = f"{GITHUB_API}/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    try:
        resp = requests.post(url, headers=headers, json={"body": text}, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"status": "error", "message": str(e)}
    return {"status": "success", "url": resp.json().get("html_url")}