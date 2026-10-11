# LoanLens India — personal-loan eligibility web app

Full-stack app around a deterministic, source-traceable rule engine. **No ML, no LLM, no external APIs.** Results are indicative, never an approval.

**Status (honest):** only 3 of 20 lenders (SBI, HDFC Bank, Bajaj Finance) have researched rules; the other 17 return `INSUFFICIENT_INFORMATION`. The UI shows this everywhere. See `data_quality_report.md`.

## Architecture
```
React (Vite+TS+Tailwind)  --HTTP/JSON-->  FastAPI (backend/app)  --imports-->  engine/engine.py  --reads-->  data/*.csv|json
```
`POST /api/eligibility` validates the profile (Pydantic), calls `engine.evaluate()` for each lender, then adds explanations, gaps, EMI/total-repayment arithmetic and a recommendation guard. No eligibility logic lives in the API or the frontend.

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | app + data-load status |
| `GET /api/lenders`, `GET /api/lenders/{id}` | directory with coverage; rules + sources per lender |
| `GET /api/coverage` | coverage stats computed from the CSVs (landing page) |
| `GET /api/metadata` | form fields built from `data/input_variables.csv` + limits |
| `POST /api/eligibility` | run the engine |

## Structure
`frontend/` (pages: Landing, Assessment, Results, LenderDetail, Directory) · `backend/app/{api,schemas,services,core}` · `backend/tests` · `engine/` · `data/` · `tests/` (original research profiles/results/validator).

## Setup (Windows PowerShell, from the repo root)
Prerequisites: Python 3.10+, Node 18+.
```powershell
# Terminal 1 - backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env   # optional; env vars are read from the shell
uvicorn app.main:app --reload --port 8000 --app-dir backend

# Terminal 2 - frontend
cd frontend
Copy-Item .env.example .env
npm install
npm run dev        # http://localhost:5173
```
If PowerShell blocks activation: `Set-ExecutionPolicy -Scope Process Bypass`.

## Tests
```powershell
python tests\validate.py                 # data-quality checks (original)
python engine\engine.py                  # regenerates tests/results.json
pytest backend\tests                     # engine/service + API tests
cd frontend; npm run build                # tsc type-check + production build
```
`backend/tests/test_service.py` also runs without pytest: `python backend\tests\test_service.py`.

## Adding a lender / rule / source
1. Add the source row to `engine/build_data.py` (`S`), the lender to `L`, and rules to `R` as `(lender, key, category, value, unit, status, source_ids, extracted_text, notes)`.
2. `python engine/build_data.py` (regenerates all CSVs; missing core keys become `UNKNOWN`), then `python tests/validate.py` and the tests.
Rule keys used by the engine: `min_age, max_age_application, max_age_at_maturity, min_income (category-specific), min_cibil, employment_scope, salary_account_required, emi_nmi_max_ratio, amount_max, rate_min/max, tenure_min/max`. Statuses: VERIFIED_OFFICIAL, VERIFIED_SECONDARY, OBSERVED_IN_CALCULATOR, ESTIMATED, UNKNOWN, CONFLICTING, NOT_APPLICABLE. Never copy one lender's threshold to another.

## Engine changes made for the app
Additive only (verified: the stored statuses for all 14 profiles are unchanged): `passed_rules` and `missing_applicant_inputs` in output; `load(data_dir)`/`assumed_cap()` accept a data directory; a missing salary-account answer now yields "missing input" instead of a rejection.

## Security / deployment
CORS is limited to `CORS_ORIGINS` (wildcards are ignored). Validation errors never echo submitted values; 500s return a generic message. No auth, DB or secrets are used. For production: serve the built frontend (`npm run build`) from a static host, set `VITE_API_BASE_URL` and `CORS_ORIGINS`, run uvicorn behind HTTPS.


## Extraction
Extract this ZIP's `pl_eligibility/` folder INTO your existing project folder (merge, do not replace). It adds `backend/`, `frontend/`, `README_APP.md`, `gitignore_append.txt` and `OPTIONAL_engine_patched/engine.py`. It does not contain `data/`, `engine/` or `tests/`.
The backend needs the patched engine: if your `engine/engine.py` lacks `assumed_cap`, back it up and copy `OPTIONAL_engine_patched/engine.py` over it.
