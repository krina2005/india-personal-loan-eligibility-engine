# """Deterministic rule engine. Usage: python engine/engine.py  (reads tests/profiles.json, writes tests/results.json + results_flat.csv)"""
# import csv, json, os, collections
# B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
# HARD = {"VERIFIED_OFFICIAL", "VERIFIED_SECONDARY", "OBSERVED_IN_CALCULATOR"}
# def assumed_cap(data_dir=None):
#     return json.load(open(f"{data_dir or B + '/data'}/model_assumptions.json"))["global_affordability_assumption"]["emi_to_income_cap"]

# def load(data_dir=None):
#     d = data_dir or f"{B}/data"
#     rules = collections.defaultdict(lambda: collections.defaultdict(list))
#     for r in csv.DictReader(open(f"{d}/lender_rules_detailed.csv", encoding="utf-8")):
#         rules[r["lender_id"]][r["rule_key"]].append(r)
#     lenders = list(csv.DictReader(open(f"{d}/lenders.csv", encoding="utf-8")))
#     return rules, lenders

# def usable(rs):  # rows that carry a usable hard value
#     return [r for r in rs if r["status"] in HARD and r["value"] != ""]
# def num(rs):
#     u = usable(rs); return float(u[0]["value"]) if u else None
# def emi(p, rate, n):
#     r = rate / 1200
#     return p / n if r == 0 else p * r * (1 + r) ** n / ((1 + r) ** n - 1)
# def pv(e, rate, n):
#     r = rate / 1200
#     return e * n if r == 0 else e * ((1 + r) ** n - 1) / (r * (1 + r) ** n)

