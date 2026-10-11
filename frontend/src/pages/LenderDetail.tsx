import { ArrowLeft, CheckCircle2, ExternalLink, HelpCircle, XCircle } from "lucide-react";
import type { ReactNode } from "react";
import { api } from "../lib/api";
import { pct, range, rupees } from "../lib/format";
import { useAsync } from "../hooks/useAsync";
import { ErrorBox, EvidenceBadge, Notice, RuleStatus, Skeleton, StatusBadge } from "../components/ui";
import type { EligibilityResponse } from "../types/api";

const Sec = ({ title, children }: { title: string; children: ReactNode }) => <section className="card p-5 mt-5"><h2 className="text-lg mb-3">{title}</h2>{children}</section>;

export default function LenderDetail({ id, result }: { id: string; result: EligibilityResponse | null }) {
  const d = useAsync(() => api.detail(id), [id]);
  const r = result?.lenders.find((l) => l.lender_id === id);
  if (d.loading) return <div className="mx-auto max-w-4xl px-5 py-10 space-y-4"><Skeleton className="h-10 w-1/2" /><Skeleton className="h-48" /></div>;
  if (d.error || !d.data) return <div className="mx-auto max-w-4xl px-5 py-10"><ErrorBox message={d.error ?? "Lender not found."} /></div>;
  const { lender: L, rules, sources } = d.data; const e = r?.estimate;
  const srcById = Object.fromEntries(sources.map((s) => [s.source_id, s]));
  return (
    <div className="mx-auto max-w-4xl px-5 py-10 rise">
      <a href={result ? "#/results" : "#/lenders"} className="text-sm text-ink-soft inline-flex items-center gap-1"><ArrowLeft size={15} aria-hidden />Back</a>
      <div className="flex flex-wrap items-start justify-between gap-3 mt-3">
        <div><h1 className="text-3xl">{L.brand_name}</h1><p className="text-sm text-ink-soft">{L.legal_name} · {L.category.replace("_", " ").toLowerCase()}</p>
          <p className="text-sm mt-1">{L.product === "NOT_VERIFIED" ? "Personal-loan product not verified yet" : L.product}{L.product_url && <> · <a className="text-brand-dark underline inline-flex items-center gap-1" href={L.product_url} target="_blank" rel="noreferrer noopener">Product page<ExternalLink size={12} aria-hidden /></a></>}</p></div>
        <div className="flex flex-col items-end gap-2">{r && <StatusBadge status={r.status} />}<EvidenceBadge level={L.evidence_level} /></div>
      </div>

      {r ? <Sec title="How this result was determined"><p className="text-sm">{r.explanation}</p>
        {r.missing_applicant_inputs.length > 0 && <div className="mt-3"><Notice tone="sky"><strong>Missing from your answers:</strong> {r.missing_applicant_inputs.join(", ")}. This is different from an unknown lender rule: you can fix it by providing the value.</Notice></div>}
      </Sec> : <Notice tone="sky">Run an eligibility check to see how you were assessed by this lender. The recorded rules and sources are shown below.</Notice>}

      {r && <>
        <div className="grid md:grid-cols-2 gap-5">
          <Sec title="Passed mandatory rules">{r.passed_rules.length ? <ul className="space-y-2 text-sm">{r.passed_rules.map((p) => <li key={p.code} className="flex gap-2"><CheckCircle2 size={16} className="text-brand mt-0.5 shrink-0" aria-hidden /><span>{p.detail} <span className="text-xs text-ink-mute">({p.evidence_status.join(", ").toLowerCase().replace(/_/g, " ")}; {p.rule_ids.join(", ")})</span></span></li>)}</ul> : <p className="text-sm text-ink-mute">None evaluated.</p>}</Sec>
          <Sec title="Failed mandatory rules">{r.rejection_reasons.length ? <ul className="space-y-2 text-sm">{r.rejection_reasons.map((p) => <li key={p.code} className="flex gap-2"><XCircle size={16} className="text-rose2 mt-0.5 shrink-0" aria-hidden /><span>{p.reason} <span className="text-xs text-ink-mute">({p.evidence_status.join(", ").toLowerCase().replace(/_/g, " ")}; {p.rule_ids.join(", ")})</span></span></li>)}</ul> : <p className="text-sm text-ink-mute">No verified rule failed.</p>}</Sec>
        </div>
        <Sec title="Unknown or conflicting lender rules">{r.rule_gaps.length ? <ul className="space-y-2 text-sm">{r.rule_gaps.map((g) => <li key={g.rule_key} className="flex gap-2 items-start"><HelpCircle size={16} className="text-amber2 mt-0.5 shrink-0" aria-hidden /><span><code className="text-xs">{g.rule_key}</code> <RuleStatus s={g.status} /> <span className="text-xs text-ink-mute">{g.rule_ids.join(", ")}</span></span></li>)}</ul> : <p className="text-sm text-ink-mute">All core rules have values.</p>}
          {r.unknowns_not_evaluated.length > 0 && <details className="mt-3 text-sm"><summary className="cursor-pointer text-ink-soft">Other rules not evaluated ({r.unknowns_not_evaluated.length})</summary><ul className="list-disc pl-5 mt-2 text-ink-soft">{r.unknowns_not_evaluated.map((u) => <li key={u}>{u}</li>)}</ul></details>}</Sec>
        <Sec title="Indicative amount, rate and cost">{e ? <>
          <dl className="grid sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <dt className="text-ink-soft">Maximum amount</dt><dd>{e.max_amount_inr ? rupees(e.max_amount_inr) : "Not computable"}</dd>
            <dt className="text-ink-soft">Published rate range</dt><dd>{pct(e.rate_range_pct)}</dd>
            <dt className="text-ink-soft">Possible tenure</dt><dd>{range(e.tenure_months_range, (n) => `${n} months`)}</dd>
            <dt className="text-ink-soft">EMI for requested amount</dt><dd>{range(e.emi_for_requested_inr, rupees)}</dd>
            <dt className="text-ink-soft">Total repayment</dt><dd>{range(e.total_repayment_for_requested_inr, rupees)}</dd></dl>
          {e.max_amount_basis && <p className="text-xs text-ink-mute mt-3">Basis: {e.max_amount_basis}</p>}
          <ul className="list-disc pl-5 mt-2 text-xs text-ink-mute">{e.limitations.map((x) => <li key={x}>{x}</li>)}</ul></> : <p className="text-sm text-ink-mute">Not shown: the verified rules needed for a reliable estimate are missing, or this lender is not potentially eligible.</p>}
          {r.notes.length > 0 && <ul className="mt-3 text-sm space-y-1">{r.notes.map((n) => <li key={n}>• {n}</li>)}</ul>}</Sec></>}

      <Sec title={`Recorded rules (${rules.length})`}>
        <div className="overflow-x-auto"><table className="w-full text-sm min-w-[640px]"><thead className="text-left text-xs text-ink-mute border-b border-line"><tr><th className="py-2 pr-3">Rule</th><th className="pr-3">Category</th><th className="pr-3">Value</th><th className="pr-3">Status</th><th>Source</th></tr></thead>
          <tbody>{rules.map((x) => <tr key={x.rule_id} className="border-b border-line last:border-0 align-top"><td className="py-2 pr-3"><code className="text-xs">{x.rule_key}</code><div className="text-[11px] text-ink-mute">{x.rule_id}</div></td><td className="pr-3">{x.applicant_category}</td><td className="pr-3">{x.value ? `${x.value} ${x.unit}` : <span className="text-ink-mute">—</span>}{x.notes && <div className="text-[11px] text-ink-mute max-w-xs">{x.notes}</div>}</td><td className="pr-3"><RuleStatus s={x.status} /></td>
            <td>{x.source_ids ? x.source_ids.split(";").map((s) => <a key={s} href={srcById[s]?.url} target="_blank" rel="noreferrer noopener" className="text-brand-dark underline mr-2">{s}</a>) : <span className="text-ink-mute">none</span>}</td></tr>)}</tbody></table></div>
      </Sec>
      <Sec title="Sources">{sources.length ? <ul className="space-y-3 text-sm">{sources.map((s) => <li key={s.source_id}><a href={s.url} target="_blank" rel="noreferrer noopener" className="text-brand-dark underline inline-flex items-center gap-1">{s.source_id} · {s.title}<ExternalLink size={12} aria-hidden /></a><div className="text-xs text-ink-mute">{s.publisher} · {s.evidence_quality.replace(/_/g, " ").toLowerCase()} · accessed {s.date_accessed}{s.publication_date && ` · published ${s.publication_date}`}</div>{s.notes && <div className="text-xs text-ink-soft">{s.notes}</div>}</li>)}</ul> : <p className="text-sm text-ink-mute">No sources: no rules for this lender were researched in this repository yet.</p>}</Sec>
    </div>
  );
}
