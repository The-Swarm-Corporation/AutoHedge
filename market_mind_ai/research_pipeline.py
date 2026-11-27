"""
Research-only pipeline for Market Mind AI.

This module implements a deterministic, testable research workflow:

    create task -> discover entities -> retrieve sources -> validate data
    -> process -> model-assisted analysis -> persist -> complete/fail

The pipeline never submits orders, connects to brokers, or performs any
real-money action. Model-assisted analysis is optional: without a configured
Qwen2.5 model the pipeline degrades gracefully and records an explicit
``unavailable`` status instead of inventing analysis.

Task states are persisted atomically and transitions are guarded so duplicate
processing of the same task cannot produce conflicting results.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator

from market_mind_ai.env_loader import qwen_is_configured
from market_mind_ai.models.qwen_client import QwenClient
from market_mind_ai.models.qwen_model import QwenModel

# --------------------------------------------------------------------------- #
# Contracts
# --------------------------------------------------------------------------- #

_ENTITY_RE = re.compile(r"\b[A-Z][A-Z0-9.\-]{0,9}\b")
_STOPWORDS = {
    "THE", "AND", "FOR", "WITH", "FROM", "THIS", "THAT", "WHAT",
    "WHEN", "WHERE", "ANALYZE", "RESEARCH", "TASK", "STOCK", "STOCKS",
    "MARKET", "JSON", "ONLY", "TRUE", "FALSE", "NULL", "AI", "CEO",
    "IPO", "ETF", "USD", "USDC", "SOL", "BTC", "ETH", "TODAY",
    "YESTERDAY", "TOMORROW", "NEWS", "LATEST", "REPORT", "QUARTER",
}
_ALLOWED_STATES = {
    "created", "discovering", "retrieving", "validating", "processing",
    "analyzing", "completed", "failed",
}


class ResearchSource(BaseModel):
    """A retrieved source document for a research task."""

    url: str
    title: str = ""
    snippet: str = ""
    retrieved_at: str = ""

    @field_validator("url")
    @classmethod
    def _url_must_be_nonempty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("url must not be empty")
        return value


class ResearchFinding(BaseModel):
    """Structured model-assisted analysis output for one entity."""

    entity: str
    summary: str = ""
    sentiment: str = "neutral"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)
    status: str = "pending"

    @field_validator("status")
    @classmethod
    def _valid_status(cls, value: str) -> str:
        if value not in {"pending", "analyzed", "unavailable", "failed"}:
            raise ValueError(f"invalid finding status: {value}")
        return value


class ResearchTask(BaseModel):
    """Persistent state of a research task."""

    task_id: str
    query: str
    state: str = "created"
    entities: List[str] = Field(default_factory=list)
    sources: List[ResearchSource] = Field(default_factory=list)
    findings: List[ResearchFinding] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    attempts: int = 0

    @field_validator("state")
    @classmethod
    def _valid_state(cls, value: str) -> str:
        if value not in _ALLOWED_STATES:
            raise ValueError(f"invalid task state: {value}")
        return value


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _task_id(query: str) -> str:
    return hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()[:16]


def _parse_json(text: Any) -> Optional[Any]:
    if not text:
        return None
    raw = str(text).strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return None


# --------------------------------------------------------------------------- #
# File-backed task store (atomic writes, no external DB required)
# --------------------------------------------------------------------------- #


class FileTaskStore:
    """Minimal JSON-file task store with atomic writes."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, task_id: str) -> Path:
        return self.directory / f"{task_id}.json"

    def load(self, task_id: str) -> Optional[ResearchTask]:
        path = self._path(task_id)
        if not path.exists():
            return None
        try:
            return ResearchTask.model_validate(json.loads(path.read_text()))
        except Exception:
            return None

    def save(self, task: ResearchTask) -> None:
        task.updated_at = _utc_now()
        path = self._path(task.task_id)
        fd, tmp_name = tempfile.mkstemp(
            dir=str(self.directory), prefix=".task-", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(task.model_dump(), handle, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, path)
        except BaseException:
            Path(tmp_name).unlink(missing_ok=True)
            raise

    def exists(self, task_id: str) -> bool:
        return self._path(task_id).exists()


# --------------------------------------------------------------------------- #
# Pipeline
# --------------------------------------------------------------------------- #


class ResearchPipeline:
    """
    Research-only workflow with explicit, auditable state transitions.

    Args:
        store: task persistence adapter (defaults to FileTaskStore).
        client: optional Qwen client for model-assisted analysis. When
            omitted, a client is created only when Qwen is configured.
        source_retriever: callable(query, entity) -> list of source dicts.
            Injected for tests; defaults to an empty-list retriever so the
            pipeline works offline without paid external APIs.
    """

    def __init__(
        self,
        store: Optional[FileTaskStore] = None,
        client: Optional[QwenClient] = None,
        source_retriever: Any = None,
        output_dir: str = "research_tasks",
    ) -> None:
        self.store = store or FileTaskStore(output_dir)
        self.client: Optional[QwenClient] = client
        if self.client is None and qwen_is_configured():
            self.client = QwenClient()
        self._retriever: Callable[[str, str], Any] = (
            source_retriever or (lambda query, entity: [])
        )
        self._cached_model: Optional[QwenModel] = None

    @property
    def model_available(self) -> bool:
        return self.client is not None and self.client.is_available

    def _model(self) -> Optional[QwenModel]:
        if not self.model_available:
            return None
        if self._cached_model is None:
            assert self.client is not None
            self._cached_model = QwenModel(client=self.client)
        return self._cached_model

    # -- stage 1: task creation ------------------------------------------- #
    def create_task(self, query: str) -> ResearchTask:
        query = str(query).strip()
        if not query:
            raise ValueError("query must not be empty")
        task = ResearchTask(
            task_id=_task_id(query),
            query=query,
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )
        # Idempotent: an existing completed task is returned unchanged.
        existing = self.store.load(task.task_id)
        if existing is not None:
            return existing
        self.store.save(task)
        return task

    # -- stage 2: entity discovery ---------------------------------------- #
    def discover_entities(self, query: str) -> List[str]:
        candidates = _ENTITY_RE.findall(query.upper())
        entities: List[str] = []
        for candidate in candidates:
            if candidate in _STOPWORDS or len(candidate) < 2:
                continue
            if candidate not in entities:
                entities.append(candidate)
        return entities[:10]

    # -- stage 3: source retrieval ---------------------------------------- #
    def retrieve_sources(
        self, query: str, entities: List[str]
    ) -> Tuple[List[ResearchSource], List[str]]:
        sources: List[ResearchSource] = []
        errors: List[str] = []
        seen: set[str] = set()
        for entity in entities:
            raw_sources = self._retriever(query, entity) or []
            for item in raw_sources:
                if isinstance(item, ResearchSource):
                    source = item
                elif isinstance(item, dict):
                    try:
                        source = ResearchSource.model_validate(item)
                    except Exception as exc:
                        errors.append(f"invalid source for {entity}: {exc}")
                        continue
                else:
                    errors.append(
                        f"invalid source for {entity}: unsupported type "
                        f"{type(item).__name__}"
                    )
                    continue
                if source.url in seen:
                    continue
                seen.add(source.url)
                if not source.retrieved_at:
                    source.retrieved_at = _utc_now()
                sources.append(source)
        return sources, errors

    # -- stage 4: data validation ----------------------------------------- #
    def validate_sources(
        self, sources: List[ResearchSource]
    ) -> Tuple[List[ResearchSource], List[str]]:
        valid: List[ResearchSource] = []
        errors: List[str] = []
        for source in sources:
            try:
                ResearchSource.model_validate(source.model_dump())
                valid.append(source)
            except Exception as exc:
                errors.append(f"invalid source {source.url!r}: {exc}")
        return valid, errors

    # -- stage 5-6: processing + model-assisted analysis ------------------ #
    def _analyze_with_model(
        self, entity: str, sources: List[ResearchSource]
    ) -> ResearchFinding:
        model = self._model()
        if model is None or not model.is_available:
            return ResearchFinding(
                entity=entity,
                summary="Model unavailable; no analysis performed",
                status="unavailable",
            )

        evidence = [s.url for s in sources][:5]
        context = " ".join(s.snippet for s in sources)[:1200]
        prompt = (
            f"Research entity: {entity}\n"
            f"Sources: {context or 'none provided'}\n"
            "Return JSON with keys: summary, sentiment, confidence, evidence."
        )
        data = model.client.complete_json(
            prompt,
            system="You are a research analyst. Respond with JSON only.",
        )
        if not data or not isinstance(data, dict):
            return ResearchFinding(
                entity=entity,
                summary="Model returned no usable analysis",
                status="failed",
                evidence=evidence,
            )
        try:
            return ResearchFinding.model_validate(
                {
                    "entity": entity,
                    "summary": str(data.get("summary", ""))[:1000],
                    "sentiment": str(data.get("sentiment", "neutral")),
                    "confidence": float(data.get("confidence", 0.0)),
                    "evidence": data.get("evidence") or evidence,
                    "status": "analyzed",
                }
            )
        except Exception:
            return ResearchFinding(
                entity=entity,
                summary="Model returned invalid structured output",
                status="failed",
                evidence=evidence,
            )

    # -- orchestration ---------------------------------------------------- #
    def run(self, query: str) -> ResearchTask:
        """Run the full workflow. Never raises for model/network failures."""
        task = self.create_task(query)
        # Duplicate processing guard: terminal states are immutable.
        if task.state in {"completed", "failed"}:
            return task

        task.attempts += 1

        def _transition(state: str) -> None:
            task.state = state
            self.store.save(task)

        try:
            _transition("discovering")
            task.entities = self.discover_entities(task.query)
            if not task.entities:
                raise ValueError("no entities discovered from query")

            _transition("retrieving")
            task.sources, retrieval_errors = self.retrieve_sources(
                task.query, task.entities
            )
            task.errors.extend(retrieval_errors)

            _transition("validating")
            task.sources, source_errors = self.validate_sources(task.sources)
            task.errors.extend(source_errors)

            _transition("processing")

            _transition("analyzing")
            task.findings = [
                self._analyze_with_model(entity, task.sources)
                for entity in task.entities
            ]
            if not task.findings:
                raise ValueError("no findings produced")

            task.state = "completed"
            self.store.save(task)
            return task
        except Exception as exc:
            task.state = "failed"
            task.errors.append(str(exc))
            self.store.save(task)
            return task
