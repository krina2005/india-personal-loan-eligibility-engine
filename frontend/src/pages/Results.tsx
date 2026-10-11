import { ArrowDownUp, ChevronDown, Pencil, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Empty, EvidenceBadge, Notice, StatusBadge } from "../components/ui";
import { pct, range, rupees } from "../lib/format";
import type { EligibilityResponse, LenderResult, Status } from "../types/api";

type Sort = "name" | "amount" | "rate";
export default function Results({ data }: { data: EligibilityResponse | null }) {
  const [q, setQ] = useState(""); const [f, setF] = useState<"ALL" | Status>("ALL"); const [sort, setSort] = useState<Sort>("name"); const [open, setOpen] = useState<string | null>(null);
  const rows = useMemo(() => {
    if (!data) return [];
    let r = data.lenders.filter((l) => (f === "ALL" || l.status === f) && (l.brand_name + l.legal_name + l.category).toLowerCase().includes(q.toLowerCase()));
    const key = (l: LenderResult) => sort === "amount" ? l.estimate?.max_amount_inr ?? null : sort === "rate" ? l.estimate?.rate_range_pct?.[1] ?? null : null;
    if (sort === "name") return [...r].sort((a, b) => a.brand_name.localeCompare(b.brand_name));
    const have = r.filter((l) => key(l) != null).sort((a, b) => sort === "amount" ? key(b)! - key(a)! : key(a)! - key(b)!);
    return [...have, ...r.filter((l) => key(l) == null)];   // unavailable values go last, never treated as zero
  }, [data, q, f, sort]);

  if (!data) return <div className="mx-auto max-w-2xl px-5 py-16"><Empty title="No results yet">Fill in the form to see how lenders assess your profile. <a href="#/check" className="text-brand-dark underline">Check eligibility</a></Empty></div>;
  const { overall: o } = data; const chart = data.lenders.filter((l) => l.estimate?.max_amount_inr).map((l) => ({ name: l.brand_name, amount: l.estimate!.max_amount_inr! }));
  const rec = o.recommendation.lender_id ? data.lenders.find((l) => l.lender_id === o.recommendation.lender_id) : null;
  const tiles: [string, number, string, Status][] = [["Potentially eligible", o.counts.potentially_eligible, "text-brand-dark", "POTENTIALLY_ELIGIBLE"], ["Not eligible", o.counts.not_eligible, "text-rose2", "NOT_ELIGIBLE"], ["More information needed", o.counts.insufficient_information, "text-amber2", "INSUFFICIENT_INFORMATION"]];
  return (
    <div className="mx-auto max-w-6xl px-5 py-10 rise">
      <div className="flex flex-wrap justify-between gap-4 items-start">
        <div><h1 className="text-3xl">Your results</h1><p className="mt-2 text-ink-soft max-w-2xl">{o.headline}</p></div>
        <a href="#/check" className="btn-ghost"><Pencil size={15} aria-hidden />Edit details &amp; recalculate</a>
      </div>
      <div className="grid sm:grid-cols-3 gap-4 mt-6">
        {tiles.map(([l, n, c, s]) => <button key={l} onClick={() => setF(f === s ? "ALL" : s)} aria-pressed={f === s} className={`card p-5 text-left ${f === s ? "ring-2 ring-brand" : ""}`}><p className={`font-display text-4xl ${c}`}>{n}</p><p className="text-sm mt-1">{l}</p></button>)}
      </div>
      <div className="mt-4 space-y-3">
        <Notice tone="sky"><strong>Best option:</strong> {rec ? <>{rec.brand_name}. {o.recommendation.why}</> : o.recommendation.why}</Notice>
        {o.researched_lenders < data.lenders.length && <Notice>Only {o.researched_lenders} of {data.lenders.length} lenders have researched rules. The rest cannot be assessed yet and appear as “more information needed”, not as rejections.</Notice>}
      </div>

      {chart.length > 0 && <section className="card p-5 mt-6" aria-label="Indicative maximum amount chart"><h2 className="text-lg">Indicative maximum loan amount</h2><p className="text-xs text-ink-mute mb-3">Only lenders with enough verified rules. Indicative, not an offer.</p>
        <div className="h-56"><ResponsiveContainer><BarChart data={chart}><CartesianGrid strokeDasharray="3 3" stroke="#E3DDD1" vertical={false} /><XAxis dataKey="name" tick={{ fontSize: 12 }} /><YAxis tickFormatter={(v: number) => `₹${v / 100000}L`} tick={{ fontSize: 12 }} width={56} /><Tooltip formatter={(v: number) => rupees(v)} /><Bar dataKey="amount" fill="#0B8F6D" radius={[6, 6, 0, 0]} /></BarChart></ResponsiveContainer></div></section>}

      <section className="mt-8" aria-label="Lender comparison">
        <div className="flex flex-wrap gap-3 mb-3">
          <div className="relative flex-1 min-w-[200px]"><Search size={16} className="absolute left-3 top-3 text-ink-mute" aria-hidden /><input className="input pl-9" placeholder="Search lenders" aria-label="Search lenders" value={q} onChange={(e) => setQ(e.target.value)} /></div>
          <select className="input w-auto" aria-label="Filter by status" value={f} onChange={(e) => setF(e.target.value as "ALL" | Status)}><option value="ALL">All statuses</option><option value="POTENTIALLY_ELIGIBLE">Potentially eligible</option><option value="NOT_ELIGIBLE">Not eligible</option><option value="INSUFFICIENT_INFORMATION">More information needed</option></select>
          <label className="flex items-center gap-2 text-sm"><ArrowDownUp size={15} aria-hidden /><select className="input w-auto" value={sort} onChange={(e) => setSort(e.target.value as Sort)} aria-label="Sort by"><option value="name">Name</option><option value="amount">Max amount (where known)</option><option value="rate">Rate (where known)</option></select></label>
        </div>
        {rows.length === 0 ? <Empty title="No lenders match">Try clearing the search or filter.</Empty> : (
          <div className="card overflow-x-auto"><table className="w-full text-sm min-w-[760px]">
            <thead className="text-left text-xs text-ink-mute border-b border-line"><tr><th className="p-3">Lender</th><th className="p-3">Status</th><th className="p-3">Max amount</th><th className="p-3">Rate</th><th className="p-3">Tenure</th><th className="p-3">EMI (requested)</th><th className="p-3">Evidence</th><th className="p-3"><span className="sr-only">Details</span></th></tr></thead>
            <tbody>{rows.map((l) => <Row key={l.lender_id} l={l} open={open === l.lender_id} toggle={() => setOpen(open === l.lender_id ? null : l.lender_id)} />)}</tbody></table></div>)}
      </section>
      <p className="text-xs text-ink-mute mt-6">{o.disclaimer}</p>
    </div>
  );
}
function Row({ l, open, toggle }: { l: LenderResult; open: boolean; toggle: () => void }) {
  const e = l.estimate; const dash = <span className="text-ink-mute" title="Not available">—</span>;
  return (<>
    <tr className="border-b border-line last:border-0 hover:bg-paper">
      <td className="p-3"><a className="font-medium hover:text-brand-dark" href={`#/lender/${l.lender_id}`}>{l.brand_name}</a><div className="text-xs text-ink-mute">{l.category.replace("_", " ").toLowerCase()}</div></td>
      <td className="p-3"><StatusBadge status={l.status} /></td>
      <td className="p-3">{e?.max_amount_inr ? rupees(e.max_amount_inr) : dash}</td>
      <td className="p-3">{e?.rate_range_pct ? pct(e.rate_range_pct) : dash}</td>
      <td className="p-3">{e?.tenure_months_range ? range(e.tenure_months_range, (n) => `${n} mo`) : dash}</td>
      <td className="p-3">{e?.emi_for_requested_inr ? range(e.emi_for_requested_inr, rupees) : dash}</td>
      <td className="p-3"><EvidenceBadge level={l.evidence_level} /></td>
      <td className="p-3"><button onClick={toggle} aria-expanded={open} aria-label={`Why ${l.brand_name} got this result`} className="p-1"><ChevronDown className={`transition ${open ? "rotate-180" : ""}`} size={18} /></button></td>
    </tr>
    {open && <tr className="bg-paper"><td colSpan={8} className="p-4 text-sm"><p>{l.explanation}</p><a href={`#/lender/${l.lender_id}`} className="inline-block mt-2 text-brand-dark underline">Full explanation and sources</a></td></tr>}
  </>);
}
