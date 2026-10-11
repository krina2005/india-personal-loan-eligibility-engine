"""Orchestration around the existing deterministic engine (engine/engine.py). No eligibility logic is duplicated here."""
import collections
from .data_service import dataset, engine

DISCLAIMER = ("Indicative estimate based on publicly documented lender rules. It is not a lender decision and does not guarantee approval; "
              "actual approval, amount and rate are decided by the lender.")
CORE_KEYS = ["min_age", "max_age_application", "max_age_at_maturity", "min_income", "min_cibil", "employment_scope"]
FORM = {  # section, kind, min, max, options, help, placeholder, required override
 "age": dict(section="personal", kind="number", min=18, max=100, step=1, hint="Your completed age today."),
 "city": dict(section="personal", kind="text", hint="Only used if a lender publishes city rules. No city rule has been verified yet."),
 "employment_type": dict(section="employment", kind="select", options=[["salaried", "Salaried"], ["self_employed", "Self-employed"]], hint="Researched rules mostly cover salaried products."),
 "employer_category": dict(section="employment", kind="text", hint="Optional. No verified lender rule uses this yet."),
 "current_job_months": dict(section="employment", kind="number", min=0, max=600, step=1, hint="Months with your current employer. Optional."),
 "total_experience_months": dict(section="employment", kind="number", min=0, max=720, step=1, hint="Total work experience in months. Optional."),
 "business_vintage_months": dict(section="employment", kind="number", min=0, max=720, step=1, hint="Self-employed only. Optional."),
 "net_monthly_income": dict(section="income", kind="number", min=0, max=10_000_000, step=500, hint="Take-home pay per month. Self-employed: documented monthly income, not turnover."),
 "cibil_score": dict(section="credit", kind="number", min=300, max=900, step=1, required=False, hint="Leave blank if unknown. Lenders needing it will then report 'more information needed' rather than a guess."),
 "salary_account_bank": dict(section="credit", kind="select", options=[["HDFC Bank", "HDFC Bank"], ["SBI", "State Bank of India"], ["OTHER", "Another bank"]], hint="Bank where your salary is credited. Some lenders price or restrict by this."),
 "existing_monthly_emi": dict(section="obligations", kind="number", min=0, max=10_000_000, step=500, hint="Total EMIs you pay each month, including credit-card EMIs. Enter 0 if none."),
 "requested_amount": dict(section="loan", kind="number", min=1000, max=100_000_000, step=10000, hint="Amount you want to borrow."),
 "preferred_tenure_months": dict(section="loan", kind="number", min=3, max=120, step=1, hint="Repayment period in months (e.g. 48 = 4 years)."),
}
SECTIONS = [["personal", "Personal"], ["employment", "Employment"], ["income", "Income"], ["credit", "Credit profile"], ["obligations", "Existing obligations"], ["loan", "Loan requirements"]]

def metadata():
    ds = dataset(); fields = []
    for v in ds["input_variables"]:
        cfg = FORM.get(v["name"])
        if not cfg: continue
        req = cfg.get("required", v["required"] == "Y")
        fields.append({"name": v["name"], "label": v["label"], "type": v["type"], "unit": v["unit"], "description": v["description"], "required": req,
                       "provided_by": v["provided_by"], "used_by": v["used_by"], **{k: x for k, x in cfg.items() if k != "required"}})
    return {"sections": [{"id": a, "label": b} for a, b in SECTIONS], "fields": fields}

def _cov_lenders():
    ds = dataset(); rules = collections.defaultdict(list)
    for r in ds["lender_rules_detailed"]: rules[r["lender_id"]].append(r)
    out = []
    for l in ds["lenders"]:
        rs = rules[l["lender_id"]]; st = collections.Counter(r["status"] for r in rs)
        official, secondary = st["VERIFIED_OFFICIAL"], st["VERIFIED_SECONDARY"]
        evidence = "OFFICIAL" if official else ("SECONDARY_ONLY" if secondary else "NONE")
        out.append({"lender_id": l["lender_id"], "brand_name": l["brand_name"], "legal_name": l["legal_name"], "category": l["category"],
                    "product": l["personal_loan_product"], "product_url": l["product_url"], "offers_pl_evidence": l["offers_pl_evidence_status"],
                    "research_depth": l["rules_research_depth"], "evidence_level": evidence, "rules_total": len(rs), "rules_known": len(rs) - st["UNKNOWN"],
                    "rules_unknown": st["UNKNOWN"], "rules_conflicting": st["CONFLICTING"], "rules_official": official, "rules_secondary": secondary})
    return out
