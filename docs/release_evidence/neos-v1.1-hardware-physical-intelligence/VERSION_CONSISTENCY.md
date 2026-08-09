# Version Consistency

Observed canonical values:

| Path | Value | Role |
| --- | --- | --- |
| `VERSION` | `1.1.0` | repository source version |
| `pyproject.toml` | `1.1.0` | Python package version |
| `src/neos/__init__.py` | `1.1.0` | Python source version |
| `neos/__init__.py` | `1.1.0` | namespace package version |
| `src/neos/service/models.py` | `1.1.0` | service default version |
| `apps/desktop/pubspec.yaml` | `1.1.0+1` | Flutter build name |
| `apps/desktop/windows/runner/Runner.rc` | `1.1.0` | Windows version string fallback |
| `scripts/package_windows.ps1` | `1.1.0` | package naming and manifest version |
| `dist\\New-Earth-Engineering-OS-Windows-v1.1.0\\VERSION` | `1.1.0` | shipped package version |
| `dist\\New-Earth-Engineering-OS-Windows-v1.1.0\\BUILD_MANIFEST.json` | `1.1.0` | packaged build version |

Database schema remained:

- `11`

API version remained:

- `v1`