# def evaluate(p, lender, rules, cap_assumption=None):
#     if cap_assumption is None: cap_assumption = assumed_cap()
#     R = rules[lender["lender_id"]]; fails, blocking, notes, unknowns = [], [], [], []
#     passed, missing = [], []
#     def ok(code, msg, rs): passed.append({"code": code, "detail": msg, "evidence_status": sorted({r["status"] for r in rs}), "rule_ids": [r["rule_id"] for r in rs]})
#     def fail(code, msg, rs): fails.append({"code": code, "reason": msg, "evidence_status": sorted({r["status"] for r in rs}), "rule_ids": [r["rule_id"] for r in rs]})
#     # --- applicant inputs missing
#     for f in ("age", "employment_type", "net_monthly_income", "cibil_score"):
#         if p.get(f) is None: blocking.append(f"applicant input missing: {f}"); missing.append(f)
#     if blocking and p.get("cibil_score") is None and p.get("age") is None: pass
#     # --- blocking-rule availability
#     scope = usable(R["employment_scope"])
#     if not scope: blocking.append("employment scope rule UNKNOWN")
#     elif p.get("employment_type") and p["employment_type"] not in scope[0]["value"].split(";"):
#         blocking.append(f"researched product covers '{scope[0]['value']}' only; '{p['employment_type']}' rules not researched")
#     if not usable(R["min_age"]): blocking.append("min_age UNKNOWN")
#     if not usable(R["max_age_application"]) and not usable(R["max_age_at_maturity"]): blocking.append("max age rule UNKNOWN")
#     if not usable(R["min_cibil"]): blocking.append("min_cibil " + ("CONFLICTING" if any(r["status"]=="CONFLICTING" for r in R["min_cibil"]) else "UNKNOWN"))
#     mi = R["min_income"]
#     if not usable(mi): blocking.append("min_income " + ("CONFLICTING" if any(r["status"]=="CONFLICTING" for r in mi) else "UNKNOWN"))
#     # --- hard checks (verified/observed rules only)
#     age, cibil, inc = p.get("age"), p.get("cibil_score"), p.get("net_monthly_income")
#     mn = num(R["min_age"])
#     if age is not None and mn is not None and age < mn: fail("AGE_BELOW_MIN", f"age {age} < min {mn:g}", usable(R["min_age"]))
#     elif age is not None and mn is not None: ok("AGE_MIN", f"age {age:g} >= min {mn:g}", usable(R["min_age"]))
#     ma = num(R["max_age_application"])
#     if age is not None and ma is not None and age > ma: fail("AGE_ABOVE_MAX", f"age {age} > max {ma:g} at application", usable(R["max_age_application"]))
#     elif age is not None and ma is not None: ok("AGE_MAX", f"age {age:g} <= max {ma:g} at application", usable(R["max_age_application"]))
#     mc = num(R["min_cibil"])
#     if cibil is not None and mc is not None and cibil < mc: fail("CIBIL_BELOW_MIN", f"score {cibil} < min {mc:g}", usable(R["min_cibil"]))
#     elif cibil is not None and mc is not None: ok("CIBIL_MIN", f"score {cibil:g} >= min {mc:g}", usable(R["min_cibil"]))
#     sa = usable(R["salary_account_required"])
#     bank = p.get("salary_account_bank")
#     if sa and bank is None and p.get("employment_type") in ("salaried", None):
#         blocking.append("applicant input missing: salary_account_bank"); missing.append("salary_account_bank")
#     elif sa and bank != sa[0]["value"] and p.get("employment_type") in ("salaried", None):
#         fail("SALARY_ACCOUNT_REQUIRED", f"requires salary account with {sa[0]['value']}; applicant has {bank}", sa)
#     elif sa: ok("SALARY_ACCOUNT", f"salary account with {sa[0]['value']} held", sa)
#     u = usable(mi)   # income: category-specific
#     if u and inc is not None and len(u) > 1 and bank is None:
#         blocking.append("applicant input missing: salary_account_bank"); missing.append("salary_account_bank")
#     elif u and inc is not None:
#         if len(u) > 1:  # HDFC-style tiers
#             cat = "salary_account_holder" if p.get("salary_account_bank") == lender_bank(lender) else "non_salary_account"
#             u = [r for r in u if r["applicant_category"] == cat] or u
#         thr = float(u[0]["value"])
#         if inc < thr: fail("INCOME_BELOW_MIN", f"net income {inc:g} < min {thr:g} ({u[0]['applicant_category']})", u)
#         else: ok("INCOME_MIN", f"net income {inc:g} >= min {thr:g} ({u[0]['applicant_category']})", u)
#     # --- tenure / maturity
#     tmin, tmax = num(R["tenure_min"]), num(R["tenure_max"]); mat = num(R["max_age_at_maturity"])
#     perm_max = tmax
#     if mat is not None and age is not None:
#         cap = int((mat - age) * 12)
#         perm_max = cap if perm_max is None else min(perm_max, cap)
#         if tmin is not None and cap < tmin: fail("AGE_AT_MATURITY", f"age {age} leaves {cap} months to age {mat:g}; min tenure {tmin:g}", usable(R["max_age_at_maturity"]))
#         else: ok("AGE_AT_MATURITY", f"{cap} months remain to age {mat:g}", usable(R["max_age_at_maturity"]))
#     pref = p.get("preferred_tenure_months")
#     tenure = None
#     if perm_max is not None and pref is not None:
#         tenure = min(pref, perm_max)
#         if tmin is not None: tenure = max(tenure, tmin) if tenure >= tmin else None
#         if pref > perm_max: notes.append(f"preferred tenure {pref} reduced to {perm_max:g} months (max tenure / age at maturity)")
#     # --- affordability
#     cap_r = num(R["emi_nmi_max_ratio"]); cap_src = "published (" + (usable(R["emi_nmi_max_ratio"])[0]["status"] if cap_r else "") + ")" if cap_r else None
#     est = False
#     if cap_r is None: cap_r, est, cap_src = cap_assumption, True, "ESTIMATED modelling assumption (not lender policy)"
#     ex = p.get("existing_monthly_emi") or 0
#     rmin, rmax = num(R["rate_min"]), num(R["rate_max"])
#     rate_status = "KNOWN" if rmax is not None else ("CONFLICTING" if any(r["status"]=="CONFLICTING" for r in R["rate_max"]) else "UNKNOWN")
#     headroom = (cap_r * inc - ex) if inc is not None else None
#     if headroom is not None and headroom <= 0:
#         if not est and usable(R["emi_nmi_max_ratio"]): fail("EMI_NMI_EXCEEDED", f"existing EMI {ex:g} already >= {cap_r:.0%} of income", usable(R["emi_nmi_max_ratio"]))
#         else: notes.append(f"WARNING: under assumed {cap_r:.0%} obligation cap there is no EMI headroom (estimate, not a rejection)")
#     max_amt, amt_basis = None, None
#     amt_cap = num(R["amount_max"])
#     if headroom is not None and headroom > 0 and tenure and rmax is not None:
#         max_amt = pv(headroom, rmax, tenure); amt_basis = f"PV(headroom {headroom:,.0f} @ rate_max {rmax:g}% / {tenure:g}m) using {cap_src}"
#         if amt_cap is not None and amt_cap < max_amt: max_amt, amt_basis = amt_cap, f"published amount_max {amt_cap:,.0f}"
#     elif amt_cap is not None and rmax is None:
#         notes.append(f"affordability amount not computable (rate {rate_status}); only published cap {amt_cap:,.0f} known")
#     if max_amt is not None and p.get("requested_amount") and p["requested_amount"] > max_amt: notes.append(f"requested {p['requested_amount']:,.0f} exceeds estimate {max_amt:,.0f}")
#     # --- non-blocking unknowns that are relevant to this applicant
#     chk = {"min_current_job_months": p.get("current_job_months"), "min_total_experience_months": p.get("total_experience_months"),
#            "min_business_vintage_months": p.get("business_vintage_months") if p.get("employment_type") == "self_employed" else None, "city_restrictions": p.get("city")}
#     for k, v in chk.items():
#         if v is not None and not usable(R[k]): unknowns.append(f"{k} not published/found -> not evaluated")
#     for k in ("foir_max", "income_multiple_max"):
#         if not usable(R[k]): unknowns.append(f"{k} not published/found -> not evaluated")
#     if any('researched product covers' in b for b in blocking): fails = []; passed = []  # product-scope mismatch: rules for this applicant type were not researched, so no hard rejection
#     # --- status
#     if fails: status = "NOT_ELIGIBLE"
#     elif blocking: status = "INSUFFICIENT_INFORMATION"
#     else: status = "POTENTIALLY_ELIGIBLE"
#     out = dict(lender_id=lender["lender_id"], brand=lender["brand_name"], status=status, passed_rules=passed, missing_applicant_inputs=sorted(set(missing)), rejection_reasons=fails,
#                insufficient_information_reasons=blocking if status != "NOT_ELIGIBLE" else [],
#                max_amount_estimate_inr=round(max_amt) if (max_amt and status == "POTENTIALLY_ELIGIBLE") else None, max_amount_basis=amt_basis if status == "POTENTIALLY_ELIGIBLE" else None,
#                rate_range_pct=[rmin, rmax] if (rmax is not None and status == "POTENTIALLY_ELIGIBLE") else None, rate_status=rate_status,
#                tenure_months_range=[tmin, perm_max] if perm_max is not None else None, tenure_used_months=tenure,
#                est_emi_for_requested_inr=[round(emi(p["requested_amount"], rmin, tenure)), round(emi(p["requested_amount"], rmax, tenure))] if (status == "POTENTIALLY_ELIGIBLE" and rmin and rmax and tenure and p.get("requested_amount")) else None,
#                notes=notes, unknowns_not_evaluated=unknowns)
#     return out
# def lender_bank(l): return {"L02": "HDFC Bank", "L01": "SBI"}.get(l["lender_id"], "")

