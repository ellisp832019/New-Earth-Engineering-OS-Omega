from __future__ import annotations

from pathlib import Path
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
_src = Path(__file__).resolve().parent.parent / "src" / "neos"
if _src.exists():
    __path__.append(str(_src))

__version__ = "1.2.0"

from .cli import main  # noqa: E402

