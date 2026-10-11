import { ArrowDownUp, ChevronDown, Pencil, Search } from "lucide-react";
import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  Empty,
  EvidenceBadge,
  Notice,
  StatusBadge,
} from "../components/ui";
import { pct, range, rupees } from "../lib/format";
import type {
  EligibilityResponse,
  LenderResult,
  Status,
} from "../types/api";

type Sort = "name" | "amount" | "rate";

export default function Results({
  data,
}: {
  data: EligibilityResponse | null;
}) {
  const [q, setQ] = useState("");
  const [f, setF] = useState<"ALL" | Status>("ALL");
  const [sort, setSort] = useState<Sort>("name");
  const [open, setOpen] = useState<string | null>(null);

  const rows = useMemo(() => {
    if (!data) return [];

    const query = q.trim().toLowerCase();

    const filtered = data.lenders.filter(
      (l) =>
        (f === "ALL" || l.status === f) &&
        `${l.brand_name} ${l.legal_name} ${l.category}`
          .toLowerCase()
          .includes(query),
    );

    if (sort === "name") {
      return [...filtered].sort((a, b) =>
        a.brand_name.localeCompare(b.brand_name),
      );
    }

    const getSortValue = (l: LenderResult): number | null => {
      if (sort === "amount") {
        return l.estimate?.max_amount_inr ?? null;
      }

      return l.estimate?.rate_range_pct?.[1] ?? null;
    };

    const available = filtered
      .filter((l) => getSortValue(l) != null)
      .sort((a, b) => {
        const aValue = getSortValue(a)!;
        const bValue = getSortValue(b)!;

        return sort === "amount"
          ? bValue - aValue
          : aValue - bValue;
      });

    const unavailable = filtered.filter(
      (l) => getSortValue(l) == null,
    );

    // Keep unavailable values last instead of treating them as zero.
    return [...available, ...unavailable];
  }, [data, q, f, sort]);

  if (!data) {
    return (
      <div className="mx-auto max-w-2xl px-5 py-16">
        <Empty title="No results yet">
          Fill in the form to see how lenders assess your profile.{" "}
          <a href="#/check" className="text-brand-dark underline">
            Check eligibility
          </a>
        </Empty>
      </div>
    );
  }

  const { overall: o } = data;

  const ii = o.counts.insufficient_information;
  const pe = o.counts.potentially_eligible;
  const ne = o.counts.not_eligible;

  // Include only lenders for which the API provides an amount.
  // A known amount alone does not prove that an estimate is verified.
  const chart = data.lenders
    .filter((l) => l.estimate?.max_amount_inr != null)
    .map((l) => ({
      name: l.brand_name,
      amount: l.estimate!.max_amount_inr!,
    }));

  let infoMsg: React.ReactNode;

  if (ii > 0 && pe === 0 && ne === 0) {
    infoMsg = (
      <Notice tone="sky">
        All lenders need more information or better-researched rules
        before an assessment can be made.
      </Notice>
    );
  } else if (ii > 0) {
    infoMsg = (
      <Notice tone="sky">
        {ii} lender(s) need more information or better-researched
        rules. They appear as "more information needed", not as
        rejections.
      </Notice>
    );
  } else if (pe > 0) {
    infoMsg = (
      <>
        {pe} lender(s) pass every rule the model could verify.
      </>
    );
  } else if (ne > 0) {
    infoMsg = (
      <>
        Every lender classified as not eligible has failed at least
        one mandatory condition evaluated by the model.
      </>
    );
  } else {
    infoMsg = (
      <Notice>
        No lenders could be assessed with the provided profile.
      </Notice>
    );
  }

  const tiles: [string, number, string, Status][] = [
    [
      "Potentially eligible",
      pe,
      "text-brand-dark",
      "POTENTIALLY_ELIGIBLE",
    ],
    [
      "Not eligible",
      ne,
      "text-rose2",
      "NOT_ELIGIBLE",
    ],
    [
      "More information needed",
      ii,
      "text-amber2",
      "INSUFFICIENT_INFORMATION",
    ],
  ];

  return (
    <div className="mx-auto max-w-6xl px-5 py-10 rise">
      <div className="flex flex-wrap justify-between gap-4 items-start">
        <div>
          <h1 className="text-3xl">Your results</h1>
          <p className="mt-2 text-ink-soft max-w-2xl">
            {o.headline}
          </p>
        </div>

        <a href="#/check" className="btn-ghost">
          <Pencil size={15} aria-hidden />
          Edit details &amp; recalculate
        </a>
      </div>

      <div className="grid sm:grid-cols-3 gap-4 mt-6">
        {tiles.map(([label, count, color, status]) => (
          <button
            key={label}
            onClick={() =>
              setF((current) =>
                current === status ? "ALL" : status,
              )
            }
            aria-pressed={f === status}
            className={`card p-5 text-left ${
              f === status ? "ring-2 ring-brand" : ""
            }`}
          >
            <p className={`font-display text-4xl ${color}`}>
              {count}
            </p>
            <p className="text-sm mt-1">{label}</p>
          </button>
        ))}
      </div>

      <div className="mt-4 space-y-3">
        {infoMsg}

        <Notice>
          All {data.lenders.length} lenders returned by the API are
          included in this assessment. Unknown or conflicting rules
          should result in "more information needed" when they prevent
          a reliable assessment.
        </Notice>
      </div>

      {chart.length > 0 && (
        <section
          className="card p-5 mt-6"
          aria-label="Indicative maximum amount chart"
        >
          <h2 className="text-lg">
            Indicative maximum loan amount
          </h2>

          <p className="text-xs text-ink-mute mb-3">
            Amounts returned by the assessment API. Availability and
            evidence quality may vary. Indicative, not a lender offer.
          </p>

          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chart}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#E3DDD1"
                  vertical={false}
                />

                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 12 }}
                />

                <YAxis
                  tickFormatter={(value: number) =>
                    `₹${value / 100000}L`
                  }
                  tick={{ fontSize: 12 }}
                  width={56}
                />

                <Tooltip
                  formatter={(value) => rupees(Number(value))}
                />

                <Bar
                  dataKey="amount"
                  fill="#0B8F6D"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      <section className="mt-8" aria-label="Lender comparison">
        <div className="flex flex-wrap gap-3 mb-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search
              size={16}
              className="absolute left-3 top-3 text-ink-mute"
              aria-hidden
            />

            <input
              className="input pl-9"
              placeholder="Search lenders"
              aria-label="Search lenders"
              value={q}
              onChange={(event) => setQ(event.target.value)}
            />
          </div>

          <select
            className="input w-auto"
            aria-label="Filter by status"
            value={f}
            onChange={(event) =>
              setF(event.target.value as "ALL" | Status)
            }
          >
            <option value="ALL">All statuses</option>
            <option value="POTENTIALLY_ELIGIBLE">
              Potentially eligible
            </option>
            <option value="NOT_ELIGIBLE">Not eligible</option>
            <option value="INSUFFICIENT_INFORMATION">
              More information needed
            </option>
          </select>

          <label className="flex items-center gap-2 text-sm">
            <ArrowDownUp size={15} aria-hidden />

            <select
              className="input w-auto"
              value={sort}
              onChange={(event) =>
                setSort(event.target.value as Sort)
              }
              aria-label="Sort by"
            >
              <option value="name">Name</option>
              <option value="amount">
                Max amount (where known)
              </option>
              <option value="rate">
                Rate (where known)
              </option>
            </select>
          </label>
        </div>

        {rows.length === 0 ? (
          <Empty title="No lenders match">
            Try clearing the search or filter.
          </Empty>
        ) : (
          <div className="card overflow-x-auto">
            <table className="w-full text-sm min-w-[760px]">
              <thead className="text-left text-xs text-ink-mute border-b border-line">
                <tr>
                  <th className="p-3">Lender</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Max amount</th>
                  <th className="p-3">Rate</th>
                  <th className="p-3">Tenure</th>
                  <th className="p-3">EMI (requested)</th>
                  <th className="p-3">Evidence</th>
                  <th className="p-3">
                    <span className="sr-only">Details</span>
                  </th>
                </tr>
              </thead>

              <tbody>
                {rows.map((lender) => (
                  <Row
                    key={lender.lender_id}
                    l={lender}
                    open={open === lender.lender_id}
                    toggle={() =>
                      setOpen((current) =>
                        current === lender.lender_id
                          ? null
                          : lender.lender_id,
                      )
                    }
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <p className="text-xs text-ink-mute mt-6">
        {o.disclaimer}
      </p>
    </div>
  );
}

function Row({
  l,
  open,
  toggle,
}: {
  l: LenderResult;
  open: boolean;
  toggle: () => void;
}) {
  const e = l.estimate;

  const dash = (
    <span className="text-ink-mute" title="Not available">
      —
    </span>
  );

  return (
    <>
      <tr className="border-b border-line last:border-0 hover:bg-paper">
        <td className="p-3">
          <a
            className="font-medium hover:text-brand-dark"
            href={`#/lender/${l.lender_id}`}
          >
            {l.brand_name}
          </a>

          <div className="text-xs text-ink-mute">
            {l.category.replace(/_/g, " ").toLowerCase()}
          </div>
        </td>

        <td className="p-3">
          <StatusBadge status={l.status} />
        </td>

        <td className="p-3">
          {e?.max_amount_inr != null
            ? rupees(e.max_amount_inr)
            : dash}
        </td>

        <td className="p-3">
          {e?.rate_range_pct != null
            ? pct(e.rate_range_pct)
            : dash}
        </td>

        <td className="p-3">
          {e?.tenure_months_range != null
            ? range(
                e.tenure_months_range,
                (months) => `${months} mo`,
              )
            : dash}
        </td>

        <td className="p-3">
          {e?.emi_for_requested_inr != null
            ? range(e.emi_for_requested_inr, rupees)
            : dash}
        </td>

        <td className="p-3">
          <EvidenceBadge level={l.evidence_level} />
        </td>

        <td className="p-3">
          <button
            onClick={toggle}
            aria-expanded={open}
            aria-label={`Why ${l.brand_name} got this result`}
            className="p-1"
            type="button"
          >
            <ChevronDown
              className={`transition ${
                open ? "rotate-180" : ""
              }`}
              size={18}
            />
          </button>
        </td>
      </tr>

      {open && (
        <tr className="bg-paper">
          <td colSpan={8} className="p-4 text-sm">
            <p>{l.explanation}</p>

            <a
              href={`#/lender/${l.lender_id}`}
              className="inline-block mt-2 text-brand-dark underline"
            >
              Full explanation and sources
            </a>
          </td>
        </tr>
      )}
    </>
  );
}