# def recommend(res):
#     ok = [r for r in res if r["status"] == "POTENTIALLY_ELIGIBLE" and r["rate_range_pct"]]
#     if len(ok) < 2: return {"recommended": None, "why": f"Not enough comparable evidence: {len(ok)} potentially-eligible lender(s) with a published rate range; need >=2 to compare."}
#     b = min(ok, key=lambda r: (r["rate_range_pct"][1], r["rate_range_pct"][0]))
#     return {"recommended": b["lender_id"], "why": "Lowest published maximum rate among comparable potentially-eligible lenders; applicant-specific quote not known."}

# def main():
#     rules, lenders = load(); profiles = json.load(open(f"{B}/tests/profiles.json"))
#     results = []
#     for p in profiles:
#         res = [evaluate(p["inputs"], l, rules) for l in lenders]
#         results.append(dict(profile_id=p["profile_id"], purpose=p["purpose"], inputs=p["inputs"], summary=dict(collections.Counter(r["status"] for r in res)), recommendation=recommend(res), lenders=res))
#     json.dump(results, open(f"{B}/tests/results.json", "w"), indent=1)
#     with open(f"{B}/tests/results_flat.csv", "w", newline="", encoding="utf-8") as f:
#         wr = csv.writer(f); wr.writerow(["profile_id", "lender_id", "brand", "status", "rejection_codes", "reasons", "max_amount_inr", "rate_pct", "tenure_months", "notes"])
#         for r in results:
#             for l in r["lenders"]:
#                 wr.writerow([r["profile_id"], l["lender_id"], l["brand"], l["status"], ";".join(x["code"] for x in l["rejection_reasons"]),
#                              " | ".join([x["reason"] for x in l["rejection_reasons"]] + l["insufficient_information_reasons"]), l["max_amount_estimate_inr"] or "",
#                              "-".join(map(str, l["rate_range_pct"])) if l["rate_range_pct"] else l["rate_status"], l["tenure_used_months"] or "", " | ".join(l["notes"])])
#     print("wrote results for", len(results), "profiles")
# if __name__ == "__main__": main()




# """Deterministic rule engine. Usage: python engine/engine.py  (reads tests/profiles.json, writes tests/results.json + results_flat.csv)"""
# import csv, json, os, collections, math
# from pathlib import Path
# B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
# HARD = {"VERIFIED_OFFICIAL", "VERIFIED_SECONDARY", "OBSERVED_IN_CALCULATOR"}
# _UNSET = object()


# def assumed_cap(data_dir=None):
#     directory = Path(data_dir) if data_dir is not None else Path(B) / "data"
#     with (directory / "model_assumptions.json").open(encoding="utf-8-sig") as handle:
#         config = json.load(handle)
#     policy = config.get("global_affordability_assumption",
#                         config.get("affordability_assumption", {}))
#     if not isinstance(policy, dict):
#         raise ValueError("Affordability assumption must be a JSON object")
#     if policy.get("enabled", policy.get("enabled_by_default", True)) is False:
#         return None
#     value = policy.get("emi_to_income_cap", policy.get("optional_total_emi_to_net_income_cap"))
#     if value is None:
#         return None
#     if isinstance(value, bool):
#         raise ValueError("Affordability cap must be a number, not a boolean")
#     cap = float(value)
#     if not math.isfinite(cap) or not 0 < cap <= 1:
#         raise ValueError("Affordability cap must be finite and between 0 and 1")
#     return cap


# def _read_csv(path, required=()):
#     path = Path(path)
#     with path.open("r", encoding="utf-8-sig", newline="") as handle:
#         reader = csv.DictReader(handle)
#         if reader.fieldnames is None:
#             raise ValueError(f"{path.name}: CSV header is missing")
#         headers = [h.strip().lstrip("\ufeff").strip() for h in reader.fieldnames]
#         if any(not h for h in headers) or len(headers) != len(set(headers)):
#             raise ValueError(f"{path.name}: empty or duplicate CSV headers")
#         missing = set(required) - set(headers)
#         if missing:
#             raise ValueError(f"{path.name}: missing columns {sorted(missing)}; headers={headers}")
#         reader.fieldnames = headers
#         rows = []
#         for row in reader:
#             if None in row:
#                 raise ValueError(f"{path.name}: extra CSV fields near line {reader.line_num}")
#             if any(value is None for value in row.values()):
#                 raise ValueError(f"{path.name}: missing CSV cells near line {reader.line_num}")
#             if not any(value.strip() for value in row.values()):
#                 continue
#             for key in ("lender_id", "rule_id", "rule_key", "source_id", "status", "name"):
#                 if key in row:
#                     row[key] = row[key].strip()
#             rows.append(row)
#     return rows


# def load(data_dir=None):
#     directory = Path(data_dir) if data_dir is not None else Path(B) / "data"
#     lenders = _read_csv(directory / "lenders.csv", {"lender_id", "brand_name"})
#     rule_rows = _read_csv(directory / "lender_rules_detailed.csv",
#                          {"rule_id", "lender_id", "rule_key", "applicant_category",
#                           "status", "value", "source_ids"})
#     if not lenders:
#         raise ValueError("lenders.csv contains no lenders")
#     ids = set()
#     for lender in lenders:
#         lid = lender["lender_id"]
#         if not lid or lid in ids:
#             raise ValueError(f"lenders.csv: blank or duplicate lender_id {lid!r}")
#         ids.add(lid)
#     rules = collections.defaultdict(lambda: collections.defaultdict(list))
#     seen_rules = set()
#     for row in rule_rows:
#         if not row["rule_id"] or row["rule_id"] in seen_rules:
#             raise ValueError(f"lender_rules_detailed.csv: blank/duplicate rule_id {row['rule_id']!r}")
#         if row["lender_id"] not in ids:
#             raise ValueError(f"lender_rules_detailed.csv: unknown lender_id {row['lender_id']!r}")
#         if not row["rule_key"] or not row["status"]:
#             raise ValueError(f"lender_rules_detailed.csv: missing key/status in {row['rule_id']}")
#         seen_rules.add(row["rule_id"])
#         rules[row["lender_id"]][row["rule_key"]].append(row)
#     for lid in ids:
#         rules[lid]
#     return rules, lenders


