"""Select an AutoHedge backend after .env and CLI options are loaded."""

import os


def resolve_llm_backend(value: str | None = None) -> str:
    """Resolve explicit selection before the environment and default."""
    backend = (
        value
        if value is not None
        else os.getenv("AUTOHEDGE_LLM_BACKEND", "litellm")
    )
    if backend not in {"litellm", "codex"}:
        raise ValueError("llm_backend must be 'litellm' or 'codex'")
    return backend


def create_director(backend: str, codex_config: dict | None = None):
    """Lazily construct only the selected backend."""
    backend = resolve_llm_backend(backend)
    if backend == "litellm":
        if codex_config is not None:
            raise ValueError(
                "codex_config requires llm_backend='codex'"
            )
        from autohedge.workers import director_agent

        return director_agent

    if codex_config is not None and not isinstance(
        codex_config, dict
    ):
        raise ValueError("codex_config must be a dictionary")
    config = dict(codex_config or {})
    unknown = config.keys() - {"model", "timeout"}
    if unknown:
        raise ValueError(
            "Unknown codex_config options: "
            + ", ".join(sorted(unknown))
        )
    if "model" not in config:
        config["model"] = os.getenv("AUTOHEDGE_CODEX_MODEL") or None
    if "timeout" not in config:
        try:
            config["timeout"] = float(
                os.getenv("AUTOHEDGE_CODEX_TIMEOUT", "180")
            )
        except ValueError as error:
            raise ValueError(
                "AUTOHEDGE_CODEX_TIMEOUT must be a number"
            ) from error

    from autohedge.codex_research import CodexResearchDirector

    return CodexResearchDirector(**config)
