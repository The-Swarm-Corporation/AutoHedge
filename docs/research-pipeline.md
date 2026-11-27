# Research Pipeline and Qwen2.5 Integration

## Research-only boundary

This project is research-only. The research pipeline never connects to a
broker, submits orders, or performs real-money transactions. The legacy
`MarketMindAI` trading pipeline keeps `enable_trading=False` and
`dry_run=True` by default; signed order submission requires an explicit
opt-in call site.

## Required configuration

Copy `.env.example` to `.env` **outside version control** and set only the
variables you need. All model configuration is environment-driven — no
credentials or machine-specific model paths are stored in the repository.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `QWEN_API_KEY` | For model analysis | unset | Bearer token for Qwen-compatible API |
| `QWEN_API_BASE` | no | `https://dashscope.aliyuncs.com/api/v1` | OpenAI-compatible base URL |
| `QWEN_MODEL` | no | `qwen2.5-1.5b-instruct` | Model identifier |
| `QWEN_TIMEOUT` | no | `30` | Per-request timeout (seconds) |
| `QWEN_MAX_TOKENS` | no | `4096` | Max response tokens |
| `QWEN_TEMPERATURE` | no | `0.7` | Sampling temperature |

Without `QWEN_API_KEY` the pipeline still runs: findings are recorded with
status `unavailable`, and the task completes with an explicit audit trail.
No network call is made when the model is unconfigured.

### Using the OpenCode Packet.ai provider

Qwen2.5 1.5B Instruct is available through the configured `packet` provider
in OpenCode. To run the real model through OpenCode:

```bash
opencode model packet/qwen-qwen2-5-1-5b-instruct
```

Do **not** commit API keys. OpenCode reads them from the local config file
(`~/.config/opencode/packet_api_key`).

## Research workflow

`ResearchPipeline.run(query)` executes:

1. **Task creation** — deterministic SHA-256-derived task ID; duplicate
   processing of a completed/failed task is a no-op.
2. **Entity discovery** — uppercase entity tokens from the query, with
   stopwords filtered.
3. **Source retrieval** — via an injected retriever (defaults to offline,
   empty sources; no paid APIs).
4. **Data validation** — Pydantic validation of every source; invalid
   sources are recorded in `task.errors` and dropped.
5. **Processing** — state transition recorded atomically.
6. **Model-assisted analysis** — optional; `QwenClient.complete_research`
   validates `summary`, `sentiment`, and `confidence` (0–1).
7. **Result persistence** — atomic JSON-file writes with `os.replace`.
8. **Completion/failure** — terminal state with full error and audit trail.

State transitions are persisted at each stage and guarded so concurrent
runs of the same query cannot leave divergent state.

## Tests and CI

```bash
python -m pytest tests/ -v          # full suite
python -m pytest tests/test_qwen.py -v
python -m pytest tests/test_research_pipeline.py -v
python -m pytest tests/test_research_api_contracts.py -v
ruff check market_mind_ai tests
mypy market_mind_ai --ignore-missing-imports
```

All model-inference tests use **mocked** HTTP clients. No test claims real
Qwen inference. CI workflows under `.github/workflows/` call reusable stages:
`_python-setup.yml`, `model-integration.yml`, `research-pipeline.yml`. They
require no API keys, paid external services or production database access.
