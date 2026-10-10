"""Tests for review.py. A fake model replaces Gemini, so no quota is used."""

import asyncio
from unittest.mock import AsyncMock, patch

from google.adk.agents import LlmAgent
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types

import review
from my_agent.agent import summarizer


class FakeLlm(BaseLlm):
    """A model that always answers 'FAKE REVIEW'. Never touches the network."""

    model: str = "fake-model"

    async def generate_content_async(self, llm_request, stream=False):
        yield LlmResponse(
            content=types.Content(role="model", parts=[types.Part(text="FAKE REVIEW")])
        )


# ---------- run_agent: the real ADK Runner, with a fake model ----------


def test_run_agent_returns_state_and_text():
    agent = LlmAgent(
        name="writer",
        model=FakeLlm(),
        instruction="Write a review.",
        output_key="final_review",
    )

    state, texts = asyncio.run(review.run_agent(agent, "Review PR 1 in o/r"))

    assert state["final_review"] == "FAKE REVIEW"
    assert texts["writer"] == "FAKE REVIEW"


# ---------- contract between agent.py and review.py ----------


def test_summarizer_saves_result_under_final_review():
    # review.py reads state["final_review"], so the summarizer must write it.
    assert summarizer.output_key == "final_review"


# ---------- review_pr ----------


def test_review_pr_posts_comment_when_review_exists():
    run = AsyncMock(return_value=({"final_review": "GOOD REVIEW"}, {}))
    ok = {"status": "success", "url": "https://github.com/o/r/pull/1#c1"}
    with patch("review.run_agent", run), patch(
        "review.post_pr_comment", return_value=ok
    ) as post:
        code = review.review_pr("o/r", 1)

    assert code == 0
    post.assert_called_once_with("o/r", 1, "GOOD REVIEW")


def test_review_pr_dry_run_does_not_post():
    run = AsyncMock(return_value=({"final_review": "GOOD REVIEW"}, {}))
    with patch("review.run_agent", run), patch("review.post_pr_comment") as post:
        code = review.review_pr("o/r", 1, post=False)

    assert code == 0
    post.assert_not_called()


def test_review_pr_without_review_fails_and_shows_fetcher_message(capsys):
    # Happens when the fetch fails (e.g. PR 999 -> 404): the guard skips the rest.
    run = AsyncMock(return_value=({}, {"fetcher": "PR 999 could not be found (404)"}))
    with patch("review.run_agent", run), patch("review.post_pr_comment") as post:
        code = review.review_pr("o/r", 999)

    assert code == 1
    post.assert_not_called()
    assert "404" in capsys.readouterr().err


def test_review_pr_returns_error_code_when_posting_fails(capsys):
    run = AsyncMock(return_value=({"final_review": "R"}, {}))
    bad = {"status": "error", "message": "403 Forbidden"}
    with patch("review.run_agent", run), patch("review.post_pr_comment", return_value=bad):
        code = review.review_pr("o/r", 1)

    assert code == 1
    assert "403" in capsys.readouterr().err


# ---------- command-line parsing ----------


def test_main_passes_arguments_through():
    with patch("review.review_pr", return_value=0) as rp:
        code = review.main(["owner/repo", "5"])

    assert code == 0
    rp.assert_called_once_with("owner/repo", 5, post=True)


def test_main_dry_run_flag_disables_posting():
    with patch("review.review_pr", return_value=0) as rp:
        review.main(["owner/repo", "5", "--dry-run"])

    rp.assert_called_once_with("owner/repo", 5, post=False)