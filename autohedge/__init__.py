from autohedge.env_loader import load_env

load_env()

# Environment must be loaded before importing Swarms or selecting a backend.
from autohedge.main import AutoHedge  # noqa: E402

__all__ = ["AutoHedge"]
