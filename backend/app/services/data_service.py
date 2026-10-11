"""Loads repository CSV/JSON data. Raises DataUnavailable when files are missing/malformed."""
import csv, importlib.util, json
from functools import lru_cache
from pathlib import Path
from ..core.config import ENGINE_PATH, data_dir

class DataUnavailable(Exception): pass
FILES = ["lenders.csv", "lender_rules_detailed.csv", "lender_rule_summary.csv", "sources.csv", "input_variables.csv", "model_assumptions.json"]

def missing_files(d: Path) -> list[str]: return [f for f in FILES if not (d / f).is_file()]

@lru_cache(maxsize=1)
def _engine():
    if not ENGINE_PATH.is_file(): raise DataUnavailable("engine module not found")
    spec = importlib.util.spec_from_file_location("pl_rule_engine", ENGINE_PATH)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def engine(): return _engine()

def _csv(path: Path): 
    with open(path, encoding="utf-8", newline="") as f: return list(csv.DictReader(f))

def load_dataset(d: Path | None = None) -> dict:
    d = Path(d) if d else data_dir()
    miss = missing_files(d)
    if miss: raise DataUnavailable(f"missing data files: {', '.join(miss)}")
    try:
        ds = {n.split(".")[0]: _csv(d / n) for n in FILES if n.endswith(".csv")}
        ds["model_assumptions"] = json.loads((d / "model_assumptions.json").read_text(encoding="utf-8"))
        ds["dir"] = str(d)
    except Exception as e: raise DataUnavailable(f"data files malformed: {type(e).__name__}") from e
    return ds

@lru_cache(maxsize=1)
def _cached(d: str): return load_dataset(Path(d))
def dataset() -> dict: return _cached(str(data_dir()))
def clear_cache(): _cached.cache_clear()
