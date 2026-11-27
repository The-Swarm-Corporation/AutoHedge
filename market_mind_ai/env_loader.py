"""
Load .env from project root so API keys work when running from any directory.
"""

import os
from pathlib import Path
from typing import Any

load_dotenv: Any = None
try:
    from dotenv import load_dotenv as _load_dotenv

    load_dotenv = _load_dotenv
except ImportError:  # python-dotenv is optional at import time
    pass


def find_project_env() -> Path | None:
    """Find .env by walking up from cwd (so CLI/scripts work from any subdir)."""
    cwd = Path(os.getcwd()).resolve()
    for parent in [cwd, *cwd.parents]:
        env_file = parent / ".env"
        if env_file.is_file():
            return env_file
    return None


def load_env() -> None:
    """Load .env from project root; fall back to cwd. Does not override existing env."""
    if load_dotenv is None:
        return
    env_path = find_project_env()
    if env_path:
        load_dotenv(env_path, override=False)
    else:
        load_dotenv()


def require_openai_key() -> bool:
    """Return True if OPENAI_API_KEY is set (required for swarms gpt-4.x)."""
    return bool(os.getenv("OPENAI_API_KEY"))


def require_qwen_key() -> bool:
    """Return True if QWEN_API_KEY is set (required for Qwen2.5)."""
    return bool(os.getenv("QWEN_API_KEY"))


def qwen_is_configured() -> bool:
    """Return True when Qwen2.5 is configured via environment variables."""
    return require_qwen_key()
