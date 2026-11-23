from autohedge.env_loader import load_env

load_env()

from autohedge.main import AutoHedge  # noqa: E402  (env must load first)

__all__ = ["AutoHedge"]
