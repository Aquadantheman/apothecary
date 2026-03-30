"use client";

import { useState } from "react";
import type { Interaction } from "@/lib/api";

interface Props {
  interactions: Interaction[];
}

const SEVERITY_CONFIG: Record<
  string,
  { icon: string; bg: string; border: string; text: string; label: string }
> = {
  critical: {
    icon: "🔴",
    bg: "bg-red-500/10",
    border: "border-red-500/30",
    text: "text-red-400",
    label: "Discuss with your prescriber before combining",
  },
  high: {
    icon: "🟠",
    bg: "bg-orange-500/10",
    border: "border-orange-500/30",
    text: "text-orange-400",
    label: "Mention to your prescriber at your next visit",
  },
  moderate: {
    icon: "🟡",
    bg: "bg-yellow-500/10",
    border: "border-yellow-500/30",
    text: "text-yellow-400",
    label: "Good to know — usually manageable",
  },
  low: {
    icon: "🔵",
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
    text: "text-blue-400",
    label: "Minor note — typically not a concern",
  },
  beneficial: {
    icon: "🟢",
    bg: "bg-green-500/10",
    border: "border-green-500/30",
    text: "text-green-400",
    label: "This combination may be helpful",
  },
};

const SEVERITY_ORDER = ["critical", "high", "moderate", "low", "beneficial"];

const SECTION_HEADERS: Record<string, { title: string; description: string }> = {
  critical: {
    title: "Requires Attention",
    description: "These combinations need to be discussed with your healthcare provider.",
  },
  high: {
    title: "Worth Discussing",
    description: "These may affect how your medications work. Common in prescribed regimens, but worth mentioning to your prescriber.",
  },
  moderate: {
    title: "Good to Know",
    description: "Minor interactions that are typically manageable with timing or monitoring.",
  },
  low: {
    title: "Minor Notes",
    description: "Low-significance observations. Usually no action needed.",
  },
  beneficial: {
    title: "Working in Your Favor",
    description: "These combinations are complementary or protective.",
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

  // Group by severity
  const grouped: Record<string, Interaction[]> = {};
  for (const interaction of interactions) {
    const sev = interaction.severity;
    if (!grouped[sev]) grouped[sev] = [];
    grouped[sev].push(interaction);
  }

  // Track global index for expand/collapse
  let globalIdx = 0;

  return (
    <div className="space-y-6">
      {SEVERITY_ORDER.filter((sev) => grouped[sev]?.length).map((sev) => {
        const config = SEVERITY_CONFIG[sev] || SEVERITY_CONFIG.low;
        const header = SECTION_HEADERS[sev];

        return (
          <div key={sev}>
            {/* Section header */}
            <div className="mb-2">
              <h3 className={`text-sm font-semibold ${config.text}`}>
                {config.icon} {header.title}
              </h3>
              <p className="text-xs text-[var(--color-text-muted)]">
                {header.description}
              </p>
            </div>

            {/* Interactions in this group */}
            <div className="space-y-2">
              {grouped[sev].map((interaction) => {
                const idx = globalIdx++;
                const isExpanded = expandedIdx === idx;

                return (
                  <div
                    key={idx}
                    className={`rounded-lg border ${config.border} ${config.bg} overflow-hidden transition-all`}
                  >
                    <button
                      onClick={() => setExpandedIdx(isExpanded ? null : idx)}
                      className="w-full px-4 py-3 text-left flex items-start gap-3"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium">{interaction.title}</p>
                        <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                          {interaction.type.replace(/_/g, " ")} · {interaction.confidence}
                        </p>
                      </div>
                      <span className="text-[var(--color-text-muted)] text-xs mt-1 shrink-0">
                        {isExpanded ? "▲" : "▼"}
                      </span>
                    </button>

                    {isExpanded && (
                      <div className="px-4 pb-4 space-y-2">
                        <div>
                          <p className="text-xs font-medium text-[var(--color-text-muted)] mb-0.5">
                            What's happening
                          </p>
                          <p className="text-sm leading-relaxed">{interaction.mechanism}</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-[var(--color-text-muted)] mb-0.5">
                            What to do
                          </p>
                          <p className={`text-sm ${config.text}`}>
                            → {interaction.recommendation}
                          </p>
                        </div>
                        {interaction.timing_relevant && interaction.timing_suggestion && (
                          <div>
                            <p className="text-xs font-medium text-[var(--color-text-muted)] mb-0.5">
                              Timing tip
                            </p>
                            <p className="text-sm text-green-400">
                              ⏰ {interaction.timing_suggestion}
                            </p>
                          </div>
                        )}
                        <p className="text-xs text-[var(--color-text-muted)] mt-1 italic">
                          {config.label}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