# def usable(rs):  # rows that carry a usable hard value
#     return [r for r in rs if r["status"] in HARD and r["value"] != ""]
# def num(rs):
#     u = usable(rs); return float(u[0]["value"]) if u else None
# def emi(p, rate, n):
#     r = rate / 1200
#     return p / n if r == 0 else p * r * (1 + r) ** n / ((1 + r) ** n - 1)
# def pv(e, rate, n):
#     r = rate / 1200
#     return e * n if r == 0 else e * ((1 + r) ** n - 1) / (r * (1 + r) ** n)

# def evaluate(p, lender, rules, cap_assumption=_UNSET):
#     if cap_assumption is _UNSET: cap_assumption = assumed_cap()
#     R = rules[lender["lender_id"]]; fails, blocking, notes, unknowns = [], [], [], []
#     passed, missing = [], []
#     def ok(code, msg, rs): passed.append({"code": code, "detail": msg, "evidence_status": sorted({r["status"] for r in rs}), "rule_ids": [r["rule_id"] for r in rs]})
#     def fail(code, msg, rs): fails.append({"code": code, "reason": msg, "evidence_status": sorted({r["status"] for r in rs}), "rule_ids": [r["rule_id"] for r in rs]})
#     # --- applicant inputs missing
#     for f in ("age", "employment_type", "net_monthly_income", "cibil_score"):
#         if p.get(f) is None: blocking.append(f"applicant input missing: {f}"); missing.append(f)
#     if blocking and p.get("cibil_score") is None and p.get("age") is None: pass
#     # --- blocking-rule availability
#     scope = usable(R["employment_scope"])
#     if not scope: blocking.append("employment scope rule UNKNOWN")
#     elif p.get("employment_type") and p["employment_type"] not in scope[0]["value"].split(";"):
#         blocking.append(f"researched product covers '{scope[0]['value']}' only; '{p['employment_type']}' rules not researched")
#     if not usable(R["min_age"]): blocking.append("min_age UNKNOWN")
#     if not usable(R["max_age_application"]) and not usable(R["max_age_at_maturity"]): blocking.append("max age rule UNKNOWN")
#     if not usable(R["min_cibil"]): blocking.append("min_cibil " + ("CONFLICTING" if any(r["status"]=="CONFLICTING" for r in R["min_cibil"]) else "UNKNOWN"))
#     mi = R["min_income"]
#     if not usable(mi): blocking.append("min_income " + ("CONFLICTING" if any(r["status"]=="CONFLICTING" for r in mi) else "UNKNOWN"))
#     # --- hard checks (verified/observed rules only)
#     age, cibil, inc = p.get("age"), p.get("cibil_score"), p.get("net_monthly_income")
#     mn = num(R["min_age"])
#     if age is not None and mn is not None and age < mn: fail("AGE_BELOW_MIN", f"age {age} < min {mn:g}", usable(R["min_age"]))
#     elif age is not None and mn is not None: ok("AGE_MIN", f"age {age:g} >= min {mn:g}", usable(R["min_age"]))
#     ma = num(R["max_age_application"])
#     if age is not None and ma is not None and age > ma: fail("AGE_ABOVE_MAX", f"age {age} > max {ma:g} at application", usable(R["max_age_application"]))
#     elif age is not None and ma is not None: ok("AGE_MAX", f"age {age:g} <= max {ma:g} at application", usable(R["max_age_application"]))
#     mc = num(R["min_cibil"])
#     if cibil is not None and mc is not None and cibil < mc: fail("CIBIL_BELOW_MIN", f"score {cibil} < min {mc:g}", usable(R["min_cibil"]))
#     elif cibil is not None and mc is not None: ok("CIBIL_MIN", f"score {cibil:g} >= min {mc:g}", usable(R["min_cibil"]))
#     sa = usable(R["salary_account_required"])
#     bank = p.get("salary_account_bank")
#     if sa and bank is None and p.get("employment_type") in ("salaried", None):
#         blocking.append("applicant input missing: salary_account_bank"); missing.append("salary_account_bank")
#     elif sa and bank != sa[0]["value"] and p.get("employment_type") in ("salaried", None):
#         fail("SALARY_ACCOUNT_REQUIRED", f"requires salary account with {sa[0]['value']}; applicant has {bank}", sa)
#     elif sa: ok("SALARY_ACCOUNT", f"salary account with {sa[0]['value']} held", sa)
#     u = usable(mi)   # income: category-specific
#     if u and inc is not None and len(u) > 1 and bank is None:
#         blocking.append("applicant input missing: salary_account_bank"); missing.append("salary_account_bank")
#     elif u and inc is not None:
#         if len(u) > 1:  # HDFC-style tiers
#             cat = "salary_account_holder" if p.get("salary_account_bank") == lender_bank(lender) else "non_salary_account"
#             u = [r for r in u if r["applicant_category"] == cat] or u
#         thr = float(u[0]["value"])
#         if inc < thr: fail("INCOME_BELOW_MIN", f"net income {inc:g} < min {thr:g} ({u[0]['applicant_category']})", u)
#         else: ok("INCOME_MIN", f"net income {inc:g} >= min {thr:g} ({u[0]['applicant_category']})", u)
#     # --- tenure / maturity
#     tmin, tmax = num(R["tenure_min"]), num(R["tenure_max"]); mat = num(R["max_age_at_maturity"])
#     perm_max = tmax
#     if mat is not None and age is not None:
#         cap = int((mat - age) * 12)
#         perm_max = cap if perm_max is None else min(perm_max, cap)
#         if tmin is not None and cap < tmin: fail("AGE_AT_MATURITY", f"age {age} leaves {cap} months to age {mat:g}; min tenure {tmin:g}", usable(R["max_age_at_maturity"]))
#         else: ok("AGE_AT_MATURITY", f"{cap} months remain to age {mat:g}", usable(R["max_age_at_maturity"]))
#     pref = p.get("preferred_tenure_months")
#     tenure = None
#     if perm_max is not None and pref is not None:
#         tenure = min(pref, perm_max)
#         if tmin is not None: tenure = max(tenure, tmin) if tenure >= tmin else None
#         if pref > perm_max: notes.append(f"preferred tenure {pref} reduced to {perm_max:g} months (max tenure / age at maturity)")
#     # --- affordability
#     cap_r = num(R["emi_nmi_max_ratio"]); cap_src = "published (" + (usable(R["emi_nmi_max_ratio"])[0]["status"] if cap_r else "") + ")" if cap_r else None
#     est = False
#     if cap_r is None: cap_r, est, cap_src = cap_assumption, True, "ESTIMATED modelling assumption (not lender policy)"
#     ex = p.get("existing_monthly_emi") or 0
#     rmin, rmax = num(R["rate_min"]), num(R["rate_max"])
#     rate_status = "KNOWN" if rmax is not None else ("CONFLICTING" if any(r["status"]=="CONFLICTING" for r in R["rate_max"]) else "UNKNOWN")
#     headroom = (cap_r * inc - ex) if inc is not None and cap_r is not None else None
#     if cap_r is None:
#         notes.append("Affordability estimate disabled or unavailable; no assumed EMI cap applied.")
#     if headroom is not None and headroom <= 0:
#         if not est and usable(R["emi_nmi_max_ratio"]): fail("EMI_NMI_EXCEEDED", f"existing EMI {ex:g} already >= {cap_r:.0%} of income", usable(R["emi_nmi_max_ratio"]))
#         else: notes.append(f"WARNING: under assumed {cap_r:.0%} obligation cap there is no EMI headroom (estimate, not a rejection)")
#     max_amt, amt_basis = None, None
#     amt_cap = num(R["amount_max"])
#     if headroom is not None and headroom > 0 and tenure and rmax is not None:
#         max_amt = pv(headroom, rmax, tenure); amt_basis = f"PV(headroom {headroom:,.0f} @ rate_max {rmax:g}% / {tenure:g}m) using {cap_src}"
#         if amt_cap is not None and amt_cap < max_amt: max_amt, amt_basis = amt_cap, f"published amount_max {amt_cap:,.0f}"
#     elif amt_cap is not None and rmax is None:
#         notes.append(f"affordability amount not computable (rate {rate_status}); only published cap {amt_cap:,.0f} known")
#     if max_amt is not None and p.get("requested_amount") and p["requested_amount"] > max_amt: notes.append(f"requested {p['requested_amount']:,.0f} exceeds estimate {max_amt:,.0f}")
#     # --- non-blocking unknowns that are relevant to this applicant
#     chk = {"min_current_job_months": p.get("current_job_months"), "min_total_experience_months": p.get("total_experience_months"),
#            "min_business_vintage_months": p.get("business_vintage_months") if p.get("employment_type") == "self_employed" else None, "city_restrictions": p.get("city")}
#     for k, v in chk.items():
#         if v is not None and not usable(R[k]): unknowns.append(f"{k} not published/found -> not evaluated")
#     for k in ("foir_max", "income_multiple_max"):
#         if not usable(R[k]): unknowns.append(f"{k} not published/found -> not evaluated")
#     if any('researched product covers' in b for b in blocking): fails = []; passed = []  # product-scope mismatch: rules for this applicant type were not researched, so no hard rejection
#     # --- status
#     if fails: status = "NOT_ELIGIBLE"
#     elif blocking: status = "INSUFFICIENT_INFORMATION"
#     else: status = "POTENTIALLY_ELIGIBLE"
#     out = dict(lender_id=lender["lender_id"], brand=lender["brand_name"], status=status, passed_rules=passed, missing_applicant_inputs=sorted(set(missing)), rejection_reasons=fails,
#                insufficient_information_reasons=blocking if status != "NOT_ELIGIBLE" else [],
#                max_amount_estimate_inr=round(max_amt) if (max_amt and status == "POTENTIALLY_ELIGIBLE") else None, max_amount_basis=amt_basis if status == "POTENTIALLY_ELIGIBLE" else None,
#                rate_range_pct=[rmin, rmax] if (rmax is not None and status == "POTENTIALLY_ELIGIBLE") else None, rate_status=rate_status,
#                tenure_months_range=[tmin, perm_max] if perm_max is not None else None, tenure_used_months=tenure,
#                est_emi_for_requested_inr=[round(emi(p["requested_amount"], rmin, tenure)), round(emi(p["requested_amount"], rmax, tenure))] if (status == "POTENTIALLY_ELIGIBLE" and rmin is not None and rmax is not None and tenure and p.get("requested_amount")) else None,
#                notes=notes, unknowns_not_evaluated=unknowns)
#     return out
# def lender_bank(l): return {"L02": "HDFC Bank", "L01": "SBI"}.get(l["lender_id"], "")

