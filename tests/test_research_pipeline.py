"""
Research pipeline integration tests.

All model inference here is MOCKED via injected fake clients. No real Qwen
API calls or paid external APIs are made; actual model inference is never
claimed by these tests.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from market_mind_ai.models.qwen_client import QwenClient
from market_mind_ai.research_pipeline import (
    FileTaskStore,
    ResearchFinding,
    ResearchPipeline,
    ResearchSource,
    ResearchTask,
)


class FakeClient:
    """Mock Qwen client: returns canned structured responses."""

    def __init__(self, response=None, available=True):
        self.response = response
        self.available = available
        self.calls = []

    @property
    def is_available(self):
        return self.available

    def complete_json(self, prompt, system=None, **kwargs):
        self.calls.append((prompt, system))
        return self.response

    def close(self):
        pass


class ResearchPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _pipeline(self, client=None, retriever=None):
        return ResearchPipeline(
            store=FileTaskStore(self.tmp.name),
            client=client,
            source_retriever=retriever,
        )

    def test_full_workflow_offline_completes_with_unavailable_model(self):
        p = self._pipeline()
        task = p.run("Analyze NVDA and MSFT")
        self.assertEqual(task.state, "completed")
        self.assertEqual(task.entities, ["NVDA", "MSFT"])
        self.assertEqual(len(task.findings), 2)
        self.assertTrue(all(f.status == "unavailable" for f in task.findings))
        self.assertTrue((Path(self.tmp.name) / f"{task.task_id}.json").exists())

    def test_idempotent_task_creation(self):
        p = self._pipeline()
        first = p.run("Analyze NVDA")
        second = p.run("Analyze NVDA")
        self.assertEqual(first.task_id, second.task_id)
        self.assertEqual(second.attempts, 1)
        self.assertEqual(second.state, "completed")

    def test_entity_discovery_filters_stopwords(self):
        p = self._pipeline()
        entities = p.discover_entities("Analyze the market for NVDA and MSFT")
        self.assertIn("NVDA", entities)
        self.assertIn("MSFT", entities)
        self.assertNotIn("THE", entities)
        self.assertNotIn("MARKET", entities)

    def test_source_retrieval_validation_and_deduplication(self):
        def retriever(query, entity):
            return [
                {"url": f"https://example.com/{entity}", "title": "Source", "snippet": "positive"},
                {"url": f"https://example.com/{entity}"},
                {"url": ""},
            ]

        p = self._pipeline(retriever=retriever)
        task = p.run("Analyze NVDA")
        self.assertEqual(task.state, "completed")
        self.assertEqual(len(task.sources), 1)
        self.assertTrue(any("invalid source" in e for e in task.errors))

    def test_model_assisted_analysis_with_mocked_structured_output(self):
        client = FakeClient(
            response={
                "summary": "Positive momentum from mocked analysis",
                "sentiment": "bullish",
                "confidence": 0.85,
                "evidence": ["https://example.com/NVDA"],
            }
        )
        p = self._pipeline(client=client)
        task = p.run("Analyze NVDA")
        self.assertEqual(task.state, "completed")
        self.assertEqual(task.findings[0].status, "analyzed")
        self.assertEqual(task.findings[0].sentiment, "bullish")
        self.assertEqual(task.findings[0].confidence, 0.85)
        self.assertTrue(client.calls)

    def test_invalid_model_output_is_rejected(self):
        for bad in (
            {"summary": 123, "sentiment": "bullish", "confidence": 5.0},
            "not a dict",
        ):
            with self.subTest(bad=bad):
                p = self._pipeline(client=FakeClient(response=bad))
                task = p.run("Analyze NVDA")
                self.assertEqual(task.state, "completed")
                self.assertEqual(task.findings[0].status, "failed")

    def test_model_unavailable_degrades_gracefully(self):
        p = self._pipeline(client=FakeClient(available=False))
        task = p.run("Analyze NVDA")
        self.assertEqual(task.state, "completed")
        self.assertEqual(task.findings[0].status, "unavailable")

    def test_empty_query_fails_validation(self):
        p = self._pipeline()
        with self.assertRaises(ValueError):
            p.create_task("   ")

    def test_no_entities_marks_task_failed(self):
        p = self._pipeline()
        task = p.run("Analyze the market today")
        self.assertEqual(task.state, "failed")
        self.assertTrue(any("no entities" in e for e in task.errors))

    def test_corrupt_task_file_is_ignored(self):
        task_id = "deadbeefdeadbeef"
        (Path(self.tmp.name) / f"{task_id}.json").write_text("not json")
        store = FileTaskStore(self.tmp.name)
        self.assertIsNone(store.load(task_id))

    def test_task_model_rejects_invalid_state(self):
        with self.assertRaises(ValueError):
            ResearchTask(task_id="x", query="q", state="bogus")

    def test_source_model_rejects_empty_url(self):
        with self.assertRaises(ValueError):
            ResearchSource(url="   ")

    def test_finding_model_rejects_invalid_status(self):
        with self.assertRaises(ValueError):
            ResearchFinding(entity="NVDA", status="bogus")


class ResearchPipelineQwenConfigTests(unittest.TestCase):
    """Verify the research pipeline reads model config from env only."""

    def test_pipeline_uses_configured_qwen_client(self):
        env = {
            "QWEN_API_KEY": "test-key",
            "QWEN_API_BASE": "https://example.invalid/v1",
        }
        with patch.dict(os.environ, env, clear=True):
            with tempfile.TemporaryDirectory() as d:
                p = ResearchPipeline(output_dir=d)
                self.assertTrue(p.model_available)
                self.assertIsInstance(p.client, QwenClient)
                self.assertEqual(
                    p.client.config.api_base, "https://example.invalid/v1"
                )
                p.client.close()

    def test_pipeline_without_qwen_key_has_no_client(self):
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as d:
                p = ResearchPipeline(output_dir=d)
                self.assertFalse(p.model_available)
                self.assertIsNone(p.client)


class ResearchRetryAndAuditTests(unittest.TestCase):
    """Retry, lineage and audit regressions."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = FileTaskStore(self.tmp.name)

    def test_failed_task_can_be_retried_and_preserves_lineage(self):
        p = ResearchPipeline(store=self.store)
        failed = p.run("Analyze the market today")  # no entities -> failed
        self.assertEqual(failed.state, "failed")
        self.assertEqual(failed.attempts, 1)
        self.assertEqual(
            [t.state for t in failed.history][-1], "failed"
        )

        # Retry with a query that now yields entities changes the task ID, so
        # simulate a transient failure on the same query via a failing
        # retriever, then a working one.
        def failing(q, e):
            raise RuntimeError("offline")

        p1 = ResearchPipeline(store=self.store, source_retriever=failing)
        first = p1.run("Analyze NVDA")
        self.assertEqual(first.state, "failed")

        def working(q, e):
            return [{"url": "https://example.com/NVDA"}]

        p2 = ResearchPipeline(store=self.store, source_retriever=working)
        retried = p2.retry("Analyze NVDA")
        self.assertIsNotNone(retried)
        self.assertEqual(retried.state, "completed")
        self.assertEqual(retried.attempts, 2)
        states = [t.state for t in retried.history]
        self.assertIn("failed", states)
        self.assertIn("created", states)
        self.assertEqual(states[-1], "completed")

    def test_retry_of_completed_task_is_noop(self):
        p = ResearchPipeline(store=self.store)
        done = p.run("Analyze NVDA")
        retried = p.retry("Analyze NVDA")
        self.assertEqual(retried.attempts, 1)
        self.assertEqual(retried.state, "completed")
        self.assertEqual(retried.history, done.history)

    def test_retry_of_missing_task_returns_none(self):
        p = ResearchPipeline(store=self.store)
        self.assertIsNone(p.retry("never seen"))

    def test_audit_timeline_records_every_stage(self):
        p = ResearchPipeline(store=self.store)
        task = p.run("Analyze NVDA")
        states = [t.state for t in task.history]
        for expected in (
            "discovering", "retrieving", "validating", "processing",
            "analyzing", "completed",
        ):
            self.assertIn(expected, states)
        self.assertTrue(all(t.at for t in task.history))

    def test_failure_records_error_in_timeline(self):
        p = ResearchPipeline(store=self.store)
        task = p.run("Analyze the market today")
        self.assertEqual(task.state, "failed")
        self.assertTrue(any(t.note for t in task.history))


if __name__ == "__main__":
    unittest.main()
