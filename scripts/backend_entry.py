from __future__ import annotations

import subprocess
import sys
from pathlib import Path


# NEOS_FIX_03B_WINDOWS_NO_WINDOW_POLICY
# Prevent transient Windows console windows from child CLI tools such as git.exe.
# Stdout/stderr remain available to NEOS; only console-window creation is suppressed.
def _install_windows_no_window_policy() -> None:
    if sys.platform != "win32":
        return

    no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if not no_window:
        return

    original_popen = subprocess.Popen

    def _popen_without_console(*args, **kwargs):
        existing_flags = int(kwargs.get("creationflags", 0) or 0)
        kwargs["creationflags"] = existing_flags | no_window
        return original_popen(*args, **kwargs)

    subprocess.Popen = _popen_without_console


_install_windows_no_window_policy()


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))

from neos.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