# def recommend(res):
#     ok = [r for r in res if r["status"] == "POTENTIALLY_ELIGIBLE"
#           and r["rate_range_pct"] and len(r["rate_range_pct"]) == 2
#           and all(isinstance(v, (int, float)) and math.isfinite(v)
#                   for v in r["rate_range_pct"])]
#     if len(ok) < 2: return {"recommended": None, "why": f"Not enough comparable evidence: {len(ok)} potentially-eligible lender(s) with a published rate range; need >=2 to compare."}
#     b = min(ok, key=lambda r: (r["rate_range_pct"][1], r["rate_range_pct"][0]))
#     return {"recommended": b["lender_id"], "why": "Lowest published maximum rate among comparable potentially-eligible lenders; applicant-specific quote not known."}

# def main():
#     rules, lenders = load()
#     with open(f"{B}/tests/profiles.json", encoding="utf-8-sig") as handle:
#         profiles = json.load(handle)
#     cap = assumed_cap()
#     results = []
#     for p in profiles:
#         res = [evaluate(p["inputs"], l, rules, cap) for l in lenders]
#         results.append(dict(profile_id=p["profile_id"], purpose=p["purpose"], inputs=p["inputs"], summary=dict(collections.Counter(r["status"] for r in res)), recommendation=recommend(res), lenders=res))
#     with open(f"{B}/tests/results.json", "w", encoding="utf-8") as handle:
#         json.dump(results, handle, indent=1)
#     with open(f"{B}/tests/results_flat.csv", "w", newline="", encoding="utf-8") as f:
#         wr = csv.writer(f); wr.writerow(["profile_id", "lender_id", "brand", "status", "rejection_codes", "reasons", "max_amount_inr", "rate_pct", "tenure_months", "notes"])
#         for r in results:
#             for l in r["lenders"]:
#                 wr.writerow([r["profile_id"], l["lender_id"], l["brand"], l["status"], ";".join(x["code"] for x in l["rejection_reasons"]),
#                              " | ".join([x["reason"] for x in l["rejection_reasons"]] + l["insufficient_information_reasons"]), l["max_amount_estimate_inr"] or "",
#                              "-".join(map(str, l["rate_range_pct"])) if l["rate_range_pct"] else l["rate_status"], l["tenure_used_months"] or "", " | ".join(l["notes"])])
#     print("wrote results for", len(results), "profiles")
# if __name__ == "__main__": main()




