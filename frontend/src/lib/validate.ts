import type { FieldMeta, Profile } from "../types/api";
export function validateField(f: FieldMeta, v: string): string | null {
  if (v.trim() === "") return f.required ? `${f.label} is required.` : null;
  if (f.kind === "number") {
    const n = Number(v);
    if (!Number.isFinite(n)) return "Enter a valid number.";
    if (f.min != null && n < f.min) return `Must be at least ${f.min.toLocaleString("en-IN")}.`;
    if (f.max != null && n > f.max) return `Must be at most ${f.max.toLocaleString("en-IN")}.`;
    if (f.type === "int" && !Number.isInteger(n)) return "Enter a whole number.";
  }
  return null;
}
export function validateAll(fields: FieldMeta[], p: Profile) {
  const e: Record<string, string> = {};
  for (const f of fields) { const m = validateField(f, p[f.name] ?? ""); if (m) e[f.name] = m; }
  return e;
}
