"""Tests for secret redaction. No network, no AI."""

import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import review
from my_agent.agent import fetch_pr_diff
from my_agent.redact import REDACTED, redact_secrets

# ---------- the redaction function ----------


def test_masks_quoted_api_key_assignment():
    out = redact_secrets('API_KEY = "sk-12345-secret"')

    assert "sk-12345-secret" not in out
    assert "API_KEY" in out  # the name stays so the reviewer can still flag it
    assert REDACTED in out


def test_masks_password_assignment():
    out = redact_secrets('PASSWORD = "admin123"')

    assert "admin123" not in out
    assert REDACTED in out


def test_masks_dictionary_style_secret():
    out = redact_secrets('config = {"password": "hunter2"}')

    assert "hunter2" not in out


def test_masks_single_quotes_and_colon_style():
    out = redact_secrets("db_password: 'correct-horse'")

    assert "correct-horse" not in out


def test_masks_github_token():
    token = "ghp_" + "a1B2c3D4e5" * 4
    out = redact_secrets(f"the token {token} was committed")

    assert token not in out


def test_masks_fine_grained_github_token():
    token = "github_pat_" + "A1b2C3d4E5" * 4
    out = redact_secrets(f"+TOKEN_VALUE {token}")

    assert token not in out


def test_masks_google_api_key():
    key = "AIza" + "x" * 35
    out = redact_secrets(f"key is {key}")

    assert key not in out


def test_masks_aws_access_key():
    out = redact_secrets("id AKIAABCDEFGHIJKLMNOP here")

    assert "AKIAABCDEFGHIJKLMNOP" not in out


def test_masks_private_key_block():
    block = "-----BEGIN RSA PRIVATE KEY-----\nMIIEabc123\nxyz789\n-----END RSA PRIVATE KEY-----"
    out = redact_secrets(f"+{block}")

    assert "MIIEabc123" not in out
    assert "xyz789" not in out


def test_leaves_normal_code_unchanged():
    code = "def divide(a, b):\n    return a / b\n"

    assert redact_secrets(code) == code


def test_leaves_unrelated_names_unchanged():
    code = 'author = "Bob"\nusername = "alice"'

    assert redact_secrets(code) == code


def test_leaves_env_var_reads_unchanged():
    code = 'API_KEY = os.environ["API_KEY"]'

    assert redact_secrets(code) == code


def test_is_idempotent():
    once = redact_secrets('API_KEY = "sk-12345-secret"')

    assert redact_secrets(once) == once


def test_handles_empty_text():
    assert redact_secrets("") == ""


def test_is_fast_on_big_adversarial_input():
    nasty = "password" * 3000 + "a" * 20000
    start = time.time()
    redact_secrets(nasty)

    assert time.time() - start < 1.0


# ---------- wired into the pipeline ----------


def test_fetch_hides_secrets_before_the_ai_sees_them():
    diff = '+API_KEY = "sk-12345-secret"\n+PASSWORD = "admin123"\n+def f(): pass\n'
    resp = MagicMock()
    resp.text = diff
    ctx = SimpleNamespace(state={})
    with patch("my_agent.agent.requests.get", return_value=resp):
        fetch_pr_diff("o/r", 1, ctx)

    saved = ctx.state["pr_diff"]
    assert "sk-12345-secret" not in saved
    assert "admin123" not in saved
    assert "def f()" in saved


def test_review_pr_masks_secrets_before_printing_and_posting(capsys):
    leaky = 'The key `API_KEY = "sk-12345-secret"` is hardcoded.'
    run = AsyncMock(return_value=({"final_review": leaky}, {}))
    ok = {"status": "success", "url": "https://example.com/c1"}
    with patch("review.run_agent", run), patch(
        "review.post_pr_comment", return_value=ok
    ) as post:
        review.review_pr("o/r", 1)

    posted = post.call_args.args[2]
    assert "sk-12345-secret" not in posted
    assert "sk-12345-secret" not in capsys.readouterr().out