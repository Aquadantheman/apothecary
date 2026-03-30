"use client";

import { useState } from "react";
import type { DepletionGap } from "@/lib/api";

interface Props {
  gaps: DepletionGap[];
}

export function DepletionPanel({ gaps }: Props) {
  const [expandedNutrient, setExpandedNutrient] = useState<string | null>(null);

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
    <div className="space-y-3">
      {gaps.map((gap) => {
        const isExpanded = expandedNutrient === gap.nutrient;
        const hasFoods = gap.food_sources && gap.food_sources.length > 0;
        const hasSymptoms = gap.symptoms && gap.symptoms.length > 0;
        const hasTips = gap.lifestyle_tips && gap.lifestyle_tips.length > 0;
        const hasDetails = hasFoods || hasSymptoms || hasTips;

        return (
          <div
            key={gap.nutrient}
            className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden"
          >
            <button
              onClick={() => setExpandedNutrient(isExpanded ? null : gap.nutrient)}
              className="w-full px-4 py-3 text-left flex items-start gap-3"
            >
              <span className="text-base mt-0.5 shrink-0">⚠️</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-semibold text-[var(--color-accent)]">
                    {gap.nutrient.replace(/_/g, " ")}
                  </span>
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
                </div>
                <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                  Depleted by: {gap.depleted_by.join(", ")}
                </p>
                <p className="text-sm text-green-400 mt-1">
                  💊 {gap.suggestion}
                </p>
              </div>
              {hasDetails && (
                <span className="text-[var(--color-text-muted)] text-xs mt-1 shrink-0">
                  {isExpanded ? "▲" : "▼"}
                </span>
              )}
            </button>

            {isExpanded && hasDetails && (
              <div className="px-4 pb-4 pl-11 space-y-4 border-t border-[var(--color-border)] pt-3">
                {hasFoods && (
                  <div>
                    <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wide mb-1.5">
                      🥗 Food Sources
                    </p>
                    <div className="space-y-1">
                      {gap.food_sources.map((food, i) => (
                        <p key={i} className="text-sm text-[var(--color-text)]">
                          • {food}
                        </p>
                      ))}
                    </div>
                  </div>
                )}

                {hasSymptoms && (
                  <div>
                    <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wide mb-1.5">
                      🔍 Signs of Deficiency
                    </p>
                    <div className="space-y-1">
                      {gap.symptoms.map((symptom, i) => (
                        <p key={i} className="text-sm text-yellow-300/80">
                          • {symptom}
                        </p>
                      ))}
                    </div>
                  </div>
                )}

                {hasTips && (
                  <div>
                    <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wide mb-1.5">
                      💡 What You Can Do
                    </p>
                    <div className="space-y-1">
                      {gap.lifestyle_tips.map((tip, i) => (
                        <p key={i} className="text-sm text-green-300/80">
                          • {tip}
                        </p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
