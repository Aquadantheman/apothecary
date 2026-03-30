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
              {/* Analysis Summary */}
              {analysis && (
                <div className={`rounded-lg border p-4 mb-4 ${
                  (analysis.counts.critical || 0) > 0
                    ? "border-red-500/30 bg-red-500/5"
                    : (analysis.counts.high || 0) > 0
                      ? "border-orange-500/20 bg-orange-500/5"
                      : (analysis.counts.beneficial || 0) > 0
                        ? "border-green-500/20 bg-green-500/5"
                        : "border-[var(--color-border)] bg-[var(--color-surface)]"
                }`}>
                  <p className="text-sm leading-relaxed">
                    {(analysis.counts.critical || 0) > 0 ? (
                      <>
                        <span className="font-semibold text-red-400">⚠ Action needed:</span>{" "}
                        {analysis.counts.critical} combination{(analysis.counts.critical || 0) > 1 ? "s" : ""} in your
                        stack {(analysis.counts.critical || 0) > 1 ? "are" : "is"} potentially dangerous.
                        Review the critical interactions below and discuss with your prescriber or pharmacist before continuing.
                      </>
                    ) : (analysis.counts.high || 0) > 0 ? (
                      <>
                        <span className="font-semibold text-orange-400">Worth reviewing:</span>{" "}
                        No dangerous combinations detected, but {analysis.counts.high} interaction{(analysis.counts.high || 0) > 1 ? "s" : ""} may
                        affect how your medications work. These are common in prescribed regimens — review the details
                        below and mention to your prescriber at your next visit.
                        {(analysis.counts.beneficial || 0) > 0 && (
                          <span className="text-green-400"> {analysis.counts.beneficial} beneficial combination{(analysis.counts.beneficial || 0) > 1 ? "s" : ""} detected.</span>
                        )}
                      </>
                    ) : (analysis.counts.moderate || 0) > 0 ? (
                      <>
                        <span className="font-semibold text-green-400">Looking good.</span>{" "}
                        No significant interactions detected. {analysis.counts.moderate} minor note{(analysis.counts.moderate || 0) > 1 ? "s" : ""} to
                        be aware of, but nothing that requires immediate action.
                        {(analysis.counts.beneficial || 0) > 0 && (
                          <span className="text-green-400"> {analysis.counts.beneficial} beneficial combination{(analysis.counts.beneficial || 0) > 1 ? "s" : ""} detected.</span>
                        )}
                      </>
                    ) : (
                      <>
                        <span className="font-semibold text-green-400">All clear.</span>{" "}
                        No significant interactions detected between your substances.
                        {(analysis.counts.beneficial || 0) > 0 && (
                          <span> {analysis.counts.beneficial} beneficial combination{(analysis.counts.beneficial || 0) > 1 ? "s" : ""} found.</span>
                        )}
                      </>
                    )}
                  </p>

                  {/* Compact severity counts */}
                  <div className="flex gap-3 mt-2 flex-wrap">
                    {Object.entries(analysis.counts)
                      .filter(([, count]) => count > 0)
                      .map(([severity, count]) => {
                        const styles: Record<string, string> = {
                          critical: "text-red-400",
                          high: "text-orange-400",
                          moderate: "text-yellow-400",
                          low: "text-blue-400",
                          beneficial: "text-green-400",
                        };
                        return (
                          <span key={severity} className={`text-xs ${styles[severity] || "text-gray-400"}`}>
                            {count} {severity}
                          </span>
                        );
                      })}
                  </div>
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
              <div className="mt-6 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
                <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">
                  <span className="font-medium text-[var(--color-text)]">About this analysis:</span>{" "}
                  Apothecary identifies potential interactions based on known pharmacological pathways (CYP450 metabolism, receptor activity, nutrient depletions). 
                  This is not a substitute for professional medical advice. Many flagged interactions are common in prescribed regimens and are already accounted for by your doctor. 
                  Use this as a conversation starter with your prescriber or pharmacist — not as a reason to change your medications on your own.
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
