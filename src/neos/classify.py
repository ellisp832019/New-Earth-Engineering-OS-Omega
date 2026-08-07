from pathlib import Path

DOC_EXT = {".md", ".rst", ".txt", ".adoc", ".pdf"}
TEST_MARKERS = {"test", "tests", "spec", "specs", "__tests__"}
CONFIG_NAMES = {
    "pyproject.toml",
    "platformio.ini",
    "pubspec.yaml",
    "dockerfile",
    "cmakelists.txt",
    "package.json",
    "tsconfig.json",
    "analysis_options.yaml",
}
SOURCE_EXT = {".py", ".dart", ".c", ".cc", ".cpp", ".h", ".hpp", ".ino", ".rs", ".js", ".ts", ".java", ".kt", ".cs"}
HARDWARE_EXT = {".hex", ".bin", ".elf", ".uf2", ".dfu", ".eep", ".img", ".fw"}
CONFIG_EXT = {".yaml", ".yml", ".toml", ".ini", ".json"}
RELEASE_MARKERS = {"release", "releases", "changelog", "changes", "relnotes"}
BUILD_MARKERS = {"build", "cmake", "make", "gradle", "cargo", "workflow", "pipelines"}
HARDWARE_MARKERS = {"firmware", "hardware", "pcb", "board", "kicad", "esp32", "embedded"}


def _parts(rel: Path) -> set[str]:
    return {part.lower() for part in rel.parts}


def classify(rel: Path) -> str:
    name = rel.name.lower()
    parts = _parts(rel)
    suffix = rel.suffix.lower()

    if ".github" in parts and "workflows" in parts:
        return "ci_workflow"
    if any(marker in parts or name.startswith(f"{marker}_") or f"/{marker}/" in rel.as_posix().lower() for marker in TEST_MARKERS):
        return "test"
    if name in {"makefile", "dockerfile", "build.gradle", "build.gradle.kts", "pom.xml", "cargo.toml"} or any(
        marker in parts for marker in BUILD_MARKERS
    ):
        return "build_definition"
    if any(marker in parts for marker in RELEASE_MARKERS) or name in {"changelog.md", "release-notes.md"}:
        return "release_documentation"
    if suffix in HARDWARE_EXT or any(marker in parts for marker in HARDWARE_MARKERS):
        return "hardware_firmware_asset"
    if name in CONFIG_NAMES or suffix in CONFIG_EXT:
        return "application_configuration"
    if suffix in DOC_EXT or "docs" in parts or name in {"readme.md", "readme.rst", "readme.txt"}:
        return "documentation"
    if suffix in SOURCE_EXT:
        return "source_code"
    return "artefact"
