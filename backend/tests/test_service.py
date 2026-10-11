"""Engine/service tests (pytest style, but plain asserts so they also run without pytest)."""
import csv, json, math, os, shutil, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.services import data_service as ds, eligibility_service as svc

BASE = dict(age=32, employment_type="salaried", net_monthly_income=80000, existing_monthly_emi=5000, requested_amount=500000, preferred_tenure_months=48,
            cibil_score=760, salary_account_bank="OTHER", city=None, employer_category=None, current_job_months=None, total_experience_months=None, business_vintage_months=None)
def run(**k): return {x["lender_id"]: x for x in svc.assess({**BASE, **k})["lenders"]}

def test_dataset_loads_from_other_cwd():
    old = os.getcwd(); os.chdir(tempfile.gettempdir())
    try: assert len(ds.dataset()["lenders"]) == 20
    finally: os.chdir(old)
def test_missing_data_raises():
    try: ds.load_dataset(Path(tempfile.mkdtemp())); assert False
    except ds.DataUnavailable: pass
def test_malformed_json_raises():
    d = Path(tempfile.mkdtemp()); shutil.copytree(ROOT / "data", d, dirs_exist_ok=True); (d / "model_assumptions.json").write_text("{bad")
    try: ds.load_dataset(d); assert False
    except ds.DataUnavailable: pass
def test_all_existing_profiles_match_stored_results():
    stored = json.load(open(ROOT / "tests/results.json"))
    for p in stored:
        got = {x["lender_id"]: x["status"] for x in svc.assess({**BASE, **{k: v for k, v in p["inputs"].items()}})["lenders"]}
        assert got == {l["lender_id"]: l["status"] for l in p["lenders"]}, p["profile_id"]
def test_potentially_eligible_has_evidence_and_passed_rules():
    r = run(salary_account_bank="HDFC Bank", net_monthly_income=150000)["L02"]
    assert r["status"] == "POTENTIALLY_ELIGIBLE" and r["passed_rules"] and r["estimate"]["indicative"] and r["source_ids"]
def test_verified_failure_is_not_eligible_with_rule_ids():
    r = run(cibil_score=610, salary_account_bank="HDFC Bank")["L02"]
    assert r["status"] == "NOT_ELIGIBLE" and r["rejection_reasons"][0]["rule_ids"]
def test_unknown_rules_never_pass():
    for lid, r in run().items():
        if lid not in ("L01", "L02"): assert r["status"] == "INSUFFICIENT_INFORMATION" and r["rule_gaps"] and r["estimate"] is None
def test_conflicting_rule_stays_visible():
    r = run()["L13"]; assert r["status"] == "INSUFFICIENT_INFORMATION" and any(g["status"] == "CONFLICTING" for g in r["rule_gaps"])
def test_missing_cibil_is_missing_input_not_failure():
    r = run(cibil_score=None, salary_account_bank="HDFC Bank")["L02"]
    assert r["status"] == "INSUFFICIENT_INFORMATION" and "cibil_score" in r["missing_applicant_inputs"] and not r["rejection_reasons"]
def test_missing_salary_bank_not_rejected():
    r = run(salary_account_bank=None)["L01"]; assert r["status"] != "NOT_ELIGIBLE" and "salary_account_bank" in r["missing_applicant_inputs"]
def test_self_employed_not_given_salaried_verdict():
    assert run(employment_type="self_employed", business_vintage_months=60)["L02"]["status"] == "INSUFFICIENT_INFORMATION"
def test_no_recommendation_without_comparable_evidence():
    assert svc.assess({**BASE, "salary_account_bank": "HDFC Bank"})["overall"]["recommendation"]["lender_id"] is None
def test_boundaries():
    assert run(net_monthly_income=25000, cibil_score=650, salary_account_bank="HDFC Bank")["L02"]["status"] == "POTENTIALLY_ELIGIBLE"
    assert run(net_monthly_income=24999, salary_account_bank="HDFC Bank")["L02"]["status"] == "NOT_ELIGIBLE"
def test_age_at_maturity_reduces_tenure():
    r = run(age=57, salary_account_bank="SBI", net_monthly_income=100000, cibil_score=780)["L01"]
    assert r["status"] == "POTENTIALLY_ELIGIBLE" and r["estimate"]["tenure_used_months"] == 36
def test_amortization_math_and_zero_rate():
    e = svc.engine(); emi = e.emi(100000, 12, 12); assert abs(e.pv(emi, 12, 12) - 100000) < 1e-6
    assert e.emi(120000, 0, 12) == 10000 and e.pv(10000, 0, 12) == 120000
def test_amount_never_exceeds_published_cap():
    r = run(net_monthly_income=10_000_000, existing_monthly_emi=0, salary_account_bank="HDFC Bank", requested_amount=1_000_000)["L02"]
    assert r["estimate"]["max_amount_inr"] <= 4_000_000
def test_sources_resolve():
    d = ds.dataset(); ids = {s["source_id"] for s in d["sources"]}
    assert all(x in ids for r in d["lender_rules_detailed"] for x in r["source_ids"].split(";") if x)
def test_coverage_is_computed_from_data():
    c = svc.coverage(); assert c["lenders_total"] == 20 and c["lenders_official_evidence"] == 20 and c["rules_unknown"] > 200 and c["sources_total"] == len(ds.dataset()["sources"])
def test_metadata_fields_are_known_engine_variables():
    names = {f["name"] for f in svc.metadata()["fields"]}; assert {"age", "net_monthly_income", "cibil_score"} <= names
def test_lender_detail_and_unknown_id():
    assert svc.lender_detail("L02")["sources"] and svc.lender_detail("ZZ") is None

if __name__ == "__main__":
    fails = 0
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            try: f(); print("PASS", n)
            except Exception as e: fails += 1; print("FAIL", n, repr(e))
    sys.exit(1 if fails else 0)
