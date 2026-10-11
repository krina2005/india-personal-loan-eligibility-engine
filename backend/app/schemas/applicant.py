from typing import Literal, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

class ApplicantProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    age: float = Field(ge=18, le=100, description="years")
    employment_type: Literal["salaried", "self_employed"]
    net_monthly_income: float = Field(ge=0, le=10_000_000, description="INR/month")
    existing_monthly_emi: float = Field(ge=0, le=10_000_000, description="INR/month")
    requested_amount: float = Field(ge=1000, le=100_000_000, description="INR")
    preferred_tenure_months: int = Field(ge=3, le=120)
    cibil_score: Optional[int] = Field(default=None, ge=300, le=900)
    salary_account_bank: Optional[Literal["HDFC Bank", "SBI", "OTHER"]] = None
    city: Optional[str] = Field(default=None, max_length=80)
    employer_category: Optional[str] = Field(default=None, max_length=80)
    current_job_months: Optional[int] = Field(default=None, ge=0, le=600)
    total_experience_months: Optional[int] = Field(default=None, ge=0, le=720)
    business_vintage_months: Optional[int] = Field(default=None, ge=0, le=720)

class Reason(BaseModel):
    code: str; reason: str; evidence_status: list[str]; rule_ids: list[str]
class Passed(BaseModel):
    code: str; detail: str; evidence_status: list[str]; rule_ids: list[str]
class Gap(BaseModel):
    rule_key: str; status: str; rule_ids: list[str]
class Estimate(BaseModel):
    indicative: bool = True
    max_amount_inr: Optional[int] = None; max_amount_basis: Optional[str] = None
    rate_range_pct: Optional[list[float]] = None; tenure_months_range: Optional[list[float]] = None; tenure_used_months: Optional[float] = None
    emi_for_requested_inr: Optional[list[int]] = None; total_repayment_for_requested_inr: Optional[list[int]] = None
    limitations: list[str] = []
class LenderResult(BaseModel):
    lender_id: str; brand_name: str; legal_name: str; category: str; product: str; product_url: str; research_depth: str; evidence_level: str
    status: Literal["POTENTIALLY_ELIGIBLE", "NOT_ELIGIBLE", "INSUFFICIENT_INFORMATION"]
    explanation: str
    rejection_reasons: list[Reason]; passed_rules: list[Passed]; missing_applicant_inputs: list[str]; rule_gaps: list[Gap]
    insufficient_information_reasons: list[str]; estimate: Optional[Estimate] = None
    notes: list[str]; unknowns_not_evaluated: list[str]; source_ids: list[str]
class Overall(BaseModel):
    status: str; headline: str; counts: dict[str, int]; recommendation: dict[str, Any]; disclaimer: str; assumptions: dict[str, Any]; researched_lenders: int
class EligibilityResponse(BaseModel):
    overall: Overall; lenders: list[LenderResult]
