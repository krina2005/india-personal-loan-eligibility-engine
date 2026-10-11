"""Per-rule CSV -> labelled default resolution for demo screening.
Unknown lender policy is never converted into verified bank policy.
"""
import collections
import csv
import json
import math
import re
from pathlib import Path

B = str(Path(__file__).resolve().parent.parent)
HARD = {"VERIFIED_OFFICIAL"}
UNSET = object()
DEFAULT_CONFIG = {
    "mode": "STRICT", "enabled": False,
    "fallback_on_unresolved_scope": True,
    "fallback_on_conflict": False,
    "defaults": {
        "min_age": {"value": 21, "unit": "years", "basis": "Illustrative demo age minimum; not bank policy."},
        "max_age_application": {"value": 60, "unit": "years", "basis": "Illustrative demo application-age ceiling; not bank policy."},
        "min_income": {"value": 25000, "unit": "INR/month net", "basis": "Illustrative demo net-income floor; not bank policy."},
        "min_cibil": {"value": 700, "unit": "score", "basis": "Arbitrary demo credit cutoff; not calibrated or a lender cutoff."},
        "employment_scope": {"value": "salaried;self_employed", "unit": "", "basis": "Illustrative demo product scope; not actual lender coverage."},
        "amount_min": {"value": 50000, "unit": "INR", "basis": "Illustrative demo principal minimum."},
        "amount_max": {"value": 1000000, "unit": "INR", "basis": "Illustrative demo principal ceiling."},
        "tenure_min": {"value": 12, "unit": "months", "basis": "Illustrative demo repayment range."},
        "tenure_max": {"value": 60, "unit": "months", "basis": "Illustrative demo repayment range."},
        "rate_min": {"value": 12, "unit": "% p.a.", "basis": "Hypothetical nominal interest rate; not predicted pricing."},
        "rate_max": {"value": 24, "unit": "% p.a.", "basis": "Hypothetical nominal interest rate; not predicted pricing."},
        "emi_nmi_max_ratio": {"value": 0.5, "unit": "ratio", "basis": "Hypothetical total-EMI/net-income ratio; not universal policy."},
    },
}


def _csv(path, required=()):
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


def policy(data_dir=None):
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    path = (Path(data_dir) if data_dir is not None else Path(B) / "data") / "engine_config.json"
    if path.exists():
        with path.open(encoding="utf-8-sig") as handle:
            supplied = json.load(handle)
        if not isinstance(supplied, dict):
            raise ValueError("engine_config.json must contain an object")
        for key in ("mode", "enabled", "fallback_on_unresolved_scope", "fallback_on_conflict"):
            if key in supplied:
                config[key] = supplied[key]
        if "defaults" in supplied:
            if not isinstance(supplied["defaults"], dict):
                raise ValueError("defaults must contain an object")
            for key, entry in supplied["defaults"].items():
                if key not in config["defaults"] or not isinstance(entry, dict):
                    raise ValueError(f"Unsupported/default malformed key {key!r}")
                config["defaults"][key].update(entry)
    if config["mode"] not in {"STRICT", "DEMO"}:
        raise ValueError("mode must be STRICT or DEMO")
    for key in ("enabled", "fallback_on_unresolved_scope", "fallback_on_conflict"):
        if not isinstance(config[key], bool):
            raise ValueError(f"{key} must be boolean")
    for key, entry in config["defaults"].items():
        if not entry.get("basis"):
            raise ValueError(f"Default {key} needs a modelling basis")
        value = entry["value"]
        if key == "employment_scope":
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Default employment scope must be text")
        elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"Default {key} must be a finite nonnegative number")
        elif key not in {"rate_min", "rate_max"} and value == 0:
            raise ValueError(f"Default {key} must be positive")
        if key == "min_cibil" and not 300 <= value <= 900:
            raise ValueError("Default CIBIL must be 300-900")
        if key == "emi_nmi_max_ratio" and not 0 < value <= 1:
            raise ValueError("Default EMI ratio must be in (0,1]")
        if key.startswith("tenure_") and not float(value).is_integer():
            raise ValueError("Default tenure must be whole months")
    for lo, hi in (("min_age", "max_age_application"), ("rate_min", "rate_max"), ("amount_min", "amount_max"), ("tenure_min", "tenure_max")):
        if config["defaults"][lo]["value"] > config["defaults"][hi]["value"]:
            raise ValueError(f"Default {lo} exceeds {hi}")
    return config


