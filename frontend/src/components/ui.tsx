import { AlertTriangle, CheckCircle2, CircleHelp, Loader2, ShieldAlert, XCircle } from "lucide-react";
import type { ReactNode } from "react";
import type { Status } from "../types/api";

const STY: Record<Status, { cls: string; label: string; Icon: typeof CheckCircle2 }> = {
  POTENTIALLY_ELIGIBLE: { cls: "bg-brand-tint text-brand-dark", label: "Potentially eligible", Icon: CheckCircle2 },
  NOT_ELIGIBLE: { cls: "bg-rose2-tint text-rose2", label: "Not eligible", Icon: XCircle },
  INSUFFICIENT_INFORMATION: { cls: "bg-amber2-tint text-amber2", label: "More information needed", Icon: CircleHelp },
};
export function StatusBadge({ status }: { status: Status }) {
  const { cls, label, Icon } = STY[status];
  return <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium whitespace-nowrap ${cls}`}><Icon size={14} aria-hidden />{label}</span>;
}
const EV: Record<string, string> = { OFFICIAL: "bg-brand-tint text-brand-dark", SECONDARY_ONLY: "bg-sky2-tint text-sky2", NONE: "bg-paper-deep text-ink-soft" };
export function EvidenceBadge({ level }: { level: string }) {
  const t = level === "OFFICIAL" ? "Official evidence" : level === "SECONDARY_ONLY" ? "Secondary sources only" : "Not researched";
  return <span className={`rounded-full px-2.5 py-1 text-xs font-medium whitespace-nowrap ${EV[level] ?? EV.NONE}`}>{t}</span>;
}
export function RuleStatus({ s }: { s: string }) {
  const c = s === "VERIFIED_OFFICIAL" ? "text-brand-dark bg-brand-tint" : s === "UNKNOWN" ? "text-ink-soft bg-paper-deep" : s === "CONFLICTING" ? "text-rose2 bg-rose2-tint" : "text-sky2 bg-sky2-tint";
  return <span className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${c}`}>{s.replace(/_/g, " ")}</span>;
}
export const Spinner = () => <Loader2 className="animate-spin" size={16} aria-label="Loading" />;
export function Skeleton({ className = "h-6 w-full" }: { className?: string }) { return <div className={`animate-pulse rounded bg-paper-deep ${className}`} aria-hidden />; }
export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="card border-rose2/30 p-5 flex gap-3 items-start">
      <ShieldAlert className="text-rose2 shrink-0" aria-hidden />
      <div><p className="font-medium">Something went wrong</p><p className="text-sm text-ink-soft mt-1">{message}</p>
        {onRetry && <button className="btn-ghost mt-3" onClick={onRetry}>Try again</button>}</div>
    </div>
  );
}
export function Notice({ children, tone = "amber" }: { children: ReactNode; tone?: "amber" | "sky" }) {
  const c = tone === "amber" ? "bg-amber2-tint text-ink" : "bg-sky2-tint text-ink";
  return <div className={`rounded-lg px-4 py-3 text-sm flex gap-2.5 ${c}`}><AlertTriangle size={16} className="mt-0.5 shrink-0 text-amber2" aria-hidden /><div>{children}</div></div>;
}
export const Empty = ({ title, children }: { title: string; children?: ReactNode }) => (
  <div className="card p-10 text-center"><p className="font-display text-lg">{title}</p><div className="text-sm text-ink-soft mt-2">{children}</div></div>
);