"""Deterministic rule engine. Usage: python engine/engine.py  (reads tests/profiles.json, writes tests/results.json + results_flat.csv)"""
import csv, json, os, collections, math
from pathlib import Path
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
HARD = {"VERIFIED_OFFICIAL", "VERIFIED_SECONDARY", "OBSERVED_IN_CALCULATOR"}
_UNSET = object()


def assumed_cap(data_dir=None):
    directory = Path(data_dir) if data_dir is not None else Path(B) / "data"
    with (directory / "model_assumptions.json").open(encoding="utf-8-sig") as handle:
        config = json.load(handle)
    policy = config.get("global_affordability_assumption",
                        config.get("affordability_assumption", {}))
    if not isinstance(policy, dict):
        raise ValueError("Affordability assumption must be a JSON object")
    if policy.get("enabled", policy.get("enabled_by_default", True)) is False:
        return None
    value = policy.get("emi_to_income_cap", policy.get("optional_total_emi_to_net_income_cap"))
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("Affordability cap must be a number, not a boolean")
    cap = float(value)
    if not math.isfinite(cap) or not 0 < cap <= 1:
        raise ValueError("Affordability cap must be finite and between 0 and 1")
    return cap


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


def load(data_dir=None):
    directory = Path(data_dir) if data_dir is not None else Path(B) / "data"
    lenders = _read_csv(directory / "lenders.csv", {"lender_id", "brand_name"})
    rule_rows = _read_csv(directory / "lender_rules_detailed.csv",
                         {"rule_id", "lender_id", "rule_key", "applicant_category",
                          "status", "value", "source_ids"})
    if not lenders:
        raise ValueError("lenders.csv contains no lenders")
    ids = set()
    for lender in lenders:
        lid = lender["lender_id"]
        if not lid or lid in ids:
            raise ValueError(f"lenders.csv: blank or duplicate lender_id {lid!r}")
        ids.add(lid)
    rules = collections.defaultdict(lambda: collections.defaultdict(list))
    seen_rules = set()
    for row in rule_rows:
        if not row["rule_id"] or row["rule_id"] in seen_rules:
            raise ValueError(f"lender_rules_detailed.csv: blank/duplicate rule_id {row['rule_id']!r}")
        if row["lender_id"] not in ids:
            raise ValueError(f"lender_rules_detailed.csv: unknown lender_id {row['lender_id']!r}")
        if not row["rule_key"] or not row["status"]:
            raise ValueError(f"lender_rules_detailed.csv: missing key/status in {row['rule_id']}")
        seen_rules.add(row["rule_id"])
        rules[row["lender_id"]][row["rule_key"]].append(row)
    for lid in ids:
        rules[lid]
    return rules, lenders


def usable(rs):  # rows that carry a usable hard value
    return [r for r in rs if r["status"] in HARD and r["value"] != ""]
def num(rs):
    u = usable(rs); return float(u[0]["value"]) if u else None
def emi(p, rate, n):
    r = rate / 1200
    return p / n if r == 0 else p * r * (1 + r) ** n / ((1 + r) ** n - 1)
def pv(e, rate, n):
    r = rate / 1200
    return e * n if r == 0 else e * ((1 + r) ** n - 1) / (r * (1 + r) ** n)

