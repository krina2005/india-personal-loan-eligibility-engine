# Personal-Loan Eligibility Dataset & Rule Engine (India) — PARTIAL, honest-gaps edition

**Research date:** 2026-10-10. **Status: incomplete.** Only 3 of 20 shortlisted lenders (SBI, HDFC Bank, Bajaj Finance) have researched rules; the other 17 are in the dataset with every rule `UNKNOWN`. Nothing was invented to fill them. See `data_quality_report.md`.

## 1. Purpose and scope
Personal loans only. Public sources only (search snippets and one page fetch in this session; no logins, no customer data). A deterministic rule engine (no ML) evaluates a profile against 20 lenders.

## 2. How the 20 lenders were chosen — and the limits
I searched for a lender-level personal-loan ranking (CRIF, JM Financial, Equifax, Experian, RBI summaries: sources M01–M06). Only **segment-level** shares were retrievable (e.g. PSB 37.8% / private banks 32.9% / NBFC 24.1% of PL portfolio, Sep-2024; NBFCs 68.7% of active loans — M01). **No credible lender-level top-20 ranking was found, so this list is NOT a ranking and not claimed to be the top 20.** It is an analyst shortlist spanning public banks (4), private banks (8) and NBFCs (8). Fintech platforms were excluded because the actual lender could not be identified in this session. Only SBI, HDFC Bank and Bajaj Finance have verified official personal-loan pages (see `lenders.csv: offers_pl_evidence_status`); the other 17 are `NOT_VERIFIED_THIS_SESSION`. Legal names come from general knowledge, not from fetched sources. Some may not belong in a true top 20; replacing them is a next step.

## 3. Files (all in `data/` unless noted)
| File | One row = | Links |
|---|---|---|
| `lenders.csv` | one selected lender (20 rows) | `lender_id` |
| `lender_rule_summary.csv` | one lender, key rule values + status columns (20 rows, derived from detailed rules) | `lender_id` |
| `lender_rules_detailed.csv` | one rule for one lender/applicant category, with `status`, `source_ids`, extracted text, notes (422 rows) | `lender_id`, `source_ids` -> `sources.csv` |
| `sources.csv` | one source URL with title, publisher, `date_accessed` (ISO), quality, notes | `source_id` |
| `input_variables.csv` | one model input variable (type, unit, source, which lenders use it) | — |
| `model_assumptions.json` | status definitions, the one ESTIMATED affordability assumption, amount formula | — |
| `tests/profiles.json` | 14 fictional profiles | — |
| `tests/results.json`, `tests/results_flat.csv` | engine output per profile x 20 lenders (flat CSV is spreadsheet-friendly) | `profile_id`, `lender_id` |
| `engine/build_data.py`, `engine/engine.py`, `tests/validate.py` | data builder, rule engine, validator | — |

CSV + JSON were chosen: CSV is spreadsheet-reviewable and normalises rules/evidence; JSON holds nested engine output and assumptions.

## 4. Method, sources, conflicts
Source priority: official page > FAQ/calculator > terms/rates > RBI > market research > comparison sites. **Not completed:** no official rate cards, fee schedules, T&Cs, FAQ pages or RBI circulars were read; most official pages were seen only as truncated search snippets (several numbers cut off). Status meanings: `VERIFIED_OFFICIAL`, `VERIFIED_SECONDARY` (comparison site only; still applied as a hard rule but flagged in outputs), `OBSERVED_IN_CALCULATOR`, `ESTIMATED`, `UNKNOWN` (never treated as 0/false/eligible), `CONFLICTING` (engine ignores the value), `NOT_APPLICABLE`.
Conflicts handled: HDFC tenure 72 (official) vs 60 (BankBazaar) -> official; HDFC rate floor 10.90 (official) vs 9.99 (BankBazaar) -> official; SBI max amount 30 lakh (official) vs 20 lakh (BankBazaar) -> official; SBI max age 60 (official) vs <58 (ClearTax) -> official; **SBI interest rate stays CONFLICTING** (3 secondary sources disagree); **Bajaj minimum salary stays CONFLICTING** (25,001 on one page; a second page implies lower salaries but its content could not be extracted).
**Unlisted rules:** the only "hidden" rules surfaced were SBI's EMI/NMI < 50% and CIBIL 750 (from a comparison site, `VERIFIED_SECONDARY`), HDFC's 650 score (comparison site), and a Bajaj statement that its calculator uses city of residence (no thresholds). No FOIR, income multiple, job-tenure, work-experience, employer-category, or city-list rule was found for any lender; they are `UNKNOWN`.

