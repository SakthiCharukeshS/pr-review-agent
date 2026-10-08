"""Unit tests for the PR review tool and guard.

These tests never call Gemini or GitHub: requests.get is replaced by a fake,
and the ADK contexts are replaced by tiny stand-ins that only have `.state`.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import requests

from my_agent.agent import fetch_pr_diff, require_diff


def fake_context(state=None):
    """Stand-in for ToolContext / CallbackContext: only needs a .state dict."""
    return SimpleNamespace(state=state if state is not None else {})


def fake_response(text="diff --git a/x.py b/x.py", error=None):
    """Stand-in for a requests.Response."""
    resp = MagicMock()
    resp.text = text
    if error is not None:
        resp.raise_for_status.side_effect = error
    return resp


# ---------- fetch_pr_diff ----------


def test_fetch_success_saves_diff_in_state():
    ctx = fake_context()
    with patch("my_agent.agent.requests.get", return_value=fake_response("DIFF TEXT")):
        result = fetch_pr_diff("owner/repo", 1, ctx)

    assert result["status"] == "success"
    assert ctx.state["pr_diff"] == "DIFF TEXT"


def test_fetch_404_returns_error_and_leaves_state_empty():
    ctx = fake_context()
    err = requests.HTTPError("404 Client Error: Not Found")
    with patch("my_agent.agent.requests.get", return_value=fake_response(error=err)):
        result = fetch_pr_diff("owner/repo", 999, ctx)

    assert result["status"] == "error"
    assert "404" in result["message"]
    assert ctx.state["pr_diff"] == ""


def test_fetch_network_failure_returns_error():
    ctx = fake_context()
    with patch(
        "my_agent.agent.requests.get",
        side_effect=requests.ConnectionError("network down"),
    ):
        result = fetch_pr_diff("owner/repo", 1, ctx)

    assert result["status"] == "error"
    assert ctx.state["pr_diff"] == ""


def test_fetch_clears_stale_diff_from_earlier_request():
    ctx = fake_context({"pr_diff": "OLD DIFF FROM PR 1"})
    err = requests.HTTPError("404 Client Error: Not Found")
    with patch("my_agent.agent.requests.get", return_value=fake_response(error=err)):
        fetch_pr_diff("owner/repo", 999, ctx)

    assert ctx.state["pr_diff"] == ""


def test_fetch_truncates_huge_diff_to_20000_chars():
    ctx = fake_context()
    with patch("my_agent.agent.requests.get", return_value=fake_response("a" * 30000)):
        result = fetch_pr_diff("owner/repo", 1, ctx)

    assert len(ctx.state["pr_diff"]) == 20000
    assert result["diff_chars"] == 20000


def test_fetch_sends_token_when_set(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    ctx = fake_context()
    with patch("my_agent.agent.requests.get", return_value=fake_response()) as get:
        fetch_pr_diff("owner/repo", 1, ctx)

    headers = get.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer fake-token"


def test_fetch_works_without_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    ctx = fake_context()
    with patch("my_agent.agent.requests.get", return_value=fake_response()) as get:
        fetch_pr_diff("owner/repo", 1, ctx)

    assert "Authorization" not in get.call_args.kwargs["headers"]


def test_fetch_calls_correct_github_url():
    ctx = fake_context()
    with patch("my_agent.agent.requests.get", return_value=fake_response()) as get:
        fetch_pr_diff("someone/project", 42, ctx)

    assert get.call_args.args[0] == "https://api.github.com/repos/someone/project/pulls/42"


# ---------- require_diff (the guard) ----------


def test_guard_skips_when_diff_missing():
    result = require_diff(fake_context({}))

    assert result is not None
    assert "Skipped" in result.parts[0].text


def test_guard_skips_when_diff_is_empty_string():
    result = require_diff(fake_context({"pr_diff": ""}))

    assert result is not None


def test_guard_lets_agent_run_when_diff_exists():
    result = require_diff(fake_context({"pr_diff": "some diff"}))

    assert result is None