def assumed_cap(data_dir=None):
    config = policy(data_dir)
    return config["defaults"]["emi_nmi_max_ratio"]["value"] if config["enabled"] and config["mode"] == "DEMO" else None


def load(data_dir=None):
    directory = Path(data_dir) if data_dir is not None else Path(B) / "data"
    config = policy(directory)
    lenders = _csv(directory / "lenders.csv", {"lender_id", "brand_name"})
    rows = _csv(directory / "lender_rules_detailed.csv", {"lender_id", "rule_id", "rule_key", "applicant_category", "value", "status", "source_ids"})
    ids = [l["lender_id"] for l in lenders]
    if not ids or any(not x for x in ids) or len(ids) != len(set(ids)):
        raise ValueError("lenders.csv: missing/duplicate lender IDs")
    seen = set()
    rules = collections.defaultdict(lambda: collections.defaultdict(list))
    for row in rows:
        if not row["rule_id"] or row["rule_id"] in seen:
            raise ValueError("lender_rules_detailed.csv: missing/duplicate rule IDs")
        seen.add(row["rule_id"])
        if row["lender_id"] not in ids:
            raise ValueError("Rule references unknown lender ID")
        rules[row["lender_id"]][row["rule_key"]].append(row)
    for lender in lenders:
        lender["_engine_config"] = config
        rules[lender["lender_id"]]
    return rules, lenders


def usable(rows):
    return [r for r in rows if r.get("status") == "VERIFIED_OFFICIAL" and str(r.get("value", "")).strip()]


def num(rows):
    try:
        values = {float(r["value"]) for r in usable(rows)}
    except (ValueError, TypeError):
        return None
    return next(iter(values)) if len(values) == 1 and all(math.isfinite(x) for x in values) else None


