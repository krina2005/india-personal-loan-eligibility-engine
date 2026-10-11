"""Synthetic tests of per-rule fallbacks, not approval accuracy."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("per_rule_test_engine", Path(__file__).resolve().parents[1] / "engine" / "engine.py")
eng = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eng)
PROFILE = dict(age=30, employment_type="salaried", net_monthly_income=60000, cibil_score=780,
               existing_monthly_emi=5000, salary_account_bank="HDFC Bank", requested_amount=300000,
               preferred_tenure_months=36, current_job_months=24, total_experience_months=48)


def record(key, value, status="VERIFIED_OFFICIAL", category="ALL"):
    return dict(rule_id=f"R_{key}_{value}_{category}", lender_id="TEST", rule_key=key,
                applicant_category=category, value="" if value is None else str(value), status=status,
                source_ids="TEST_SOURCE" if status == "VERIFIED_OFFICIAL" else "",
                unit={"min_income": "INR/month net", "min_cibil": "score", "min_age": "years"}.get(key, ""))


def evaluate(records=(), changes=None, mode="DEMO", scope_fallback=True, conflict_fallback=True):
    config = copy.deepcopy(eng.DEFAULT_CONFIG)
    config.update(mode=mode, enabled=mode == "DEMO", fallback_on_unresolved_scope=scope_fallback,
                  fallback_on_conflict=conflict_fallback)
    lender = dict(lender_id="TEST", brand_name="Synthetic lender", personal_loan_product="Personal Loan", _engine_config=config)
    rules = {}
    for row in records:
        rules.setdefault(row["rule_key"], []).append(row)
    return eng.evaluate({**PROFILE, **(changes or {})}, lender, {"TEST": rules})


class PerRuleFallbackTests(unittest.TestCase):
    def test_exact_three_rule_workflow(self):
        rows = [record("min_age", 21), record("min_income", None, "UNKNOWN"), record("min_cibil", 750)]
        result = evaluate(rows, {"net_monthly_income": 10000})
        self.assertEqual(result["rule_provenance"]["min_age"]["status"], "VERIFIED_OFFICIAL")
        self.assertEqual(result["rule_provenance"]["min_cibil"]["status"], "VERIFIED_OFFICIAL")
        self.assertEqual(result["rule_provenance"]["min_income"]["status"], "ESTIMATED")
        self.assertEqual(result["status"], "NOT_ELIGIBLE")
        self.assertEqual(result["decision_basis"], "MODEL_SCENARIO_FAILURE")

    def test_axis_selector_fallback(self):
        rows = [record("min_income", 15000, category="existing_Axis_customer"), record("min_income", 25000, category="non_Axis_customer")]
        result = evaluate(rows, {"net_monthly_income": 10000})
        self.assertEqual(result["rule_provenance"]["min_income"]["selection_status"], "UNRESOLVED_SCOPE")
        self.assertEqual(result["status"], "NOT_ELIGIBLE")
        self.assertFalse(result["insufficient_information_reasons"])

    def test_known_scalar_wins(self):
        result = evaluate([record("min_income", 20000)])
        self.assertEqual(result["rule_provenance"]["min_income"]["value"], 20000)
        self.assertEqual(result["rule_provenance"]["min_income"]["status"], "VERIFIED_OFFICIAL")

    def test_known_credit_cutoff_not_weakened(self):
        result = evaluate([record("min_cibil", 750)], {"cibil_score": 720})
        self.assertEqual(result["decision_basis"], "PUBLISHED_RULE_FAILURE")
        self.assertFalse(any(a["rule_key"] == "min_cibil" for a in result["assumptions_used"]))

    def test_default_failure_is_model_failure(self):
        result = evaluate(changes={"cibil_score": 650})
        self.assertEqual(result["status"], "NOT_ELIGIBLE")
        self.assertFalse(result["verified_rejection_reasons"])
        self.assertFalse(result["bank_rejection_claimed"])
        self.assertTrue(all(r["is_model_assumption"] for r in result["scenario_failed_rules"]))

    def test_missing_actual_score_stays_missing(self):
        result = evaluate(changes={"cibil_score": None})
        self.assertEqual(result["status"], "INSUFFICIENT_INFORMATION")
        self.assertIn("cibil_score", result["missing_applicant_inputs"])

    def test_strict_does_not_use_defaults(self):
        result = evaluate(mode="STRICT")
        self.assertEqual(result["status"], "INSUFFICIENT_INFORMATION")
        self.assertFalse(result["uses_estimates"])

    def test_conflict_switch(self):
        rows = [record("min_cibil", None, "CONFLICTING")]
        self.assertEqual(evaluate(rows)["rule_provenance"]["min_cibil"]["status"], "ESTIMATED")
        self.assertEqual(evaluate(rows, conflict_fallback=False)["status"], "INSUFFICIENT_INFORMATION")

    def test_known_employment_scope_not_widened(self):
        rows = [record("employment_scope", "salaried", category="salaried_personal_loan")]
        result = evaluate(rows, {"employment_type": "self_employed"})
        self.assertEqual(result["rule_provenance"]["employment_scope"]["status"], "VERIFIED_OFFICIAL")
        self.assertEqual(result["status"], "NOT_ELIGIBLE")


if __name__ == "__main__":
    unittest.main()
