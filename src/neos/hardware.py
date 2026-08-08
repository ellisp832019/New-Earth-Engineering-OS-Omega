from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .db import connect

ENGINE_VERSION = "1.1.0"

HARDWARE_SUFFIXES = {
    ".kicad_pro",
    ".kicad_sch",
    ".kicad_pcb",
    ".csv",
    ".json",
    ".md",
    ".txt",
    ".ini",
    ".yaml",
    ".yml",
}

HARDWARE_HINTS = (
    "hardware",
    "board",
    "board revision",
    "revision",
    "schematic",
    "pcb",
    "bom",
    "bill of materials",
    "pin map",
    "pinmap",
    "gpio",
    "datasheet",
    "validation",
    "bring-up",
    "bring up",
    "bench",
    "power",
    "relay",
    "sensor",
    "actuator",
    "connector",
    "kicad",
    "platformio",
)

GPIO_RE = re.compile(r"\b(GPIO\d+)\b\s*(?:[:=]|->|=>)\s*([A-Za-z0-9_./-]+)", re.IGNORECASE)
PIN_PAIR_RE = re.compile(
    r"\b([A-Z][A-Z0-9_./-]{1,40})\b\s*(?:[:=]|->|=>)\s*([A-Z0-9_./-]{1,40})",
    re.IGNORECASE,
)
DATASHEET_RE = re.compile(r"(https?://\S+|datasheet\s*[:=]\s*[^\s)]+)", re.IGNORECASE)
BOARD_REV_RE = re.compile(r"\b(?:rev(?:ision)?|r)\s*([a-z0-9]+)\b", re.IGNORECASE)
NET_RE = re.compile(r"\b(3V3|5V|VIN|VBAT|VCC|GND|AGND|DGND|VREF)\b", re.IGNORECASE)
CONNECTOR_RE = re.compile(r"\b(J\d+|JP\d+|P\d+|CN\d+|CONN\d+)\b", re.IGNORECASE)
COMPONENT_RE = re.compile(r"\b(R\d+|C\d+|L\d+|D\d+|U\d+|Q\d+|J\d+|JP\d+|P\d+|CN\d+|F\d+)\b", re.IGNORECASE)


