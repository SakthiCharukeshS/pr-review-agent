# NOTES.md: ADK PR Review Agent

> Learning log. Short, factual, updated after every session.
> Rule: if I can't explain it in 3 lines, I haven't learned it yet.

---

## 1. Project in one line
Agent that reads a GitHub PR diff and posts a code review (style, bugs, security, summary).

## 2. Environment
| Item | Value |
|---|---|
| OS | Windows |
| Python | 3.12.10 |
| ADK version | google-adk 2.11.0 |
| Model | gemini-3.8-flash (Gemini API / AI Studio key) |
| Venv location | `D:\venv` (outside repo) |
| Repo | `D:\pr-review-agent` |

## 3. Commands I actually use
| Task | Command |
|---|---|
| Activate venv | `D:\venv\Scripts\activate` |
| Create agent project | `adk create my_agent` |
| Run in browser | `adk web` (run from the folder that CONTAINS `my_agent/`) |
| Run in terminal | `adk run my_agent` |
| Stop server | `Ctrl+C` |
| Check ADK version | `pip show google-adk` |
| Git: check ignored files | `git status --ignored` |

## 4. Concepts learned
### Agent (`root_agent`)
- **What:** the LLM + instructions + tools, defined in `my_agent/agent.py`.
- **Rule:** the variable must be named `root_agent`. ADK looks for that name.
- **Key fields:** `name`, `model`, `description`, `instruction`.
- **`instruction`** controls behavior. Change it, behavior changes.

*(add: Tools, Workflow agents, Sessions/State, Callbacks, Evaluate, Deploy as I learn them)*

## 5. Gotchas (things that bit me)
- ADK is 2.x. Many tutorials show 1.x. If code from a tutorial breaks, check the version first.
- `.env` holds the API key. It must stay in `.gitignore`. Verify with `git status --ignored`.
- `.adk/` holds the local session DB. Ignored too.
- `AFC` warning in the terminal logs: ADK internal note, ignored.
- `adk web` blocks the terminal. Stop it with `Ctrl+C` before running git commands.

## 6. Docs reading log
Docs: https://google.github.io/adk-docs

| Date | Page | Status | One-line takeaway |
|---|---|---|---|
| 2026-10-03 | Get started > Python Quickstart | done | `adk create` makes the agent, `root_agent` is the only required part |
| | Agents > Models & Authentication | skim | how to set the API key and pick a model |
| | Agents > LLM Agents | TODO | |
| | Tools > Function tools | TODO | |
| | Workflow agents (Sequential / Parallel) | TODO | |
| | Sessions & State | TODO | |
| | Callbacks | TODO | |
| | Evaluate | TODO | |
| | Deploy | TODO | |

## 7. Progress log
- **2026-10-03**: Setup done. Repo created. First agent created with `adk create`. Ran it in `adk web` and got a reply. Pushed to GitHub.

## 8. Next up
- [ ] Read LLM Agents page. Change `instruction` to "strict senior code reviewer". Test with buggy code.
- [ ] Read Function tools page. Write `get_pr_diff()` returning a hardcoded diff.
- [ ] Give the tool to the agent and ask for a review.
- [ ] Replace the fake diff with the real GitHub API.

## 9. Open questions
- (write anything confusing here, then ask)
