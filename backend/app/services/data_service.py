"""Load and validate repository data, including UTF-8 files with a BOM."""
import csv
import importlib.util
import json
from functools import lru_cache
from pathlib import Path

from ..core.config import ENGINE_PATH, data_dir


class DataUnavailable(Exception):
    """Required repository data or engine module is unavailable/invalid."""


FILES = [
    "lenders.csv", "lender_rules_detailed.csv", "lender_rule_summary.csv",
    "sources.csv", "input_variables.csv", "model_assumptions.json",
]
REQUIRED_COLUMNS = {
    "lenders": {"lender_id", "brand_name", "legal_name", "category",
                "personal_loan_product", "product_url", "offers_pl_evidence_status",
                "rules_research_depth"},
    "lender_rules_detailed": {"rule_id", "lender_id", "rule_key", "applicant_category",
                              "value", "status", "source_ids"},
    "lender_rule_summary": {"lender_id"},
    "sources": {"source_id", "date_accessed", "evidence_quality"},
    "input_variables": {"name", "label", "type", "unit", "description",
                        "required", "provided_by", "used_by"},
}


def missing_files(d: Path) -> list[str]:
    return [name for name in FILES if not (Path(d) / name).is_file()]


@lru_cache(maxsize=1)
def _engine():
    path = Path(ENGINE_PATH)
    if not path.is_file():
        raise DataUnavailable(f"Engine module not found: {path}")
    try:
        spec = importlib.util.spec_from_file_location("pl_rule_engine", path)
        if spec is None or spec.loader is None:
            raise ImportError("Cannot create engine module loader")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as exc:
        raise DataUnavailable(f"Cannot load engine {path}: {exc}") from exc


def engine():
    return _engine()


def _read_csv(path, required=()):
    path = Path(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path.name}: CSV header is missing")
        headers = [h.strip().lstrip("\ufeff").strip() for h in reader.fieldnames]
        if any(not h for h in headers) or len(headers) != len(set(headers)):
            raise ValueError(f"{path.name}: empty or duplicate CSV headers")
        missing = set(required) - set(headers)
        if missing:
            raise ValueError(f"{path.name}: missing columns {sorted(missing)}; headers={headers}")
        reader.fieldnames = headers
        rows = []
        for row in reader:
            if None in row:
                raise ValueError(f"{path.name}: extra CSV fields near line {reader.line_num}")
            if any(value is None for value in row.values()):
                raise ValueError(f"{path.name}: missing CSV cells near line {reader.line_num}")
            if not any(value.strip() for value in row.values()):
                continue
            for key in ("lender_id", "rule_id", "rule_key", "source_id", "status", "name"):
                if key in row:
                    row[key] = row[key].strip()
            rows.append(row)
    return rows


def _csv(path: Path):
    return _read_csv(path, REQUIRED_COLUMNS.get(Path(path).stem, ()))


def _validate_identifiers(rows, key, table):
    seen = set()
    for row in rows:
        value = row[key]
        if not value:
            raise ValueError(f"{table}: blank {key}")
        if value in seen:
            raise ValueError(f"{table}: duplicate {key} {value!r}")
        seen.add(value)
    return seen


def load_dataset(d: Path | None = None) -> dict:
    directory = Path(d) if d is not None else Path(data_dir())
    missing = missing_files(directory)
    if missing:
        raise DataUnavailable(f"Missing data files in {directory}: {', '.join(missing)}")
    try:
        ds = {Path(name).stem: _csv(directory / name)
              for name in FILES if name.endswith(".csv")}
        with (directory / "model_assumptions.json").open(encoding="utf-8-sig") as handle:
            ds["model_assumptions"] = json.load(handle)
        if not isinstance(ds["model_assumptions"], dict):
            raise ValueError("model_assumptions.json must contain an object")
        if not ds["lenders"]:
            raise ValueError("lenders.csv contains no lenders")
        ids = _validate_identifiers(ds["lenders"], "lender_id", "lenders")
        _validate_identifiers(ds["lender_rules_detailed"], "rule_id", "lender_rules_detailed")
        _validate_identifiers(ds["lender_rule_summary"], "lender_id", "lender_rule_summary")
        _validate_identifiers(ds["sources"], "source_id", "sources")
        _validate_identifiers(ds["input_variables"], "name", "input_variables")
        for name in ("lender_rules_detailed", "lender_rule_summary"):
            for row in ds[name]:
                if row["lender_id"] not in ids:
                    raise ValueError(f"{name}: unknown lender_id {row['lender_id']!r}")
        ds["dir"] = str(directory)
        return ds
    except Exception as exc:
        raise DataUnavailable(f"Data files malformed in {directory}: {exc}") from exc


@lru_cache(maxsize=1)
def _cached(directory: str):
    return load_dataset(Path(directory))


def dataset() -> dict:
    return _cached(str(data_dir()))


def clear_cache():
    _cached.cache_clear()
    _engine.cache_clear()