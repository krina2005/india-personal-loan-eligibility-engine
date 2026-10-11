from fastapi import APIRouter, HTTPException
from ..core.config import data_dir
from ..schemas.applicant import ApplicantProfile, EligibilityResponse
from ..services import data_service as ds, eligibility_service as svc

router = APIRouter(prefix="/api")

@router.get("/health")
def health():
    d = data_dir(); miss = ds.missing_files(d); ok = not miss
    if ok:
        try: ds.dataset(); ds.engine()
        except ds.DataUnavailable as e: ok, miss = False, [str(e)]
    return {"status": "ok" if ok else "degraded", "data_loaded": ok, "problems": miss}

@router.get("/lenders")
def lenders(): return {"lenders": svc.lenders(), "coverage": svc.coverage()}

@router.get("/lenders/{lender_id}")
def lender(lender_id: str):
    d = svc.lender_detail(lender_id)
    if d is None: raise HTTPException(404, "Lender not found")
    return d

@router.get("/coverage")
def coverage(): return svc.coverage()

@router.get("/metadata")
def metadata(): return svc.metadata()

@router.post("/eligibility", response_model=EligibilityResponse)
def eligibility(profile: ApplicantProfile): return svc.assess(profile.model_dump())
