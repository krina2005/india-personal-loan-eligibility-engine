"""Return explicit model decisions and per-rule official/default provenance."""
import collections
from .data_service import dataset, engine

DISCLAIMER = (
    "This is a preliminary model assessment, not a bank decision. DEMO mode substitutes "
    "explicit hypothetical defaults when CSV criteria cannot be resolved. A failed demo "
    "scenario does not establish bank rejection; a passed scenario does not establish approval. "
    "Actual eligibility, availability, pricing and sanction require lender review."
)

FORM = {'age': dict(section='personal', kind='number', min=18, max=100, step=1, hint='Your completed age today.'), 'city': dict(section='personal', kind='text', hint='City helps category selection where implemented.'), 'employment_type': dict(section='employment', kind='select', options=[['salaried', 'Salaried'], ['self_employed', 'Self-employed']], hint='Researched rules mostly cover salaried products.'), 'employer_category': dict(section='employment', kind='text', hint='Employer category helps select applicable published tiers.'), 'current_job_months': dict(section='employment', kind='number', min=0, max=600, step=1, hint='May be needed when an applicable verified job-tenure rule exists.'), 'total_experience_months': dict(section='employment', kind='number', min=0, max=720, step=1, hint='May be needed when an applicable verified experience rule exists.'), 'business_vintage_months': dict(section='employment', kind='number', min=0, max=720, step=1, hint='Self-employed only. Optional.'), 'net_monthly_income': dict(section='income', kind='number', min=0, max=10000000, step=500, hint='Take-home pay per month. Self-employed: documented monthly income, not turnover.'), 'cibil_score': dict(section='credit', kind='number', min=300, max=900, step=1, required=False, hint="Leave blank if unknown. Lenders needing it will then report 'more information needed' rather than a guess."), 'salary_account_bank': dict(section='credit', kind='select', options=[['HDFC Bank', 'HDFC Bank'], ['SBI', 'State Bank of India'], ['OTHER', 'Another bank']], hint='Bank where your salary is credited. Some lenders price or restrict by this.'), 'existing_monthly_emi': dict(section='obligations', kind='number', min=0, max=10000000, step=500, hint='Total EMIs you pay each month, including credit-card EMIs. Enter 0 if none.'), 'requested_amount': dict(section='loan', kind='number', min=1000, max=100000000, step=10000, hint='Amount you want to borrow.'), 'preferred_tenure_months': dict(section='loan', kind='number', min=3, max=120, step=1, hint='Repayment period in months (e.g. 48 = 4 years).')}

SECTIONS = [['personal', 'Personal'], ['employment', 'Employment'], ['income', 'Income'], ['credit', 'Credit profile'], ['obligations', 'Existing obligations'], ['loan', 'Loan requirements']]

def metadata():
    ds = dataset()
    necessary = {"age", "employment_type", "net_monthly_income", "existing_monthly_emi", "requested_amount", "preferred_tenure_months"}
    fields = []
    for row in ds["input_variables"]:
        cfg = FORM.get(row["name"])
        if not cfg:
            continue
        required = row["name"] in necessary or cfg.get("required", row["required"] == "Y")
        fields.append({**{k: row[k] for k in ("name", "label", "type", "unit", "description", "provided_by", "used_by")},
                       "required": required, **{k: v for k, v in cfg.items() if k != "required"}})
    return {"sections": [{"id": a, "label": b} for a, b in SECTIONS], "fields": fields,
            "assessment_mode": ds["engine_config"]["mode"], "disclaimer": DISCLAIMER}


def _cov_lenders():
    ds = dataset()
    grouped = collections.defaultdict(list)
    for row in ds["lender_rules_detailed"]:
        grouped[row["lender_id"]].append(row)
    output = []
    for lender in ds["lenders"]:
        rows = grouped[lender["lender_id"]]
        counts = collections.Counter(r["status"] for r in rows)
        official, secondary = counts["VERIFIED_OFFICIAL"], counts["VERIFIED_SECONDARY"]
        output.append({"lender_id": lender["lender_id"], "brand_name": lender["brand_name"], "legal_name": lender["legal_name"],
                       "category": lender["category"], "product": lender["personal_loan_product"], "product_url": lender["product_url"],
                       "offers_pl_evidence": lender["offers_pl_evidence_status"], "research_depth": lender["rules_research_depth"],
                       "evidence_level": "OFFICIAL" if official else ("SECONDARY_ONLY" if secondary else "NONE"),
                       "rules_total": len(rows), "rules_known": sum(1 for r in rows if r["status"] == "VERIFIED_OFFICIAL" and r["value"]),
                       "rules_unknown": counts["UNKNOWN"], "rules_conflicting": counts["CONFLICTING"],
                       "rules_official": official, "rules_secondary": secondary,
                       "availability_status": lender.get("availability_status", "LIVE_OFFER_NOT_VERIFIED")})
    return output


