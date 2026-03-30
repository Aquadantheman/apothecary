"use client";

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

export function StackList({ substances, onRemove, serotoninLoad, cvFlags }: Props) {
  if (substances.length === 0) return null;

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
                  {s.category}
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

      {/* Aggregate Metrics */}
      {(serotoninLoad !== undefined || cvFlags !== undefined) && (
        <div className="px-4 py-2.5 border-t border-[var(--color-border)] space-y-1">
          {serotoninLoad !== undefined && serotoninLoad > 0 && (
            <div className="flex justify-between text-xs">
              <span className="text-[var(--color-text-muted)]">
                Serotonin load
              </span>
              <span
                className={
                  serotoninLoad >= 0.9
                    ? "text-red-400 font-medium"
                    : serotoninLoad >= 0.6
                      ? "text-yellow-400"
                      : "text-green-400"
                }
              >
                {serotoninLoad.toFixed(2)} / 1.0
              </span>
            </div>
          )}
          {cvFlags !== undefined && cvFlags > 1 && (
            <div className="flex justify-between text-xs">
              <span className="text-[var(--color-text-muted)]">
                CV-flagged substances
              </span>
              <span className="text-yellow-400">{cvFlags}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
