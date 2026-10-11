import { ArrowLeft, ArrowRight, Check, Pencil } from "lucide-react";
import { useMemo, useState } from "react";
import { ApiError, api } from "../lib/api";
import { validateAll, validateField } from "../lib/validate";
import { useAsync } from "../hooks/useAsync";
import { ErrorBox, Skeleton, Spinner } from "../components/ui";
import type { EligibilityResponse, FieldMeta, Profile } from "../types/api";

interface Props { profile: Profile; setProfile: (p: Profile) => void; onResult: (r: EligibilityResponse) => void }

export default function Assessment({ profile, setProfile, onResult }: Props) {
  const meta = useAsync(() => api.metadata(), []);
  const [step, setStep] = useState(0);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [busy, setBusy] = useState(false);
  const [serverErr, setServerErr] = useState<string | null>(null);

  const fields = useMemo(() => (meta.data?.fields ?? []).filter((f) => f.name !== "business_vintage_months" || profile.employment_type === "self_employed"), [meta.data, profile.employment_type]);
  if (meta.loading) return <div className="mx-auto max-w-2xl px-5 py-10 space-y-4"><Skeleton className="h-8 w-1/2" /><Skeleton className="h-64" /></div>;
  if (meta.error || !meta.data) return <div className="mx-auto max-w-2xl px-5 py-10"><ErrorBox message={meta.error ?? "Could not load the form definition."} /></div>;

  const sections = meta.data.sections.filter((s) => fields.some((f) => f.section === s.id));
  const steps = [...sections.map((s) => s.label), "Review"];
  const isReview = step === sections.length;
  const cur = isReview ? [] : fields.filter((f) => f.section === sections[step].id);
  const numeric = new Set(meta.data.fields.filter((f) => f.kind === "number").map((f) => f.name));
  const set = (f: FieldMeta, v: string) => { setProfile({ ...profile, [f.name]: v }); if (touched[f.name]) setErrors({ ...errors, [f.name]: validateField(f, v) ?? "" }); };
  const blur = (f: FieldMeta) => { setTouched({ ...touched, [f.name]: true }); setErrors({ ...errors, [f.name]: validateField(f, profile[f.name] ?? "") ?? "" }); };

  const next = () => {
    const e = validateAll(cur, profile); setErrors({ ...errors, ...e }); setTouched({ ...touched, ...Object.fromEntries(cur.map((f) => [f.name, true])) });
    if (Object.keys(e).length === 0) { setStep(step + 1); window.scrollTo({ top: 0 }); }
  };
  const submit = async () => {
    if (busy) return;
    const e = validateAll(fields, profile);
    if (Object.keys(e).length) { setErrors(e); const bad = sections.findIndex((s) => fields.some((f) => f.section === s.id && e[f.name])); setStep(Math.max(bad, 0)); return; }
    setBusy(true); setServerErr(null);
    try { onResult(await api.assess(profile, numeric)); location.hash = "#/results"; }
    catch (err) {
      if (err instanceof ApiError && err.details.length) {
        const m: Record<string, string> = {}; err.details.forEach((d) => (m[d.field] = d.message)); setErrors(m);
        const bad = sections.findIndex((s) => fields.some((f) => f.section === s.id && m[f.name])); if (bad >= 0) setStep(bad);
      }
      setServerErr((err as Error).message);
    } finally { setBusy(false); }
  };

  return (
    <div className="mx-auto max-w-2xl px-5 py-10 rise">
      <h1 className="text-3xl">Check your eligibility</h1>
      <p className="text-ink-soft mt-2 text-sm">Fields marked optional can be left blank. Anything you leave blank is reported as missing, never assumed.</p>
      <ol className="mt-6 flex gap-1.5" aria-label="Progress">
        {steps.map((s, i) => <li key={s} className="flex-1" aria-current={i === step ? "step" : undefined}><div className={`h-1.5 rounded-full ${i <= step ? "bg-brand" : "bg-line"}`} /><span className={`hidden sm:block text-[11px] mt-1.5 ${i === step ? "text-ink font-medium" : "text-ink-mute"}`}>{s}</span></li>)}
      </ol>
      <p className="sm:hidden text-xs text-ink-mute mt-2">Step {step + 1} of {steps.length}: {steps[step]}</p>

      <div className="card p-6 mt-6">
        {!isReview ? (
          <div className="space-y-5">
            <h2 className="text-xl">{sections[step].label}</h2>
            {cur.map((f) => <Field key={f.name} f={f} v={profile[f.name] ?? ""} err={errors[f.name]} onChange={(v) => set(f, v)} onBlur={() => blur(f)} />)}
          </div>
        ) : (
          <div>
            <h2 className="text-xl">Review your details</h2>
            <dl className="mt-4 divide-y divide-line">
              {sections.map((s, i) => (
                <div key={s.id} className="py-3">
                  <div className="flex justify-between items-center"><dt className="text-sm font-medium">{s.label}</dt><button className="text-sm text-brand-dark inline-flex gap-1 items-center" onClick={() => setStep(i)}><Pencil size={13} aria-hidden />Edit</button></div>
                  {fields.filter((f) => f.section === s.id).map((f) => <dd key={f.name} className="flex justify-between text-sm py-0.5"><span className="text-ink-soft">{f.label}</span><span>{show(f, profile[f.name])}</span></dd>)}
                </div>))}
            </dl>
            {serverErr && <div className="mt-4"><ErrorBox message={serverErr} /></div>}
          </div>
        )}
      </div>

      <div className="mt-6 flex justify-between">
        <button className="btn-ghost" disabled={step === 0 || busy} onClick={() => setStep(step - 1)}><ArrowLeft size={16} aria-hidden />Back</button>
        {!isReview ? <button className="btn-primary" onClick={next}>Continue<ArrowRight size={16} aria-hidden /></button>
          : <button className="btn-primary" onClick={submit} disabled={busy}>{busy ? <><Spinner />Checking…</> : <><Check size={16} aria-hidden />See my results</>}</button>}
      </div>
    </div>
  );
}
const show = (f: FieldMeta, v?: string) => (!v ? <span className="text-ink-mute">Not provided</span> : f.kind === "select" ? f.options?.find((o) => o[0] === v)?.[1] ?? v : f.unit && f.unit.startsWith("INR") ? "₹" + Number(v).toLocaleString("en-IN") : f.unit ? `${v} ${f.unit}` : v);

