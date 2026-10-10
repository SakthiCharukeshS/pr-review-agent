import os
from typing import Optional

import requests
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import ToolContext
from google.genai import types

MODEL = "gemini-3.6-flash"

RETRY_CONFIG = types.GenerateContentConfig(
    http_options=types.HttpOptions(
        timeout=60000,  # 60 seconds per request, in milliseconds
        retry_options=types.HttpRetryOptions(
            attempts=5,        # 1 original try + 4 retries
            initial_delay=15,  # seconds before the first retry
            max_delay=60,      # never wait longer than this between retries
        ),
    )
)


def require_diff(callback_context: CallbackContext) -> Optional[types.Content]:
    """Skips an agent when no PR diff was fetched."""
    if not callback_context.state.get("pr_diff"):
        return types.Content(
            role="model",
            parts=[types.Part(text="Skipped: no diff to review.")],
        )
    return None


def fetch_pr_diff(repo: str, pr_number: int, tool_context: ToolContext) -> dict:
    """Fetches the diff of a GitHub pull request and saves it for the reviewers.

    Args:
        repo: Repository in "owner/name" format, e.g. "SakthiCharukeshS/pr-review-agent".
        pr_number: The pull request number.

    Returns:
        A dict with the status. The diff itself is saved in session state.
    """
    tool_context.state["pr_diff"] = ""  # clear any old diff first
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
    diff = resp.text[:20000]
    tool_context.state["pr_diff"] = diff
    return {"status": "success", "diff_chars": len(diff)}


fetcher = LlmAgent(
    name="fetcher",
    model=MODEL,
    instruction=(
        "The user gives a repo (owner/name) and a PR number. "
        "Call fetch_pr_diff once. If it succeeds, reply only: Diff fetched. "
        "If it returns an error, explain the error to the user."
    ),
    tools=[fetch_pr_diff],
    generate_content_config=RETRY_CONFIG,
)

style_agent = LlmAgent(
    name="style_agent",
    model=MODEL,
    instruction="""Review this PR diff for STYLE issues only.
Max 3 bullet points. Mention the file name for each.

Diff:
{pr_diff}""",
    output_key="style_review",
    generate_content_config=RETRY_CONFIG,
)

bug_agent = LlmAgent(
    name="bug_agent",
    model=MODEL,
    instruction="""Review this PR diff for BUGS and logic errors only.
Max 3 bullet points. Mention the file name for each.

Diff:
{pr_diff}""",
    output_key="bug_review",
    generate_content_config=RETRY_CONFIG,
)

security_agent = LlmAgent(
    name="security_agent",
    model=MODEL,
    instruction="""Review this PR diff for SECURITY issues only.
Max 3 bullet points. Mention the file name for each.

Diff:
{pr_diff}""",
    output_key="security_review",
    generate_content_config=RETRY_CONFIG,
)

parallel_reviews = ParallelAgent(
    name="parallel_reviews",
    sub_agents=[style_agent, bug_agent, security_agent],
    before_agent_callback=require_diff,
)

summarizer = LlmAgent(
    name="summarizer",
    model=MODEL,
    instruction="""Combine the three reviews below into one short final PR review.
Group it under: Bugs, Security, Style. Remove duplicates.

Style review: {style_review}
Bug review: {bug_review}
Security review: {security_review}""",
    generate_content_config=RETRY_CONFIG,
    output_key="final_review",
    before_agent_callback=require_diff,
)

root_agent = SequentialAgent(
    name="pr_review_pipeline",
    sub_agents=[fetcher, parallel_reviews, summarizer],
)