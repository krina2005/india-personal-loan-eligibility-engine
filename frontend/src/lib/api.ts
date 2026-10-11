import type { Coverage, EligibilityResponse, LenderDetail, LenderInfo, Metadata, Profile } from "../types/api";
const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ?? "http://localhost:8000";
export class ApiError extends Error { status: number; details: { field: string; message: string }[];
  constructor(msg: string, status: number, details: { field: string; message: string }[] = []) { super(msg); this.status = status; this.details = details; } }
async function req<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try { res = await fetch(BASE + path, { headers: { "Content-Type": "application/json" }, ...init }); }
  catch { throw new ApiError("Cannot reach the server. Is the backend running?", 0); }
  if (!res.ok) {
    let body: { error?: string; message?: string; details?: { field: string; message: string }[] } = {};
    try { body = await res.json(); } catch { /* ignore */ }
    throw new ApiError(body.message ?? (res.status === 422 ? "Some inputs are invalid." : "Request failed."), res.status, body.details ?? []);
  }
  return res.json() as Promise<T>;
}
export const api = {
  metadata: () => req<Metadata>("/api/metadata"),
  coverage: () => req<Coverage>("/api/coverage"),
  lenders: () => req<{ lenders: LenderInfo[]; coverage: Coverage }>("/api/lenders"),
  detail: (id: string) => req<LenderDetail>(`/api/lenders/${encodeURIComponent(id)}`),
  assess: (p: Profile, numeric: Set<string>) => {
    const body: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(p)) { if (v === "") continue; body[k] = numeric.has(k) ? Number(v) : v; }
    return req<EligibilityResponse>("/api/eligibility", { method: "POST", body: JSON.stringify(body) });
  },
};
