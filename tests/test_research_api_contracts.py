"""
API contract and failure-regression tests for the research pipeline.

Contracts are validated with Pydantic; all inference is mocked. No real
model calls, brokers, paid APIs or production database migrations occur.
"""

import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from market_mind_ai.models import CycleResult
from market_mind_ai.research_pipeline import (
    FileTaskStore,
    ResearchPipeline,
    ResearchTask,
)


class ResearchApiContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _pipeline(self):
        return ResearchPipeline(store=FileTaskStore(self.tmp.name))

    def test_task_json_roundtrip_matches_api_contract(self):
        task = self._pipeline().run("Analyze NVDA")
        payload = json.loads(task.model_dump_json())
        restored = ResearchTask.model_validate(payload)
        self.assertEqual(restored.task_id, task.task_id)
        self.assertEqual(restored.state, "completed")
        self.assertIn("entities", payload)
        self.assertIn("findings", payload)
        self.assertIn("errors", payload)
        self.assertIn("attempts", payload)

    def test_persisted_task_matches_in_memory_task(self):
        p = self._pipeline()
        task = p.run("Analyze MSFT")
        loaded = p.store.load(task.task_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.findings, task.findings)
        self.assertEqual(loaded.sources, task.sources)

    def test_concurrent_duplicate_processing_is_controlled(self):
        """Two runs of the same query must not leave divergent state."""
        store = FileTaskStore(self.tmp.name)
        p1 = ResearchPipeline(store=store)
        p2 = ResearchPipeline(store=store)
        results = []
        threads = [
            threading.Thread(target=lambda p=p: results.append(p.run("Analyze NVDA")))
            for p in (p1, p2)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].task_id, results[1].task_id)
        self.assertEqual(results[0].state, results[1].state)
        self.assertEqual(results[0].entities, results[1].entities)

    def test_environment_isolation_from_real_credentials(self):
        """No QWEN_API_KEY leaks into persisted task payloads."""
        with patch.dict(
            "os.environ", {"QWEN_API_KEY": "super-secret-test-value"}, clear=True
        ):
            task = self._pipeline().run("Analyze NVDA")
        raw = (Path(self.tmp.name) / f"{task.task_id}.json").read_text()
        self.assertNotIn("super-secret-test-value", raw)

    def test_trading_pipeline_result_still_validates(self):
        """Legacy pipeline contract is unchanged by research additions."""
        payload = {
            "task": "Analyze NVDA",
            "tickers": ["NVDA"],
            "results": [],
            "errors": [],
            "executions": [],
        }
        result = CycleResult.model_validate(payload)
        self.assertEqual(result.task, "Analyze NVDA")
        self.assertEqual(result.executions, [])


if __name__ == "__main__":
    unittest.main()
