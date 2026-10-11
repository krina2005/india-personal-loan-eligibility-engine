import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]          # repository root, independent of CWD
ENGINE_PATH = ROOT / "engine" / "engine.py"
def data_dir() -> Path: return Path(os.environ.get("PL_DATA_DIR") or ROOT / "data")
def cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [o.strip() for o in raw.split(",") if o.strip() and o.strip() != "*"]