## 5. How the engine uses the data
`python engine/engine.py` reads rules by `lender_id`.
- **NOT_ELIGIBLE** — a verified/observed mandatory rule fails (reason + rule ids returned).
- **INSUFFICIENT_INFORMATION** — a core rule (min age, max age, min income, min CIBIL, employment scope) is UNKNOWN/CONFLICTING, applicant input is missing, or the researched product doesn't cover the applicant type (e.g. self-employed).
- **POTENTIALLY_ELIGIBLE** — known rules pass; never a guarantee. Unevaluated unknowns (job tenure, city, FOIR…) are listed in each output.
Max amount = min(published cap, PV of EMI headroom at the lender's *maximum* published rate over the permitted tenure). Where no lender EMI cap is known, an **ESTIMATED 50% obligation cap** is used for the amount only (never to reject; produces a warning). Rate is a published range, not a quote. A best option is recommended only when >=2 potentially-eligible lenders have comparable published rates — which never happened in the tests.

## 6. Tests
`python engine/engine.py` regenerates `tests/results.json` from `tests/profiles.json` (14 profiles: strong salaried, low score, high EMI, new job, self-employed, ages 20/21/57/61, income 24,999 and 25,000, restricted city, missing bureau score, CIBIL 700/650 boundaries). Outputs are never hand-written. `python tests/validate.py` runs data checks.

## 7. Observations (test dataset only — NOT claims about the Indian market)
Across 14 profiles x 20 lenders = 280 evaluations: {'NOT_ELIGIBLE': 19, 'POTENTIALLY_ELIGIBLE': 9, 'INSUFFICIENT_INFORMATION': 252}. Rejections come only from the 3 researched lenders:
- `SALARY_ACCOUNT_REQUIRED`: 9 lender-profile rejections across 9 of 14 profiles
- `CIBIL_BELOW_MIN`: 6 lender-profile rejections across 3 of 14 profiles
- `INCOME_BELOW_MIN`: 3 lender-profile rejections across 3 of 14 profiles
- `AGE_BELOW_MIN`: 3 lender-profile rejections across 1 of 14 profiles
- `EMI_NMI_EXCEEDED`: 1 lender-profile rejections across 1 of 14 profiles
- `AGE_AT_MATURITY`: 1 lender-profile rejections across 1 of 14 profiles
- `AGE_ABOVE_MAX`: 1 lender-profile rejections across 1 of 14 profiles
Interpretation: results are dominated by the data gap — 17 lenders always return `INSUFFICIENT_INFORMATION`. The fact that `SALARY_ACCOUNT_REQUIRED` is the most common rejection is an artifact of my profile mix (most profiles have a non-SBI salary account) and says nothing about real applicants. Lender differences seen in the researched rules only: Bajaj tolerates ages to 80 at maturity vs SBI 60; CIBIL cut-offs 685 (Bajaj, official) vs 650 (HDFC, secondary) vs 750 (SBI, secondary); HDFC income threshold depends on salary-account status (25,000 vs 50,000).

## 8. Limitations / next steps
1. Research the 17 unresearched lenders (official page, FAQ, calculator, rate card, fee schedule) and verify they offer personal loans. 2. Replace comparison-site (`VERIFIED_SECONDARY`) values with official ones; resolve SBI rate and Bajaj minimum salary. 3. Obtain a real lender-level market ranking (e.g. CRIF/RBI lender-wise PL data) and re-select. 4. Add self-employed, city, tenure-with-employer, score-based rate bands, processing fees. 5. Applicant-specific rate quotes are not modelled. 6. This estimates eligibility against public info only; lenders decide actual approval.