function Field({ f, v, err, onChange, onBlur }: { f: FieldMeta; v: string; err?: string; onChange: (v: string) => void; onBlur: () => void }) {
  const id = `f-${f.name}`; const common = { id, value: v, onBlur, "aria-invalid": !!err, "aria-describedby": `${id}-h` };
  return (
    <div>
      <label htmlFor={id} className="label">{f.label} {f.unit && <span className="text-ink-mute font-normal">({f.unit})</span>} {!f.required && <span className="text-xs text-ink-mute font-normal ml-1">optional</span>}</label>
      {f.kind === "select" ? (
        <select {...common} className="input" onChange={(e) => onChange(e.target.value)}><option value="">{f.required ? "Select…" : "Prefer not to say"}</option>{f.options?.map(([val, lab]) => <option key={val} value={val}>{lab}</option>)}</select>
      ) : (
        <input {...common} className={`input ${err ? "border-rose2" : ""}`} type={f.kind === "number" ? "number" : "text"} inputMode={f.kind === "number" ? "decimal" : undefined} min={f.min} max={f.max} step={f.step} onChange={(e) => onChange(e.target.value)} />
      )}
      <p id={`${id}-h`} className={`text-xs mt-1 ${err ? "text-rose2" : "text-ink-mute"}`}>{err || f.hint || f.description}</p>
    </div>
  );
}
