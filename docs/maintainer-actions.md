# Maintainer-only actions for PR #58

These actions **cannot** be performed by the contributor and must not be
bypassed. They are documented here so the PR can proceed once the maintainer
is ready.

## 1. Approve `action_required` workflow runs

Five fork-PR workflows are paused pending maintainer approval because the
head branch comes from a first-time contributor fork (`djny45/AutoHedge`):

| Workflow | Latest run |
|---|---|
| Continuous Integration | <https://github.com/The-Swarm-Corporation/AutoHedge/actions/runs/46018641393> |
| Model integration (Qwen2.5) | <https://github.com/The-Swarm-Corporation/AutoHedge/actions/runs/46018641032> |
| Research pipeline CI | <https://github.com/The-Swarm-Corporation/AutoHedge/actions/runs/46018641106> |
| test | <https://github.com/The-Swarm-Corporation/AutoHedge/actions/runs/46018641003> |
| build (unit-test) | <https://github.com/The-Swarm-Corporation/AutoHedge/actions/runs/46018641121> |

**Procedure:** open each run → click **"Approve and rerun"** (or approve all
pending runs from the Actions tab). This is a deliberate GitHub security
gate for fork contributions; do not attempt to circumvent it. Once approved,
the workflows execute the same commands already validated locally:

```bash
pytest tests/ -v
python -m pytest tests/test_qwen.py -v
python -m pytest tests/test_research_pipeline.py -v
ruff check market_mind_ai tests
mypy market_mind_ai --ignore-missing-imports
mkdocs build --strict
```

## 2. Resolve the upstream billing lock

The `label` (and previously `Welcome`) checks fail with the exact check-run
annotation:

> The job was not started because your account is locked due to a billing issue.

This is an **account-level billing lock** on the upstream repository owner,
not a workflow permission or configuration defect in this PR. No change to
`.github/workflows/label.yml`, `.github/workflows/welcome.yml` or
`.github/labeler.yml` can clear it. The account owner must resolve the
billing state with GitHub, then re-run the failed check.

The branch-side labeler configuration issue (three duplicate `Documentation`
keys silently overriding each other) was already fixed in commit `475ab898`;
that fix is independent of the billing lock.

## 3. Optional real-provider validation (manual)

No real Qwen inference was executed — the contributor has no authorized
credential. To produce evidence, a maintainer with a credential should:

```bash
export QWEN_API_KEY="$(read-from-your-secret-store)"
python scripts/validate_qwen_real_inference.py
```

The script reads the key from the environment only, never prints or logs it,
uses a synthetic non-sensitive research task, and prints a `PASSED` verdict
only after a successful real call whose structured output validates. Attach
the sanitized output to PR #58. If no credential is available, leave this as
an explicitly documented optional blocker — do not claim real inference.

## 4. Merge gate

Keep PR #58 **open and unmerged** until:
- the five `action_required` runs are approved and green, and
- the billing lock is resolved and the `label` check passes (or is explicitly
  waived by the maintainer).

Real-provider validation is recommended but is not required for merge because
all inference tests are intentionally mocked and safe offline.