def lenders():
    return _cov_lenders()


def coverage():
    ds = dataset()
    listing = _cov_lenders()
    counts = collections.Counter(r["status"] for r in ds["lender_rules_detailed"])
    dates = sorted({r["date_accessed"] for r in ds["sources"] if r["date_accessed"]})
    return {"lenders_total": len(listing),
            "lenders_official_evidence": sum(r["evidence_level"] == "OFFICIAL" for r in listing),
            "lenders_secondary_only": sum(r["evidence_level"] == "SECONDARY_ONLY" for r in listing),
            "lenders_no_evidence": sum(r["evidence_level"] == "NONE" for r in listing),
            "lenders_with_conflicts": sum(r["rules_conflicting"] > 0 for r in listing),
            "lenders_with_unknown_rules": sum(r["rules_unknown"] > 0 for r in listing),
            "rules_total": sum(counts.values()), "rules_by_status": dict(counts), "rules_unknown": counts["UNKNOWN"],
            "sources_total": len(ds["sources"]), "sources_by_quality": dict(collections.Counter(s["evidence_quality"] for s in ds["sources"])),
            "source_dates": {"earliest": dates[0] if dates else None, "latest": dates[-1] if dates else None},
            "assessment_mode": ds["engine_config"]["mode"],
            "note": "Scenario defaults do not increase verified lender-rule coverage."}


def lender_detail(lender_id):
    ds = dataset()
    lender = next((r for r in _cov_lenders() if r["lender_id"] == lender_id), None)
    if lender is None:
        return None
    rows = [r for r in ds["lender_rules_detailed"] if r["lender_id"] == lender_id]
    ids = {s for r in rows for s in r["source_ids"].split(";") if s}
    sources = {r["source_id"]: r for r in ds["sources"]}
    return {"lender": lender, "rules": rows, "sources": [sources[i] for i in sorted(ids) if i in sources],
            "dangling_source_ids": sorted(ids - set(sources)),
            "summary_row": next((r for r in ds["lender_rule_summary"] if r["lender_id"] == lender_id), None),
            "known_rules": sum(1 for r in rows if r["status"] == "VERIFIED_OFFICIAL" and r["value"])}


def _explain(result, gaps=None):
    if result["decision_basis"] == "PRODUCT_UNAVAILABLE":
        return "The published product notice says new sourcing is unavailable. This is not a borrower rejection."
    if result["decision_basis"] == "APPLICANT_INFORMATION":
        return "Applicant information is missing/invalid: " + "; ".join(result["insufficient_information_reasons"])
    if result["status"] == "NOT_ELIGIBLE":
        if result["decision_basis"] == "MODEL_SCENARIO_FAILURE":
            return "Not eligible under the illustrative model defaults: " + "; ".join(r["reason"] for r in result["scenario_failed_rules"]) + ". This is not a bank rejection."
        return "Fails an applicable recorded published condition: " + "; ".join(r["reason"] for r in result["verified_rejection_reasons"]) + ". This is model screening, not a bank decision."
    if result["status"] == "POTENTIALLY_ELIGIBLE":
        return ("Passes the illustrative model scenario; some lender criteria were assumed, not verified. No approval is guaranteed."
                if result["uses_estimates"] else "Passes the evaluated published checks; final lender decision is unknown.")
    return "Assessment needs rule review: " + "; ".join(result["insufficient_information_reasons"])


