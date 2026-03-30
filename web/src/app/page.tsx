"use client";

import { useState, useEffect, useCallback } from "react";
import { SubstanceSearch } from "@/components/SubstanceSearch";
import { StackList } from "@/components/StackList";
import { InteractionPanel } from "@/components/InteractionPanel";
import { TimelinePanel } from "@/components/TimelinePanel";
import { DepletionPanel } from "@/components/DepletionPanel";
import {
  analyzeStack,
  getTimeline,
  type SubstanceSummary,
  type AnalysisResult,
  type Timeline,
} from "@/lib/api";

type Tab = "interactions" | "timeline" | "depletions";

export default function Home() {
  const [stack, setStack] = useState<SubstanceSummary[]>([]);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("interactions");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runAnalysis = useCallback(async (substances: SubstanceSummary[]) => {
    if (substances.length === 0) {
      setAnalysis(null);
      setTimeline(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const ids = substances.map((s) => s.id);
      const [analysisResult, timelineResult] = await Promise.all([
        analyzeStack(ids),
        getTimeline(ids),
      ]);
      setAnalysis(analysisResult);
      setTimeline(timelineResult);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    runAnalysis(stack);
  }, [stack, runAnalysis]);

  const addSubstance = (substance: SubstanceSummary) => {
    if (!stack.find((s) => s.id === substance.id)) {
      setStack((prev) => [...prev, substance]);
    }
  };

  const removeSubstance = (id: string) => {
    setStack((prev) => prev.filter((s) => s.id !== id));
  };

  const hasCritical = analysis?.counts?.critical
    ? analysis.counts.critical > 0
    : false;

  return (
    <main className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-1">
          <span className="text-[var(--color-accent)]">⚗</span> Apothecary
        </h1>
        <p className="text-[var(--color-text-muted)]">
          Your full stack, understood.
        </p>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column — Search + Stack */}
        <div className="lg:col-span-1 space-y-4">
          <SubstanceSearch onSelect={addSubstance} excludeIds={stack.map((s) => s.id)} />
          <StackList
            substances={stack}
            onRemove={removeSubstance}
            serotoninLoad={analysis?.aggregate_serotonin_load}
            cvFlags={analysis?.aggregate_cardiovascular_flags}
          />
        </div>

        {/* Right Column — Analysis Results */}
        <div className="lg:col-span-2">
          {stack.length === 0 ? (
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-12 text-center">
              <p className="text-5xl mb-4">⚗️</p>
              <h2 className="text-xl font-semibold mb-2">Add your substances</h2>
              <p className="text-[var(--color-text-muted)] max-w-md mx-auto">
                Search for your medications, supplements, and dietary factors.
                Apothecary will analyze how they work together — interactions,
                timing, and nutrient gaps.
              </p>
            </div>
          ) : (
            <>
              {/* Severity Summary Bar */}
              {analysis && (
                <div className="flex gap-3 mb-4 flex-wrap">
                  {analysis.counts.critical > 0 && (
                    <span className="px-3 py-1 rounded-full text-sm font-medium bg-red-500/15 text-red-400 border border-red-500/30">
                      🔴 {analysis.counts.critical} Critical
                    </span>
                  )}
                  {analysis.counts.high > 0 && (
                    <span className="px-3 py-1 rounded-full text-sm font-medium bg-orange-500/15 text-orange-400 border border-orange-500/30">
                      🟠 {analysis.counts.high} High
                    </span>
                  )}
                  {analysis.counts.moderate > 0 && (
                    <span className="px-3 py-1 rounded-full text-sm font-medium bg-yellow-500/15 text-yellow-400 border border-yellow-500/30">
                      🟡 {analysis.counts.moderate} Moderate
                    </span>
                  )}
                  {analysis.counts.low > 0 && (
                    <span className="px-3 py-1 rounded-full text-sm font-medium bg-blue-500/15 text-blue-400 border border-blue-500/30">
                      🔵 {analysis.counts.low} Low
                    </span>
                  )}
                  {analysis.counts.beneficial > 0 && (
                    <span className="px-3 py-1 rounded-full text-sm font-medium bg-green-500/15 text-green-400 border border-green-500/30">
                      🟢 {analysis.counts.beneficial} Beneficial
                    </span>
                  )}
                </div>
              )}

              {/* Tab Bar */}
              <div className="flex border-b border-[var(--color-border)] mb-4">
                {(
                  [
                    ["interactions", "Interactions"],
                    ["timeline", "Daily Timeline"],
                    ["depletions", "Nutrient Gaps"],
                  ] as [Tab, string][]
                ).map(([tab, label]) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === tab
                        ? "border-[var(--color-accent)] text-[var(--color-accent)]"
                        : "border-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
                    }`}
                  >
                    {label}
                    {tab === "interactions" && analysis && (
                      <span className="ml-1.5 text-xs opacity-60">
                        ({analysis.interactions.length})
                      </span>
                    )}
                    {tab === "depletions" && analysis && analysis.depletion_gaps.length > 0 && (
                      <span className="ml-1.5 text-xs opacity-60">
                        ({analysis.depletion_gaps.length})
                      </span>
                    )}
                  </button>
                ))}
              </div>

              {/* Loading State */}
              {loading && (
                <div className="text-center py-8 text-[var(--color-text-muted)]">
                  Analyzing...
                </div>
              )}

              {/* Error State */}
              {error && (
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-red-400">
                  {error}
                </div>
              )}

              {/* Tab Content */}
              {!loading && analysis && (
                <>
                  {activeTab === "interactions" && (
                    <InteractionPanel interactions={analysis.interactions} />
                  )}
                  {activeTab === "timeline" && timeline && (
                    <TimelinePanel timeline={timeline} />
                  )}
                  {activeTab === "depletions" && (
                    <DepletionPanel gaps={analysis.depletion_gaps} />
                  )}
                </>
              )}

              {/* Disclaimer */}
              <p className="mt-6 text-xs text-[var(--color-text-muted)] leading-relaxed">
                This report is for informational purposes only and does not
                constitute medical advice. Always consult a qualified healthcare
                professional before starting, stopping, or changing any
                medication or supplement.
              </p>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
