"""API tests. Require fastapi/httpx (pip install -r backend/requirements.txt); skipped otherwise."""
import sys
from pathlib import Path
import pytest
pytest.importorskip("fastapi"); pytest.importorskip("httpx")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app.main import app
c = TestClient(app, raise_server_exceptions=False)
OK = dict(age=32, employment_type="salaried", net_monthly_income=150000, existing_monthly_emi=0, requested_amount=500000, preferred_tenure_months=48, cibil_score=780, salary_account_bank="HDFC Bank")

def test_health(): assert c.get("/api/health").json()["data_loaded"] is True
def test_lenders(): j = c.get("/api/lenders").json(); assert len(j["lenders"]) == 20 and j["coverage"]["lenders_official_evidence"] == 3
def test_metadata(): assert any(f["name"] == "age" for f in c.get("/api/metadata").json()["fields"])
def test_detail_404(): assert c.get("/api/lenders/NOPE").status_code == 404
def test_eligibility_ok():
    j = c.post("/api/eligibility", json=OK).json(); assert len(j["lenders"]) == 20 and j["overall"]["counts"]["potentially_eligible"] >= 1
def test_missing_required(): r = c.post("/api/eligibility", json={"age": 30}); assert r.status_code == 422 and r.json()["error"] == "invalid_input"
def test_bad_values():
    for k, v in [("age", 5), ("cibil_score", 100), ("net_monthly_income", -1), ("preferred_tenure_months", 1), ("employment_type", "x")]:
        assert c.post("/api/eligibility", json={**OK, k: v}).status_code == 422
def test_extra_field_rejected(): assert c.post("/api/eligibility", json={**OK, "password": "x"}).status_code == 422
def test_data_unavailable(monkeypatch, tmp_path):
    from app.services import data_service as d
    monkeypatch.setenv("PL_DATA_DIR", str(tmp_path)); d.clear_cache()
    try: assert c.post("/api/eligibility", json=OK).status_code == 503; assert c.get("/api/health").json()["status"] == "degraded"
    finally: monkeypatch.undo(); d.clear_cache()
