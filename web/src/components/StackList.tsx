"use client";

import { useState } from "react";
import type { SubstanceSummary } from "@/lib/api";

interface Props {
  substances: SubstanceSummary[];
  onRemove: (id: string) => void;
  serotoninLoad?: number;
  cvFlags?: number;
}

const TYPE_DOTS: Record<string, string> = {
  prescription: "bg-blue-400",
  supplement: "bg-green-400",
  otc: "bg-yellow-400",
  dietary: "bg-orange-400",
};

function getSerotoninContext(load: number): {
  label: string;
  color: string;
  explanation: string;
} {
  if (load >= 1.5) {
    return {
      label: "Elevated",
      color: "text-red-400",
      explanation:
        "Your combined serotonin load is high. This doesn't mean you're in danger — many prescribed combinations produce this level — but discuss with your prescriber, especially if you experience agitation, rapid heart rate, tremor, or confusion.",
    };
  }
  if (load >= 0.9) {
    return {
      label: "Moderate",
      color: "text-yellow-400",
      explanation:
        "This is a typical level for someone on an SSRI/SNRI with mild serotonergic supplements. Your prescriber likely accounts for this. Watch for unusual symptoms like excessive sweating, restlessness, or muscle twitching — but these combinations are commonly used safely.",
    };
  }
  if (load >= 0.4) {
    return {
      label: "Low–Moderate",
      color: "text-blue-400",
      explanation:
        "Your serotonin load is in a normal range. No special monitoring needed beyond your usual care.",
    };
  }
  return {
    label: "Minimal",
    color: "text-green-400",
    explanation: "Very low serotonergic activity. No concerns.",
  };
}

function getCVContext(flags: number): {
  label: string;
  explanation: string;
} {
  if (flags >= 3) {
    return {
      label: `${flags} substances`,
      explanation:
        "Multiple substances in your stack can affect heart rate or blood pressure. Consider monitoring BP at home and mentioning this combination to your prescriber.",
    };
  }
  if (flags >= 2) {
    return {
      label: `${flags} substances`,
      explanation:
        "Two substances with cardiovascular effects — common in many prescribed regimens. Worth monitoring if you notice heart racing or dizziness.",
    };
  }
  return {
    label: `${flags} substance`,
    explanation: "",
  };
}

export function StackList({ substances, onRemove, serotoninLoad, cvFlags }: Props) {
  const [showSerotoninInfo, setShowSerotoninInfo] = useState(false);
  const [showCVInfo, setShowCVInfo] = useState(false);

  if (substances.length === 0) return null;

  const serotoninCtx = serotoninLoad !== undefined ? getSerotoninContext(serotoninLoad) : null;
  const cvCtx = cvFlags !== undefined && cvFlags > 1 ? getCVContext(cvFlags) : null;

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
      <div className="px-4 py-3 border-b border-[var(--color-border)] flex justify-between items-center">
        <h2 className="text-sm font-semibold">
          Your Stack ({substances.length})
        </h2>
      </div>

      <div className="divide-y divide-[var(--color-border)]">
        {substances.map((s) => (
          <div
            key={s.id}
            className="px-4 py-2.5 flex items-center justify-between group"
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <span
                className={`w-2 h-2 rounded-full shrink-0 ${TYPE_DOTS[s.type] || "bg-gray-400"}`}
              />
              <div className="min-w-0">
                <div className="text-sm font-medium truncate">{s.name}</div>
                <div className="text-xs text-[var(--color-text-muted)]">
                  {s.category.replace(/_/g, " ")}
                </div>
              </div>
            </div>
            <button
              onClick={() => onRemove(s.id)}
              className="text-[var(--color-text-muted)] hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all text-lg leading-none px-1"
              aria-label={`Remove ${s.name}`}
            >
              ×
            </button>
          </div>
        ))}
      </div>

      {/* Aggregate Metrics with Context */}
      {(serotoninCtx || cvCtx) && (
        <div className="border-t border-[var(--color-border)]">
          {serotoninCtx && serotoninLoad! > 0 && (
            <div className="px-4 py-2.5">
              <button
                onClick={() => setShowSerotoninInfo(!showSerotoninInfo)}
                className="w-full flex justify-between items-center text-xs"
              >
                <span className="text-[var(--color-text-muted)] flex items-center gap-1">
                  Serotonin activity
                  <span className="text-[10px] opacity-50">ⓘ</span>
                </span>
                <span className={`font-medium ${serotoninCtx.color}`}>
                  {serotoninCtx.label}
                </span>
              </button>
              {showSerotoninInfo && (
                <p className="text-xs text-[var(--color-text-muted)] mt-2 leading-relaxed">
                  {serotoninCtx.explanation}
                </p>
              )}
            </div>
          )}
          {cvCtx && (
            <div className="px-4 py-2.5 border-t border-[var(--color-border)]">
              <button
                onClick={() => setShowCVInfo(!showCVInfo)}
                className="w-full flex justify-between items-center text-xs"
              >
                <span className="text-[var(--color-text-muted)] flex items-center gap-1">
                  Cardiovascular
                  <span className="text-[10px] opacity-50">ⓘ</span>
                </span>
                <span className="text-yellow-400 font-medium">
                  {cvCtx.label}
                </span>
              </button>
              {showCVInfo && cvCtx.explanation && (
                <p className="text-xs text-[var(--color-text-muted)] mt-2 leading-relaxed">
                  {cvCtx.explanation}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
