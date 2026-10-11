"""BOM-safe data/configuration loading for per-rule demo fallbacks."""
import csv
import json
import importlib.util
from pathlib import Path
from functools import lru_cache
from ..core.config import ENGINE_PATH, data_dir

class DataUnavailable(Exception):
    pass

FILES = ["lenders.csv", "lender_rules_detailed.csv", "lender_rule_summary.csv", "sources.csv", "input_variables.csv", "model_assumptions.json"]
REQUIRED = {
    "lenders": {"lender_id", "brand_name", "legal_name", "category", "personal_loan_product", "product_url", "offers_pl_evidence_status", "rules_research_depth"},
    "lender_rules_detailed": {"rule_id", "lender_id", "rule_key", "applicant_category", "value", "status", "source_ids"},
    "lender_rule_summary": {"lender_id"},
    "sources": {"source_id", "date_accessed", "evidence_quality"},
    "input_variables": {"name", "label", "type", "unit", "description", "required", "provided_by", "used_by"},
}

def missing_files(directory):
    return [name for name in FILES if not (Path(directory) / name).is_file()]

@lru_cache(maxsize=1)
def _engine():
    path = Path(ENGINE_PATH)
    if not path.is_file():
        raise DataUnavailable(f"Engine not found: {path}")
    try:
        spec = importlib.util.spec_from_file_location("pl_rule_engine", path)
        if spec is None or spec.loader is None:
            raise ImportError("No engine module loader")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as exc:
        raise DataUnavailable(f"Engine loading failed: {exc}") from exc

def engine():
    return _engine()

def _read_csv(path, required=()):
    path = Path(path)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{path.name}: missing CSV header")
        header = [x.strip().lstrip("\ufeff").strip() for x in reader.fieldnames]
        if any(not x for x in header) or len(header) != len(set(header)):
            raise ValueError(f"{path.name}: duplicate/empty CSV header")
        missing = set(required) - set(header)
        if missing:
            raise ValueError(f"{path.name}: missing columns {sorted(missing)}")
        reader.fieldnames = header
        rows = []
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f"{path.name}: malformed CSV near line {reader.line_num}")
            if not any(v.strip() for v in row.values()):
                continue
            for key in ("lender_id", "rule_id", "rule_key", "status", "source_id", "name"):
                if key in row:
                    row[key] = row[key].strip()
            rows.append(row)
        return rows



def _csv(path):
    return _read_csv(path, REQUIRED.get(Path(path).stem, ()))

def load_dataset(d=None):
    directory = Path(d) if d is not None else Path(data_dir())
    missing = missing_files(directory)
    if missing:
        raise DataUnavailable(f"Missing files in {directory}: {', '.join(missing)}")
    try:
        ds = {Path(name).stem: _csv(directory / name) for name in FILES if name.endswith(".csv")}
        with (directory / "model_assumptions.json").open(encoding="utf-8-sig") as handle:
            ds["model_assumptions"] = json.load(handle)
        if not isinstance(ds["model_assumptions"], dict):
            raise ValueError("model_assumptions.json must contain an object")
        for table, key in (("lenders", "lender_id"), ("lender_rule_summary", "lender_id"), ("lender_rules_detailed", "rule_id"), ("sources", "source_id"), ("input_variables", "name")):
            ids = [r[key] for r in ds[table]]
            if any(not i for i in ids) or len(ids) != len(set(ids)):
                raise ValueError(f"{table}: blank or duplicate {key}")
        lender_ids = {r["lender_id"] for r in ds["lenders"]}
        if not lender_ids:
            raise ValueError("No lender records")
        for table in ("lender_rules_detailed", "lender_rule_summary"):
            if any(r["lender_id"] not in lender_ids for r in ds[table]):
                raise ValueError(f"{table}: unknown lender reference")
        ds["dir"] = str(directory)
        ds["engine_config"] = engine().policy(directory)
        return ds
    except Exception as exc:
        raise DataUnavailable(f"Malformed data/configuration in {directory}: {exc}") from exc

@lru_cache(maxsize=1)
def _cached(directory):
    return load_dataset(Path(directory))

def dataset():
    return _cached(str(data_dir()))

def clear_cache():
    _cached.cache_clear()
    _engine.cache_clear()