def _norm(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")


def _employment(value):
    value = _norm(value)
    return "self_employed" if value.startswith("self_employed") else value


def lender_bank(lender):
    return {"L01": "SBI", "L02": "HDFC Bank"}.get(lender["lender_id"], lender.get("brand_name", ""))


def _scope(scope, profile, lender):
    name = _norm(scope)
    employment = _employment(profile.get("employment_type"))
    if name in {"", "all", "personal_loan", "personal_loans"}:
        return True
    if name in {"xpress_credit", "sbi_personal_loan"}:
        return employment == "salaried" if employment else None
    if name in {"salary_account_holder", "non_salary_account"}:
        bank = profile.get("salary_account_bank")
        return None if bank is None else (bank == lender_bank(lender)) == (name == "salary_account_holder")
    if name in {"existing_axis_customer", "non_axis_customer"}:
        existing = profile.get("existing_lender_customer")
        return None if not isinstance(existing, bool) else existing == (name == "existing_axis_customer")
    if name in {"government", "government_or_defence", "corporate", "government_or_defence_sector"}:
        employer = _norm(profile.get("employer_category"))
        if not employer:
            return None
        return employer in {"government", "defence", "psu"} if "government" in name else employer == "corporate"
    if name in {"kotak_salary_account_holder", "non_kotak_salary_account_holder", "kotak_employee"}:
        if name == "kotak_employee":
            answer = profile.get("is_kotak_employee")
            return None if answer is None else bool(answer)
        bank = profile.get("salary_account_bank")
        return None if bank is None else (bank == "Kotak Mahindra Bank") == (name == "kotak_salary_account_holder")
    if name in {"salaried_delhi_or_mumbai", "salaried_other_city"}:
        if employment and employment != "salaried":
            return False
        city = _norm(profile.get("city"))
        if not city:
            return None
        metro = city in {"delhi", "new_delhi", "mumbai"}
        return metro if name == "salaried_delhi_or_mumbai" else not metro
    if name == "credit_history_present":
        status = profile.get("credit_history_status")
        return status == "scored" if status else profile.get("cibil_score") is not None
    if name in {"regular", "instant_online", "regular_personal_loan", "instant_personal_loan", "prime", "delight", "term", "flexi"}:
        selected = _norm(profile.get("product_variant"))
        return None if not selected else selected == name
    if name == "instant_online_or_regular":
        return True
    if "salaried" in name and "self_employed" not in name:
        return employment == "salaried" if employment else None
    if name in {"self_employed", "non_salaried"}:
        return employment == "self_employed" if employment else None
    if name in {"self_employed_professional", "self_employed_individual"}:
        return None if _norm(profile.get("employment_type")) == "self_employed" else _norm(profile.get("employment_type")) == name
    if name == _norm(lender.get("personal_loan_product")) and name != "not_verified":
        return True
    return None


def resolve_rule(key, R, profile, lender, config, fallback=True):
    records = R.get(key, [])
    matched, undecided = [], []
    for row in records:
        if row.get("status") == "UNKNOWN" and not str(row.get("value", "")).strip():
            continue
        match = _scope(row.get("applicant_category"), profile, lender)
        category = _norm(row.get("applicant_category"))
        if key == "employment_scope" and match is False and ("salaried" in category or category.startswith("self_employed")):
            match = True  # Compare the explicit scope value; do not replace it to suit the applicant.
        if match is True:
            matched.append(row)
        elif match is None:
            undecided.append(row)
    origin, reason = "UNKNOWN", "No applicable usable official value was established."
    evidence = matched or undecided or records
    if any(r.get("status") == "CONFLICTING" for r in matched):
        origin, reason = "CONFLICTING", "Applicable source statements conflict."
    elif undecided:
        origin, reason = "UNRESOLVED_SCOPE", "Required category/product selector is absent or not implemented."
    else:
        official = usable(matched)
        if official:
            units = {_norm(r.get("unit")) for r in official}
            if key == "min_income" and any("net" not in unit or "month" not in unit for unit in units):
                origin, reason = "UNRESOLVED_INCOME_BASIS", "Published income cannot safely be equated to net monthly income."
            elif key == "min_cibil" and any("cic" in unit or "bureau_unspecified" in unit for unit in units):
                origin, reason = "UNRESOLVED_BUREAU", "An unspecified bureau/CIC score cannot be mapped to CIBIL."
            else:
                try:
                    values = [r["value"] for r in official] if key in {"employment_scope", "salary_account_required"} else [float(r["value"]) for r in official]
                    valid = key in {"employment_scope", "salary_account_required"} or all(math.isfinite(v) for v in values)
                except (TypeError, ValueError):
                    values, valid = [], False
                if not valid:
                    origin, reason = "UNRESOLVED_VALUE", "Published value is not a usable scalar."
                elif len(set(values)) != 1 or len(units) != 1:
                    origin, reason = "UNRESOLVED_SCOPE", "Multiple applicable thresholds/units cannot be selected reliably."
                else:
                    return {"key": key, "value": values[0], "status": "VERIFIED_OFFICIAL", "selection_status": "RESOLVED",
                            "basis": "Applicable recorded official CSV rule.", "rows": official, "candidate_rows": [], "unit": official[0].get("unit", "")}
    demo = config["enabled"] and config["mode"] == "DEMO"
    permitted = fallback and key in config["defaults"] and demo
    if origin == "CONFLICTING":
        permitted = permitted and config["fallback_on_conflict"]
    elif origin != "UNKNOWN":
        permitted = permitted and config["fallback_on_unresolved_scope"]
    if permitted:
        fixed = config["defaults"][key]
        return {"key": key, "value": fixed["value"], "status": "ESTIMATED", "selection_status": origin,
                "basis": fixed["basis"], "fallback_reason": reason, "rows": [], "candidate_rows": evidence, "unit": fixed.get("unit", "")}
    return {"key": key, "value": None, "status": origin, "selection_status": origin,
            "basis": reason, "rows": evidence, "candidate_rows": [], "unit": ""}


def _source_ids(rows):
    return sorted({x for row in rows for x in row.get("source_ids", "").split(";") if x})


def _check(code, message, result):
    return {"code": code, "reason": message, "detail": message, "evidence_status": [result["status"]],
            "threshold": result["value"], "rule_ids": [r["rule_id"] for r in result["rows"]],
            "source_ids": _source_ids(result["rows"]), "is_model_assumption": result["status"] == "ESTIMATED"}


def emi(principal, rate, months):
    r = rate / 1200
    return principal / months if r == 0 else principal * r / (1 - (1 + r) ** (-months))


def pv(payment, rate, months):
    r = rate / 1200
    return payment * months if r == 0 else payment * (1 - (1 + r) ** (-months)) / r


def evaluate(profile, lender, rules, cap_assumption=UNSET):
    R = rules.get(lender["lender_id"], {})
    config = lender.get("_engine_config", DEFAULT_CONFIG)
    resolved, assumptions, notes, blockers, missing = {}, [], [], [], []
    passed, official_fails, assumed_passed, assumed_fails = [], [], [], []
    p = dict(profile)
    required = {"age", "employment_type", "net_monthly_income", "cibil_score", "existing_monthly_emi", "requested_amount", "preferred_tenure_months"}
    for name in sorted(required):
        value = p.get(name)
        if value is None:
            missing.append(name); blockers.append(f"Applicant input missing: {name}")
        elif name != "employment_type":
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                blockers.append(f"Applicant input invalid: {name}"); p[name] = None
            elif name in {"requested_amount", "preferred_tenure_months"} and value <= 0:
                blockers.append(f"Applicant input invalid: {name} must be positive"); p[name] = None
    if p.get("employment_type") is not None and _employment(p["employment_type"]) not in {"salaried", "self_employed"}:
        blockers.append("Applicant input invalid: employment_type"); p["employment_type"] = None
    if p.get("cibil_score") is not None and (not 300 <= p["cibil_score"] <= 900 or not float(p["cibil_score"]).is_integer()):
        blockers.append("Applicant score must be 300-900; do not encode NH/unknown as zero."); p["cibil_score"] = None
    if p.get("preferred_tenure_months") is not None and not float(p["preferred_tenure_months"]).is_integer():
        blockers.append("Applicant tenure must be whole months."); p["preferred_tenure_months"] = None

    def get(key, fallback=True, required_rule=False):
        if key not in resolved:
            selected = resolve_rule(key, R, profile, lender, config, fallback)
            resolved[key] = selected
            if selected["status"] == "ESTIMATED":
                assumptions.append({"rule_key": key, "value": selected["value"], "unit": selected["unit"], "status": "ESTIMATED",
                                    "basis": selected["basis"], "fallback_reason": selected.get("fallback_reason"),
                                    "csv_resolution": selected["selection_status"], "source_ids": [], "rule_ids": [],
                                    "candidate_source_ids_not_used": _source_ids(selected["candidate_rows"]),
                                    "candidate_rule_ids_not_used": [r["rule_id"] for r in selected["candidate_rows"]]})
                notes.append(f"DEMO assumption: {key}={selected['value']}; {selected['basis']}")
        if required_rule and resolved[key]["value"] is None:
            blockers.append(f"{key}: {resolved[key]['basis']}")
        return resolved[key]

    def check(code, condition, message, selected):
        entry = _check(code, message, selected)
        if selected["status"] == "ESTIMATED":
            (assumed_passed if condition else assumed_fails).append(entry)
        else:
            (passed if condition else official_fails).append(entry)

    availability = lender.get("availability_status", "LIVE_OFFER_NOT_VERIFIED")
    if any(r.get("status") == "VERIFIED_OFFICIAL" and str(r.get("value", "")).lower() == "false" for r in R.get("new_personal_loan_sourcing_available", [])):
        availability = "SOURCING_UNAVAILABLE"
    unavailable = availability == "SOURCING_UNAVAILABLE"
    if unavailable:
        blockers.append("Product notice says new personal-loan sourcing is unavailable.")

    scope = get("employment_scope", required_rule=True)
    if scope["value"] is not None and p.get("employment_type"):
        types = {_employment(x) for x in re.split(r"[;,|]", str(scope["value"]))}
        check("EMPLOYMENT_SCOPE", _employment(p["employment_type"]) in types, "Employment checked against the evaluated product/scenario scope.", scope)
    min_age = get("min_age", required_rule=True)
    income = get("min_income", required_rule=True)
    score = get("min_cibil", required_rule=True)
    maturity = get("max_age_at_maturity", False)
    maximum = get("max_age_application", False)
    if maximum["value"] is None and maturity["value"] is None:
        resolved.pop("max_age_application", None)
        maximum = get("max_age_application", required_rule=True)
    age, inc, cibil = p.get("age"), p.get("net_monthly_income"), p.get("cibil_score")
    for value, selected, condition, code, label in (
        (age, min_age, lambda a, b: a >= b, "AGE_MIN", "Age minimum"),
        (age, maximum, lambda a, b: a <= b, "AGE_MAX", "Application age maximum"),
        (inc, income, lambda a, b: a >= b, "INCOME_MIN", "Net monthly income minimum"),
        (cibil, score, lambda a, b: a >= b, "CIBIL_MIN", "Credit-score minimum"),
    ):
        if value is not None and selected["value"] is not None:
            check(code, condition(value, selected["value"]), f"{label}: applicant {value}, threshold {selected['value']}", selected)
    account = get("salary_account_required", False)
    if account["value"] is not None and _employment(p.get("employment_type")) == "salaried":
        bank = p.get("salary_account_bank")
        if bank is None:
            missing.append("salary_account_bank"); blockers.append("Applicant input missing: salary_account_bank")
        else:
            check("SALARY_ACCOUNT_REQUIRED", bank == account["value"], f"Salary bank {bank}; evaluated product requires {account['value']}", account)

    tmin, tmax = get("tenure_min"), get("tenure_max")
    lower, upper = tmin["value"], tmax["value"]
    if maturity["value"] is not None and age is not None:
        months_left = math.floor((maturity["value"] - age) * 12)
        upper = months_left if upper is None else min(upper, months_left)
        check("AGE_AT_MATURITY", months_left > 0 and (lower is None or months_left >= lower), f"Months to evaluated maturity boundary: {months_left}", maturity)
    if lower is not None and upper is not None and lower > upper:
        notes.append("No consistent term remains under the selected age/tenure limits.")
    pref = p.get("preferred_tenure_months")
    tenure = min(pref, upper) if pref is not None and upper is not None and upper > 0 else None
    if tenure is not None and lower is not None and tenure < lower:
        check("TENURE_MIN", False, f"Requested tenure {pref} is below selected minimum {lower}", tmin)
        tenure = None
    elif tenure is not None and pref != tenure:
        notes.append(f"Calculation tenure reduced from {pref} to {tenure:g} months.")
    requested = p.get("requested_amount")
    amin, amax = get("amount_min"), get("amount_max")
    if requested is not None:
        if amin["value"] is not None:
            check("AMOUNT_MIN", requested >= amin["value"], f"Requested principal {requested}; selected minimum {amin['value']}", amin)
        if amax["value"] is not None:
            check("AMOUNT_MAX", requested <= amax["value"], f"Requested principal {requested}; selected ceiling {amax['value']}", amax)
    ratio = get("emi_nmi_max_ratio")
    ex = p.get("existing_monthly_emi")
    cap = ratio["value"]
    if cap is not None and not 0 < cap <= 1:
        blockers.append("Selected EMI ratio is invalid."); cap = None
    headroom = cap * inc - ex if cap is not None and inc is not None and ex is not None else None
    if headroom is not None:
        check("EXISTING_EMI_HEADROOM", headroom > 0, f"Headroom under selected EMI ratio: {headroom:.2f}", ratio)
    rate_min, rate_max = get("rate_min"), get("rate_max")
    rmin, rmax = rate_min["value"], rate_max["value"]
    valid_rates = rmin is not None and rmax is not None and 0 <= rmin <= rmax
    if rmin is not None and rmax is not None and not valid_rates:
        notes.append("CSV/default rate bounds are inconsistent; pricing estimate suppressed.")
    max_amount, emi_range, basis = None, None, None
    if headroom is not None and headroom > 0 and tenure and valid_rates:
        max_amount = pv(headroom, rmax, tenure)
        if amax["value"] is not None:
            max_amount = min(max_amount, amax["value"])
        basis = "Illustrative upper-rate PV of EMI headroom; see rule_provenance and assumptions_used. Not lender sanction."
        if requested is not None:
            emi_range = [round(emi(requested, rmin, tenure)), round(emi(requested, rmax, tenure))]
            if requested > max_amount:
                notes.append("Requested amount exceeds the selected illustrative affordability estimate.")
                if any(s["status"] == "ESTIMATED" for s in (ratio, rate_max, tmax, amax)):
                    simulation = {"value": max_amount, "status": "ESTIMATED", "rows": []}
                    assumed_fails.append(_check("SCENARIO_AFFORDABILITY", "Requested amount exceeds model-scenario affordability; not a bank decline.", simulation))

    for key, field in (("min_current_job_months", "current_job_months"), ("min_total_experience_months", "total_experience_months"), ("min_business_vintage_months", "business_vintage_months")):
        if key == "min_business_vintage_months" and _employment(p.get("employment_type")) != "self_employed":
            continue
        selected = get(key, False)
        if selected["value"] is not None:
            value = p.get(field)
            if value is None:
                missing.append(field); blockers.append(f"Applicant input missing: {field}")
            elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                blockers.append(f"Applicant input invalid: {field}")
            else:
                check(key.upper(), value >= selected["value"], f"{field} {value}; selected minimum {selected['value']}", selected)
    complex_keys = {"income_multiple_max", "foir_max", "residual_takehome_requirement", "coobligation_required", "guarantor_required", "guarantor_requirement",
                    "education_requirement", "city_restrictions", "min_service_months", "min_continuous_service_months", "min_annual_household_income",
                    "min_gross_annual_income", "min_annual_net_income_post_tax", "min_annual_turnover", "min_bank_relationship_months", "account_relationship"}
    unevaluated = sorted(k for k in complex_keys if usable(R.get(k, [])))
    if unevaluated:
        notes.append("Additional published rules not implemented automatically: " + ", ".join(unevaluated))
    failures = official_fails + assumed_fails
    if unavailable:
        status, decision_basis = "INSUFFICIENT_INFORMATION", "PRODUCT_UNAVAILABLE"
        official_fails, assumed_fails, failures = [], [], []
    elif missing or any(x.startswith("Applicant input invalid") or x.startswith("Applicant score") or x.startswith("Applicant tenure") for x in blockers):
        status, decision_basis = "INSUFFICIENT_INFORMATION", "APPLICANT_INFORMATION"
    elif failures:
        status = "NOT_ELIGIBLE"
        decision_basis = "PUBLISHED_RULE_FAILURE" if official_fails else "MODEL_SCENARIO_FAILURE"
    elif blockers:
        status, decision_basis = "INSUFFICIENT_INFORMATION", "LENDER_RULE_REVIEW"
    else:
        status = "POTENTIALLY_ELIGIBLE"
        decision_basis = "MODEL_SCENARIO_PASS" if assumptions else "PUBLISHED_RULE_SCREENING"
    scenario = "FAIL" if assumed_fails else ("INCOMPLETE" if blockers else ("PASS" if assumptions else "NOT_USED"))
    show_estimate = status == "POTENTIALLY_ELIGIBLE"
    gaps = [{"rule_key": key, "status": s["status"], "reason": s["basis"], "rule_ids": [r["rule_id"] for r in s["rows"]]} for key, s in resolved.items() if s["value"] is None]
    provenance = {key: {"value": s["value"], "status": s["status"], "unit": s["unit"], "basis": s["basis"],
                        "selection_status": s["selection_status"], "source_ids": _source_ids(s["rows"]),
                        "rule_ids": [r["rule_id"] for r in s["rows"]]} for key, s in resolved.items()}
    return {"lender_id": lender["lender_id"], "brand": lender["brand_name"], "status": status,
            "passed_rules": passed, "rejection_reasons": failures, "verified_rejection_reasons": official_fails,
            "scenario_passed_rules": assumed_passed, "scenario_failed_rules": assumed_fails,
            "missing_applicant_inputs": sorted(set(missing)), "insufficient_information_reasons": blockers if status == "INSUFFICIENT_INFORMATION" else [],
            "rule_gaps": gaps, "unknowns_not_evaluated": [f"{g['rule_key']}: {g['reason']}" for g in gaps],
            "max_amount_estimate_inr": round(max_amount) if max_amount is not None and show_estimate else None,
            "max_amount_basis": basis if show_estimate else None,
            "rate_range_pct": [rmin, rmax] if valid_rates and show_estimate else None,
            "rate_status": "ESTIMATED" if valid_rates and any(r["status"] == "ESTIMATED" for r in (rate_min, rate_max)) else ("KNOWN" if valid_rates else "UNAVAILABLE"),
            "tenure_months_range": [lower, upper] if lower is not None or upper is not None else None,
            "tenure_used_months": tenure, "est_emi_for_requested_inr": emi_range if show_estimate else None,
            "notes": notes, "uses_estimates": bool(assumptions), "assumptions_used": assumptions,
            "assessment_mode": config["mode"], "scenario_result": scenario, "decision_basis": decision_basis,
            "rule_provenance": provenance, "availability_status": availability,
            "requires_lender_review": True, "approval_guaranteed": False, "bank_rejection_claimed": False,
            "assessment_evidence_level": "MIXED_OFFICIAL_AND_ASSUMED" if assumptions and (passed or official_fails) else ("ASSUMED" if assumptions else "OFFICIAL_SCREENING"),
            "unevaluated_published_rules": unevaluated}


def recommend(results):
    rows = [r for r in results if r["status"] == "POTENTIALLY_ELIGIBLE" and not r["uses_estimates"]
            and not r["unevaluated_published_rules"] and r["rate_range_pct"] and r["availability_status"] != "SOURCING_UNAVAILABLE"]
    if len(rows) < 2:
        return {"recommended": None, "why": "Fewer than two non-scenario comparable assessments; hypothetical matches are not actual lender offers."}
    best = min(rows, key=lambda r: (r["rate_range_pct"][1], r["rate_range_pct"][0]))
    return {"recommended": best["lender_id"], "why": "Lowest published upper nominal rate among comparable non-scenario results; actual quote/fees/approval unknown."}


def main():
    rules, lenders = load()
    with (Path(B) / "tests" / "profiles.json").open(encoding="utf-8-sig") as handle:
        profiles = json.load(handle)
    results = []
    for profile in profiles:
        rows = [evaluate(profile["inputs"], lender, rules) for lender in lenders]
        results.append({"profile_id": profile["profile_id"], "inputs": profile["inputs"],
                        "summary": dict(collections.Counter(r["status"] for r in rows)), "recommendation": recommend(rows), "lenders": rows})
    target = Path(B) / "tests" / "results.json"
    with target.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, allow_nan=False)
    print(f"Wrote results to {target}")


if __name__ == "__main__":
    main()
