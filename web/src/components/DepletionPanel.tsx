"use client";

import type { DepletionGap } from "@/lib/api";

interface Props {
  gaps: DepletionGap[];
}

export function DepletionPanel({ gaps }: Props) {
  if (gaps.length === 0) {
    return (
      <div className="text-center py-8 text-[var(--color-text-muted)]">
        No nutrient depletion gaps detected.
        <br />
        <span className="text-xs">
          Your supplements appear to address all medication-induced depletions.
        </span>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-[var(--color-border)] overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-[var(--color-surface-2)] border-b border-[var(--color-border)]">
            <th className="px-4 py-2.5 text-left font-semibold text-xs uppercase text-[var(--color-text-muted)]">
              Nutrient
            </th>
            <th className="px-4 py-2.5 text-left font-semibold text-xs uppercase text-[var(--color-text-muted)]">
              Depleted By
            </th>
            <th className="px-4 py-2.5 text-left font-semibold text-xs uppercase text-[var(--color-text-muted)]">
              Significance
            </th>
            <th className="px-4 py-2.5 text-left font-semibold text-xs uppercase text-[var(--color-text-muted)]">
              Suggestion
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--color-border)]">
          {gaps.map((gap) => (
            <tr key={gap.nutrient} className="bg-[var(--color-surface)]">
              <td className="px-4 py-3 font-medium text-[var(--color-accent)]">
                {gap.nutrient.replace(/_/g, " ")}
              </td>
              <td className="px-4 py-3 text-[var(--color-text-muted)]">
                {gap.depleted_by.join(", ")}
              </td>
              <td className="px-4 py-3">
                <span
                  className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    gap.clinical_significance === "high"
                      ? "bg-red-500/15 text-red-400"
                      : gap.clinical_significance === "moderate"
                        ? "bg-yellow-500/15 text-yellow-400"
                        : "bg-blue-500/15 text-blue-400"
                  }`}
                >
                  {gap.clinical_significance}
                </span>
              </td>
              <td className="px-4 py-3 text-green-400 text-xs">
                {gap.suggestion}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
