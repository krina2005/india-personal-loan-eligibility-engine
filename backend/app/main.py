import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .api.routes import router
from .core.config import cors_origins
from .services.data_service import DataUnavailable

log = logging.getLogger("loanlens")
app = FastAPI(title="LoanLens India API", version="1.0.0", description="Indicative personal-loan eligibility from documented lender rules.")
app.add_middleware(CORSMiddleware, allow_origins=cors_origins(), allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
app.include_router(router)

@app.exception_handler(RequestValidationError)
async def _invalid(_: Request, exc: RequestValidationError):
    details = [{"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"error": "invalid_input", "details": details})   # never echo submitted values

@app.exception_handler(DataUnavailable)
async def _nodata(_: Request, exc: DataUnavailable):
    log.error("data unavailable: %s", exc)
    return JSONResponse(status_code=503, content={"error": "data_unavailable", "message": "Lender data is temporarily unavailable."})

@app.exception_handler(Exception)
async def _boom(_: Request, exc: Exception):
    log.exception("unhandled error")
    return JSONResponse(status_code=500, content={"error": "internal_error", "message": "Something went wrong. Please try again."})
