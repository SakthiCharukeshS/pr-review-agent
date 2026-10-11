"""Review a GitHub pull request with the AI pipeline.

Usage:
    python review.py owner/repo 12             review PR 12 and post the comment
    python review.py owner/repo 12 --dry-run   review it, only print the result
"""

import argparse
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from my_agent.agent import root_agent
from my_agent.github_client import post_pr_comment
from my_agent.redact import redact_secrets

APP_NAME = "pr_review"
USER_ID = "cli"


async def run_agent(agent, prompt: str) -> tuple[dict, dict]:
    """Runs an agent once, with no browser.

    Returns:
        (final session state, {agent name: its last final text})
    """
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)

    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    texts: dict[str, str] = {}
    async for event in runner.run_async(
        user_id=USER_ID, session_id=session.id, new_message=message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            texts[event.author] = event.content.parts[0].text or ""

    final = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session.id
    )
    return dict(final.state), texts


def review_pr(repo: str, pr_number: int, post: bool = True) -> int:
    """Runs the pipeline on one PR. Returns a process exit code (0 = success)."""
    prompt = f"Review PR {pr_number} in {repo}"
    state, texts = asyncio.run(run_agent(root_agent, prompt))

    review = state.get("final_review")
    if not review:
        reason = texts.get("fetcher") or "The pipeline produced no review."
        print(f"No review produced. {reason}", file=sys.stderr)
        return 1

    review = redact_secrets(review)  # never print or post a leaked secret
    print(review)
    if not post:
        return 0

    result = post_pr_comment(repo, pr_number, review)
    if result["status"] != "success":
        print(f"Could not post comment: {result['message']}", file=sys.stderr)
        return 1
    print(f"\nPosted: {result['url']}")
    return 0


def main(argv=None) -> int:
    # Windows consoles often can't print everything an AI writes (arrows, quotes).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # Local runs read keys from my_agent/.env. In CI the env vars already exist.
    load_dotenv(Path(__file__).parent / "my_agent" / ".env")

    parser = argparse.ArgumentParser(description="Review a GitHub PR with AI.")
    parser.add_argument("repo", help='Repository as "owner/name"')
    parser.add_argument("pr_number", type=int, help="Pull request number")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print the review, don't post it"
    )
    args = parser.parse_args(argv)
    return review_pr(args.repo, args.pr_number, post=not args.dry_run)


if __name__ == "__main__":
    sys.exit(main())