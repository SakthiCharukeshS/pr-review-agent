"""Unit tests for post_pr_comment. No real GitHub calls are made."""

from unittest.mock import MagicMock, patch

import requests

from my_agent.github_client import FOOTER, MAX_COMMENT_CHARS, post_pr_comment


def fake_post_response(html_url="https://github.com/o/r/pull/1#issuecomment-1", error=None):
    resp = MagicMock()
    resp.json.return_value = {"html_url": html_url}
    if error is not None:
        resp.raise_for_status.side_effect = error
    return resp


def test_success_returns_comment_url():
    with patch("my_agent.github_client.requests.post", return_value=fake_post_response()):
        result = post_pr_comment("o/r", 1, "looks good", token="t")

    assert result["status"] == "success"
    assert result["url"].endswith("#issuecomment-1")


def test_posts_to_correct_url_with_body_and_footer():
    with patch("my_agent.github_client.requests.post", return_value=fake_post_response()) as post:
        post_pr_comment("owner/repo", 7, "my review", token="t")

    assert post.call_args.args[0] == "https://api.github.com/repos/owner/repo/issues/7/comments"
    sent = post.call_args.kwargs["json"]["body"]
    assert sent.startswith("my review")
    assert sent.endswith(FOOTER)


def test_sends_bearer_token_header():
    with patch("my_agent.github_client.requests.post", return_value=fake_post_response()) as post:
        post_pr_comment("o/r", 1, "x", token="abc123")

    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer abc123"


def test_uses_env_token_when_none_passed(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "from-env")
    with patch("my_agent.github_client.requests.post", return_value=fake_post_response()) as post:
        post_pr_comment("o/r", 1, "x")

    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer from-env"


def test_no_token_returns_error_without_calling_github(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with patch("my_agent.github_client.requests.post") as post:
        result = post_pr_comment("o/r", 1, "x")

    assert result["status"] == "error"
    post.assert_not_called()


def test_empty_body_is_refused_without_calling_github():
    with patch("my_agent.github_client.requests.post") as post:
        result = post_pr_comment("o/r", 1, "   ", token="t")

    assert result["status"] == "error"
    post.assert_not_called()


def test_long_body_is_truncated():
    with patch("my_agent.github_client.requests.post", return_value=fake_post_response()) as post:
        post_pr_comment("o/r", 1, "a" * 100000, token="t")

    sent = post.call_args.kwargs["json"]["body"]
    assert len(sent) == MAX_COMMENT_CHARS + len(FOOTER)


def test_http_error_returns_error():
    err = requests.HTTPError("403 Client Error: Forbidden")
    with patch("my_agent.github_client.requests.post", return_value=fake_post_response(error=err)):
        result = post_pr_comment("o/r", 1, "x", token="t")

    assert result["status"] == "error"
    assert "403" in result["message"]


def test_network_failure_returns_error():
    with patch(
        "my_agent.github_client.requests.post",
        side_effect=requests.ConnectionError("network down"),
    ):
        result = post_pr_comment("o/r", 1, "x", token="t")

    assert result["status"] == "error"