def lenders(): return _cov_lenders()

def coverage():
    ds = dataset(); L = _cov_lenders(); st = collections.Counter(r["status"] for r in ds["lender_rules_detailed"])
    dates = sorted({s["date_accessed"] for s in ds["sources"] if s["date_accessed"]})
    return {"lenders_total": len(L), "lenders_official_evidence": sum(l["evidence_level"] == "OFFICIAL" for l in L),
            "lenders_secondary_only": sum(l["evidence_level"] == "SECONDARY_ONLY" for l in L), "lenders_no_evidence": sum(l["evidence_level"] == "NONE" for l in L),
            "lenders_with_conflicts": sum(l["rules_conflicting"] > 0 for l in L), "lenders_with_unknown_rules": sum(l["rules_unknown"] > 0 for l in L),
            "rules_total": sum(st.values()), "rules_by_status": dict(st), "rules_unknown": st["UNKNOWN"], "sources_total": len(ds["sources"]),
            "sources_by_quality": dict(collections.Counter(s["evidence_quality"] for s in ds["sources"])),
            "source_dates": {"earliest": dates[0] if dates else None, "latest": dates[-1] if dates else None},
            "note": "A lender record does not mean its rules were researched; see per-lender evidence_level."}

def lender_detail(lender_id):
    ds = dataset(); L = {l["lender_id"]: l for l in lenders()}
    if lender_id not in L: return None
    rules = [r for r in ds["lender_rules_detailed"] if r["lender_id"] == lender_id]
    sids = {x for r in rules for x in r["source_ids"].split(";") if x}
    src = {s["source_id"]: s for s in ds["sources"]}
    known = [r for r in rules if r["status"] != "UNKNOWN"]
    return {"lender": L[lender_id], "rules": rules, "sources": [src[i] for i in sorted(sids) if i in src], "dangling_source_ids": sorted(sids - set(src)),
            "summary_row": next((r for r in ds["lender_rule_summary"] if r["lender_id"] == lender_id), None), "known_rules": len(known)}

def _explain(r, gaps):
    n = r["status"]
    if n == "NOT_ELIGIBLE": return "A mandatory rule with supporting evidence failed: " + "; ".join(x["reason"] for x in r["rejection_reasons"]) + "."
    if n == "POTENTIALLY_ELIGIBLE": return "All mandatory rules that are known for this lender passed. Rules not published or not found (listed below) were not evaluated, so this is preliminary."
    parts = []
    if r["missing_applicant_inputs"]: parts.append("you have not provided: " + ", ".join(r["missing_applicant_inputs"]))
    if gaps: parts.append("lender rules are unknown or conflicting: " + ", ".join(g["rule_key"] + " (" + g["status"] + ")" for g in gaps))
    other = [b for b in r["insufficient_information_reasons"] if "applicant input missing" not in b and "UNKNOWN" not in b and "CONFLICTING" not in b]
    parts += other
    return "A reliable assessment is not possible because " + "; ".join(parts) + "."

