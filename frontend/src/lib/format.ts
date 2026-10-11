const inr = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });
export const rupees = (n: number | null | undefined) => (n == null ? "—" : inr.format(n));
export const pct = (r: number[] | null | undefined) => (!r ? "—" : r[0] === r[1] ? `${r[0]}% p.a.` : `${r[0]}–${r[1]}% p.a.`);
export const range = (r: number[] | null | undefined, f: (n: number) => string) => (!r ? "—" : r[0] === r[1] ? f(r[0]) : `${f(r[0])} – ${f(r[1])}`);
export const labelStatus = (s: string) => s.replace(/_/g, " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase());