def evaluate(p, lender, rules, cap_assumption=_UNSET):
    if cap_assumption is _UNSET: cap_assumption = assumed_cap()
    R = rules[lender["lender_id"]]; fails, blocking, notes, unknowns = [], [], [], []
    passed, missing = [], []
    def ok(code, msg, rs): passed.append({"code": code, "detail": msg, "evidence_status": sorted({r["status"] for r in rs}), "rule_ids": [r["rule_id"] for r in rs]})
    def fail(code, msg, rs): fails.append({"code": code, "reason": msg, "evidence_status": sorted({r["status"] for r in rs}), "rule_ids": [r["rule_id"] for r in rs]})
    # --- applicant inputs missing
    for f in ("age", "employment_type", "net_monthly_income", "cibil_score"):
        if p.get(f) is None: blocking.append(f"applicant input missing: {f}"); missing.append(f)
    if blocking and p.get("cibil_score") is None and p.get("age") is None: pass
    # --- blocking-rule availability
    scope = usable(R["employment_scope"])
    if not scope: blocking.append("employment scope rule UNKNOWN")
    elif p.get("employment_type") and p["employment_type"] not in scope[0]["value"].split(";"):
        blocking.append(f"researched product covers '{scope[0]['value']}' only; '{p['employment_type']}' rules not researched")
    if not usable(R["min_age"]): blocking.append("min_age UNKNOWN")
    if not usable(R["max_age_application"]) and not usable(R["max_age_at_maturity"]): blocking.append("max age rule UNKNOWN")
    if not usable(R["min_cibil"]): blocking.append("min_cibil " + ("CONFLICTING" if any(r["status"]=="CONFLICTING" for r in R["min_cibil"]) else "UNKNOWN"))
    mi = R["min_income"]
    if not usable(mi): blocking.append("min_income " + ("CONFLICTING" if any(r["status"]=="CONFLICTING" for r in mi) else "UNKNOWN"))
    # --- hard checks (verified/observed rules only)
    age, cibil, inc = p.get("age"), p.get("cibil_score"), p.get("net_monthly_income")
    mn = num(R["min_age"])
    if age is not None and mn is not None and age < mn: fail("AGE_BELOW_MIN", f"age {age} < min {mn:g}", usable(R["min_age"]))
    elif age is not None and mn is not None: ok("AGE_MIN", f"age {age:g} >= min {mn:g}", usable(R["min_age"]))
    ma = num(R["max_age_application"])
    if age is not None and ma is not None and age > ma: fail("AGE_ABOVE_MAX", f"age {age} > max {ma:g} at application", usable(R["max_age_application"]))
    elif age is not None and ma is not None: ok("AGE_MAX", f"age {age:g} <= max {ma:g} at application", usable(R["max_age_application"]))
    mc = num(R["min_cibil"])
    if cibil is not None and mc is not None and cibil < mc: fail("CIBIL_BELOW_MIN", f"score {cibil} < min {mc:g}", usable(R["min_cibil"]))
    elif cibil is not None and mc is not None: ok("CIBIL_MIN", f"score {cibil:g} >= min {mc:g}", usable(R["min_cibil"]))
    sa = usable(R["salary_account_required"])
    bank = p.get("salary_account_bank")
    if sa and bank is None and p.get("employment_type") in ("salaried", None):
        blocking.append("applicant input missing: salary_account_bank"); missing.append("salary_account_bank")
    elif sa and bank != sa[0]["value"] and p.get("employment_type") in ("salaried", None):
        fail("SALARY_ACCOUNT_REQUIRED", f"requires salary account with {sa[0]['value']}; applicant has {bank}", sa)
    elif sa: ok("SALARY_ACCOUNT", f"salary account with {sa[0]['value']} held", sa)
    u = usable(mi)   # income: category-specific
    if u and inc is not None and len(u) > 1 and bank is None:
        blocking.append("applicant input missing: salary_account_bank"); missing.append("salary_account_bank")
    elif u and inc is not None:
        if len(u) > 1:  # HDFC-style tiers
            cat = "salary_account_holder" if p.get("salary_account_bank") == lender_bank(lender) else "non_salary_account"
            u = [r for r in u if r["applicant_category"] == cat] or u
        thr = float(u[0]["value"])
        if inc < thr: fail("INCOME_BELOW_MIN", f"net income {inc:g} < min {thr:g} ({u[0]['applicant_category']})", u)
        else: ok("INCOME_MIN", f"net income {inc:g} >= min {thr:g} ({u[0]['applicant_category']})", u)
    # --- tenure / maturity
    tmin, tmax = num(R["tenure_min"]), num(R["tenure_max"]); mat = num(R["max_age_at_maturity"])
    perm_max = tmax
    if mat is not None and age is not None:
        cap = int((mat - age) * 12)
        perm_max = cap if perm_max is None else min(perm_max, cap)
        if tmin is not None and cap < tmin: fail("AGE_AT_MATURITY", f"age {age} leaves {cap} months to age {mat:g}; min tenure {tmin:g}", usable(R["max_age_at_maturity"]))
        else: ok("AGE_AT_MATURITY", f"{cap} months remain to age {mat:g}", usable(R["max_age_at_maturity"]))
    pref = p.get("preferred_tenure_months")
    tenure = None
    if perm_max is not None and pref is not None:
        tenure = min(pref, perm_max)
        if tmin is not None: tenure = max(tenure, tmin) if tenure >= tmin else None
        if pref > perm_max: notes.append(f"preferred tenure {pref} reduced to {perm_max:g} months (max tenure / age at maturity)")
    # --- affordability
    cap_r = num(R["emi_nmi_max_ratio"]); cap_src = "published (" + (usable(R["emi_nmi_max_ratio"])[0]["status"] if cap_r else "") + ")" if cap_r else None
    est = False
    if cap_r is None: cap_r, est, cap_src = cap_assumption, True, "ESTIMATED modelling assumption (not lender policy)"
    ex = p.get("existing_monthly_emi") or 0
    rmin, rmax = num(R["rate_min"]), num(R["rate_max"])
    rate_status = "KNOWN" if rmax is not None else ("CONFLICTING" if any(r["status"]=="CONFLICTING" for r in R["rate_max"]) else "UNKNOWN")
    headroom = (cap_r * inc - ex) if inc is not None and cap_r is not None else None
    if cap_r is None:
        notes.append("Affordability estimate disabled or unavailable; no assumed EMI cap applied.")
    if headroom is not None and headroom <= 0:
        if not est and usable(R["emi_nmi_max_ratio"]): fail("EMI_NMI_EXCEEDED", f"existing EMI {ex:g} already >= {cap_r:.0%} of income", usable(R["emi_nmi_max_ratio"]))
        else: notes.append(f"WARNING: under assumed {cap_r:.0%} obligation cap there is no EMI headroom (estimate, not a rejection)")
    max_amt, amt_basis = None, None
    amt_cap = num(R["amount_max"])
    if headroom is not None and headroom > 0 and tenure and rmax is not None:
        max_amt = pv(headroom, rmax, tenure); amt_basis = f"PV(headroom {headroom:,.0f} @ rate_max {rmax:g}% / {tenure:g}m) using {cap_src}"
        if amt_cap is not None and amt_cap < max_amt: max_amt, amt_basis = amt_cap, f"published amount_max {amt_cap:,.0f}"
    elif amt_cap is not None and rmax is None:
        notes.append(f"affordability amount not computable (rate {rate_status}); only published cap {amt_cap:,.0f} known")
    if max_amt is not None and p.get("requested_amount") and p["requested_amount"] > max_amt: notes.append(f"requested {p['requested_amount']:,.0f} exceeds estimate {max_amt:,.0f}")
    # --- non-blocking unknowns that are relevant to this applicant
    chk = {"min_current_job_months": p.get("current_job_months"), "min_total_experience_months": p.get("total_experience_months"),
           "min_business_vintage_months": p.get("business_vintage_months") if p.get("employment_type") == "self_employed" else None, "city_restrictions": p.get("city")}
    for k, v in chk.items():
        if v is not None and not usable(R[k]): unknowns.append(f"{k} not published/found -> not evaluated")
    for k in ("foir_max", "income_multiple_max"):
        if not usable(R[k]): unknowns.append(f"{k} not published/found -> not evaluated")
    if any('researched product covers' in b for b in blocking): fails = []; passed = []  # product-scope mismatch: rules for this applicant type were not researched, so no hard rejection
    # --- status
    if fails: status = "NOT_ELIGIBLE"
    elif blocking: status = "INSUFFICIENT_INFORMATION"
    else: status = "POTENTIALLY_ELIGIBLE"
    out = dict(lender_id=lender["lender_id"], brand=lender["brand_name"], status=status, passed_rules=passed, missing_applicant_inputs=sorted(set(missing)), rejection_reasons=fails,
               insufficient_information_reasons=blocking if status != "NOT_ELIGIBLE" else [],
               max_amount_estimate_inr=round(max_amt) if (max_amt and status == "POTENTIALLY_ELIGIBLE") else None, max_amount_basis=amt_basis if status == "POTENTIALLY_ELIGIBLE" else None,
               rate_range_pct=[rmin, rmax] if (rmax is not None and status == "POTENTIALLY_ELIGIBLE") else None, rate_status=rate_status,
               tenure_months_range=[tmin, perm_max] if perm_max is not None else None, tenure_used_months=tenure,
               est_emi_for_requested_inr=[round(emi(p["requested_amount"], rmin, tenure)), round(emi(p["requested_amount"], rmax, tenure))] if (status == "POTENTIALLY_ELIGIBLE" and rmin is not None and rmax is not None and tenure and p.get("requested_amount")) else None,
               notes=notes, unknowns_not_evaluated=unknowns)
    return out
