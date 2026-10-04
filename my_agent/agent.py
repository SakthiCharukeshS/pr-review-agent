import os

import requests
from google.adk.agents import Agent


def get_pr_diff(repo: str, pr_number: int) -> dict:
    """Fetches the diff (code changes) of a GitHub pull request.

    Args:
        repo: Repository in "owner/name" format, e.g. "SakthiCharukeshS/pr-review-agent".
        pr_number: The pull request number.

    Returns:
        A dict with status and the diff text, or an error message.
    """
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {"Accept": "application/vnd.github.v3.diff"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"status": "error", "message": str(e)}
    return {"status": "success", "diff": resp.text[:20000]}


root_agent = Agent(
    name="root_agent",
    model="gemini-3.8-flash",
    description="Reviews GitHub pull requests.",
    instruction=(
        "You are a strict senior engineer. The user gives a repo (owner/name) "
        "and a PR number. Call get_pr_diff to fetch it, then review the diff. "
        "List problems under: Bugs, Security, Style. Be specific and brief. "
        "If the tool returns an error, explain it to the user."
    ),
    tools=[get_pr_diff],
)