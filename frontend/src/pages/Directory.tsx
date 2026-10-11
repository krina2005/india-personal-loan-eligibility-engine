import { api } from "../lib/api";
import { useAsync } from "../hooks/useAsync";
import { Empty, ErrorBox, EvidenceBadge, Notice, Skeleton } from "../components/ui";

export default function Directory() {
  const d = useAsync(() => api.lenders(), []);
  return (
    <div className="mx-auto max-w-6xl px-5 py-10 rise">
      <h1 className="text-3xl">Lenders &amp; research evidence</h1>
      <p className="text-ink-soft mt-2 max-w-2xl">The 20 lenders are an analyst shortlist, not a market-share ranking. A lender being listed does not mean its rules were researched.</p>
      {d.loading && <div className="mt-6 space-y-3">{[0, 1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-12" />)}</div>}
      {d.error && <div className="mt-6"><ErrorBox message={d.error} /></div>}
      {d.data && (d.data.lenders.length === 0 ? <Empty title="No lenders in the dataset" /> : <>
        <div className="mt-6"><Notice>{d.data.coverage.lenders_official_evidence} of {d.data.coverage.lenders_total} lenders have official-page evidence; {d.data.coverage.lenders_no_evidence} have none; {d.data.coverage.lenders_with_conflicts} have conflicting rules; {d.data.coverage.rules_unknown} of {d.data.coverage.rules_total} rules are unknown.</Notice></div>
        <div className="card overflow-x-auto mt-4"><table className="w-full text-sm min-w-[720px]"><thead className="text-left text-xs text-ink-mute border-b border-line"><tr><th className="p-3">Lender</th><th className="p-3">Category</th><th className="p-3">Product</th><th className="p-3">Evidence</th><th className="p-3">Known / unknown rules</th></tr></thead>
          <tbody>{d.data.lenders.map((l) => <tr key={l.lender_id} className="border-b border-line last:border-0"><td className="p-3"><a className="font-medium hover:text-brand-dark" href={`#/lender/${l.lender_id}`}>{l.brand_name}</a></td><td className="p-3">{l.category.replace("_", " ").toLowerCase()}</td><td className="p-3 text-ink-soft">{l.product === "NOT_VERIFIED" ? "Not verified" : l.product}</td><td className="p-3"><EvidenceBadge level={l.evidence_level} /></td><td className="p-3">{l.rules_known} / {l.rules_unknown}{l.rules_conflicting > 0 && <span className="text-rose2 text-xs ml-2">{l.rules_conflicting} conflicting</span>}</td></tr>)}</tbody></table></div></>)}
    </div>
  );
}