@dataclass(frozen=True)
class BoardRevision:
    id: str
    project_id: str
    name: str
    revision: str
    status: str
    source: str
    schematic_path: str | None
    pcb_path: str | None
    bom_path: str | None
    created_at: str
    observed_at: str
    scan_id: str | None
    source_commit: str | None
    confidence: float
    provenance: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ComponentModel:
    id: str
    project_id: str
    manufacturer: str | None
    manufacturer_part_number: str | None
    category: str
    description: str
    package: str | None
    value: str | None
    voltage_rating: str | None
    current_rating: str | None
    tolerance: str | None
    datasheet: str | None
    lifecycle_status: str | None
    source: str
    confidence: float
    provenance: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ComponentInstance:
    id: str
    project_id: str
    board_id: str
    reference_designator: str
    component_model_id: str | None
    footprint: str | None
    value: str | None
    location: str | None
    pins: list[str] = field(default_factory=list)
    net_relationships: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.5
    provenance: str = "deterministic-hardware-parser"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Connector:
    id: str
    project_id: str
    board_id: str
    reference: str
    connector_type: str
    pins: list[dict[str, Any]]
    source: str
    confidence: float
    provenance: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PinMapping:
    id: str
    project_id: str
    board_id: str | None
    hardware_pin: str
    signal: str
    firmware_symbol: str | None
    source_paths: list[str]
    confidence: float
    validation_status: str
    provenance: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PowerRail:
    id: str
    project_id: str
    name: str
    voltage_domain: str | None
    source_paths: list[str]
    consumers: list[str] = field(default_factory=list)
    confidence: float = 0.5
    provenance: str = "deterministic-hardware-parser"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DatasheetReference:
    id: str
    project_id: str
    component_ref: str | None
    component_model_id: str | None
    reference: str
    source_path: str
    source_line: int | None
    confidence: float
    availability: str
    provenance: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HardwareValidationEvidence:
    id: str
    project_id: str
    board_id: str | None
    validation_type: str
    result: str
    evidence_path: str
    summary: str
    confidence: float
    provenance: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HardwareRisk:
    id: str
    project_id: str
    title: str
    status: str
    confidence: float
    evidence_paths: list[str]
    provenance: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HardwareGap:
    id: str
    project_id: str
    title: str
    gap_type: str
    severity: str
    confidence: float
    evidence_paths: list[str]
    provenance: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HardwareSnapshot:
    id: str
    project_id: str
    observed_at: str
    source_commit: str | None
    source_branch: str | None
    repo_path: str
    schematic_hash: str | None
    pcb_hash: str | None
    bom_hash: str | None
    pin_map_hash: str | None
    component_inventory_hash: str | None
    validation_state: str
    boards: list[BoardRevision]
    components: list[ComponentModel]
    component_instances: list[ComponentInstance]
    connectors: list[Connector]
    pins: list[PinMapping]
    power_rails: list[PowerRail]
    datasheets: list[DatasheetReference]
    validations: list[HardwareValidationEvidence]
    risks: list[HardwareRisk]
    gaps: list[HardwareGap]
    traceability: dict[str, Any]
    summary: dict[str, Any]
    provenance: str = "deterministic-hardware-parser"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "boards": [item.to_dict() for item in self.boards],
            "components": [item.to_dict() for item in self.components],
            "component_instances": [item.to_dict() for item in self.component_instances],
            "connectors": [item.to_dict() for item in self.connectors],
            "pins": [item.to_dict() for item in self.pins],
            "power_rails": [item.to_dict() for item in self.power_rails],
            "datasheets": [item.to_dict() for item in self.datasheets],
            "validations": [item.to_dict() for item in self.validations],
            "risks": [item.to_dict() for item in self.risks],
            "gaps": [item.to_dict() for item in self.gaps],
        }


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _json_dumps(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _json_loads(raw: str | None, fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _stable_id(*parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _is_candidate_path(path: Path) -> bool:
    lowered = path.as_posix().lower()
    if path.suffix.lower() in HARDWARE_SUFFIXES:
        return True
    return any(token in lowered for token in HARDWARE_HINTS)


def _hardware_paths(repo_root: Path) -> list[Path]:
    results: list[Path] = []
    for base, dirs, files in os.walk(repo_root):
        dirs[:] = sorted(
            d
            for d in dirs
            if d not in {".git", ".neos", ".venv", "build", "dist", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", ".dart_tool"}
        )
        base_path = Path(base)
        for name in sorted(files):
            path = base_path / name
            rel = path.relative_to(repo_root)
            if _is_candidate_path(rel):
                results.append(rel)
    return results


def _board_name_from_path(path: Path) -> str:
    stem = path.stem
    stem = re.sub(r"[_-]+", " ", stem).strip()
    return stem.title() or path.parent.name.title() or "Hardware Board"


def _revision_from_text(text: str, fallback: str = "unknown") -> str:
    match = BOARD_REV_RE.search(text)
    if match:
        return match.group(1).upper()
    return fallback


def _normalise_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _parse_bom_csv(path: Path, project_id: str, board_id: str) -> tuple[list[ComponentModel], list[ComponentInstance], str | None]:
    try:
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
    except (OSError, csv.Error):
        return [], [], None

    if not rows:
        return [], [], None

    headers = {_normalise_header(header): header for header in (reader.fieldnames or [])}

    def column(*names: str) -> str | None:
        for name in names:
            if name in headers:
                return headers[name]
        return None

    ref_col = column("reference", "refdes", "designator", "ref")
    value_col = column("value", "partvalue")
    footprint_col = column("footprint", "package")
    manufacturer_col = column("manufacturer", "mfr")
    mpn_col = column("manufacturerpartnumber", "mpn", "partnumber", "partno")
    description_col = column("description", "desc")
    datasheet_col = column("datasheet", "sheet")
    quantity_col = column("quantity", "qty")

    components: list[ComponentModel] = []
    instances: list[ComponentInstance] = []
    for index, row in enumerate(rows):
        ref = str(row.get(ref_col, "")).strip() if ref_col else ""
        value = str(row.get(value_col, "")).strip() if value_col else ""
        footprint = str(row.get(footprint_col, "")).strip() if footprint_col else ""
        manufacturer = str(row.get(manufacturer_col, "")).strip() if manufacturer_col else ""
        mpn = str(row.get(mpn_col, "")).strip() if mpn_col else ""
        description = str(row.get(description_col, "")).strip() if description_col else ""
        datasheet = str(row.get(datasheet_col, "")).strip() if datasheet_col else ""
        category = "connector" if CONNECTOR_RE.fullmatch(ref or "") else "component"
        component_model_id = _stable_id(project_id, manufacturer, mpn, value, footprint, description, category)
        if mpn or manufacturer or description or value:
            components.append(
                ComponentModel(
                    id=component_model_id,
                    project_id=project_id,
                    manufacturer=manufacturer or None,
                    manufacturer_part_number=mpn or None,
                    category=category,
                    description=description or value or ref or "BOM component",
                    package=footprint or None,
                    value=value or None,
                    voltage_rating=None,
                    current_rating=None,
                    tolerance=None,
                    datasheet=datasheet or None,
                    lifecycle_status=None,
                    source=str(path.as_posix()),
                    confidence=0.82,
                    provenance="bom-csv-parser",
                    metadata={"row_index": index, "quantity": row.get(quantity_col) if quantity_col else None},
                )
            )
        if ref:
            instances.append(
                ComponentInstance(
                    id=_stable_id(project_id, board_id, ref, footprint, value),
                    project_id=project_id,
                    board_id=board_id,
                    reference_designator=ref,
                    component_model_id=component_model_id,
                    footprint=footprint or None,
                    value=value or None,
                    location=None,
                    pins=[],
                    net_relationships=[],
                    confidence=0.78,
                    provenance="bom-csv-parser",
                    metadata={"source_path": str(path.as_posix())},
                )
            )
    return components, instances, str(path.as_posix())


def _parse_bom_json(path: Path, project_id: str, board_id: str) -> tuple[list[ComponentModel], list[ComponentInstance], str | None]:
    try:
        data = json.loads(_read_text(path))
    except json.JSONDecodeError:
        return [], [], None
    rows: list[dict[str, Any]] = []
    if isinstance(data, list):
        rows = [row for row in data if isinstance(row, dict)]
    elif isinstance(data, dict):
        for key in ("items", "components", "bom", "rows"):
            value = data.get(key)
            if isinstance(value, list):
                rows = [row for row in value if isinstance(row, dict)]
                break
    if not rows:
        return [], [], None
    components: list[ComponentModel] = []
    instances: list[ComponentInstance] = []
    for index, row in enumerate(rows):
        ref = str(row.get("reference") or row.get("ref") or row.get("designator") or "").strip()
        value = str(row.get("value") or row.get("part_value") or "").strip()
        footprint = str(row.get("footprint") or row.get("package") or "").strip()
        manufacturer = str(row.get("manufacturer") or row.get("mfr") or "").strip()
        mpn = str(row.get("mpn") or row.get("manufacturer_part_number") or row.get("part_number") or "").strip()
        description = str(row.get("description") or row.get("desc") or "").strip()
        datasheet = str(row.get("datasheet") or row.get("sheet") or "").strip()
        category = str(row.get("category") or ("connector" if CONNECTOR_RE.fullmatch(ref or "") else "component")).strip() or "component"
        component_model_id = _stable_id(project_id, manufacturer, mpn, value, footprint, description, category)
        components.append(
            ComponentModel(
                id=component_model_id,
                project_id=project_id,
                manufacturer=manufacturer or None,
                manufacturer_part_number=mpn or None,
                category=category,
                description=description or value or ref or "BOM component",
                package=footprint or None,
                value=value or None,
                voltage_rating=str(row.get("voltage_rating") or row.get("voltage") or "").strip() or None,
                current_rating=str(row.get("current_rating") or row.get("current") or "").strip() or None,
                tolerance=str(row.get("tolerance") or "").strip() or None,
                datasheet=datasheet or None,
                lifecycle_status=str(row.get("lifecycle") or row.get("lifecycle_status") or "").strip() or None,
                source=str(path.as_posix()),
                confidence=0.9,
                provenance="bom-json-parser",
                metadata={"row_index": index},
            )
        )
        if ref:
            instances.append(
                ComponentInstance(
                    id=_stable_id(project_id, board_id, ref, footprint, value),
                    project_id=project_id,
                    board_id=board_id,
                    reference_designator=ref,
                    component_model_id=component_model_id,
                    footprint=footprint or None,
                    value=value or None,
                    location=str(row.get("location") or "").strip() or None,
                    pins=[str(pin) for pin in row.get("pins", [])] if isinstance(row.get("pins"), list) else [],
                    net_relationships=[],
                    confidence=0.86,
                    provenance="bom-json-parser",
                    metadata={"source_path": str(path.as_posix())},
                )
            )
    return components, instances, str(path.as_posix())


def _parse_pin_map(path: Path, project_id: str, board_id: str) -> list[PinMapping]:
    text = _read_text(path)
    mappings: list[PinMapping] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        gpio = GPIO_RE.search(stripped)
        pin_match = PIN_PAIR_RE.search(stripped)
        if gpio:
            hardware_pin, signal = gpio.group(1), gpio.group(2)
        elif pin_match and ("gpio" in stripped.lower() or "pin" in stripped.lower() or "signal" in stripped.lower() or "->" in stripped or "=" in stripped):
            hardware_pin, signal = pin_match.group(1), pin_match.group(2)
        else:
            continue
        firmware_symbol = None
        if signal.upper().startswith(("GPIO", "I2C_", "SPI_", "UART_", "PWM_", "ADC_", "DAC_", "SDA", "SCL")):
            firmware_symbol = signal
        mappings.append(
            PinMapping(
                id=_stable_id(project_id, board_id, hardware_pin, signal, str(path.as_posix())),
                project_id=project_id,
                board_id=board_id,
                hardware_pin=hardware_pin.upper(),
                signal=signal.upper(),
                firmware_symbol=firmware_symbol,
                source_paths=[str(path.as_posix())],
                confidence=0.88,
                validation_status="unverified",
                provenance="deterministic-pin-map-parser",
                metadata={"line": stripped},
            )
        )
    return mappings


def _parse_datasheets(path: Path, project_id: str) -> list[DatasheetReference]:
    text = _read_text(path)
    references: list[DatasheetReference] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if "datasheet" not in line.lower() and "http" not in line.lower():
            continue
        match = DATASHEET_RE.search(line)
        if not match:
            continue
        references.append(
            DatasheetReference(
                id=_stable_id(project_id, str(path.as_posix()), line_no, match.group(1)),
                project_id=project_id,
                component_ref=None,
                component_model_id=None,
                reference=match.group(1).strip(),
                source_path=str(path.as_posix()),
                source_line=line_no,
                confidence=0.7,
                availability="referenced",
                provenance="deterministic-datasheet-parser",
                metadata={"line": line.strip()},
            )
        )
    return references


def _parse_validation(path: Path, project_id: str, board_id: str) -> list[HardwareValidationEvidence]:
    text = _read_text(path)
    lowered = text.lower()
    if not any(token in lowered for token in ("validation", "bring-up", "bring up", "bench", "hardware test", "power-on", "continuity")):
        return []
    result = "pass" if any(token in lowered for token in ("pass", "passed", "healthy", "verified")) else "unknown"
    validation_type = "manual inspection"
    if "power" in lowered:
        validation_type = "power-on"
    elif "continuity" in lowered:
        validation_type = "continuity"
    elif "bench" in lowered:
        validation_type = "bench test"
    elif "sensor" in lowered:
        validation_type = "sensor functional"
    return [
        HardwareValidationEvidence(
            id=_stable_id(project_id, board_id, str(path.as_posix()), validation_type),
            project_id=project_id,
            board_id=board_id,
            validation_type=validation_type,
            result=result,
            evidence_path=str(path.as_posix()),
            summary=_summary_sentence(text),
            confidence=0.78,
            provenance="deterministic-validation-parser",
            metadata={"source_path": str(path.as_posix())},
        )
    ]


def _summary_sentence(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:240]
    return ""


def _extract_board_revisions(repo_root: Path, project_id: str, source_commit: str | None, scan_id: str | None, hardware_paths: list[Path]) -> list[BoardRevision]:
    boards: dict[str, BoardRevision] = {}
    for path in hardware_paths:
        if path.suffix.lower() not in {".kicad_pro", ".kicad_sch", ".kicad_pcb"}:
            continue
        text = _read_text(repo_root / path)
        name = _board_name_from_path(path)
        revision = _revision_from_text(text, fallback=_revision_from_text(path.as_posix(), "unknown"))
        board_key = _stable_id(project_id, name, revision)
        existing = boards.get(board_key)
        if existing is not None:
            schematic_path = existing.schematic_path or (str(path.as_posix()) if path.suffix.lower() == ".kicad_sch" else None)
            pcb_path = existing.pcb_path or (str(path.as_posix()) if path.suffix.lower() == ".kicad_pcb" else None)
            source = existing.source + ";detected"
            boards[board_key] = BoardRevision(
                id=existing.id,
                project_id=project_id,
                name=existing.name,
                revision=existing.revision,
                status=existing.status,
                source=source,
                schematic_path=schematic_path,
                pcb_path=pcb_path,
                bom_path=existing.bom_path,
                created_at=existing.created_at,
                observed_at=existing.observed_at,
                scan_id=scan_id,
                source_commit=source_commit,
                confidence=max(existing.confidence, 0.78),
                provenance=existing.provenance,
                metadata=existing.metadata,
            )
            continue
        boards[board_key] = BoardRevision(
            id=board_key,
            project_id=project_id,
            name=name,
            revision=revision,
            status="unknown",
            source="deterministic-file-discovery",
            schematic_path=str(path.as_posix()) if path.suffix.lower() == ".kicad_sch" else None,
            pcb_path=str(path.as_posix()) if path.suffix.lower() == ".kicad_pcb" else None,
            bom_path=None,
            created_at=_utcnow(),
            observed_at=_utcnow(),
            scan_id=scan_id,
            source_commit=source_commit,
            confidence=0.8,
            provenance="deterministic-hardware-parser",
            metadata={"source_path": str(path.as_posix())},
        )
    if boards:
        return sorted(boards.values(), key=lambda item: (item.name.lower(), item.revision.lower()))
    return [
        BoardRevision(
            id=_stable_id(project_id, repo_root.name, source_commit or "unknown"),
            project_id=project_id,
            name=repo_root.name.replace("-", " ").replace("_", " ").title(),
            revision="unknown",
            status="unknown",
            source="repository-root",
            schematic_path=None,
            pcb_path=None,
            bom_path=None,
            created_at=_utcnow(),
            observed_at=_utcnow(),
            scan_id=scan_id,
            source_commit=source_commit,
            confidence=0.3,
            provenance="deterministic-hardware-parser",
            metadata={"source_path": str(repo_root.as_posix())},
        )
    ]


def _hardware_risks_and_gaps(
    *,
    project_id: str,
    boards: list[BoardRevision],
    components: list[ComponentModel],
    component_instances: list[ComponentInstance],
    pins: list[PinMapping],
    datasheets: list[DatasheetReference],
    validations: list[HardwareValidationEvidence],
    hardware_paths: list[Path],
) -> tuple[list[HardwareRisk], list[HardwareGap], dict[str, Any]]:
    risks: list[HardwareRisk] = []
    gaps: list[HardwareGap] = []
    traceability = {
        "board_count": len(boards),
        "component_count": len(components),
        "component_instance_count": len(component_instances),
        "pin_mapping_count": len(pins),
        "datasheet_reference_count": len(datasheets),
        "validation_count": len(validations),
    }
    if not boards or (len(boards) == 1 and boards[0].revision == "unknown"):
        gaps.append(
            HardwareGap(
                id=_stable_id(project_id, "board-gap"),
                project_id=project_id,
                title="No explicit board revision evidence",
                gap_type="board",
                severity="medium",
                confidence=0.7,
                evidence_paths=[str(path.as_posix()) for path in hardware_paths[:3]],
                provenance="deterministic-hardware-parser",
                metadata={},
            )
        )
    if not components:
        gaps.append(
            HardwareGap(
                id=_stable_id(project_id, "component-gap"),
                project_id=project_id,
                title="No component inventory evidence",
                gap_type="component",
                severity="medium",
                confidence=0.8,
                evidence_paths=[str(path.as_posix()) for path in hardware_paths[:3]],
                provenance="deterministic-hardware-parser",
                metadata={},
            )
        )
    if not pins:
        gaps.append(
            HardwareGap(
                id=_stable_id(project_id, "pin-gap"),
                project_id=project_id,
                title="No explicit firmware-to-hardware pin mapping evidence",
                gap_type="pin_mapping",
                severity="high",
                confidence=0.9,
                evidence_paths=[str(path.as_posix()) for path in hardware_paths[:3]],
                provenance="deterministic-hardware-parser",
                metadata={},
            )
        )
    if not validations:
        gaps.append(
            HardwareGap(
                id=_stable_id(project_id, "validation-gap"),
                project_id=project_id,
                title="No hardware validation evidence found",
                gap_type="validation",
                severity="high",
                confidence=0.9,
                evidence_paths=[str(path.as_posix()) for path in hardware_paths[:3]],
                provenance="deterministic-hardware-parser",
                metadata={},
            )
        )
    if not datasheets:
        gaps.append(
            HardwareGap(
                id=_stable_id(project_id, "datasheet-gap"),
                project_id=project_id,
                title="No datasheet references found",
                gap_type="datasheet",
                severity="low",
                confidence=0.75,
                evidence_paths=[str(path.as_posix()) for path in hardware_paths[:3]],
                provenance="deterministic-hardware-parser",
                metadata={},
            )
        )

    if pins and any(pin.validation_status == "unverified" for pin in pins):
        risks.append(
            HardwareRisk(
                id=_stable_id(project_id, "pin-risk"),
                project_id=project_id,
                title="Pin mappings are present but remain unverified",
                status="requires_review",
                confidence=0.72,
                evidence_paths=[pin.source_paths[0] for pin in pins[:5]],
                provenance="deterministic-hardware-parser",
                metadata={},
            )
        )
    if components and not datasheets:
        risks.append(
            HardwareRisk(
                id=_stable_id(project_id, "datasheet-risk"),
                project_id=project_id,
                title="Components exist without datasheet references",
                status="datasheet_gap",
                confidence=0.75,
                evidence_paths=[instance.reference_designator for instance in component_instances[:5] if instance.reference_designator],
                provenance="deterministic-hardware-parser",
                metadata={},
            )
        )
    if not validations and (boards or components):
        risks.append(
            HardwareRisk(
                id=_stable_id(project_id, "validation-risk"),
                project_id=project_id,
                title="Hardware evidence exists without validation coverage",
                status="requires_review",
                confidence=0.85,
                evidence_paths=[str(path.as_posix()) for path in hardware_paths[:5]],
                provenance="deterministic-hardware-parser",
                metadata={},
            )
        )
    return risks, gaps, traceability


def _build_power_rails(project_id: str, hardware_paths: list[Path]) -> list[PowerRail]:
    rails: dict[str, PowerRail] = {}
    for path in hardware_paths:
        text = _read_text(path)
        for match in NET_RE.finditer(text):
            rail = match.group(1).upper()
            if rail not in rails:
                rails[rail] = PowerRail(
                    id=_stable_id(project_id, rail),
                    project_id=project_id,
                    name=rail,
                    voltage_domain="unknown" if rail in {"GND", "AGND", "DGND"} else None,
                    source_paths=[str(path.as_posix())],
                    consumers=[],
                    confidence=0.68,
                    provenance="deterministic-power-parser",
                    metadata={},
                )
            else:
                rail = rail.upper()
                rail_obj = rails[rail]
                if str(path.as_posix()) not in rail_obj.source_paths:
                    rails[rail] = PowerRail(
                        id=rail_obj.id,
                        project_id=project_id,
                        name=rail_obj.name,
                        voltage_domain=rail_obj.voltage_domain,
                        source_paths=sorted({*rail_obj.source_paths, str(path.as_posix())}),
                        consumers=rail_obj.consumers,
                        confidence=rail_obj.confidence,
                        provenance=rail_obj.provenance,
                        metadata=rail_obj.metadata,
                    )
    return sorted(rails.values(), key=lambda item: item.name)


def _board_files_by_revision(board: BoardRevision, hardware_paths: list[Path]) -> tuple[str | None, str | None, str | None]:
    schematic = board.schematic_path
    pcb = board.pcb_path
    bom = None
    if board.name:
        name = board.name.lower().replace(" ", "")
        for path in hardware_paths:
            lowered = path.as_posix().lower()
            if name in lowered and "bom" in lowered and path.suffix.lower() in {".csv", ".json"}:
                bom = str(path.as_posix())
                break
            if "bom" in lowered and path.suffix.lower() in {".csv", ".json"}:
                bom = str(path.as_posix())
    return schematic, pcb, bom


def build_hardware_intelligence(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    row = conn.execute("SELECT project_id, name, repo_path FROM projects WHERE project_id=?", (project_id,)).fetchone()
    if row is None:
        conn.close()
        raise ValueError(f"Unknown project: {project_id}")
    scan = conn.execute("SELECT scan_id, git_commit, git_branch, created_at FROM scans WHERE project_id=? ORDER BY created_at DESC, scan_id DESC LIMIT 1", (project_id,)).fetchone()
    conn.close()

    repo_root = Path(row["repo_path"]).resolve()
    hardware_paths = _hardware_paths(repo_root)
    source_commit = scan["git_commit"] if scan else None
    source_branch = scan["git_branch"] if scan else None
    observed_at = scan["created_at"] if scan else _utcnow()

    boards = _extract_board_revisions(repo_root, project_id, source_commit, scan["scan_id"] if scan else None, hardware_paths)
    components: list[ComponentModel] = []
    component_instances: list[ComponentInstance] = []
    pins: list[PinMapping] = []
    datasheets: list[DatasheetReference] = []
    validations: list[HardwareValidationEvidence] = []
    connectors: list[Connector] = []
    bom_sources: list[str] = []

    board_id = boards[0].id if boards else _stable_id(project_id, repo_root.name)
    for path in hardware_paths:
        full_path = repo_root / path
        lower = path.as_posix().lower()
        text = _read_text(full_path)
        if path.suffix.lower() == ".csv" and "bom" in lower:
            new_components, new_instances, bom_source = _parse_bom_csv(full_path, project_id, board_id)
            components.extend(new_components)
            component_instances.extend(new_instances)
            if bom_source:
                bom_sources.append(bom_source)
        elif path.suffix.lower() == ".json" and "bom" in lower:
            new_components, new_instances, bom_source = _parse_bom_json(full_path, project_id, board_id)
            components.extend(new_components)
            component_instances.extend(new_instances)
            if bom_source:
                bom_sources.append(bom_source)

        if any(token in lower for token in ("pin", "gpio", "mapping", "wiring")) or GPIO_RE.search(text):
            pins.extend(_parse_pin_map(full_path, project_id, board_id))

        if any(token in lower for token in ("datasheet", "bom", "component", "hardware")):
            datasheets.extend(_parse_datasheets(full_path, project_id))

        if any(token in lower for token in ("validation", "bring-up", "bringup", "bench", "hardware-test")):
            validations.extend(_parse_validation(full_path, project_id, board_id))

        if CONNECTOR_RE.search(text) and ("connector" in lower or "schematic" in lower or "pcb" in lower):
            refs = CONNECTOR_RE.findall(text)
            for ref in refs:
                connectors.append(
                    Connector(
                        id=_stable_id(project_id, board_id, ref, str(path.as_posix())),
                        project_id=project_id,
                        board_id=board_id,
                        reference=ref.upper(),
                        connector_type="unknown",
                        pins=[],
                        source=str(path.as_posix()),
                        confidence=0.55,
                        provenance="deterministic-connector-parser",
                        metadata={"source_path": str(path.as_posix())},
                    )
                )

    if not component_instances and components:
        for component in components:
            ref = component.manufacturer_part_number or component.description or component.id
            component_instances.append(
                ComponentInstance(
                    id=_stable_id(project_id, board_id, ref),
                    project_id=project_id,
                    board_id=board_id,
                    reference_designator=ref,
                    component_model_id=component.id,
                    footprint=component.package,
                    value=component.value,
                    location=None,
                    pins=[],
                    net_relationships=[],
                    confidence=component.confidence,
                    provenance=component.provenance,
                    metadata={"synthetic_instance": True},
                )
            )

    if not pins:
        for path in hardware_paths:
            text = _read_text(repo_root / path)
            for net in NET_RE.findall(text):
                pins.append(
                    PinMapping(
                        id=_stable_id(project_id, board_id, net, str(path.as_posix())),
                        project_id=project_id,
                        board_id=board_id,
                        hardware_pin=net.upper(),
                        signal=net.upper(),
                        firmware_symbol=None,
                        source_paths=[str(path.as_posix())],
                        confidence=0.52,
                        validation_status="unknown",
                        provenance="deterministic-net-parser",
                        metadata={"source_path": str(path.as_posix())},
                    )
                )

    power_rails = _build_power_rails(project_id, hardware_paths)
    risks, gaps, traceability = _hardware_risks_and_gaps(
        project_id=project_id,
        boards=boards,
        components=components,
        component_instances=component_instances,
        pins=pins,
        datasheets=datasheets,
        validations=validations,
        hardware_paths=hardware_paths,
    )

    schematic_hash = None
    pcb_hash = None
    bom_hash = None
    pin_map_hash = None
    component_inventory_hash = None
    if hardware_paths:
        relevant = [path.as_posix() for path in hardware_paths]
        digest = hashlib.sha256(_json_dumps(relevant).encode("utf-8")).hexdigest()
        schematic_hash = digest[:16] if any(path.suffix.lower() == ".kicad_sch" for path in hardware_paths) else None
        pcb_hash = digest[16:32] if any(path.suffix.lower() == ".kicad_pcb" for path in hardware_paths) else None
        bom_hash = digest[32:48] if bom_sources else None
        pin_map_hash = digest[48:64] if pins else None
        component_inventory_hash = hashlib.sha256(_json_dumps([component.to_dict() for component in components]).encode("utf-8")).hexdigest()

    if validations:
        validation_state = "validated" if any(item.result == "pass" for item in validations) else "partial"
    elif boards or components:
        validation_state = "not_run"
    else:
        validation_state = "unknown"

    snapshot = HardwareSnapshot(
        id=_stable_id(project_id, source_commit or "unknown", observed_at, "hardware-snapshot"),
        project_id=project_id,
        observed_at=observed_at,
        source_commit=source_commit,
        source_branch=source_branch,
        repo_path=str(repo_root),
        schematic_hash=schematic_hash,
        pcb_hash=pcb_hash,
        bom_hash=bom_hash,
        pin_map_hash=pin_map_hash,
        component_inventory_hash=component_inventory_hash,
        validation_state=validation_state,
        boards=boards,
        components=components,
        component_instances=component_instances,
        connectors=connectors,
        pins=pins,
        power_rails=power_rails,
        datasheets=datasheets,
        validations=validations,
        risks=risks,
        gaps=gaps,
        traceability=traceability,
        summary={
            "project_id": project_id,
            "project_name": row["name"],
            "repo_path": str(repo_root),
            "hardware_source_count": len(hardware_paths),
            "board_count": len(boards),
            "component_count": len(components),
            "component_instance_count": len(component_instances),
            "connector_count": len(connectors),
            "pin_mapping_count": len(pins),
            "power_rail_count": len(power_rails),
            "datasheet_reference_count": len(datasheets),
            "validation_count": len(validations),
            "risk_count": len(risks),
            "gap_count": len(gaps),
            "validation_state": validation_state,
        },
        metadata={
            "hardware_paths": [str(path.as_posix()) for path in hardware_paths],
            "bom_sources": bom_sources,
        },
    )
    return snapshot.to_dict()


def hardware_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    return snapshot.get("summary", {})


def hardware_boards(snapshot: dict[str, Any]) -> dict[str, Any]:
    boards = snapshot.get("boards", [])
    return {"count": len(boards), "items": boards}


def hardware_components(snapshot: dict[str, Any]) -> dict[str, Any]:
    components = snapshot.get("components", [])
    return {"count": len(components), "items": components}


def hardware_bom(snapshot: dict[str, Any]) -> dict[str, Any]:
    instances = snapshot.get("component_instances", [])
    return {"count": len(instances), "items": instances}


def hardware_pins(snapshot: dict[str, Any]) -> dict[str, Any]:
    pins = snapshot.get("pins", [])
    return {"count": len(pins), "items": pins}


def hardware_validation(snapshot: dict[str, Any]) -> dict[str, Any]:
    validations = snapshot.get("validations", [])
    return {"count": len(validations), "items": validations, "validation_state": snapshot.get("validation_state", "unknown")}


def hardware_gaps(snapshot: dict[str, Any]) -> dict[str, Any]:
    gaps = snapshot.get("gaps", [])
    return {"count": len(gaps), "items": gaps}


def hardware_risks(snapshot: dict[str, Any]) -> dict[str, Any]:
    risks = snapshot.get("risks", [])
    return {"count": len(risks), "items": risks}


def hardware_trace(snapshot: dict[str, Any], entity_id: str) -> dict[str, Any]:
    boards = snapshot.get("boards", [])
    components = snapshot.get("components", [])
    component_instances = snapshot.get("component_instances", [])
    pins = snapshot.get("pins", [])
    validations = snapshot.get("validations", [])
    hits: list[dict[str, Any]] = []
    for collection_name, collection in (
        ("board", boards),
        ("component", components),
        ("component_instance", component_instances),
        ("pin", pins),
        ("validation", validations),
    ):
        for item in collection:
            if entity_id in json.dumps(item, sort_keys=True):
                hits.append({"collection": collection_name, "item": item})
    return {"entity_id": entity_id, "count": len(hits), "items": hits}


def hardware_impact(snapshot: dict[str, Any], entity_id: str) -> dict[str, Any]:
    trace = hardware_trace(snapshot, entity_id)
    return {
        "entity_id": entity_id,
        "count": trace["count"],
        "items": trace["items"],
        "summary": snapshot.get("summary", {}),
    }
