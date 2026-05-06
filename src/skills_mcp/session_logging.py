from __future__ import annotations

import logging
import traceback
from pathlib import Path

_ERRORS_ROOT_ATTACHED: Path | None = None


def init_project_error_logging(log_dir: Path) -> Path:
    """Ensure ``<project>/state/logs/errors.log`` exists and receives ``log_error`` lines.

    Same ``errors.log`` sink is reused if ``log_dir`` is unchanged across calls.
    Operational errors append to ``state/logs/errors.log`` only.
    """

    global _ERRORS_ROOT_ATTACHED

    root = Path(log_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    errors_path = root / "errors.log"

    lg = logging.getLogger("skills_mcp.errors")
    if _ERRORS_ROOT_ATTACHED == root and lg.handlers:
        return errors_path

    _ERRORS_ROOT_ATTACHED = root
    for h in lg.handlers:
        h.close()
    lg.handlers.clear()

    efh = logging.FileHandler(errors_path, mode="a", encoding="utf-8")
    efh.setLevel(logging.ERROR)
    efh.setFormatter(logging.Formatter("%(asctime)s ERROR %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ"))

    lg.addHandler(efh)
    lg.setLevel(logging.ERROR)
    lg.propagate = False

    return errors_path


def log_error(context: str, exc: BaseException) -> None:
    """Append one entry to ``state/logs/errors.log`` after ``configure()`` (or noop if uninitialized)."""

    lg = logging.getLogger("skills_mcp.errors")
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)).strip()
    lg.error("[%s] %s: %s\n%s", context, type(exc).__name__, exc, tb)
