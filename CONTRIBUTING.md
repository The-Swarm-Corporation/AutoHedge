# Contributing to AutoHedge

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in keys as needed
```

## Running the tests

```bash
python -m unittest discover -s tests -v
# or
pytest tests/ -v
```

Tests use fake agents and do not require API keys or network access.

## Project conventions

- Every agent response must be validated through a Pydantic model in
  `autohedge/models.py` before it is passed to the next pipeline stage.
- Tools are registered in `autohedge/tools/tools_registry.py` and attached to
  agents in `autohedge.workers.create_agents()`.
- Live trading is opt-in (`enable_trading=True`, `dry_run=False`). Never
  enable it in tests.

## Pull requests

1. Fork and create a feature branch.
2. Add or update tests for your change.
3. Run `ruff check autohedge tests` and the test suite.
4. Open a pull request describing the change and its rationale.