def lender_bank(l): return {"L02": "HDFC Bank", "L01": "SBI"}.get(l["lender_id"], "")

def recommend(res):
    ok = [r for r in res if r["status"] == "POTENTIALLY_ELIGIBLE"
          and r["rate_range_pct"] and len(r["rate_range_pct"]) == 2
          and all(isinstance(v, (int, float)) and math.isfinite(v)
                  for v in r["rate_range_pct"])]
    if len(ok) < 2: return {"recommended": None, "why": f"Not enough comparable evidence: {len(ok)} potentially-eligible lender(s) with a published rate range; need >=2 to compare."}
    b = min(ok, key=lambda r: (r["rate_range_pct"][1], r["rate_range_pct"][0]))
    return {"recommended": b["lender_id"], "why": "Lowest published maximum rate among comparable potentially-eligible lenders; applicant-specific quote not known."}

def main():
    rules, lenders = load()
    with open(f"{B}/tests/profiles.json", encoding="utf-8-sig") as handle:
        profiles = json.load(handle)
    cap = assumed_cap()
    results = []
    for p in profiles:
        res = [evaluate(p["inputs"], l, rules, cap) for l in lenders]
        results.append(dict(profile_id=p["profile_id"], purpose=p["purpose"], inputs=p["inputs"], summary=dict(collections.Counter(r["status"] for r in res)), recommendation=recommend(res), lenders=res))
    with open(f"{B}/tests/results.json", "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=1)
    with open(f"{B}/tests/results_flat.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f); wr.writerow(["profile_id", "lender_id", "brand", "status", "rejection_codes", "reasons", "max_amount_inr", "rate_pct", "tenure_months", "notes"])
        for r in results:
            for l in r["lenders"]:
                wr.writerow([r["profile_id"], l["lender_id"], l["brand"], l["status"], ";".join(x["code"] for x in l["rejection_reasons"]),
                             " | ".join([x["reason"] for x in l["rejection_reasons"]] + l["insufficient_information_reasons"]), l["max_amount_estimate_inr"] or "",
                             "-".join(map(str, l["rate_range_pct"])) if l["rate_range_pct"] else l["rate_status"], l["tenure_used_months"] or "", " | ".join(l["notes"])])
    print("wrote results for", len(results), "profiles")
if __name__ == "__main__": main()