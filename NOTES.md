# NOTES.md: what I built and what I learned

> Learning log for the ADK PR review agent. Short and factual.

## Environment
Windows, Python 3.12, google-adk 2.11.0, model gemini-3.6-flash (Gemini API key).
Venv lives outside the repo at `D:\venv`.

## Commands I actually use
| Task | Command |
|---|---|
| Activate venv | `D:\venv\Scripts\activate` |
| Go to project (cmd, switches drive) | `cd /d D:\pr-review-agent` |
| Browser debug UI | `adk web` (run from the folder that CONTAINS `my_agent/`) |
| Run tests | `python -m pytest -v` |
| Review a PR from the terminal | `python review.py owner/repo 12 --dry-run` |
| Check what git will ignore | `git status --ignored` |

## Concepts I learned
- **Agent**: LLM + instruction + tools. `root_agent` is the name ADK looks for.
- **Tool**: a plain Python function. The docstring is read by the AI, so write it well.
- **State**: `output_key="x"` saves an agent's reply; `{x}` in another instruction reads it.
  A tool can write state through `ToolContext`.
- **Workflow agents**: `ParallelAgent` runs agents at the same time (total time = slowest);
  `SequentialAgent` runs in order. Both are deprecated in ADK 2.x in favour of `Workflow`.
- **Callbacks**: `before_agent_callback` can return content to skip an agent. I used it as a
  guard when no diff was fetched.
- **Runner**: `adk web` is just a UI on top of an API server. `Runner` + a session service
  runs the same agent from plain Python (that is `review.py`).
- **Reliability**: timeouts, retries that wait long enough for the rate-limit window, and
  returning error dicts from tools instead of crashing.
- **Security**: GitHub tokens with minimum permissions, secrets in `.env` / repo secrets only,
  redacting secrets before AI sees the diff and before posting, forks get no secrets.
- **Testing without AI**: fake `requests.get`, fake contexts, and a fake LLM class so tests
  never use quota.

## Gotchas that bit me
- ADK is 2.x; many tutorials show 1.x. Check the installed version first.
- cmd: plain `cd` does not change drive. Use `cd /d D:\path`.
- `adk web` blocks the terminal. `Ctrl+C` before running git commands.
- 503 UNAVAILABLE = Google overloaded, not my code.
- 429 has two kinds: per-DAY (wait ~a day or switch model) and per-MINUTE (retries with long
  delays fix it). Quotas are per model, and a redirected model name can inherit new limits.
- A 17-minute run was a bad network connection (`httpx.ReadError`). Always set timeouts.
- LLM-cited line numbers are guesses unless the diff contains them. Real GitHub diffs do.
- GitHub returns 404 (not 403) for private repos the token cannot read.
- Fork PRs get no secrets and a read-only token, so the workflow skips them.
- Old action versions (`checkout@v4`, `setup-python@v5`) run on Node 20, which GitHub is
  retiring. Use the Node 24 versions.
- Pushing a file under `.github/workflows` can need extra permission; adding it on the GitHub
  website worked.
- Private actions can only be used by other private repos of the same owner (Access setting).
- Google retires model names. Keep `MODEL` in one place.

## Docs pages I used
Get started > Python Quickstart; Models (including the 429 section); LLM Agents;
Function tools; Parallel agents; State; Callbacks (`before_agent_callback`);
Runner / sessions; Deploy > Cloud Run (read, not used).

## Decisions and trade-offs
- GitHub Action instead of a server: no hosting, no webhook, no billing. Others bring their own key.
- Posting the comment is plain Python, not an AI tool, so the AI can never write to GitHub itself.
- Kept the model hard-coded: simpler; others fork and edit.
- Skipped evals: at 5 requests per minute they would be very slow.

## If I continue
1. Fetch the diff in plain Python (6 requests per review down to 4).
2. Label-gated reviews for fork PRs.
3. Rebuild with ADK 2.0 `Workflow`.
4. Eval set with a pass rate.