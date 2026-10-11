import { ArrowRight, BadgeCheck, FileSearch, ListChecks, PenLine } from "lucide-react";
import { api } from "../lib/api";
import { useAsync } from "../hooks/useAsync";
import { Skeleton, ErrorBox, Notice } from "../components/ui";

export default function Landing() {
  const cov = useAsync(() => api.coverage(), []);
  const c = cov.data;
  const stats: [string, string | number, string][] = c ? [
    ["Lenders in dataset", c.lenders_total, "shortlisted, not ranked"],
    ["With official-page evidence", c.lenders_official_evidence, `of ${c.lenders_total} lenders`],
    ["Rules recorded", c.rules_total, `${c.rules_unknown} still unknown`],
    ["Sources logged", c.sources_total, c.source_dates.latest ? `accessed ${c.source_dates.latest}` : ""],
  ] : [];
  return (
    <div>
      <section className="mx-auto max-w-6xl px-5 pt-16 pb-14 grid md:grid-cols-5 gap-10 items-center rise">
        <div className="md:col-span-3">
          <p className="text-sm font-medium text-brand-dark mb-4">Personal loans · India</p>
          <h1 className="text-4xl md:text-5xl leading-[1.1]">See which lenders you may qualify with — and exactly why.</h1>
          <p className="mt-5 text-lg text-ink-soft max-w-xl">LoanLens India checks your profile against documented lender rules. Every result links back to a source, and rules we could not verify stay marked as unknown.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <a href="#/check" className="btn-primary">Check My Eligibility <ArrowRight size={16} aria-hidden /></a>
            <a href="#/lenders" className="btn-ghost">See the evidence</a>
          </div>
        </div>
        <div className="md:col-span-2 card p-6 bg-ink text-paper border-ink">
          <p className="font-display text-xl">What you get</p>
          <ul className="mt-4 space-y-3 text-sm text-paper/85">
            {["A status per lender: potentially eligible, not eligible, or more information needed", "The failed rule, with its source", "Indicative amount, rate and EMI only where evidence supports them"].map((t) => <li key={t} className="flex gap-2"><BadgeCheck size={18} className="shrink-0 text-emerald-300" aria-hidden />{t}</li>)}
          </ul>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 pb-14" aria-labelledby="how">
        <h2 id="how" className="text-2xl mb-6">How it works</h2>
        <ol className="grid md:grid-cols-3 gap-4">
          {[[PenLine, "Enter details", "Age, income, credit score, existing EMIs and the loan you want."], [ListChecks, "Compare lenders", "Each lender’s documented rules are applied by a deterministic rule engine."], [FileSearch, "Review reasons", "Open any lender to see passed, failed and unknown rules with sources."]].map(([I, t, d], i) => {
            const Icon = I as typeof PenLine; return (
              <li key={String(t)} className="card p-5"><div className="flex items-center gap-3"><span className="grid place-items-center h-9 w-9 rounded-full bg-brand-tint text-brand-dark"><Icon size={18} aria-hidden /></span><span className="text-xs text-ink-mute">Step {i + 1}</span></div>
                <h3 className="text-lg mt-3">{String(t)}</h3><p className="text-sm text-ink-soft mt-1">{String(d)}</p></li>);
          })}
        </ol>
      </section>

      <section className="mx-auto max-w-6xl px-5 pb-14" aria-labelledby="cov">
        <h2 id="cov" className="text-2xl mb-6">Research coverage, as recorded in the repository</h2>
        {cov.loading && <div className="grid grid-cols-2 md:grid-cols-4 gap-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}</div>}
        {cov.error && <ErrorBox message={cov.error} />}
        {c && <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {stats.map(([l, v, s]) => <div key={l} className="card p-5"><p className="font-display text-4xl">{v}</p><p className="text-sm font-medium mt-1">{l}</p><p className="text-xs text-ink-mute mt-0.5">{s}</p></div>)}
          </div>
          <div className="mt-4"><Notice>{c.note} Currently {c.lenders_no_evidence} of {c.lenders_total} lenders have no verified rules, so they can only return “more information needed”.</Notice></div>
        </>}
      </section>

      <section className="mx-auto max-w-6xl px-5" aria-labelledby="meth">
        <h2 id="meth" className="text-2xl mb-4">Methodology and limitations</h2>
        <div className="card p-6 grid md:grid-cols-2 gap-6 text-sm text-ink-soft">
          <ul className="space-y-2 list-disc pl-5"><li>Rules come from public lender pages and comparison sites; each rule is tagged official, secondary, conflicting or unknown.</li><li>An unknown rule is never treated as a pass.</li><li>A best option is suggested only when at least two lenders are comparable.</li></ul>
          <ul className="space-y-2 list-disc pl-5"><li>Rates are published ranges, not personal quotes.</li><li>Maximum amounts are indicative and shown only when the needed rules are known.</li><li>Lenders make the final decision; nothing here guarantees approval.</li></ul>
        </div>
      </section>
    </div>
  );
}