def _recommend(output):
    rows = [r for r in output if r["status"] == "POTENTIALLY_ELIGIBLE" and not r["uses_estimates"] and not r["unevaluated_published_rules"]
            and r["estimate"] and r["estimate"]["rate_range_pct"] and r["availability_status"] != "SOURCING_UNAVAILABLE"]
    if len(rows) < 2:
        return {"lender_id": None, "why": "No reliable actual-lender ranking: fewer than two comparable non-scenario assessments. Hypothetical rules are excluded."}
    best = min(rows, key=lambda r: (r["estimate"]["rate_range_pct"][1], r["estimate"]["rate_range_pct"][0]))
    return {"lender_id": best["lender_id"], "why": "Lowest published upper nominal rate among comparable non-scenario results; actual pricing/approval unknown."}


def assess(profile):
    ds = dataset()
    eng = engine()
    rules, lender_rows = eng.load(ds["dir"])
    meta = {r["lender_id"]: r for r in _cov_lenders()}
    output = []
    for lender in lender_rows:
        result = eng.evaluate(profile, lender, rules)
        m = meta[lender["lender_id"]]
        estimate = None
        if result["status"] == "POTENTIALLY_ELIGIBLE" and any(result[k] is not None for k in ("max_amount_estimate_inr", "rate_range_pct", "tenure_months_range")):
            emis, tenure = result["est_emi_for_requested_inr"], result["tenure_used_months"]
            estimate = {"indicative": True, "uses_estimates": result["uses_estimates"], "max_amount_inr": result["max_amount_estimate_inr"],
                        "max_amount_basis": result["max_amount_basis"], "rate_range_pct": result["rate_range_pct"], "rate_status": result["rate_status"],
                        "tenure_months_range": result["tenure_months_range"], "tenure_used_months": tenure, "emi_for_requested_inr": emis,
                        "total_repayment_for_requested_inr": [round(e * tenure) for e in emis] if emis and tenure else None,
                        "limitations": ["Illustrative calculation, not a live offer or approved amount.", "Nominal-rate repayment excludes full APR/fees.", "See assumptions_used for every substituted rule."]}
        source_ids = sorted({s for records in rules[lender["lender_id"]].values() for r in records for s in r["source_ids"].split(";") if s})
        output.append({**{k: m[k] for k in ("lender_id", "brand_name", "legal_name", "category", "product", "product_url", "research_depth", "evidence_level")},
                       "status": result["status"], "explanation": _explain(result), "estimate": estimate, "source_ids": source_ids,
                       **{k: result[k] for k in ("passed_rules", "rejection_reasons", "verified_rejection_reasons", "scenario_passed_rules", "scenario_failed_rules",
                                                 "missing_applicant_inputs", "insufficient_information_reasons", "rule_gaps", "unknowns_not_evaluated", "notes",
                                                 "uses_estimates", "assumptions_used", "assessment_mode", "scenario_result", "decision_basis", "rule_provenance",
                                                 "availability_status", "requires_lender_review", "approval_guaranteed", "bank_rejection_claimed",
                                                 "assessment_evidence_level", "unevaluated_published_rules")}})
    counts = collections.Counter(r["status"] for r in output)
    pe, ne, ii = counts["POTENTIALLY_ELIGIBLE"], counts["NOT_ELIGIBLE"], counts["INSUFFICIENT_INFORMATION"]
    overall = "POTENTIALLY_ELIGIBLE" if pe else ("NOT_ELIGIBLE" if ne and not ii else "INSUFFICIENT_INFORMATION")
    headline = f"Model screening: {pe} pass, {ne} fail, {ii} need applicant information or rule review. Assumed rules are hypothetical, not bank decisions."
    return {"overall": {"status": overall, "headline": headline,
                         "counts": {"potentially_eligible": pe, "not_eligible": ne, "insufficient_information": ii},
                         "scenario_counts": {"pass": sum(r["scenario_result"] == "PASS" for r in output),
                                             "fail": sum(r["scenario_result"] == "FAIL" for r in output),
                                             "incomplete": sum(r["scenario_result"] == "INCOMPLETE" for r in output)},
                         "recommendation": _recommend(output), "disclaimer": DISCLAIMER,
                         "assumptions": ds["model_assumptions"].get("global_affordability_assumption", {}), "fallback_policy": ds["engine_config"],
                         "assessment_mode": ds["engine_config"]["mode"], "uses_estimates": any(r["uses_estimates"] for r in output),
                         "researched_lenders": sum(r["research_depth"] != "NONE" for r in output)}, "lenders": output}
