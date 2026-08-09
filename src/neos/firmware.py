from __future__ import annotations

import configparser
import hashlib
import json
import os
import re
import shlex
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .db import connect
from .hardware import build_hardware_intelligence

FIRMWARE_SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hpp",
    ".ino",
    ".inc",
    ".S",
    ".s",
    ".ld",
    ".csv",
    ".json",
    ".ini",
    ".toml",
    ".yaml",
    ".yml",
}

FIRMWARE_SOURCE_NAMES = {
    "platformio.ini",
    "sdkconfig",
    "sdkconfig.defaults",
    "CMakeLists.txt",
    "Kconfig",
    "partition.csv",
    "partitions.csv",
}

SOURCE_EXCLUDES = {
    ".git",
    ".neos",
    ".venv",
    ".pio",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".dart_tool",
    "build",
    "dist",
    "node_modules",
}

TASK_CREATE_RE = re.compile(r"\b(?P<api>xTaskCreate(?:PinnedToCore)?)\s*\((?P<args>.*?)\)", re.DOTALL)
TASK_NAME_RE = re.compile(r'"([^"]{1,64})"')
ISR_ATTACH_RE = re.compile(r"attachInterrupt\s*\(\s*([^,]+),\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:,\s*([^)]+))?\)", re.MULTILINE)
ISR_ATTR_RE = re.compile(r"\b(?:IRAM_ATTR|ISR_ATTR|interrupt)\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
TIMER_RE = re.compile(r"\b(xTimerCreate|esp_timer_create_args_t|Ticker\b|Ticker\s+[A-Za-z_])", re.IGNORECASE)
STATE_ENUM_RE = re.compile(r"enum\s+(?:class\s+)?State(?:[^{]*)\{([^}]*)\}", re.IGNORECASE | re.DOTALL)
SWITCH_STATE_RE = re.compile(r"switch\s*\(\s*state\s*\)", re.IGNORECASE)
CASE_STATE_RE = re.compile(r"case\s+([A-Za-z_][A-Za-z0-9_:]*)\s*:")
STATE_ASSIGN_RE = re.compile(r"\bstate\s*=\s*([A-Za-z_][A-Za-z0-9_:]*)\b")
FUNCTION_DEF_RE = re.compile(r"(?m)^[^\S\r\n]*(?:[A-Za-z_][A-Za-z0-9_<>\*&:\s]+?)\b(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\([^;{}]*\)\s*\{")
QUEUE_CREATE_RE = re.compile(r"\b(xQueueCreate(?:Static)?|QueueHandle_t)\b", re.IGNORECASE)
QUEUE_USE_RE = re.compile(r"\b(xQueueSend(?:FromISR)?|xQueueOverwrite(?:FromISR)?|xQueueReceive(?:FromISR)?)\s*\(", re.IGNORECASE)
SEMAPHORE_USE_RE = re.compile(r"\b(xSemaphoreCreate(?:Mutex|Binary|Counting)?|xSemaphoreTake(?:FromISR)?|xSemaphoreGive(?:FromISR)?)\s*\(", re.IGNORECASE)
EVENT_GROUP_USE_RE = re.compile(r"\b(xEventGroupCreate|xEventGroupWaitBits|xEventGroupSetBits(?:FromISR)?)\s*\(", re.IGNORECASE)
NOTIFY_USE_RE = re.compile(r"\b(?:xTaskNotifyGive|ulTaskNotifyTake|xTaskNotify(?:Wait|FromISR)?|vTaskNotifyGiveFromISR)\s*\(", re.IGNORECASE)
TIMING_DELAY_RE = re.compile(r"\b(delay|vTaskDelay|vTaskDelayUntil|sleep|usleep|sleep_ms|sleep_us)\s*\((.*?)\)", re.IGNORECASE | re.DOTALL)
TIMING_WAIT_RE = re.compile(r"\b(xQueueReceive|xSemaphoreTake|xEventGroupWaitBits|ulTaskNotifyTake)\s*\((.*?)\)", re.IGNORECASE | re.DOTALL)
WATCHDOG_RE = re.compile(r"\b(?:esp_task_wdt|wdt|watchdog)\b", re.IGNORECASE)
PACKET_STRUCT_RE = re.compile(r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{", re.MULTILINE)
SERIAL_BEGIN_RE = re.compile(r"\bSerial(?:\d+)?\.begin\s*\(\s*([^)]+)\)", re.IGNORECASE)
WIRE_BEGIN_RE = re.compile(r"\b(?:Wire|Wire1)\.begin\s*\(\s*([^)]+)\)", re.IGNORECASE)
SPI_BEGIN_RE = re.compile(r"\bSPI\.begin\s*\(\s*([^)]+)\)", re.IGNORECASE)
PERIPHERAL_HINTS = {
    "i2c": ("wire.begin", "i2c", "sda", "scl"),
    "spi": ("spi.begin", "spi", "mosi", "miso", "sck"),
    "uart": ("serial", "uart", "hardwareserial", "printf"),
    "gpio": ("pinmode", "digitalwrite", "digitalread", "gpio"),
    "pwm": ("ledc", "pwm"),
    "adc": ("analogread", "adc"),
    "dac": ("dac",),
    "can": ("can",),
    "usb": ("usb",),
    "ble": ("ble", "bluetooth"),
    "mqtt": ("mqtt",),
    "http": ("httpclient", "httpserver", "http "),
}
PROTOCOL_HINTS = {
    "i2c": ("wire.begin", "i2c"),
    "spi": ("spi.begin", "spi"),
    "uart": ("serial", "uart"),
    "http": ("httpclient", "httpserver", "rest"),
    "mqtt": ("mqtt",),
    "ble": ("ble",),
    "can": ("can",),
}
GPIO_RE = re.compile(r"\b(GPIO\d+)\b", re.IGNORECASE)
PIN_DEFINE_RE = re.compile(r"^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*PIN[A-Za-z0-9_]*)\s+([0-9]+)\b", re.IGNORECASE | re.MULTILINE)
PIN_ASSIGN_RE = re.compile(
    r"\b(?:static\s+)?(?:const\s+)?(?:int|uint8_t|uint16_t|uint32_t|long|short)\s+([A-Za-z_][A-Za-z0-9_]*PIN[A-Za-z0-9_]*)\s*=\s*([0-9]+)\b",
    re.IGNORECASE,
)


class _CaseSensitiveConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr: str) -> str:  # type: ignore[override]
        return optionstr
BUFFER_RE = re.compile(r"\b(?:static\s+)?(?:uint8_t|int8_t|char|byte|uint16_t|int16_t|uint32_t|int32_t|float|double)\s+[A-Za-z_][A-Za-z0-9_]*\s*\[\s*(\d+)\s*\]", re.IGNORECASE)
BLOCKING_RE = re.compile(r"\b(?:delay|sleep|vTaskDelay|waitFor|wait_until|blocking)\s*\(", re.IGNORECASE)
TASK_WAIT_RE = re.compile(r"\b(?:xQueueReceive|xSemaphoreTake|ulTaskNotifyTake|xEventGroupWaitBits)\s*\(", re.IGNORECASE)
PLATFORMIO_SECTION_RE = re.compile(r"^\[(?P<section>[^\]]+)\]\s*$", re.MULTILINE)
DETECTOR_VERSION = "firmware-static-2026-08-heuristic-hardened-v1"
GENERIC_SIGNAL_TOKENS = {
    "gpio",
    "pin",
    "num",
    "signal",
    "port",
    "channel",
    "io",
    "data",
    "cmd",
}
KNOWN_ROLE_TOKENS = {
    "relay",
    "sensor",
    "led",
    "button",
    "sda",
    "scl",
    "tx",
    "rx",
    "mosi",
    "miso",
    "sck",
    "cs",
    "csn",
    "chipselect",
    "uart",
    "i2c",
    "spi",
    "can",
    "pwm",
    "adc",
    "dac",
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _json_dumps(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _confidence_label(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 0.8:
        return "high_confidence"
    if score >= 0.55:
        return "moderate_confidence"
    if score > 0.0:
        return "low_confidence"
    return "unknown"


def _split_call_args(arguments: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    quote: str | None = None
    escape = False
    for char in arguments:
        if escape:
            current.append(char)
            escape = False
            continue
        if char == "\\" and quote is not None:
            current.append(char)
            escape = True
            continue
        if quote is not None:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            current.append(char)
            quote = char
            continue
        if char in "([{":
            depth += 1
            current.append(char)
            continue
        if char in ")]}":
            depth = max(0, depth - 1)
            current.append(char)
            continue
        if char == "," and depth == 0:
            part = "".join(current).strip()
            if part:
                parts.append(part)
            current = []
            continue
        current.append(char)
    part = "".join(current).strip()
    if part:
        parts.append(part)
    return parts


def _strip_wrappers(value: str) -> str:
    cleaned = value.strip().strip(",")
    cleaned = re.sub(r"^\((.*)\)$", r"\1", cleaned)
    cleaned = re.sub(r"^pdMS_TO_TICKS\((.*)\)$", r"\1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^portTICK_PERIOD_MS\s*\*\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()
    return cleaned


def _parse_int_literal(value: str) -> int | None:
    cleaned = _strip_wrappers(value).strip()
    cleaned = cleaned.rstrip("uUlL")
    if cleaned.startswith("0x"):
        try:
            return int(cleaned, 16)
        except ValueError:
            return None
    if re.fullmatch(r"-?\d+", cleaned):
        try:
            return int(cleaned)
        except ValueError:
            return None
    return None


def _extract_braced_block(text: str, open_index: int) -> tuple[str, int]:
    depth = 0
    start = open_index
    for idx in range(open_index, len(text)):
        char = text[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : idx], idx
    return text[start + 1 :], len(text)


def _normalize_identifier(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _signal_tokens(value: str | None) -> set[str]:
    tokens = {token for token in re.split(r"[^A-Za-z0-9]+", (value or "").lower()) if token}
    return {token for token in tokens if token not in GENERIC_SIGNAL_TOKENS}


def _signals_equivalent(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    left_norm = _normalize_identifier(left)
    right_norm = _normalize_identifier(right)
    if not left_norm or not right_norm:
        return False
    if left_norm == right_norm:
        return True
    left_tokens = _signal_tokens(left)
    right_tokens = _signal_tokens(right)
    if not left_tokens or not right_tokens:
        return False
    if left_tokens == right_tokens:
        return True
    return bool(left_tokens & right_tokens)


def _conditional_scope(text: str, line_number: int) -> tuple[str, list[str]]:
    lines = text.splitlines()
    stack: list[str] = []
    for index, raw_line in enumerate(lines[: max(0, line_number - 1)], start=1):
        stripped = raw_line.strip()
        if stripped.startswith(("#if ", "#ifdef", "#ifndef")):
            stack.append(stripped)
        elif stack and stripped.startswith(("#elif", "#else")):
            stack[-1] = stripped
        elif stripped.startswith("#endif") and stack:
            stack.pop()
    return ("conditional_compilation" if stack else "global", list(stack))


def _function_blocks(text: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for match in FUNCTION_DEF_RE.finditer(text):
        brace_index = text.find("{", match.end() - 1)
        if brace_index < 0:
            continue
        body, end_index = _extract_braced_block(text, brace_index)
        blocks.append(
            {
                "name": match.group("name"),
                "start_line": _line_number(text, match.start()),
                "end_line": _line_number(text, end_index),
                "body": body,
                "kind": "function",
            }
        )
    return blocks


def _line_context(text: str, line_number: int, path: str | None = None) -> str:
    blocks = _function_blocks(text)
    for block in blocks:
        if block["start_line"] <= line_number <= block["end_line"]:
            name = str(block["name"]).lower()
            if "setup" in name:
                return "setup"
            if "loop" in name:
                return "loop"
            if "task" in name:
                return "task"
            if "isr" in name or "interrupt" in name:
                return "isr"
            return "function"
    lowered_path = (path or "").lower()
    if "setup" in lowered_path:
        return "setup"
    if "task" in lowered_path:
        return "task"
    if "isr" in lowered_path or "interrupt" in lowered_path:
        return "isr"
    return "unknown"


def _normalize_duration(value: str, units: str | None) -> tuple[float | None, str | None]:
    if not value:
        return None, units
    cleaned = _strip_wrappers(value)
    numeric = _parse_int_literal(cleaned)
    if numeric is None:
        match = re.fullmatch(r"(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>ms|us|s|sec|secs|second|seconds|tick|ticks)?", cleaned, re.IGNORECASE)
        if not match:
            return None, units
        numeric_value = float(match.group("num"))
        unit = (match.group("unit") or units or "").lower()
    else:
        numeric_value = float(numeric)
        unit = (units or "").lower()
    if unit in {"ms", "millisecond", "milliseconds"}:
        return numeric_value, "ms"
    if unit in {"us", "microsecond", "microseconds"}:
        return numeric_value / 1000.0, "ms"
    if unit in {"s", "sec", "secs", "second", "seconds"}:
        return numeric_value * 1000.0, "ms"
    if unit in {"tick", "ticks"}:
        return numeric_value, "ticks"
    return numeric_value, units


def _stable_id(*parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _split_items(value: str | None) -> list[str]:
    if not value:
        return []
    items: list[str] = []
    for chunk in re.split(r"[\n,]", value):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            items.extend(part for part in shlex.split(chunk) if part)
        except ValueError:
            items.extend(part for part in chunk.split() if part)
    cleaned = [item.strip().strip('"').strip("'") for item in items if item.strip().strip('"').strip("'")]
    return cleaned


def _source_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    name = path.name.lower()
    if name == "platformio.ini":
        return "build_configuration"
    if name in {"sdkconfig", "sdkconfig.defaults", "kconfig"}:
        return "build_configuration"
    if name in {"cmakelists.txt", "partition.csv", "partitions.csv"}:
        return "build_configuration"
    if suffix in {".c", ".cc", ".cpp", ".cxx", ".ino", ".S", ".s"}:
        return "source"
    if suffix in {".h", ".hpp", ".inc"}:
        return "header"
    if suffix in {".ld"}:
        return "linker_script"
    if suffix in {".csv", ".json", ".toml", ".yaml", ".yml", ".ini"}:
        return "configuration"
    return "source"


def _language_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".c", ".cc", ".cpp", ".cxx"}:
        return "c++"
    if suffix in {".ino"}:
        return "arduino"
    if suffix in {".h", ".hpp", ".inc", ".S", ".s"}:
        return "c-family"
    if suffix in {".py"}:
        return "python"
    return "text"


def _firmware_paths(repo_root: Path) -> list[Path]:
    results: list[Path] = []
    for base, dirs, files in os.walk(repo_root):
        dirs[:] = sorted(d for d in dirs if d not in SOURCE_EXCLUDES)
        base_path = Path(base)
        for name in sorted(files):
            path = base_path / name
            rel = path.relative_to(repo_root)
            lowered = rel.as_posix().lower()
            if name in FIRMWARE_SOURCE_NAMES:
                results.append(rel)
                continue
            if path.suffix.lower() in FIRMWARE_SOURCE_SUFFIXES and any(
                token in lowered for token in ("firmware", "embedded", "platformio", "esp32", "stm32", "freertos", "zephyr", "src", "include", "lib", "boards", "variants")
            ):
                results.append(rel)
    return sorted(dict.fromkeys(results))


def _architecture_from_board(board: str | None, platform: str | None) -> str | None:
    text = " ".join(part for part in (board, platform) if part).lower()
    if not text:
        return None
    if "esp32s3" in text:
        return "xtensa-lx7"
    if "esp32s2" in text:
        return "xtensa-lx7"
    if "esp32c3" in text or "esp32c6" in text or "esp32h2" in text:
        return "risc-v"
    if "esp32" in text:
        return "xtensa"
    if "stm32" in text or "nucleo" in text or "bluepill" in text:
        return "arm-cortex-m"
    if "avr" in text or "atmega" in text:
        return "avr"
    if "nrf52" in text or "nrf53" in text:
        return "arm-cortex-m"
    if "zephyr" in text:
        return "unknown"
    return None


def _board_token(value: str | None) -> str:
    return _normalise(value or "")


def _env_is_hardware_compatible(env_board: str | None, board_name: str | None, board_revision: str | None) -> str:
    if not env_board:
        return "unknown"
    env_token = _board_token(env_board)
    board_token = _board_token(board_name)
    revision_token = _board_token(board_revision)
    if not board_token and not revision_token:
        return "compatible_with_conditions"
    if env_token and (env_token in board_token or board_token in env_token or env_token in revision_token or revision_token in env_token):
        return "compatible"
    if board_token or revision_token:
        return "possible_mismatch"
    return "unknown"


def _parse_platformio_ini(path: Path, project_id: str) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    try:
        parser = _CaseSensitiveConfigParser(interpolation=None, strict=False)
        parser.read(path, encoding="utf-8")
    except (OSError, configparser.Error):
        return [], [], []

    platformio_defaults = {}
    if parser.has_section("platformio"):
        platformio_defaults = {key: value for key, value in parser.items("platformio")}

    raw_envs: dict[str, dict[str, str]] = {}
    for section in parser.sections():
        if not section.lower().startswith("env:"):
            continue
        env_name = section.split(":", 1)[1].strip()
        raw_envs[env_name] = {key: value for key, value in parser.items(section)}

    def resolve(name: str, trail: tuple[str, ...] = ()) -> dict[str, str]:
        if name not in raw_envs or name in trail:
            return {}
        raw = dict(platformio_defaults)
        parent_names = _split_items(raw_envs[name].get("extends"))
        for parent in parent_names:
            raw.update(resolve(parent, trail + (name,)))
        raw.update(raw_envs[name])
        return raw

    environments: list[dict[str, Any]] = []
    env_names = sorted(raw_envs)
    for env_name in env_names:
        resolved = resolve(env_name)
        custom_keys = {
            key: value
            for key, value in resolved.items()
            if key
            not in {
                "platform",
                "board",
                "framework",
                "build_flags",
                "lib_deps",
                "upload_protocol",
                "monitor_speed",
                "extends",
            }
        }
        environments.append(
            FirmwareEnvironment(
                id=_stable_id(project_id, env_name, path.as_posix()),
                project_id=project_id,
                name=env_name,
                extends=_split_items(resolved.get("extends")),
                platform=resolved.get("platform") or None,
                board=resolved.get("board") or None,
                framework=_split_items(resolved.get("framework")) or ([resolved["framework"]] if resolved.get("framework") else []),
                build_flags=_split_items(resolved.get("build_flags")),
                lib_deps=_split_items(resolved.get("lib_deps")),
                upload_protocol=resolved.get("upload_protocol") or None,
                monitor_speed=resolved.get("monitor_speed") or None,
                custom_options=custom_keys,
                source_path=str(path.as_posix()),
                confidence=0.95,
                provenance="platformio-ini-parser",
                metadata={},
            ).to_dict()
        )

    default_envs = _split_items(platformio_defaults.get("default_envs"))
    supported_parsers = ["platformio"] if env_names or default_envs else []
    return environments, default_envs, supported_parsers


def _detect_tasks(text: str, source_path: str, project_id: str) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for match in TASK_CREATE_RE.finditer(text):
        call = match.group(0)
        args = _split_call_args(match.group("args"))
        name_match = TASK_NAME_RE.search(call)
        task_name = name_match.group(1) if name_match else "unnamed_task"
        entry_function = _strip_wrappers(args[0]) if args else None
        tasks.append(
            FirmwareTask(
                id=_stable_id(project_id, source_path, task_name, "task"),
                project_id=project_id,
                name=task_name,
                source_path=source_path,
                source_line=_line_number(text, match.start()),
                scheduler="freertos",
                priority=None,
                stack_size=None,
                core_affinity=None,
                evidence="xTaskCreate",
                confidence=0.88,
                provenance="static-source-parser",
                entry_function=entry_function,
                parameters=args,
                framework=_inferred_frameworks(text),
                metadata={"call": call.strip()},
            ).to_dict()
        )
    return tasks


def _detect_interrupts(text: str, source_path: str, project_id: str) -> list[dict[str, Any]]:
    interrupts: list[dict[str, Any]] = []
    for match in ISR_ATTACH_RE.finditer(text):
        pin_expr, handler, trigger_mode = match.group(1), match.group(2), match.group(3)
        interrupts.append(
            FirmwareISR(
                id=_stable_id(project_id, source_path, pin_expr.strip(), handler, "attachInterrupt"),
                project_id=project_id,
                handler=handler,
                source_path=source_path,
                trigger=pin_expr.strip(),
                peripheral=None,
                priority=None,
                shared_state=[],
                confidence=0.9,
                provenance="static-source-parser",
                registration_site=match.group(0).strip(),
                trigger_mode=trigger_mode.strip() if isinstance(trigger_mode, str) else None,
                source_line=_line_number(text, match.start()),
                metadata={"evidence": "attachInterrupt"},
            ).to_dict()
        )
    for handler in ISR_ATTR_RE.findall(text):
        if any(item["handler"] == handler for item in interrupts):
            continue
        interrupts.append(
            FirmwareISR(
                id=_stable_id(project_id, source_path, handler, "isr-attr"),
                project_id=project_id,
                handler=handler,
                source_path=source_path,
                trigger="unknown",
                peripheral=None,
                priority=None,
                shared_state=[],
                confidence=0.65,
                provenance="static-source-parser",
                registration_site=handler,
                trigger_mode=None,
                source_line=None,
                metadata={"evidence": "attribute"},
            ).to_dict()
        )
    return interrupts


def _detect_timers(text: str, source_path: str, project_id: str) -> list[dict[str, Any]]:
    timers: list[dict[str, Any]] = []
    for match in TIMER_RE.finditer(text):
        timers.append(
            FirmwareTimer(
                id=_stable_id(project_id, source_path, match.group(1), "timer"),
                project_id=project_id,
                name=match.group(1),
                source_path=source_path,
                period=None,
                period_units=None,
                callback=None,
                owner=None,
                context=_source_context(source_path, text),
                source_line=_line_number(text, match.start()),
                confidence=0.8,
                provenance="static-source-parser",
                metadata={"evidence": match.group(1)},
            ).to_dict()
        )
    return timers


def _detect_state_machines(text: str, source_path: str, project_id: str) -> list[dict[str, Any]]:
    machines: list[dict[str, Any]] = []
    enum_match = STATE_ENUM_RE.search(text)
    transitions = _detect_state_machine_transitions(text, source_path, project_id)
    switch_present = bool(SWITCH_STATE_RE.search(text))

    if enum_match:
        raw_states = [part.strip() for part in enum_match.group(1).split(",")]
        states = [state for state in raw_states if state]
        if states:
            fault_states = [state for state in states if re.search(r"(fault|error|fail)", state, re.IGNORECASE)]
            recovery_states = [state for state in states if re.search(r"(recover|reset|idle|boot)", state, re.IGNORECASE)]
            status = "canonical_state_machine" if switch_present and transitions else "state_machine_candidate"
            confidence = 0.84 if status == "canonical_state_machine" else 0.48
            machines.append(
                FirmwareStateMachine(
                    id=_stable_id(project_id, source_path, "state-machine"),
                    project_id=project_id,
                    name="State",
                    source_path=source_path,
                    states=states,
                    state_identities=[_state_identity(state, "State", "State") for state in states],
                    transitions=transitions,
                    entry_state=states[0],
                    fault_states=fault_states,
                    recovery_states=recovery_states,
                    status=status,
                    source_line=_line_number(text, enum_match.start()),
                    confidence=confidence,
                    provenance="static-source-parser",
                    metadata={
                        "evidence": "enum State",
                        "transition_count": len(transitions),
                        "switch_present": switch_present,
                    },
                ).to_dict()
            )
            return machines

    if switch_present:
        derived_states = sorted(
            dict.fromkeys(
                [transition["from_state"] for transition in transitions if transition.get("from_state")]
                + [transition["to_state"] for transition in transitions if transition.get("to_state")]
            )
        )
        machines.append(
            FirmwareStateMachine(
                id=_stable_id(project_id, source_path, "switch-state"),
                project_id=project_id,
                name="state",
                source_path=source_path,
                states=derived_states,
                state_identities=[_state_identity(state, "state", "state") for state in derived_states],
                transitions=transitions,
                entry_state=derived_states[0] if derived_states else None,
                fault_states=[state for state in derived_states if re.search(r"(fault|error|fail)", state, re.IGNORECASE)],
                recovery_states=[state for state in derived_states if re.search(r"(recover|reset|idle|boot)", state, re.IGNORECASE)],
                status="canonical_state_machine" if transitions else "state_machine_candidate",
                source_line=None,
                confidence=0.56 if transitions else 0.4,
                provenance="static-source-parser",
                metadata={"evidence": "switch(state)", "transition_count": len(transitions)},
            ).to_dict()
        )
    return machines


def _detect_peripherals(text: str, source_path: str, project_id: str) -> list[dict[str, Any]]:
    peripherals: dict[str, dict[str, Any]] = {}
    lowered = text.lower()
    for name, hints in PERIPHERAL_HINTS.items():
        if any(hint in lowered for hint in hints):
            peripherals[name] = FirmwarePeripheral(
                id=_stable_id(project_id, source_path, name, "peripheral"),
                project_id=project_id,
                name=name,
                source_path=source_path,
                peripheral_type=name,
                configuration={},
                confidence=0.7 if name not in {"gpio", "uart"} else 0.8,
                provenance="static-source-parser",
                metadata={"evidence": next(hint for hint in hints if hint in lowered)},
            ).to_dict()
    return sorted(peripherals.values(), key=lambda item: item["name"])


def _detect_protocols(text: str, source_path: str, project_id: str) -> list[dict[str, Any]]:
    protocols: dict[str, dict[str, Any]] = {}
    lowered = text.lower()
    for name, hints in PROTOCOL_HINTS.items():
        if any(hint in lowered for hint in hints):
            protocols[name] = FirmwareProtocol(
                id=_stable_id(project_id, source_path, name, "protocol"),
                project_id=project_id,
                name=name,
                source_path=source_path,
                transport=name if name in {"i2c", "spi", "uart", "http", "mqtt", "ble", "can"} else None,
                fields=[],
                confidence=0.66,
                provenance="static-source-parser",
                metadata={"evidence": next(hint for hint in hints if hint in lowered)},
            ).to_dict()
    return sorted(protocols.values(), key=lambda item: item["name"])


def _detect_gpio(text: str, source_path: str, project_id: str) -> list[dict[str, Any]]:
    gpio: list[dict[str, Any]] = []
    lines = text.splitlines()
    seen: set[tuple[str, str | None, str | None, str]] = set()

    def add_assignment(*, gpio_value: str | None, symbol: str | None, line: int | None, source_kind: str) -> None:
        normalized_pin = _normalize_gpio_pin(gpio_value)
        if not normalized_pin:
            return
        scope = "global"
        conditions: list[str] = []
        if line is not None:
            scope, conditions = _conditional_scope(text, line)
        condition = " && ".join(conditions) if conditions else None
        owner = None
        if symbol:
            owner = re.sub(r"(_)?PIN$", "", symbol, flags=re.IGNORECASE).strip("_").lower() or None
        key = (normalized_pin, symbol, owner, condition or scope)
        if key in seen:
            return
        seen.add(key)
        line_evidence = lines[line - 1].strip() if line and 0 < line <= len(lines) else source_kind
        gpio.append(
            FirmwareGPIOAssignment(
                id=_stable_id(project_id, source_path, symbol or normalized_pin, normalized_pin, source_kind),
                project_id=project_id,
                gpio=normalized_pin,
                symbol=symbol,
                source_path=source_path,
                owner=owner,
                direction=None,
                confidence=0.82 if symbol else 0.68,
                provenance="static-source-parser",
                module=None,
                purpose=next((token for token in KNOWN_ROLE_TOKENS if symbol and token in symbol.lower()), None),
                environment=None,
                hardware_signal=None,
                board_revision=None,
                status="declared" if symbol else "reference",
                scope=scope,
                condition=condition,
                source_line=line,
                metadata={"evidence": line_evidence, "source_kind": source_kind, "conditions": conditions},
            ).to_dict()
        )

    for match in PIN_DEFINE_RE.finditer(text):
        add_assignment(gpio_value=match.group(2), symbol=match.group(1), line=_line_number(text, match.start()), source_kind="gpio-define")
    for match in PIN_ASSIGN_RE.finditer(text):
        add_assignment(gpio_value=match.group(2), symbol=match.group(1), line=_line_number(text, match.start()), source_kind="gpio-assignment")
    for match in GPIO_RE.finditer(text):
        add_assignment(gpio_value=match.group(1), symbol=None, line=_line_number(text, match.start()), source_kind="gpio-reference")
    return gpio


def _detect_memory(text: str, source_path: str, project_id: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for size in BUFFER_RE.findall(text):
        n = int(size)
        finding_type = "large_static_buffer" if n >= 256 else "static_buffer"
        findings.append(
            FirmwareMemoryFinding(
                id=_stable_id(project_id, source_path, size, finding_type),
                project_id=project_id,
                name=finding_type,
                source_path=source_path,
                region="static",
                size=n,
                confidence=0.7 if n >= 256 else 0.55,
                provenance="static-source-parser",
                metadata={"evidence": "array-declaration"},
            ).to_dict()
        )
    if re.search(r"\b(?:malloc|calloc|realloc|new\s+)\b", text, re.IGNORECASE):
        findings.append(
            FirmwareMemoryFinding(
                id=_stable_id(project_id, source_path, "dynamic-allocation"),
                project_id=project_id,
                name="dynamic_allocation_candidate",
                source_path=source_path,
                region="heap",
                size=None,
                confidence=0.62,
                provenance="static-source-parser",
                metadata={"evidence": "allocation-call"},
            ).to_dict()
        )
    return findings


def _detect_tasks_or_control_risks(text: str, source_path: str, project_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    risks: list[dict[str, Any]] = []
    validation: list[dict[str, Any]] = []
    lines = text.splitlines()
    blocking_evidence: list[dict[str, Any]] = []
    for match in [*BLOCKING_RE.finditer(text), *TASK_WAIT_RE.finditer(text)]:
        line = _line_number(text, match.start())
        line_text = lines[line - 1].strip() if 0 < line <= len(lines) else match.group(0)
        if not line_text or line_text.startswith(("//", "/*")):
            continue
        context = _line_context(text, line, source_path)
        if context == "setup":
            continue
        scope, conditions = _conditional_scope(text, line)
        blocking_evidence.append(
            {
                "line": line,
                "context": context,
                "scope": scope,
                "conditions": conditions,
                "evidence": line_text,
            }
        )
    if blocking_evidence:
        confidence = 0.76 if any(item["context"] == "isr" for item in blocking_evidence) else 0.62
        risks.append(
            FirmwareRisk(
                id=_stable_id(project_id, source_path, "blocking-call"),
                project_id=project_id,
                title="Potential blocking work detected outside setup",
                risk_type="blocking_call_candidate",
                status="requires_review",
                confidence=confidence,
                evidence_paths=[source_path],
                provenance="static-source-parser",
                source_line=min(item["line"] for item in blocking_evidence),
                recommended_investigation="Confirm that waits, delays, or blocking primitive calls are intentional and not running on an ISR or time-critical path.",
                metadata={"evidence": blocking_evidence, "certainty": _confidence_label(confidence)},
            ).to_dict()
        )
    if WATCHDOG_RE.search(text):
        validation.append(
            FirmwareValidation(
                id=_stable_id(project_id, source_path, "watchdog"),
                project_id=project_id,
                validation_type="watchdog",
                result="unknown",
                evidence_path=source_path,
                summary="Watchdog-related configuration or usage detected.",
                confidence=0.58,
                provenance="static-source-parser",
                metadata={"evidence": [item for item in lines if WATCHDOG_RE.search(item)]},
            ).to_dict()
        )
    return risks, validation


def _inferred_frameworks(text: str) -> list[str]:
    lowered = text.lower()
    frameworks: set[str] = set()
    if "arduino.h" in lowered or "pinmode(" in lowered or "digitalwrite(" in lowered or "digitalread(" in lowered:
        frameworks.add("arduino")
    if "freertos" in lowered or "xtaskcreate" in lowered or "xqueue" in lowered or "xsemaphore" in lowered or "xeventgroup" in lowered:
        frameworks.add("freertos")
    if "espidf" in lowered or "esp_task_wdt" in lowered or "esp_timer" in lowered or "esp_err_t" in lowered:
        frameworks.add("espidf")
    if "zephyr" in lowered:
        frameworks.add("zephyr")
    return sorted(frameworks)


def _source_context(path: str, text: str) -> str:
    lowered = f"{path}\n{text}".lower()
    if "void setup" in lowered or "setup()" in lowered:
        return "setup"
    if "void loop" in lowered or "loop()" in lowered:
        return "loop"
    if "task" in lowered and ("xtaskcreate" in lowered or "freertos" in lowered):
        return "task"
    if "isr" in lowered or "interrupt" in lowered:
        return "isr"
    return "unknown"


def _state_identity(raw_state: str, machine_name: str | None = None, owner: str | None = None) -> dict[str, Any]:
    qualified = raw_state.strip()
    symbol = qualified.split("::")[-1]
    return {
        "raw": qualified,
        "normalized": _normalize_identifier(qualified),
        "symbol": symbol,
        "owner": owner or machine_name,
        "qualified": qualified,
    }


def _normalize_gpio_pin(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().upper()
    cleaned = cleaned.replace("GPIO_NUM_", "").replace("GPIO_", "").replace("GPIO", "")
    cleaned = cleaned.replace("PIN", "")
    cleaned = cleaned.strip("_- ")
    if re.fullmatch(r"\d+", cleaned):
        return cleaned
    if re.fullmatch(r"D\d+", cleaned):
        return None
    return cleaned or None


def _detect_build_variants(environments: list[dict[str, Any]], project_id: str) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    for env in environments:
        build_flags = list(env.get("build_flags", []))
        variants.append(
            FirmwareBuildVariant(
                id=_stable_id(project_id, env["name"], "build-variant"),
                project_id=project_id,
                environment=env["name"],
                platform=env.get("platform"),
                board=env.get("board"),
                framework=list(env.get("framework", [])),
                build_flags=build_flags,
                defines=[flag.removeprefix("-D") for flag in build_flags if flag.startswith("-D")],
                libraries=list(env.get("lib_deps", [])),
                source_filters=_split_items(env.get("custom_options", {}).get("src_filter")),
                source_path=env.get("source_path", ""),
                source_line=None,
                confidence=float(env.get("confidence", 0.75)),
                provenance="platformio-variant-derivation",
                metadata={"custom_options": env.get("custom_options", {})},
            ).to_dict()
        )
    return variants


def _detect_rtos_primitives(text: str, source_path: str, project_id: str) -> list[dict[str, Any]]:
    primitives: list[dict[str, Any]] = []
    lower = text.lower()
    line_cache = text.splitlines()
    for match in QUEUE_CREATE_RE.finditer(text):
        line = _line_number(text, match.start())
        api = match.group(1).lower()
        primitive_type = "queue" if "queue" in api else "task_handle"
        primitives.append(
            FirmwareRTOSPrimitive(
                id=_stable_id(project_id, source_path, line, primitive_type, api),
                project_id=project_id,
                primitive_type=primitive_type,
                name=api,
                source_path=source_path,
                source_line=line,
                task_name=None,
                target=None,
                operation="create" if "create" in api else "declare",
                confidence=0.86,
                provenance="static-source-parser",
                metadata={"evidence": line_cache[line - 1].strip() if 0 < line <= len(line_cache) else api},
            ).to_dict()
        )
    for pattern, primitive_type in (
        (QUEUE_USE_RE, "queue"),
        (SEMAPHORE_USE_RE, "semaphore"),
        (EVENT_GROUP_USE_RE, "event_group"),
        (NOTIFY_USE_RE, "task_notification"),
    ):
        for match in pattern.finditer(text):
            line = _line_number(text, match.start())
            api = match.group(1) if match.lastindex else match.group(0).split("(", 1)[0]
            operation = "use"
            if "create" in api.lower():
                operation = "create"
            primitives.append(
                FirmwareRTOSPrimitive(
                    id=_stable_id(project_id, source_path, line, primitive_type, api),
                    project_id=project_id,
                    primitive_type=primitive_type,
                    name=api,
                    source_path=source_path,
                    source_line=line,
                    task_name=None,
                    target=None,
                    operation=operation,
                    confidence=0.8,
                    provenance="static-source-parser",
                    metadata={"evidence": line_cache[line - 1].strip() if 0 < line <= len(line_cache) else api},
                ).to_dict()
            )
    if "mutex" in lower and "xsemaphorecreatemutex" in lower:
        primitives.append(
            FirmwareRTOSPrimitive(
                id=_stable_id(project_id, source_path, "mutex", "create"),
                project_id=project_id,
                primitive_type="mutex",
                name="xSemaphoreCreateMutex",
                source_path=source_path,
                source_line=None,
                task_name=None,
                target=None,
                operation="create",
                confidence=0.9,
                provenance="static-source-parser",
                metadata={},
            ).to_dict()
        )
    return primitives


def _detect_timing_facts(text: str, source_path: str, project_id: str) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    lines = text.splitlines()
    for match in TIMING_DELAY_RE.finditer(text):
        line = _line_number(text, match.start())
        api = match.group(1)
        raw_value = _strip_wrappers(match.group(2))
        units = "ms" if api.lower() == "delay" else "ticks" if api.lower().startswith("vtaskdelay") else "s"
        fact_type = "delay" if api.lower() == "delay" else "poll_interval"
        if api.lower() == "sleep" or "sleep" in api.lower():
            fact_type = "delay"
            units = "s"
        normalized_value_ms, normalized_units = _normalize_duration(raw_value, units)
        context = _line_context(text, line, source_path)
        scope, conditions = _conditional_scope(text, line)
        confidence = 0.9 if normalized_value_ms is not None else 0.56
        facts.append(
            FirmwareTimingFact(
                id=_stable_id(project_id, source_path, line, fact_type, api, raw_value),
                project_id=project_id,
                fact_type=fact_type,
                value=raw_value or api,
                units=normalized_units or units,
                context=context,
                owner=None,
                source_path=source_path,
                source_line=line,
                confidence=confidence,
                provenance="static-source-parser",
                normalized_value_ms=normalized_value_ms,
                certainty=_confidence_label(confidence),
                metadata={
                    "api": api,
                    "evidence": lines[line - 1].strip() if 0 < line <= len(lines) else api,
                    "scope": scope,
                    "conditions": conditions,
                    "normalized_units": normalized_units,
                },
            ).to_dict()
        )
    for match in TIMING_WAIT_RE.finditer(text):
        line = _line_number(text, match.start())
        api = match.group(1)
        raw_value = _strip_wrappers(match.group(2))
        normalized_value_ms, normalized_units = _normalize_duration(raw_value, "ticks" if "task" in api.lower() or "queue" in api.lower() or "event" in api.lower() else None)
        context = _line_context(text, line, source_path)
        scope, conditions = _conditional_scope(text, line)
        confidence = 0.82 if normalized_value_ms is not None else 0.52
        facts.append(
            FirmwareTimingFact(
                id=_stable_id(project_id, source_path, line, "timeout", api, raw_value),
                project_id=project_id,
                fact_type="timeout",
                value=raw_value or api,
                units=normalized_units or ("ticks" if "task" in api.lower() or "queue" in api.lower() or "event" in api.lower() else None),
                context=context,
                owner=None,
                source_path=source_path,
                source_line=line,
                confidence=confidence,
                provenance="static-source-parser",
                normalized_value_ms=normalized_value_ms,
                certainty=_confidence_label(confidence),
                metadata={
                    "api": api,
                    "evidence": lines[line - 1].strip() if 0 < line <= len(lines) else api,
                    "scope": scope,
                    "conditions": conditions,
                    "normalized_units": normalized_units,
                },
            ).to_dict()
        )
    if "millis()" in text.lower() or "micros()" in text.lower():
        for match in re.finditer(r"\b(millis|micros)\s*\(\s*\)", text, re.IGNORECASE):
            line = _line_number(text, match.start())
            context = _line_context(text, line, source_path)
            scope, conditions = _conditional_scope(text, line)
            confidence = 0.62
            facts.append(
                FirmwareTimingFact(
                    id=_stable_id(project_id, source_path, line, match.group(1).lower()),
                    project_id=project_id,
                    fact_type="poll_interval",
                    value=match.group(1).lower(),
                    units="ms" if match.group(1).lower() == "millis" else "us",
                    context=context,
                    owner=None,
                    source_path=source_path,
                    source_line=line,
                    confidence=confidence,
                    provenance="static-source-parser",
                    certainty=_confidence_label(confidence),
                    metadata={
                        "evidence": lines[line - 1].strip() if 0 < line <= len(lines) else match.group(1),
                        "scope": scope,
                        "conditions": conditions,
                    },
                ).to_dict()
            )
    return facts


def _detect_bus_configs(text: str, source_path: str, project_id: str) -> list[dict[str, Any]]:
    configs: list[dict[str, Any]] = []
    lines = text.splitlines()
    for match in WIRE_BEGIN_RE.finditer(text):
        line = _line_number(text, match.start())
        args = _split_call_args(match.group(1))
        pins = [arg for arg in args if arg.strip()]
        configs.append(
            FirmwareBusConfig(
                id=_stable_id(project_id, source_path, line, "i2c"),
                project_id=project_id,
                bus_type="i2c",
                name="Wire",
                source_path=source_path,
                source_line=line,
                pins=pins,
                speed=None,
                address=None,
                participants=["sensor" if "sensor" in text.lower() else "unknown"],
                confidence=0.75,
                provenance="static-source-parser",
                metadata={"evidence": lines[line - 1].strip() if 0 < line <= len(lines) else "Wire.begin"},
            ).to_dict()
        )
    for match in SPI_BEGIN_RE.finditer(text):
        line = _line_number(text, match.start())
        configs.append(
            FirmwareBusConfig(
                id=_stable_id(project_id, source_path, line, "spi"),
                project_id=project_id,
                bus_type="spi",
                name="SPI",
                source_path=source_path,
                source_line=line,
                pins=_split_call_args(match.group(1)),
                speed=None,
                address=None,
                participants=[],
                confidence=0.72,
                provenance="static-source-parser",
                metadata={"evidence": lines[line - 1].strip() if 0 < line <= len(lines) else "SPI.begin"},
            ).to_dict()
        )
    for match in SERIAL_BEGIN_RE.finditer(text):
        line = _line_number(text, match.start())
        value = _strip_wrappers(match.group(1))
        configs.append(
            FirmwareBusConfig(
                id=_stable_id(project_id, source_path, line, "uart"),
                project_id=project_id,
                bus_type="uart",
                name="Serial",
                source_path=source_path,
                source_line=line,
                pins=[],
                speed=value,
                address=None,
                participants=[],
                confidence=0.7,
                provenance="static-source-parser",
                metadata={"evidence": lines[line - 1].strip() if 0 < line <= len(lines) else "Serial.begin"},
            ).to_dict()
        )
    return configs


def _detect_packet_definitions(text: str, source_path: str, project_id: str) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    lines = text.splitlines()
    for match in PACKET_STRUCT_RE.finditer(text):
        name = match.group(1)
        line = _line_number(text, match.start())
        body, _ = _extract_braced_block(text, text.find("{", match.start()))
        fields: list[dict[str, Any]] = []
        for raw_line in body.splitlines():
            stripped = raw_line.strip().rstrip(";")
            if not stripped or stripped.startswith("//"):
                continue
            field_match = re.match(r"(?P<type>[A-Za-z_][A-Za-z0-9_<>\*&:\s]*)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*(?:\[(?P<size>\d+)\])?", stripped)
            if field_match:
                fields.append(
                    {
                        "type": field_match.group("type").strip(),
                        "name": field_match.group("name").strip(),
                        "size": int(field_match.group("size")) if field_match.group("size") else None,
                    }
                )
        packets.append(
            FirmwarePacketDefinition(
                id=_stable_id(project_id, source_path, line, name),
                project_id=project_id,
                name=name,
                fields=fields,
                source_path=source_path,
                source_line=line,
                transport="uart" if "serial" in text.lower() else None,
                producer=None,
                consumer=None,
                version=None,
                confidence=0.72,
                provenance="static-source-parser",
                metadata={"evidence": lines[line - 1].strip() if 0 < line <= len(lines) else name},
            ).to_dict()
        )
    return packets


def _detect_state_machine_transitions(text: str, source_path: str, project_id: str, machine_name: str = "State") -> list[dict[str, Any]]:
    transitions: dict[tuple[str, str, str | None, str], dict[str, Any]] = {}
    switch_match = SWITCH_STATE_RE.search(text)
    if switch_match:
        brace_index = text.find("{", switch_match.end())
        if brace_index >= 0:
            body, _ = _extract_braced_block(text, brace_index)
            body_start_line = _line_number(text, brace_index)
            current_state: str | None = None
            pending_guard: str | None = None
            for offset, segment in enumerate(body.splitlines(), start=0):
                stripped = segment.strip()
                if not stripped:
                    continue
                line_number = body_start_line + offset
                case_match = CASE_STATE_RE.search(stripped)
                if case_match:
                    current_state = case_match.group(1).split("::")[-1]
                    pending_guard = None
                    continue
                guard_match = re.search(r"\bif\s*\(([^)]+)\)", stripped)
                if guard_match:
                    pending_guard = guard_match.group(1).strip()
                target: str | None = None
                trigger = "explicit_assignment"
                if re.search(r"\b(?:setState|transitionTo)\s*\(", stripped):
                    call_match = re.search(r"\b(?:setState|transitionTo)\s*\(\s*([A-Za-z_][A-Za-z0-9_:]*)\s*\)", stripped)
                    if call_match:
                        target = call_match.group(1).split("::")[-1]
                        trigger = "explicit_transition_call"
                else:
                    assign_match = STATE_ASSIGN_RE.search(stripped)
                    if assign_match:
                        if re.search(r"\b(?:State|Status|auto|const|int|uint8_t|uint16_t|uint32_t|bool)\s+state\b", stripped):
                            continue
                        target = assign_match.group(1).split("::")[-1]
                if not target:
                    continue
                from_state = current_state or "UNKNOWN"
                key = (from_state, target, pending_guard, trigger)
                evidence_location = {"source_path": source_path, "line_start": line_number, "line_end": line_number}
                if key not in transitions:
                    transitions[key] = {
                        "id": _stable_id(project_id, source_path, from_state, target, pending_guard or "no-guard", trigger),
                        "from_state": from_state,
                        "to_state": target,
                        "from_state_identity": _state_identity(from_state, machine_name, machine_name),
                        "to_state_identity": _state_identity(target, machine_name, machine_name),
                        "trigger": trigger,
                        "guard": pending_guard,
                        "action": stripped,
                        "scope": "conditional_compilation" if pending_guard or stripped.startswith("if ") else "global",
                        "source_path": source_path,
                        "source_line": line_number,
                        "line_start": line_number,
                        "line_end": line_number,
                        "evidence_locations": [evidence_location],
                        "evidence_count": 1,
                        "confidence": 0.86 if current_state else 0.55,
                        "provenance": "static-source-parser",
                        "detector": "static-source-parser",
                        "detector_version": DETECTOR_VERSION,
                    }
                else:
                    transitions[key]["evidence_locations"].append(evidence_location)
                    transitions[key]["evidence_count"] += 1
                    transitions[key]["confidence"] = max(transitions[key]["confidence"], 0.86 if current_state else 0.55)

    for match in re.finditer(r"\b(?:setState|transitionTo)\s*\(\s*([A-Za-z_][A-Za-z0-9_:]*)\s*\)", text):
        line_number = _line_number(text, match.start())
        target = match.group(1).split("::")[-1]
        key = ("UNKNOWN", target, None, "explicit_transition_call")
        evidence_location = {"source_path": source_path, "line_start": line_number, "line_end": line_number}
        if key not in transitions:
            transitions[key] = {
                "id": _stable_id(project_id, source_path, "UNKNOWN", target, "explicit-call", "explicit_transition_call"),
                "from_state": "UNKNOWN",
                "to_state": target,
                "from_state_identity": _state_identity("UNKNOWN", machine_name, machine_name),
                "to_state_identity": _state_identity(target, machine_name, machine_name),
                "trigger": "explicit_transition_call",
                "guard": None,
                "action": match.group(0),
                "scope": "global",
                "source_path": source_path,
                "source_line": line_number,
                "line_start": line_number,
                "line_end": line_number,
                "evidence_locations": [evidence_location],
                "evidence_count": 1,
                "confidence": 0.55,
                "provenance": "static-source-parser",
                "detector": "static-source-parser",
                "detector_version": DETECTOR_VERSION,
            }
    return sorted(transitions.values(), key=lambda item: (item["source_line"], item["to_state"], item["from_state"]))


def _detect_isr_body_risks(text: str, source_path: str, project_id: str, handlers: list[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    lines = text.splitlines()
    for handler in handlers:
        header = re.search(rf"(?m)^[^\S\r\n]*(?:[A-Za-z_][A-Za-z0-9_<>\*&:\s]+?)\b{re.escape(handler)}\s*\([^;{{}}]*\)\s*\{{", text)
        if not header:
            continue
        body, _ = _extract_braced_block(text, text.find("{", header.end() - 1))
        lowered = body.lower()
        line = _line_number(text, header.start())
        risks: list[str] = []
        if BLOCKING_RE.search(body) or "while(true)" in lowered or "while (true)" in lowered or "for(;;)" in lowered.replace(" ", ""):
            risks.append("blocking_call_in_isr")
        if re.search(r"\b(?:malloc|calloc|realloc|new\s+)\b", body, re.IGNORECASE):
            risks.append("heap_allocation_in_isr")
        if re.search(r"\b(?:serial(?:\.\w+)?|printf|println|esp_log[a-z_]*|log[a-z_]*?)\b", lowered):
            risks.append("logging_in_isr")
        assignment_targets = {
            match.group(1).lower()
            for match in re.finditer(r"(?<![=!<>])\b([A-Za-z_][A-Za-z0-9_]*)\s*=", body)
        }
        if any(token in target for target in assignment_targets for token in ("state", "flag", "count", "mode", "ready", "busy")):
            risks.append("shared_state_access")
        safe_signaling = re.search(r"\b(?:xQueueSendFromISR|xSemaphoreGiveFromISR|vTaskNotifyGiveFromISR|xEventGroupSetBitsFromISR|portYIELD_FROM_ISR)\b", body)
        if safe_signaling and not risks:
            continue
        if risks:
            body_end = line + body.count("\n")
            line_text = lines[line - 1].strip() if 0 < line <= len(lines) else handler
            findings.append(
                FirmwareFinding(
                    id=_stable_id(project_id, source_path, handler, "isr-body-risk"),
                    project_id=project_id,
                    finding_type="isr_review",
                    severity="requires_review",
                    title=f"ISR body for {handler} requires review",
                    affected_entity=handler,
                    evidence_paths=[source_path],
                    source_path=source_path,
                    source_line=line,
                    confidence=0.68 if "blocking_call_in_isr" not in risks else 0.8,
                    recommended_investigation="Inspect for blocking calls, allocation, and logging in the ISR body; safe ISR signaling alone is not treated as a fault.",
                    provenance="static-source-parser",
                    entity=handler,
                    line_start=line,
                    line_end=body_end,
                    evidence=[{"source_path": source_path, "line_start": line, "line_end": body_end, "text": line_text, "risk_indicators": risks}],
                    reason="One or more ISR body heuristics exceeded the conservative review threshold.",
                    related_entities=sorted(assignment_targets),
                    scope="isr",
                    recommendation="Validate ISR work stays bounded and uses FromISR-safe signaling only.",
                    certainty=_confidence_label(0.68 if "blocking_call_in_isr" not in risks else 0.8),
                    metadata={"risk_indicators": risks, "evidence": body[:400]},
                ).to_dict()
            )
    return findings
def _discover_modules(paths: list[Path], project_id: str) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    for path in paths:
        modules.append(
            FirmwareModule(
                id=_stable_id(project_id, path.as_posix(), "module"),
                project_id=project_id,
                name=path.stem,
                path=path.as_posix(),
                kind=_source_kind(path),
                language=_language_for_path(path),
                includes=[],
                confidence=0.8,
                provenance="static-file-discovery",
                metadata={"source_path": path.as_posix()},
            ).to_dict()
        )
    return modules


def _determine_supported_parsers(paths: list[Path], envs: list[dict[str, Any]]) -> list[str]:
    lowered = {path.name.lower() for path in paths}
    parsers: list[str] = []
    if any(name == "platformio.ini" for name in lowered) or envs:
        parsers.append("platformio")
    if any(name in {"sdkconfig", "sdkconfig.defaults"} for name in lowered):
        parsers.append("esp-idf")
    if any(name == "cmakelists.txt" for name in lowered):
        parsers.append("cmake-embedded")
    if any(path.suffix.lower() in {".ino"} for path in paths):
        parsers.append("arduino")
    if any("freertos" in path.as_posix().lower() for path in paths):
        parsers.append("freertos-pattern")
    if not parsers and paths:
        parsers.append("generic-c-family")
    return sorted(dict.fromkeys(parsers))


def _build_compatibility(
    *,
    project_id: str,
    environments: list[dict[str, Any]],
    hardware_snapshot: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], str]:
    boards: list[dict[str, Any]] = []
    if hardware_snapshot:
        boards = hardware_snapshot.get("boards", []) or []
    compatibility: list[dict[str, Any]] = []
    board_labels = [
        (
            board.get("name"),
            board.get("revision"),
        )
        for board in boards
        if isinstance(board, dict)
    ]
    for env in environments:
        env_board = env.get("board")
        criteria: dict[str, str] = {"env_board": str(env_board or "unknown")}
        if not board_labels:
            status = "unknown"
            board_name = None
            board_revision = None
            evidence = ["no hardware board evidence"]
            reason = "No hardware board inventory was available for comparison."
            criteria["hardware_inventory"] = "missing"
        else:
            candidate_results: list[tuple[str, str | None, str | None, str]] = []
            for name, revision in board_labels:
                candidate = _env_is_hardware_compatible(env_board, name, revision)
                candidate_results.append((candidate, name, revision, f"{env_board} vs {name} {revision}"))
            precedence = {"compatible": 3, "compatible_with_conditions": 2, "possible_mismatch": 1, "unknown": 0}
            status, board_name, board_revision, evidence_text = max(candidate_results, key=lambda item: precedence.get(item[0], 0))
            evidence = [evidence_text]
            if status == "compatible":
                reason = f"PlatformIO board '{env_board}' matched hardware board '{board_name}' revision '{board_revision}'."
            elif status == "compatible_with_conditions":
                reason = f"PlatformIO board '{env_board}' partially matched hardware board '{board_name}' revision '{board_revision}' and should be validated against build conditions."
            elif status == "possible_mismatch":
                reason = f"PlatformIO board '{env_board}' may conflict with hardware board '{board_name}' revision '{board_revision}'."
            else:
                reason = f"PlatformIO board '{env_board}' could not be matched against the detected hardware inventory."
            criteria.update(
                {
                    "hardware_board_name": str(board_name or "unknown"),
                    "hardware_board_revision": str(board_revision or "unknown"),
                    "match_status": status,
                }
            )
        compatibility.append(
            FirmwareCompatibility(
                id=_stable_id(project_id, env["name"], board_name or "unknown", board_revision or "unknown"),
                project_id=project_id,
                firmware_variant=env["name"],
                board_revision=board_revision,
                board_name=board_name,
                status=status,
                evidence=evidence,
                confidence=0.88 if status == "compatible" else 0.62 if status == "compatible_with_conditions" else 0.48 if status == "possible_mismatch" else 0.38,
                provenance="static-compatibility-parser",
                reason=reason,
                criteria=criteria,
                certainty=_confidence_label(0.88 if status == "compatible" else 0.62 if status == "compatible_with_conditions" else 0.48 if status == "possible_mismatch" else 0.38),
                metadata={"env_board": env_board},
            ).to_dict()
        )
    overall = "unknown"
    if compatibility and any(item["status"] == "compatible" for item in compatibility):
        overall = "compatible"
    elif compatibility and any(item["status"] == "compatible_with_conditions" for item in compatibility):
        overall = "compatible_with_conditions"
    elif compatibility and any(item["status"] == "possible_mismatch" for item in compatibility):
        overall = "possible_mismatch"
    return compatibility, overall


def _build_gpio_conflicts(
    *,
    project_id: str,
    gpio: list[dict[str, Any]],
    hardware_snapshot: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    hardware_pins = [item for item in (hardware_snapshot or {}).get("pins", []) or [] if isinstance(item, dict)]
    board_revisions = [item for item in (hardware_snapshot or {}).get("boards", []) or [] if isinstance(item, dict)]
    if not gpio or not hardware_pins:
        return conflicts
    for assignment in gpio:
        gpio_value = _normalize_gpio_pin(str(assignment.get("gpio", "") or "")) or ""
        symbol = str(assignment.get("symbol") or assignment.get("owner") or "").upper()
        assignment_scope = str(assignment.get("scope") or "unknown")
        assignment_condition = assignment.get("condition")
        assignment_environment = assignment.get("environment")
        for hardware_pin in hardware_pins:
            pin_name = _normalize_gpio_pin(str(hardware_pin.get("hardware_pin") or "")) or str(hardware_pin.get("hardware_pin") or "").upper()
            signal = str(hardware_pin.get("signal") or "").upper()
            firmware_symbol = str(hardware_pin.get("firmware_symbol") or "").upper()
            hardware_scope = str(hardware_pin.get("scope") or "unknown")
            hardware_environment = hardware_pin.get("environment")
            if not gpio_value or gpio_value != str(pin_name).upper():
                continue
            if _signals_equivalent(symbol or assignment.get("purpose"), signal or firmware_symbol):
                continue
            scope = "conditional_compilation" if "conditional" in {assignment_scope, hardware_scope} or assignment_condition else assignment_scope
            status = "unknown_mapping"
            confidence = 0.42
            reason = "GPIO pin matched hardware inventory but the semantic role could not be established confidently."
            if assignment_condition or hardware_scope == "conditional_compilation":
                status = "variant_difference"
                confidence = 0.58
                reason = "GPIO pin appears in a conditional build or hardware variant and should be validated per environment."
            elif firmware_symbol or signal:
                if symbol and (signal or firmware_symbol):
                    status = "confirmed_conflict"
                    confidence = 0.82
                    reason = f"Firmware role '{symbol}' does not align with hardware signal '{signal or firmware_symbol}'."
                else:
                    status = "possible_conflict"
                    confidence = 0.52
                    reason = "GPIO mapping is present but the semantic role relationship is incomplete."
            conflicts.append(
                FirmwareGPIOConflict(
                    id=_stable_id(project_id, gpio_value, symbol or "unknown", str(pin_name) or "unknown", "gpio-conflict"),
                    project_id=project_id,
                    gpio=gpio_value,
                    status=status,
                    firmware_role=symbol or None,
                    hardware_signal=signal or None,
                    board_revision=(board_revisions[0].get("revision") if board_revisions else None),
                    source_path=str(assignment.get("source_path") or "unknown"),
                    source_line=assignment.get("source_line"),
                    confidence=confidence,
                    provenance="static-gpio-compatibility-parser",
                    scope=scope,
                    environment=assignment_environment or hardware_environment,
                    entity=symbol or assignment.get("owner") or None,
                    line_start=assignment.get("source_line"),
                    line_end=assignment.get("source_line"),
                    evidence=[{"assignment": assignment, "hardware_pin": hardware_pin, "match": {"gpio": gpio_value, "status": status}}],
                    reason=reason,
                    related_entities=[value for value in [signal or None, firmware_symbol or None, str(pin_name) if pin_name else None] if value],
                    recommendation="Verify the firmware role, pin map, and build variant before treating this as a hardware conflict.",
                    certainty=_confidence_label(confidence),
                    metadata={
                        "assignment": assignment,
                        "hardware_pin": hardware_pin,
                        "firmware_symbol": firmware_symbol or None,
                    },
                ).to_dict()
            )
            break
    return conflicts


def _build_gaps(
    *,
    project_id: str,
    paths: list[Path],
    environments: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    interrupts: list[dict[str, Any]],
    timers: list[dict[str, Any]],
    state_machines: list[dict[str, Any]],
    protocols: list[dict[str, Any]],
    compatibility: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    if not any(path.name.lower() == "platformio.ini" for path in paths):
        gaps.append(
            FirmwareGap(
                id=_stable_id(project_id, "firmware-gap", "platformio"),
                project_id=project_id,
                title="No PlatformIO build definition detected",
                gap_type="build_definition",
                severity="medium",
                confidence=0.85,
                evidence_paths=[path.as_posix() for path in paths[:3]],
                provenance="static-source-parser",
                metadata={},
            ).to_dict()
        )
    if paths and not environments:
        gaps.append(
            FirmwareGap(
                id=_stable_id(project_id, "firmware-gap", "environments"),
                project_id=project_id,
                title="Firmware sources exist but no explicit build environments were parsed",
                gap_type="environment",
                severity="medium",
                confidence=0.8,
                evidence_paths=[path.as_posix() for path in paths[:3]],
                provenance="static-source-parser",
                metadata={},
            ).to_dict()
        )
    if paths and not tasks:
        gaps.append(
            FirmwareGap(
                id=_stable_id(project_id, "firmware-gap", "tasks"),
                project_id=project_id,
                title="No explicit firmware task evidence found",
                gap_type="task",
                severity="low",
                confidence=0.72,
                evidence_paths=[path.as_posix() for path in paths[:3]],
                provenance="static-source-parser",
                metadata={},
            ).to_dict()
        )
    if paths and not interrupts:
        gaps.append(
            FirmwareGap(
                id=_stable_id(project_id, "firmware-gap", "interrupts"),
                project_id=project_id,
                title="No explicit interrupt handler evidence found",
                gap_type="interrupt",
                severity="low",
                confidence=0.72,
                evidence_paths=[path.as_posix() for path in paths[:3]],
                provenance="static-source-parser",
                metadata={},
            ).to_dict()
        )
    if paths and not timers:
        gaps.append(
            FirmwareGap(
                id=_stable_id(project_id, "firmware-gap", "timers"),
                project_id=project_id,
                title="No explicit timer evidence found",
                gap_type="timer",
                severity="low",
                confidence=0.72,
                evidence_paths=[path.as_posix() for path in paths[:3]],
                provenance="static-source-parser",
                metadata={},
            ).to_dict()
        )
    if paths and not state_machines:
        gaps.append(
            FirmwareGap(
                id=_stable_id(project_id, "firmware-gap", "state-machine"),
                project_id=project_id,
                title="No explicit state machine evidence found",
                gap_type="state_machine",
                severity="low",
                confidence=0.72,
                evidence_paths=[path.as_posix() for path in paths[:3]],
                provenance="static-source-parser",
                metadata={},
            ).to_dict()
        )
    if paths and not protocols:
        gaps.append(
            FirmwareGap(
                id=_stable_id(project_id, "firmware-gap", "protocols"),
                project_id=project_id,
                title="No explicit protocol evidence found",
                gap_type="protocol",
                severity="low",
                confidence=0.72,
                evidence_paths=[path.as_posix() for path in paths[:3]],
                provenance="static-source-parser",
                metadata={},
            ).to_dict()
        )
    if compatibility and all(item["status"] == "unknown" for item in compatibility):
        gaps.append(
            FirmwareGap(
                id=_stable_id(project_id, "firmware-gap", "compatibility"),
                project_id=project_id,
                title="Hardware compatibility remains unknown",
                gap_type="compatibility",
                severity="medium",
                confidence=0.7,
                evidence_paths=[item["firmware_variant"] for item in compatibility[:5]],
                provenance="static-compatibility-parser",
                metadata={},
            ).to_dict()
        )
    return gaps


def _build_risks(
    *,
    project_id: str,
    tasks: list[dict[str, Any]],
    interrupts: list[dict[str, Any]],
    memory_findings: list[dict[str, Any]],
    control_flow_risks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = [*control_flow_risks]
    if tasks:
        risks.append(
            FirmwareRisk(
                id=_stable_id(project_id, "firmware-risk", "tasks"),
                project_id=project_id,
                title="Firmware tasks detected and should be reviewed for synchronization",
                risk_type="requires_review",
                status="requires_review",
                confidence=0.5,
                evidence_paths=[item["source_path"] for item in tasks[:3]],
                provenance="static-source-parser",
                metadata={},
            ).to_dict()
        )
    if interrupts:
        risks.append(
            FirmwareRisk(
                id=_stable_id(project_id, "firmware-risk", "interrupts"),
                project_id=project_id,
                title="Interrupt handlers detected with unknown blocking behaviour",
                risk_type="unknown_isr_context",
                status="requires_review",
                confidence=0.55,
                evidence_paths=[item["source_path"] for item in interrupts[:3]],
                provenance="static-source-parser",
                metadata={},
            ).to_dict()
        )
    for finding in memory_findings:
        if finding["name"] == "large_static_buffer":
            risks.append(
                FirmwareRisk(
                    id=_stable_id(project_id, finding["id"], "memory-risk"),
                    project_id=project_id,
                    title="Large static buffer candidate detected",
                    risk_type="large_static_buffer",
                    status="requires_review",
                    confidence=finding["confidence"],
                    evidence_paths=[finding["source_path"]],
                    provenance="static-source-parser",
                    metadata={"memory_finding": finding["id"]},
                ).to_dict()
            )
            break
    return risks


def _scan_firmware_sources(repo_root: Path, project_id: str) -> dict[str, Any]:
    firmware_paths = _firmware_paths(repo_root)
    environments: list[dict[str, Any]] = []
    default_envs: list[str] = []
    supported_parsers = _determine_supported_parsers(firmware_paths, environments)
    modules = _discover_modules(firmware_paths, project_id)
    tasks: list[dict[str, Any]] = []
    rtos_primitives: list[dict[str, Any]] = []
    interrupts: list[dict[str, Any]] = []
    timers: list[dict[str, Any]] = []
    timing_facts: list[dict[str, Any]] = []
    state_machines: list[dict[str, Any]] = []
    peripherals: list[dict[str, Any]] = []
    buses: list[dict[str, Any]] = []
    gpio: list[dict[str, Any]] = []
    protocols: list[dict[str, Any]] = []
    packets: list[dict[str, Any]] = []
    memory_findings: list[dict[str, Any]] = []
    validations: list[dict[str, Any]] = []
    control_flow_risks: list[dict[str, Any]] = []
    isr_findings: list[dict[str, Any]] = []
    for rel_path in firmware_paths:
        path = repo_root / rel_path
        text = _read_text(path)
        lower = rel_path.as_posix().lower()
        if path.name.lower() == "platformio.ini":
            environments, default_envs, parser_names = _parse_platformio_ini(path, project_id)
            supported_parsers = sorted(dict.fromkeys([*supported_parsers, *parser_names]))
        tasks.extend(_detect_tasks(text, rel_path.as_posix(), project_id))
        rtos_primitives.extend(_detect_rtos_primitives(text, rel_path.as_posix(), project_id))
        interrupts.extend(_detect_interrupts(text, rel_path.as_posix(), project_id))
        timers.extend(_detect_timers(text, rel_path.as_posix(), project_id))
        timing_facts.extend(_detect_timing_facts(text, rel_path.as_posix(), project_id))
        state_machines.extend(_detect_state_machines(text, rel_path.as_posix(), project_id))
        peripherals.extend(_detect_peripherals(text, rel_path.as_posix(), project_id))
        buses.extend(_detect_bus_configs(text, rel_path.as_posix(), project_id))
        gpio.extend(_detect_gpio(text, rel_path.as_posix(), project_id))
        protocols.extend(_detect_protocols(text, rel_path.as_posix(), project_id))
        packets.extend(_detect_packet_definitions(text, rel_path.as_posix(), project_id))
        memory_findings.extend(_detect_memory(text, rel_path.as_posix(), project_id))
        risk_items, validation_items = _detect_tasks_or_control_risks(text, rel_path.as_posix(), project_id)
        control_flow_risks.extend(risk_items)
        validations.extend(validation_items)
        isr_findings.extend(_detect_isr_body_risks(text, rel_path.as_posix(), project_id, [item["handler"] for item in interrupts if item.get("source_path") == rel_path.as_posix()]))
        if "watchdog" in lower or "wdt" in lower:
            validations.append(
                FirmwareValidation(
                    id=_stable_id(project_id, rel_path.as_posix(), "watchdog-config"),
                    project_id=project_id,
                    validation_type="watchdog",
                    result="unknown",
                    evidence_path=rel_path.as_posix(),
                    summary="Watchdog-related evidence detected.",
                    confidence=0.55,
                    provenance="static-source-parser",
                    metadata={},
                ).to_dict()
            )
        if tasks and not validations:
            validations.append(
                FirmwareValidation(
                    id=_stable_id(project_id, "tasks", "validation"),
                    project_id=project_id,
                    validation_type="parsing",
                    result="pass",
                    evidence_path=rel_path.as_posix(),
                    summary="Firmware source parsing completed.",
                    confidence=0.8,
                    provenance="static-source-parser",
                    metadata={},
                ).to_dict()
            )
    # Deduplicate by stable id.
    def _dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for item in items:
            item_id = str(item.get("id"))
            if item_id in seen:
                continue
            seen.add(item_id)
            result.append(item)
        return result

    tasks = _dedupe(tasks)
    rtos_primitives = _dedupe(rtos_primitives)
    interrupts = _dedupe(interrupts)
    timers = _dedupe(timers)
    timing_facts = _dedupe(timing_facts)
    state_machines = _dedupe(state_machines)
    peripherals = _dedupe(peripherals)
    buses = _dedupe(buses)
    gpio = _dedupe(gpio)
    protocols = _dedupe(protocols)
    packets = _dedupe(packets)
    memory_findings = _dedupe(memory_findings)
    validations = _dedupe(validations)
    control_flow_risks = _dedupe(control_flow_risks)
    isr_findings = _dedupe(isr_findings)
    supported_parsers = sorted(dict.fromkeys(supported_parsers))
    return {
        "firmware_paths": firmware_paths,
        "supported_parsers": supported_parsers,
        "default_envs": default_envs,
        "environments": environments,
        "modules": modules,
        "tasks": tasks,
        "rtos_primitives": rtos_primitives,
        "interrupts": interrupts,
        "timers": timers,
        "timing_facts": timing_facts,
        "state_machines": state_machines,
        "peripherals": peripherals,
        "buses": buses,
        "gpio": gpio,
        "gpio_conflicts": [],
        "protocols": protocols,
        "packets": packets,
        "memory_findings": memory_findings,
        "validations": validations,
        "findings": isr_findings,
        "control_flow_risks": control_flow_risks,
    }


@dataclass(frozen=True)
class FirmwareEnvironment:
    id: str
    project_id: str
    name: str
    extends: list[str]
    platform: str | None
    board: str | None
    framework: list[str]
    build_flags: list[str]
    lib_deps: list[str]
    upload_protocol: str | None
    monitor_speed: str | None
    custom_options: dict[str, str]
    source_path: str
    confidence: float
    provenance: str
    source_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareTarget:
    id: str
    project_id: str
    environment: str
    board: str | None
    mcu: str | None
    architecture: str | None
    platform: str | None
    framework: list[str]
    source_path: str
    confidence: float
    provenance: str
    source_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareBuildVariant:
    id: str
    project_id: str
    environment: str
    platform: str | None
    board: str | None
    framework: list[str]
    build_flags: list[str]
    defines: list[str]
    libraries: list[str]
    source_filters: list[str]
    source_path: str
    source_line: int | None
    confidence: float
    provenance: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareRTOSPrimitive:
    id: str
    project_id: str
    primitive_type: str
    name: str
    source_path: str
    source_line: int | None
    task_name: str | None
    target: str | None
    operation: str
    confidence: float
    provenance: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareTimingFact:
    id: str
    project_id: str
    fact_type: str
    value: str
    units: str | None
    context: str
    owner: str | None
    source_path: str
    source_line: int | None
    confidence: float
    provenance: str
    normalized_value_ms: float | None = None
    certainty: str = "unknown"
    detector: str = "static-source-parser"
    detector_version: str = DETECTOR_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareBusConfig:
    id: str
    project_id: str
    bus_type: str
    name: str
    source_path: str
    source_line: int | None
    pins: list[str]
    speed: str | None
    address: str | None
    participants: list[str]
    confidence: float
    provenance: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwarePacketDefinition:
    id: str
    project_id: str
    name: str
    fields: list[dict[str, Any]]
    source_path: str
    source_line: int | None
    transport: str | None
    producer: str | None
    consumer: str | None
    version: str | None
    confidence: float
    provenance: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareFinding:
    id: str
    project_id: str
    finding_type: str
    severity: str
    title: str
    affected_entity: str | None
    evidence_paths: list[str]
    source_path: str
    source_line: int | None
    confidence: float
    recommended_investigation: str
    provenance: str
    environment: str | None = None
    entity: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    evidence: list[dict[str, Any]] = field(default_factory=list)
    reason: str | None = None
    related_entities: list[str] = field(default_factory=list)
    scope: str = "unknown"
    recommendation: str | None = None
    detector: str = "static-source-parser"
    detector_version: str = DETECTOR_VERSION
    certainty: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareGPIOConflict:
    id: str
    project_id: str
    gpio: str
    status: str
    firmware_role: str | None
    hardware_signal: str | None
    board_revision: str | None
    source_path: str
    source_line: int | None
    confidence: float
    provenance: str
    scope: str = "unknown"
    environment: str | None = None
    entity: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    evidence: list[dict[str, Any]] = field(default_factory=list)
    reason: str | None = None
    related_entities: list[str] = field(default_factory=list)
    recommendation: str | None = None
    detector: str = "static-gpio-compatibility-parser"
    detector_version: str = DETECTOR_VERSION
    certainty: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareModule:
    id: str
    project_id: str
    name: str
    path: str
    kind: str
    language: str
    includes: list[str]
    confidence: float
    provenance: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareTask:
    id: str
    project_id: str
    name: str
    source_path: str
    evidence: str
    confidence: float
    provenance: str
    scheduler: str | None = None
    priority: int | None = None
    stack_size: int | None = None
    core_affinity: int | None = None
    entry_function: str | None = None
    parameters: list[str] = field(default_factory=list)
    framework: list[str] = field(default_factory=list)
    source_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareISR:
    id: str
    project_id: str
    handler: str
    source_path: str
    shared_state: list[str]
    confidence: float
    provenance: str
    trigger: str | None = None
    peripheral: str | None = None
    priority: int | None = None
    registration_site: str | None = None
    trigger_mode: str | None = None
    source_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareTimer:
    id: str
    project_id: str
    name: str
    source_path: str
    confidence: float
    provenance: str
    period: str | None = None
    period_units: str | None = None
    callback: str | None = None
    owner: str | None = None
    context: str | None = None
    source_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareStateMachine:
    id: str
    project_id: str
    name: str
    source_path: str
    confidence: float
    provenance: str
    states: list[str] = field(default_factory=list)
    state_identities: list[dict[str, Any]] = field(default_factory=list)
    transitions: list[dict[str, Any]] = field(default_factory=list)
    entry_state: str | None = None
    fault_states: list[str] = field(default_factory=list)
    recovery_states: list[str] = field(default_factory=list)
    status: str = "state_machine_candidate"
    detector: str = "static-source-parser"
    detector_version: str = DETECTOR_VERSION
    source_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwarePeripheral:
    id: str
    project_id: str
    name: str
    source_path: str
    peripheral_type: str
    configuration: dict[str, Any]
    confidence: float
    provenance: str
    source_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareGPIOAssignment:
    id: str
    project_id: str
    gpio: str
    symbol: str | None
    source_path: str
    owner: str | None = None
    direction: str | None = None
    confidence: float = 0.0
    provenance: str = "static-source-parser"
    module: str | None = None
    purpose: str | None = None
    environment: str | None = None
    hardware_signal: str | None = None
    board_revision: str | None = None
    status: str = "unknown"
    scope: str = "unknown"
    condition: str | None = None
    detector: str = "static-source-parser"
    detector_version: str = DETECTOR_VERSION
    source_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareProtocol:
    id: str
    project_id: str
    name: str
    source_path: str
    confidence: float = 0.0
    provenance: str = "static-source-parser"
    transport: str | None = None
    fields: list[str] = field(default_factory=list)
    endpoint: str | None = None
    topic: str | None = None
    service: str | None = None
    message: str | None = None
    version: str | None = None
    source_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareMemoryFinding:
    id: str
    project_id: str
    name: str
    source_path: str
    region: str | None = None
    size: int | None = None
    confidence: float = 0.0
    provenance: str = "static-source-parser"
    source_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareValidation:
    id: str
    project_id: str
    validation_type: str
    result: str
    evidence_path: str
    summary: str
    confidence: float
    provenance: str
    source_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareCompatibility:
    id: str
    project_id: str
    firmware_variant: str
    board_revision: str | None
    board_name: str | None
    status: str
    evidence: list[str]
    confidence: float
    provenance: str
    reason: str | None = None
    criteria: dict[str, str] = field(default_factory=dict)
    certainty: str = "unknown"
    detector: str = "static-compatibility-parser"
    detector_version: str = DETECTOR_VERSION
    source_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareRisk:
    id: str
    project_id: str
    title: str
    risk_type: str
    status: str
    confidence: float
    evidence_paths: list[str]
    provenance: str
    source_line: int | None = None
    recommended_investigation: str | None = None
    detector: str = "static-source-parser"
    detector_version: str = DETECTOR_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareGap:
    id: str
    project_id: str
    title: str
    gap_type: str
    severity: str
    confidence: float
    evidence_paths: list[str]
    provenance: str
    source_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirmwareSnapshot:
    id: str
    project_id: str
    observed_at: str
    source_commit: str | None
    source_branch: str | None
    repo_path: str
    supported_parsers: list[str]
    firmware_paths: list[str]
    default_envs: list[str]
    environments: list[FirmwareEnvironment]
    build_variants: list[FirmwareBuildVariant]
    targets: list[FirmwareTarget]
    modules: list[FirmwareModule]
    tasks: list[FirmwareTask]
    rtos_primitives: list[FirmwareRTOSPrimitive]
    interrupts: list[FirmwareISR]
    timers: list[FirmwareTimer]
    timing_facts: list[FirmwareTimingFact]
    state_machines: list[FirmwareStateMachine]
    peripherals: list[FirmwarePeripheral]
    buses: list[FirmwareBusConfig]
    gpio: list[FirmwareGPIOAssignment]
    gpio_conflicts: list[FirmwareGPIOConflict]
    protocols: list[FirmwareProtocol]
    packets: list[FirmwarePacketDefinition]
    memory_findings: list[FirmwareMemoryFinding]
    validations: list[FirmwareValidation]
    compatibility: list[FirmwareCompatibility]
    findings: list[FirmwareFinding]
    risks: list[FirmwareRisk]
    gaps: list[FirmwareGap]
    summary: dict[str, Any]
    provenance: str = "static-firmware-parser"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "environments": [item.to_dict() for item in self.environments],
            "build_variants": [item.to_dict() for item in self.build_variants],
            "targets": [item.to_dict() for item in self.targets],
            "modules": [item.to_dict() for item in self.modules],
            "tasks": [item.to_dict() for item in self.tasks],
            "rtos_primitives": [item.to_dict() for item in self.rtos_primitives],
            "interrupts": [item.to_dict() for item in self.interrupts],
            "timers": [item.to_dict() for item in self.timers],
            "timing_facts": [item.to_dict() for item in self.timing_facts],
            "state_machines": [item.to_dict() for item in self.state_machines],
            "peripherals": [item.to_dict() for item in self.peripherals],
            "buses": [item.to_dict() for item in self.buses],
            "gpio": [item.to_dict() for item in self.gpio],
            "gpio_conflicts": [item.to_dict() for item in self.gpio_conflicts],
            "protocols": [item.to_dict() for item in self.protocols],
            "packets": [item.to_dict() for item in self.packets],
            "memory_findings": [item.to_dict() for item in self.memory_findings],
            "validations": [item.to_dict() for item in self.validations],
            "compatibility": [item.to_dict() for item in self.compatibility],
            "findings": [item.to_dict() for item in self.findings],
            "risks": [item.to_dict() for item in self.risks],
            "gaps": [item.to_dict() for item in self.gaps],
        }


def build_firmware_intelligence(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    row = conn.execute("SELECT project_id, name, repo_path FROM projects WHERE project_id=?", (project_id,)).fetchone()
    if row is None:
        conn.close()
        raise ValueError(f"Unknown project: {project_id}")
    scan = conn.execute(
        "SELECT scan_id, git_commit, git_branch, created_at FROM scans WHERE project_id=? ORDER BY created_at DESC, scan_id DESC LIMIT 1",
        (project_id,),
    ).fetchone()
    conn.close()

    repo_root = Path(row["repo_path"]).resolve()
    scan_data = _scan_firmware_sources(repo_root, project_id)
    hardware_snapshot: dict[str, Any] | None = None
    try:
        hardware_snapshot = build_hardware_intelligence(db_path, project_id)
    except ValueError:
        hardware_snapshot = None

    environments = [
        FirmwareEnvironment(**item) if isinstance(item, dict) else item
        for item in scan_data["environments"]
    ]
    targets: list[FirmwareTarget] = []
    for env in environments:
        targets.append(
            FirmwareTarget(
                id=_stable_id(project_id, env.name, env.board or env.platform or "target"),
                project_id=project_id,
                environment=env.name,
                board=env.board,
                mcu=env.board or env.platform,
                architecture=_architecture_from_board(env.board, env.platform),
                platform=env.platform,
                framework=env.framework,
                source_path=env.source_path,
                confidence=0.85 if env.board or env.platform else 0.55,
                provenance="static-target-derivation",
                metadata={"default_envs": scan_data["default_envs"]},
            )
        )

    compatibility, compatibility_state = _build_compatibility(
        project_id=project_id,
        environments=[env.to_dict() for env in environments],
        hardware_snapshot=hardware_snapshot,
    )
    build_variants = [
        FirmwareBuildVariant(**item) if isinstance(item, dict) else item
        for item in _detect_build_variants([env.to_dict() for env in environments], project_id)
    ]
    rtos_primitives = [FirmwareRTOSPrimitive(**item) if isinstance(item, dict) else item for item in scan_data["rtos_primitives"]]
    timing_facts = [FirmwareTimingFact(**item) if isinstance(item, dict) else item for item in scan_data["timing_facts"]]
    buses = [FirmwareBusConfig(**item) if isinstance(item, dict) else item for item in scan_data["buses"]]
    packets = [FirmwarePacketDefinition(**item) if isinstance(item, dict) else item for item in scan_data["packets"]]
    isr_findings = [FirmwareFinding(**item) if isinstance(item, dict) else item for item in scan_data["findings"]]
    gpio_assignments = [FirmwareGPIOAssignment(**item) if isinstance(item, dict) else item for item in scan_data["gpio"]]
    gpio_conflicts = _build_gpio_conflicts(
        project_id=project_id,
        gpio=[item.to_dict() for item in gpio_assignments],
        hardware_snapshot=hardware_snapshot,
    )
    gaps = _build_gaps(
        project_id=project_id,
        paths=scan_data["firmware_paths"],
        environments=[env.to_dict() for env in environments],
        tasks=scan_data["tasks"],
        interrupts=scan_data["interrupts"],
        timers=scan_data["timers"],
        state_machines=scan_data["state_machines"],
        protocols=scan_data["protocols"],
        compatibility=compatibility,
    )
    risks = _build_risks(
        project_id=project_id,
        tasks=scan_data["tasks"],
        interrupts=scan_data["interrupts"],
        memory_findings=scan_data["memory_findings"],
        control_flow_risks=scan_data["control_flow_risks"],
    )
    validations = [FirmwareValidation(**item) if isinstance(item, dict) else item for item in scan_data["validations"]]
    findings = isr_findings
    if gpio_conflicts:
        findings.extend(
            FirmwareFinding(
                id=_stable_id(project_id, conflict["gpio"], conflict["status"], conflict.get("hardware_signal") or "unknown", "gpio-finding"),
                project_id=project_id,
                finding_type="gpio_conflict",
                severity="requires_review" if conflict["status"] == "conflict" else "low",
                title=f"GPIO {conflict['gpio']} requires review",
                affected_entity=conflict.get("firmware_role") or conflict["gpio"],
                evidence_paths=[conflict.get("source_path") or str(repo_root)],
                source_path=conflict.get("source_path") or str(repo_root),
                source_line=conflict.get("source_line"),
                confidence=conflict["confidence"],
                recommended_investigation="Verify firmware GPIO ownership against the hardware pin map and board revision.",
                provenance="static-gpio-compatibility-parser",
                metadata={"gpio_conflict": conflict},
            )
            for conflict in gpio_conflicts
        )
    if environments and not any(item.validation_type == "parsing" and item.result == "pass" for item in validations):
        validations.append(
            FirmwareValidation(
                id=_stable_id(project_id, "parsing", "validation"),
                project_id=project_id,
                validation_type="parsing",
                result="pass",
                evidence_path=scan_data["firmware_paths"][0].as_posix() if scan_data["firmware_paths"] else str(repo_root.as_posix()),
                summary="Firmware source parsing completed.",
                confidence=0.8,
                provenance="static-source-parser",
                metadata={},
            )
        )

    snapshot = FirmwareSnapshot(
        id=_stable_id(project_id, scan["git_commit"] if scan else "unknown", scan["created_at"] if scan else "unknown", "firmware-snapshot"),
        project_id=project_id,
        observed_at=scan["created_at"] if scan else _utcnow(),
        source_commit=scan["git_commit"] if scan else None,
        source_branch=scan["git_branch"] if scan else None,
        repo_path=str(repo_root),
        supported_parsers=scan_data["supported_parsers"],
        firmware_paths=[path.as_posix() for path in scan_data["firmware_paths"]],
        default_envs=scan_data["default_envs"],
        environments=environments,
        build_variants=build_variants,
        targets=targets,
        modules=[FirmwareModule(**item) if isinstance(item, dict) else item for item in scan_data["modules"]],
        tasks=[FirmwareTask(**item) if isinstance(item, dict) else item for item in scan_data["tasks"]],
        rtos_primitives=rtos_primitives,
        interrupts=[FirmwareISR(**item) if isinstance(item, dict) else item for item in scan_data["interrupts"]],
        timers=[FirmwareTimer(**item) if isinstance(item, dict) else item for item in scan_data["timers"]],
        timing_facts=timing_facts,
        state_machines=[FirmwareStateMachine(**item) if isinstance(item, dict) else item for item in scan_data["state_machines"]],
        peripherals=[FirmwarePeripheral(**item) if isinstance(item, dict) else item for item in scan_data["peripherals"]],
        buses=buses,
        gpio=gpio_assignments,
        gpio_conflicts=[FirmwareGPIOConflict(**item) if isinstance(item, dict) else item for item in gpio_conflicts],
        protocols=[FirmwareProtocol(**item) if isinstance(item, dict) else item for item in scan_data["protocols"]],
        packets=packets,
        memory_findings=[FirmwareMemoryFinding(**item) if isinstance(item, dict) else item for item in scan_data["memory_findings"]],
        validations=validations,
        compatibility=[FirmwareCompatibility(**item) if isinstance(item, dict) else item for item in compatibility],
        findings=findings,
        risks=[FirmwareRisk(**item) if isinstance(item, dict) else item for item in risks],
        gaps=[FirmwareGap(**item) if isinstance(item, dict) else item for item in gaps],
        summary={
            "project_id": project_id,
            "project_name": row["name"],
            "repo_path": str(repo_root),
            "supported_parsers": scan_data["supported_parsers"],
            "firmware_source_count": len(scan_data["firmware_paths"]),
            "environment_count": len(environments),
            "target_count": len(targets),
            "build_variant_count": len(build_variants),
            "module_count": len(scan_data["modules"]),
            "task_count": len(scan_data["tasks"]),
            "rtos_primitive_count": len(scan_data["rtos_primitives"]),
            "interrupt_count": len(scan_data["interrupts"]),
            "timer_count": len(scan_data["timers"]),
            "timing_fact_count": len(scan_data["timing_facts"]),
            "state_machine_count": len(scan_data["state_machines"]),
            "peripheral_count": len(scan_data["peripherals"]),
            "bus_count": len(scan_data["buses"]),
            "gpio_count": len(scan_data["gpio"]),
            "gpio_conflict_count": len(gpio_conflicts),
            "protocol_count": len(scan_data["protocols"]),
            "packet_count": len(scan_data["packets"]),
            "memory_finding_count": len(scan_data["memory_findings"]),
            "validation_count": len(validations),
            "compatibility_count": len(compatibility),
            "finding_count": len(findings),
            "risk_count": len(risks),
            "gap_count": len(gaps),
            "compatibility_state": compatibility_state,
            "hardware_board_count": len((hardware_snapshot or {}).get("boards", []) or []),
        },
        metadata={
            "default_envs": scan_data["default_envs"],
            "hardware_project_present": hardware_snapshot is not None,
        },
    )
    return snapshot.to_dict()


def firmware_inventory(db_path: Path, project_id: str) -> dict[str, Any]:
    return build_firmware_intelligence(db_path, project_id)


def firmware_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    return snapshot.get("summary", {})


def _items(snapshot: dict[str, Any], key: str) -> dict[str, Any]:
    items = snapshot.get(key, [])
    return {"count": len(items), "items": items}


def firmware_environments(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "environments")


def firmware_targets(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "targets")


def firmware_build_variants(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "build_variants")


def firmware_modules(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "modules")


def firmware_tasks(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "tasks")


def firmware_rtos_primitives(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "rtos_primitives")


def firmware_interrupts(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "interrupts")


def firmware_timers(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "timers")


def firmware_timing(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "timing_facts")


def firmware_state_machines(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "state_machines")


def firmware_peripherals(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "peripherals")


def firmware_buses(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "buses")


def firmware_gpio(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "gpio")


def firmware_gpio_conflicts(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "gpio_conflicts")


def firmware_protocols(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "protocols")


def firmware_packets(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "packets")


def firmware_memory(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "memory_findings")


def firmware_findings(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "findings")


def firmware_validation(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "count": len(snapshot.get("validations", [])),
        "items": snapshot.get("validations", []),
        "compatibility_state": snapshot.get("summary", {}).get("compatibility_state", "unknown"),
    }


def firmware_compatibility(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "compatibility")


def firmware_gaps(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "gaps")


def firmware_risks(snapshot: dict[str, Any]) -> dict[str, Any]:
    return _items(snapshot, "risks")


def firmware_trace(snapshot: dict[str, Any], entity_id: str) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    for key in (
        "build_variants",
        "environments",
        "targets",
        "modules",
        "tasks",
        "rtos_primitives",
        "interrupts",
        "timers",
        "timing_facts",
        "state_machines",
        "peripherals",
        "buses",
        "gpio",
        "gpio_conflicts",
        "protocols",
        "packets",
        "memory_findings",
        "validations",
        "compatibility",
        "findings",
        "risks",
        "gaps",
    ):
        for item in snapshot.get(key, []):
            if entity_id in json.dumps(item, sort_keys=True):
                hits.append({"collection": key, "item": item})
    return {"entity_id": entity_id, "count": len(hits), "items": hits}


def firmware_impact(snapshot: dict[str, Any], entity_id: str) -> dict[str, Any]:
    trace = firmware_trace(snapshot, entity_id)
    return {
        "entity_id": entity_id,
        "count": trace["count"],
        "items": trace["items"],
        "summary": snapshot.get("summary", {}),
    }


def firmware_diff(db_path: Path, project_id: str, other_project_id: str | None = None) -> dict[str, Any]:
    primary = firmware_inventory(db_path, project_id)
    secondary = firmware_inventory(db_path, other_project_id or project_id)
    primary_summary = firmware_summary(primary)
    secondary_summary = firmware_summary(secondary)
    return {
        "from_project_id": project_id,
        "to_project_id": other_project_id or project_id,
        "from_summary": primary_summary,
        "to_summary": secondary_summary,
        "environment_count_delta": secondary_summary.get("environment_count", 0) - primary_summary.get("environment_count", 0),
        "target_count_delta": secondary_summary.get("target_count", 0) - primary_summary.get("target_count", 0),
        "build_variant_count_delta": secondary_summary.get("build_variant_count", 0) - primary_summary.get("build_variant_count", 0),
        "task_count_delta": secondary_summary.get("task_count", 0) - primary_summary.get("task_count", 0),
        "rtos_primitive_count_delta": secondary_summary.get("rtos_primitive_count", 0) - primary_summary.get("rtos_primitive_count", 0),
        "interrupt_count_delta": secondary_summary.get("interrupt_count", 0) - primary_summary.get("interrupt_count", 0),
        "timer_count_delta": secondary_summary.get("timer_count", 0) - primary_summary.get("timer_count", 0),
        "timing_fact_count_delta": secondary_summary.get("timing_fact_count", 0) - primary_summary.get("timing_fact_count", 0),
        "bus_count_delta": secondary_summary.get("bus_count", 0) - primary_summary.get("bus_count", 0),
        "gpio_conflict_count_delta": secondary_summary.get("gpio_conflict_count", 0) - primary_summary.get("gpio_conflict_count", 0),
        "packet_count_delta": secondary_summary.get("packet_count", 0) - primary_summary.get("packet_count", 0),
        "finding_count_delta": secondary_summary.get("finding_count", 0) - primary_summary.get("finding_count", 0),
        "compatibility_state_from": primary_summary.get("compatibility_state", "unknown"),
        "compatibility_state_to": secondary_summary.get("compatibility_state", "unknown"),
    }
