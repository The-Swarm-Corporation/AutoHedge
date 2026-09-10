"""Offline checks for configuration, CLI transport, and research orchestration."""

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from autohedge import AutoHedge
from autohedge import backends, cli, codex_research
from autohedge.codex_research import CodexResearchDirector


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    for name in (
        "AUTOHEDGE_LLM_BACKEND",
        "AUTOHEDGE_CODEX_MODEL",
        "AUTOHEDGE_CODEX_TIMEOUT",
        "OPENAI_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    def unexpected_api_call(*args, **kwargs):
        pytest.fail(
            "The offline test attempted an API or search call"
        )

    import httpx
    import litellm

    monkeypatch.setattr(litellm, "completion", unexpected_api_call)
    monkeypatch.setattr(httpx.Client, "send", unexpected_api_call)
    monkeypatch.setattr(
        httpx.AsyncClient, "send", unexpected_api_call
    )


@pytest.fixture
def transport(monkeypatch):
    state = SimpleNamespace(
        calls=[],
        answer=None,
        returncode=0,
        error=None,
        missing=False,
    )
    monkeypatch.setattr(
        codex_research.shutil, "which", lambda name: "/test/codex"
    )

    def popen(command, **options):
        process = Mock(pid=12345, returncode=state.returncode)

        def communicate(prompt=None, timeout=None):
            if prompt is None:
                return "", ""
            state.calls.append((command, options, prompt, timeout))
            if state.error:
                raise state.error
            if not state.missing:
                output = Path(
                    command[
                        command.index("--output-last-message") + 1
                    ]
                )
                answer = (
                    f"report-{len(state.calls)}"
                    if state.answer is None
                    else state.answer
                )
                output.write_text(answer, encoding="utf-8")
            return (
                "progress, not the final answer",
                "authentication required",
            )

        process.communicate.side_effect = communicate
        context = Mock()
        context.__enter__ = Mock(return_value=process)
        context.__exit__ = Mock(return_value=False)
        state.process = process
        return context

    monkeypatch.setattr(codex_research.subprocess, "Popen", popen)
    return state


def payload(call):
    return json.loads(call[2].split("\n", 1)[1])


def test_research_pipeline_forwards_all_prior_reports(transport):
    director = CodexResearchDirector()
    result = director.run(
        "Use only this fictional dataset: price = 10."
    )
    assert len(transport.calls) == 6
    for index, call in enumerate(transport.calls):
        sent = payload(call)
        assert sent["context"]["task"].startswith("Use only")
        assert list(sent["context"]["reports"].values()) == [
            f"report-{number}" for number in range(1, index + 1)
        ]
        assert "research-only" in sent["system_prompt"]
        assert "Never invent current prices" in sent["system_prompt"]
    assert (
        "Synthesize" in payload(transport.calls[-1])["system_prompt"]
    )
    assert "Research only; no orders executed." in result
    assert "Order proposal (not executed)" in result
    assert "report-6" in result
    assert "progress" not in result

    director.run("An unrelated new dataset.")
    assert payload(transport.calls[6])["context"]["reports"] == {}


def test_transport_isolation_stdin_and_unicode(transport):
    transport.answer = "سلام 🐍"
    director = CodexResearchDirector(model="example-model", timeout=7)
    task = "سلام; $HOME `echo do-not-execute`"
    assert (
        director._generate("Research instructions", {"task": task})
        == "سلام 🐍"
    )
    command, options, prompt, timeout = transport.calls[0]
    assert command[-1] == "-"
    assert task in prompt
    assert task not in " ".join(command)
    assert not options.get("shell")
    assert command[command.index("--model") + 1] == "example-model"
    assert command[command.index("--sandbox") + 1] == "read-only"
    assert "--ignore-user-config" in command
    assert "--ephemeral" in command
    for disabled in (
        'web_search="disabled"',
        "features.shell_tool=false",
        "features.apps=false",
        "features.plugins=false",
        "features.multi_agent=false",
        "project_doc_max_bytes=0",
    ):
        assert disabled in command
    assert options["encoding"] == "utf-8"
    assert not Path(options["cwd"]).exists()
    assert timeout == 7


def test_cli_default_model_is_not_an_api_model(transport):
    CodexResearchDirector()._generate(
        "instructions", {"task": "test"}
    )
    assert "--model" not in transport.calls[0][0]


@pytest.mark.parametrize(
    "timeout", [0, -1, True, "10", None, float("nan"), float("inf")]
)
def test_invalid_timeout(timeout, transport):
    with pytest.raises(ValueError, match="positive and finite"):
        CodexResearchDirector(timeout=timeout)
    assert not transport.calls


@pytest.mark.parametrize("model", ["", " ", 123])
def test_invalid_model(model, transport):
    with pytest.raises(ValueError, match="non-empty string"):
        CodexResearchDirector(model=model)


@pytest.mark.parametrize("task", ["", " ", None, ["task"]])
def test_invalid_task(task, transport):
    with pytest.raises(ValueError, match="non-empty text task"):
        CodexResearchDirector().run(task)
    assert not transport.calls


def test_missing_cli(monkeypatch):
    monkeypatch.setattr(
        codex_research.shutil, "which", lambda _: None
    )
    with pytest.raises(FileNotFoundError, match="codex login"):
        CodexResearchDirector()


@pytest.mark.parametrize("answer", ["", " \n"])
def test_empty_response_stops_pipeline(answer, transport):
    transport.answer = answer
    with pytest.raises(RuntimeError, match="without a final"):
        CodexResearchDirector().run("dataset")
    assert len(transport.calls) == 1


def test_missing_output_file(transport):
    transport.missing = True
    with pytest.raises(RuntimeError, match="without a final"):
        CodexResearchDirector().run("dataset")


def test_failed_auth_does_not_fallback(transport):
    transport.returncode = 1
    with pytest.raises(RuntimeError, match="codex login status"):
        CodexResearchDirector().run("dataset")
    assert len(transport.calls) == 1
    assert not Path(transport.calls[0][1]["cwd"]).exists()


@pytest.mark.parametrize("interrupted", [False, True])
def test_timeout_and_interrupt_clean_up_children(
    interrupted, transport, monkeypatch
):
    transport.error = (
        KeyboardInterrupt()
        if interrupted
        else subprocess.TimeoutExpired("codex", 1)
    )
    child = Mock()
    parent = Mock()
    parent.children.return_value = [child]
    monkeypatch.setattr(
        codex_research.psutil, "Process", lambda _: parent
    )
    with pytest.raises(
        KeyboardInterrupt if interrupted else TimeoutError
    ):
        CodexResearchDirector(timeout=1).run("dataset")
    child.kill.assert_called_once()
    transport.process.kill.assert_called_once()
    assert transport.process.communicate.call_count == 2
    assert not Path(transport.calls[0][1]["cwd"]).exists()


def test_environment_config_and_explicit_overrides(
    transport, monkeypatch
):
    monkeypatch.setenv("AUTOHEDGE_LLM_BACKEND", "codex")
    monkeypatch.setenv("AUTOHEDGE_CODEX_MODEL", "env-model")
    monkeypatch.setenv("AUTOHEDGE_CODEX_TIMEOUT", "17")
    backend = backends.resolve_llm_backend()
    assert backend == "codex"
    assert backends.resolve_llm_backend("litellm") == "litellm"
    configured = backends.create_director(backend)
    assert (configured.model, configured.timeout) == ("env-model", 17)
    options = {"model": None, "timeout": 9}
    configured = backends.create_director(backend, options)
    assert (configured.model, configured.timeout) == (None, 9)
    assert options == {"model": None, "timeout": 9}


@pytest.mark.parametrize("config", [[], {"unknown": 3}])
def test_bad_codex_options(config, transport):
    with pytest.raises(ValueError):
        backends.create_director("codex", config)


def test_invalid_backend_and_mixed_config():
    with pytest.raises(ValueError, match="llm_backend"):
        backends.resolve_llm_backend("typo")
    with pytest.raises(ValueError, match="requires"):
        backends.create_director("litellm", {})


@pytest.mark.parametrize("value", ["invalid", "nan", "0"])
def test_bad_environment_timeout(value, transport, monkeypatch):
    monkeypatch.setenv("AUTOHEDGE_CODEX_TIMEOUT", value)
    with pytest.raises(ValueError):
        backends.create_director("codex")


@pytest.mark.parametrize("output_type", ["list", "dict", "str"])
def test_real_autohedge_uses_codex_without_worker_import(
    output_type, transport, monkeypatch, tmp_path
):
    monkeypatch.setitem(sys.modules, "autohedge.workers", None)
    system = AutoHedge(
        llm_backend="codex",
        output_type=output_type,
        output_dir=str(tmp_path),
    )
    result = system.run("A synthetic research dataset.")
    assert "report-6" in str(result)
    assert len(transport.calls) == 6
    assert sys.modules["autohedge.workers"] is None


def test_default_backend_still_uses_existing_director(
    monkeypatch, tmp_path
):
    director = Mock()
    director.run.return_value = "existing director response"
    monkeypatch.setitem(
        sys.modules,
        "autohedge.workers",
        SimpleNamespace(director_agent=director),
    )
    system = AutoHedge(output_type="str", output_dir=str(tmp_path))
    assert system.llm_backend == "litellm"
    assert "existing director response" in system.run("original task")
    director.run.assert_called_once_with(task="original task")


def test_cli_codex_selection_has_no_openai_warning(
    monkeypatch, capsys
):
    repl = Mock()
    monkeypatch.setattr(cli, "run_repl", repl)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "autohedge",
            "--llm-backend",
            "codex",
            "--codex-timeout",
            "8",
        ],
    )
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 0
    repl.assert_called_once_with(
        llm_backend="codex", codex_config={"timeout": 8}
    )
    assert "OPENAI_API_KEY" not in capsys.readouterr().out


