#!/usr/bin/env python3
"""
Optional, MANUAL validation of one real Qwen2.5 inference call.

This script is NOT part of CI and is never run automatically. It exists so a
maintainer with an authorized credential can produce verifiable evidence for
PR #58 without exposing the secret.

Safety properties:
  - Reads QWEN_API_KEY from the process environment only.
  - Never prints, logs, or writes the key (or any Authorization header).
  - Uses a non-sensitive synthetic research task.
  - Prints only the validated structured result and a pass/fail verdict.
  - Exits with status 0 only when a real inference call succeeded and the
    structured output passed validation.

Usage (credential supplied by the operator's secret store):

    export QWEN_API_KEY="$(your-secret-store read qwen-api-key)"
    python scripts/validate_qwen_real_inference.py

If QWEN_API_KEY is unset, the script reports SKIPPED and exits 0 — it does
NOT claim that real inference succeeded.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from market_mind_ai.models.qwen_client import QwenClient  # noqa: E402

# Non-sensitive, synthetic research task — no real money, markets or PII.
SYNTHETIC_ENTITY = "SYNTHETIC-TEST-ENTITY"
SYNTHETIC_CONTEXT = (
    "Synthetic validation fixture. No real market data, no personal data, "
    "no trading decision. Respond with a brief summary, a sentiment label, "
    "and a confidence between 0 and 1."
)


def main() -> int:
    client = QwenClient()

    if not client.config.is_configured:
        print("RESULT: SKIPPED — QWEN_API_KEY is not set; no network call made.")
        print("Real inference was NOT validated.")
        return 0

    problems = client.config.validate()
    if problems:
        # Print only problem categories, never values.
        print("RESULT: SKIPPED — invalid configuration:")
        for problem in problems:
            print(f"  - {problem}")
        return 0

    available, reason = client.check_availability()
    if not available:
        print("RESULT: FAILED — provider unreachable (reason redacted).")
        print(f"  reason category: {type(reason).__name__}")
        return 1

    result = client.complete_research(SYNTHETIC_ENTITY, SYNTHETIC_CONTEXT)
    client.close()

    if result is None:
        print("RESULT: FAILED — no validated structured output returned.")
        return 1

    print("RESULT: PASSED — real Qwen inference executed and validated.")
    print(f"  summary:    {result['summary'][:200]}")
    print(f"  sentiment:  {result['sentiment']}")
    print(f"  confidence: {result['confidence']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
