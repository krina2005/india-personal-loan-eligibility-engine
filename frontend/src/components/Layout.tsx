import { Menu, ScanSearch, X } from "lucide-react";
import { useState } from "react";

const NAV = [["#/", "Home"], ["#/check", "Check eligibility"], ["#/lenders", "Lenders & evidence"]] as const;
export function Header({ route }: { route: string }) {
  const [open, setOpen] = useState(false);
  const active = (h: string) => (h === "#/" ? route === "/" : route.startsWith(h.slice(1)));
  return (
    <header className="sticky top-0 z-20 bg-paper/90 backdrop-blur border-b border-line">
      <div className="mx-auto max-w-6xl px-5 h-16 flex items-center justify-between">
        <a href="#/" className="flex items-center gap-2 font-display text-xl"><span className="grid place-items-center h-8 w-8 rounded-lg bg-ink text-paper"><ScanSearch size={18} aria-hidden /></span>LoanLens <span className="text-brand">India</span></a>
        <nav className="hidden md:flex gap-1" aria-label="Main">
          {NAV.map(([h, l]) => <a key={h} href={h} aria-current={active(h) ? "page" : undefined} className={`px-3 py-2 rounded-lg text-sm ${active(h) ? "bg-brand-tint text-brand-dark font-medium" : "text-ink-soft hover:bg-paper-deep"}`}>{l}</a>)}
        </nav>
        <button className="md:hidden p-2" aria-label={open ? "Close menu" : "Open menu"} aria-expanded={open} onClick={() => setOpen(!open)}>{open ? <X /> : <Menu />}</button>
      </div>
      {open && <nav className="md:hidden border-t border-line px-5 py-3 flex flex-col" aria-label="Mobile">{NAV.map(([h, l]) => <a key={h} href={h} onClick={() => setOpen(false)} className="py-2.5 text-sm">{l}</a>)}</nav>}
    </header>
  );
}
export const Footer = () => (
  <footer className="border-t border-line mt-20">
    <div className="mx-auto max-w-6xl px-5 py-8 text-sm text-ink-soft space-y-2">
      <p><strong className="text-ink">Indicative only.</strong> Results are estimates from publicly documented lender rules. They are not a lender decision and do not guarantee approval, amount or rate.</p>
      <p>We never ask for passwords, OTPs, account numbers or identity documents.</p>
    </div>
  </footer>
);