def test_cli_environment_selection(monkeypatch):
    repl = Mock()
    monkeypatch.setattr(cli, "run_repl", repl)
    monkeypatch.setenv("AUTOHEDGE_LLM_BACKEND", "codex")
    monkeypatch.setattr(sys, "argv", ["autohedge"])
    with pytest.raises(SystemExit):
        cli.main()
    repl.assert_called_once_with(
        llm_backend="codex", codex_config=None
    )


@pytest.mark.parametrize(
    "args", [["--codex-model", "model"], ["--llm-backend", "typo"]]
)
def test_cli_rejects_bad_config(args, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["autohedge", *args])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2


def test_repl_passes_configuration_and_labels_research(
    monkeypatch, capsys
):
    import autohedge

    constructor = Mock()
    constructor.return_value.run.return_value = "research result"
    monkeypatch.setattr(autohedge, "AutoHedge", constructor)
    monkeypatch.setattr(cli, "_welcome", lambda: None)
    monkeypatch.setattr(cli, "_append_recent", lambda _: None)
    lines = iter(["synthetic task", "exit"])
    monkeypatch.setattr("builtins.input", lambda: next(lines))
    cli.run_repl("codex", {"model": "model"})
    constructor.assert_called_once_with(
        llm_backend="codex", codex_config={"model": "model"}
    )
    constructor.return_value.run.assert_called_once_with(
        task="synthetic task"
    )
    printed = " ".join(capsys.readouterr().out.split())
    assert "No live search or order execution" in printed