def assess(profile: dict):
    ds = dataset(); eng = engine(); rules, lenders_ = eng.load(ds["dir"]); cap = eng.assumed_cap(ds["dir"])
    meta = {l["lender_id"]: l for l in _cov_lenders()}; out = []
    for l in lenders_:
        r = eng.evaluate(profile, l, rules, cap); m = meta[l["lender_id"]]
        gaps = [{"rule_key": k, "status": ("CONFLICTING" if any(x["status"] == "CONFLICTING" for x in rules[l["lender_id"]][k]) else "UNKNOWN"),
                 "rule_ids": [x["rule_id"] for x in rules[l["lender_id"]][k]]}
                for k in CORE_KEYS if not eng.usable(rules[l["lender_id"]][k]) and not (k.startswith("max_age") and (eng.usable(rules[l["lender_id"]]["max_age_application"]) or eng.usable(rules[l["lender_id"]]["max_age_at_maturity"])))]
        est = None
        if r["status"] == "POTENTIALLY_ELIGIBLE" and (r["max_amount_estimate_inr"] or r["rate_range_pct"] or r["tenure_months_range"]):
            emi = r["est_emi_for_requested_inr"]; t = r["tenure_used_months"]
            est = {"indicative": True, "max_amount_inr": r["max_amount_estimate_inr"], "max_amount_basis": r["max_amount_basis"], "rate_range_pct": r["rate_range_pct"],
                   "tenure_months_range": r["tenure_months_range"], "tenure_used_months": t, "emi_for_requested_inr": emi,
                   "total_repayment_for_requested_inr": [round(e * t) for e in emi] if emi and t else None,
                   "limitations": ["Rate is a published range, not a personal quote.", "Maximum amount uses the highest published rate (conservative)."] +
                                  (["Affordability uses an ESTIMATED modelling assumption, not lender policy."] if "ESTIMATED" in (r["max_amount_basis"] or "") else [])}
        src = sorted({x for k in rules[l["lender_id"]].values() for row in k for x in row["source_ids"].split(";") if x})
        out.append({**{k: m[k] for k in ("lender_id", "brand_name", "legal_name", "category", "product", "product_url", "research_depth", "evidence_level")},
                    "status": r["status"], "explanation": _explain(r, gaps), "rejection_reasons": r["rejection_reasons"], "passed_rules": r["passed_rules"],
                    "missing_applicant_inputs": r["missing_applicant_inputs"], "rule_gaps": gaps, "insufficient_information_reasons": r["insufficient_information_reasons"],
                    "estimate": est, "notes": r["notes"], "unknowns_not_evaluated": r["unknowns_not_evaluated"], "source_ids": src})
    counts = collections.Counter(x["status"] for x in out); rec = _recommend(out)
    pe = counts["POTENTIALLY_ELIGIBLE"]; ne = counts["NOT_ELIGIBLE"]; ii = counts["INSUFFICIENT_INFORMATION"]
    overall = "POTENTIALLY_ELIGIBLE" if pe else ("NOT_ELIGIBLE" if ne and not ii else "INSUFFICIENT_INFORMATION")
    headline = {"POTENTIALLY_ELIGIBLE": f"{pe} lender(s) pass every rule we could verify.", "NOT_ELIGIBLE": "Every lender with a verified rule fails at least one mandatory condition.",
                "INSUFFICIENT_INFORMATION": f"We cannot give a reliable answer for most lenders: {ii} need more information or better-researched rules."}[overall]
    return {"overall": {"status": overall, "headline": headline, "counts": {"potentially_eligible": pe, "not_eligible": ne, "insufficient_information": ii},
                        "recommendation": rec, "disclaimer": DISCLAIMER, "assumptions": ds["model_assumptions"]["global_affordability_assumption"],
                        "researched_lenders": sum(x["research_depth"] != "NONE" for x in out)}, "lenders": out}

def _recommend(out):
    ok = [x for x in out if x["status"] == "POTENTIALLY_ELIGIBLE" and x["estimate"] and x["estimate"]["rate_range_pct"]]
    if len(ok) < 2: return {"lender_id": None, "why": f"No reliable ranking: only {len(ok)} potentially eligible lender(s) have a published rate range; at least 2 comparable lenders are needed."}
    b = min(ok, key=lambda x: (x["estimate"]["rate_range_pct"][1], x["estimate"]["rate_range_pct"][0]))
    return {"lender_id": b["lender_id"], "why": "Lowest published maximum rate among comparable lenders. Your personal rate and fees may differ."}
