"""frankensettings: keep one settings file in sync between a public template and a private live file."""
from importlib.metadata import PackageNotFoundError, version

from .fileio import InputError
from .merge import KeyConflictError, deep_merge
from .paths import collapse_env, expand_env
from .privacy import is_private_permission
from .pull import pull_merge
from .report import missing_report


def _read_version() -> str:
    try:
        return version("frankensettings")
    except PackageNotFoundError:
        return "0+unknown"


__version__ = _read_version()

__all__ = [
    "InputError",
    "KeyConflictError",
    "__version__",
    "collapse_env",
    "deep_merge",
    "expand_env",
    "is_private_permission",
    "missing_report",
    "pull_merge",
]
