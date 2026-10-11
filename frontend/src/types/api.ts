export type Status = "POTENTIALLY_ELIGIBLE" | "NOT_ELIGIBLE" | "INSUFFICIENT_INFORMATION";
export interface FieldMeta {
  name: string; label: string; type: string; unit: string; description: string; required: boolean; section: string;
  kind: "number" | "text" | "select"; min?: number; max?: number; step?: number; options?: [string, string][]; hint?: string; used_by: string;
}
export interface Metadata { sections: { id: string; label: string }[]; fields: FieldMeta[] }
export interface Coverage {
  lenders_total: number; lenders_official_evidence: number; lenders_secondary_only: number; lenders_no_evidence: number;
  lenders_with_conflicts: number; lenders_with_unknown_rules: number; rules_total: number; rules_by_status: Record<string, number>;
  rules_unknown: number; sources_total: number; sources_by_quality: Record<string, number>; source_dates: { earliest: string | null; latest: string | null }; note: string;
}
export interface LenderInfo {
  lender_id: string; brand_name: string; legal_name: string; category: string; product: string; product_url: string; offers_pl_evidence: string;
  research_depth: string; evidence_level: string; rules_total: number; rules_known: number; rules_unknown: number; rules_conflicting: number;
}
export interface Reason { code: string; reason: string; evidence_status: string[]; rule_ids: string[] }
export interface Passed { code: string; detail: string; evidence_status: string[]; rule_ids: string[] }
export interface Gap { rule_key: string; status: string; rule_ids: string[] }
export interface Estimate {
  indicative: boolean; max_amount_inr: number | null; max_amount_basis: string | null; rate_range_pct: number[] | null;
  tenure_months_range: number[] | null; tenure_used_months: number | null; emi_for_requested_inr: number[] | null;
  total_repayment_for_requested_inr: number[] | null; limitations: string[];
}
export interface LenderResult {
  lender_id: string; brand_name: string; legal_name: string; category: string; product: string; product_url: string; research_depth: string; evidence_level: string;
  status: Status; explanation: string; rejection_reasons: Reason[]; passed_rules: Passed[]; missing_applicant_inputs: string[]; rule_gaps: Gap[];
  insufficient_information_reasons: string[]; estimate: Estimate | null; notes: string[]; unknowns_not_evaluated: string[]; source_ids: string[];
}
export interface EligibilityResponse {
  overall: { status: string; headline: string; counts: { potentially_eligible: number; not_eligible: number; insufficient_information: number };
    recommendation: { lender_id: string | null; why: string }; disclaimer: string; assumptions: Record<string, unknown>; researched_lenders: number };
  lenders: LenderResult[];
}
export interface Rule { rule_id: string; lender_id: string; rule_key: string; applicant_category: string; value: string; unit: string; status: string; source_ids: string; extracted_text: string; notes: string; date_accessed: string }
export interface Source { source_id: string; url: string; title: string; publisher: string; date_accessed: string; publication_date: string; evidence_quality: string; notes: string }
export interface LenderDetail { lender: LenderInfo; rules: Rule[]; sources: Source[]; dangling_source_ids: string[]; known_rules: number }
export type Profile = Record<string, string>;
