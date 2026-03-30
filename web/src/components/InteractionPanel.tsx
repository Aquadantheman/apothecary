"use client";

import { useState } from "react";
import type { Interaction } from "@/lib/api";

interface Props {
  interactions: Interaction[];
}

const SEVERITY_CONFIG: Record<
  string,
  { icon: string; bg: string; border: string; text: string }
> = {
  critical: {
    icon: "🔴",
    bg: "bg-red-500/10",
    border: "border-red-500/30",
    text: "text-red-400",
  },
  high: {
    icon: "🟠",
    bg: "bg-orange-500/10",
    border: "border-orange-500/30",
    text: "text-orange-400",
  },
  moderate: {
    icon: "🟡",
    bg: "bg-yellow-500/10",
    border: "border-yellow-500/30",
    text: "text-yellow-400",
  },
  low: {
    icon: "🔵",
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
    text: "text-blue-400",
  },
  beneficial: {
    icon: "🟢",
    bg: "bg-green-500/10",
    border: "border-green-500/30",
    text: "text-green-400",
  },
};

export function InteractionPanel({ interactions }: Props) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  if (interactions.length === 0) {
    return (
      <div className="text-center py-8 text-[var(--color-text-muted)]">
        No interactions detected between these substances.
        <br />
        <span className="text-xs">
          Note: absence of known interactions does not guarantee safety.
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {interactions.map((interaction, i) => {
        const config = SEVERITY_CONFIG[interaction.severity] || SEVERITY_CONFIG.low;
        const isExpanded = expandedIdx === i;

        return (
          <div
            key={i}
            className={`rounded-lg border ${config.border} ${config.bg} overflow-hidden transition-all`}
          >
            <button
              onClick={() => setExpandedIdx(isExpanded ? null : i)}
              className="w-full px-4 py-3 text-left flex items-start gap-3"
            >
              <span className="text-base mt-0.5 shrink-0">{config.icon}</span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`text-xs font-semibold uppercase ${config.text}`}>
                    {interaction.severity}
                  </span>
                  <span className="text-xs text-[var(--color-text-muted)]">
                    {interaction.type.replace(/_/g, " ")}
                  </span>
                  <span className="text-xs text-[var(--color-text-muted)]">
                    · {interaction.confidence}
                  </span>
                </div>
                <p className="text-sm font-medium mt-0.5">{interaction.title}</p>
              </div>
              <span className="text-[var(--color-text-muted)] text-xs mt-1 shrink-0">
                {isExpanded ? "▲" : "▼"}
              </span>
            </button>

            {isExpanded && (
              <div className="px-4 pb-4 pl-11 space-y-2">
                <div>
                  <p className="text-xs font-medium text-[var(--color-text-muted)] mb-0.5">
                    Mechanism
                  </p>
                  <p className="text-sm leading-relaxed">{interaction.mechanism}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-[var(--color-text-muted)] mb-0.5">
                    Recommendation
                  </p>
                  <p className={`text-sm ${config.text}`}>
                    → {interaction.recommendation}
                  </p>
                </div>
                {interaction.timing_relevant && interaction.timing_suggestion && (
                  <div>
                    <p className="text-xs font-medium text-[var(--color-text-muted)] mb-0.5">
                      Timing
                    </p>
                    <p className="text-sm text-green-400">
                      ⏰ {interaction.timing_suggestion}
                    </p>
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
