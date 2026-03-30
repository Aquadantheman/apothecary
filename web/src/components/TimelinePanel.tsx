"use client";

import type { Timeline } from "@/lib/api";

interface Props {
  timeline: Timeline;
}

const BLOCK_ICONS: Record<string, string> = {
  wake: "🌅",
  mid_morning: "☀️",
  midday: "🌞",
  afternoon: "🌤",
  evening: "🌆",
  pre_bed: "🌙",
};

export function TimelinePanel({ timeline }: Props) {
  return (
    <div className="space-y-4">
      {/* Time header */}
      <div className="flex gap-4 text-sm text-[var(--color-text-muted)]">
        <span>Wake: <strong className="text-[var(--color-text)]">{timeline.wake_time}</strong></span>
        <span>Sleep: <strong className="text-[var(--color-text)]">{timeline.sleep_target}</strong></span>
      </div>

      {/* Blocks */}
      <div className="relative">
        {/* Vertical timeline line */}
        <div className="absolute left-5 top-4 bottom-4 w-px bg-[var(--color-border)]" />

        <div className="space-y-4">
          {timeline.blocks.map((block) => (
            <div key={block.name} className="relative pl-12">
              {/* Time dot */}
              <div className="absolute left-3.5 top-3 w-3 h-3 rounded-full bg-[var(--color-accent)] border-2 border-[var(--color-bg)]" />

              <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
                {/* Block header */}
                <div className="px-4 py-2.5 border-b border-[var(--color-border)] flex items-center gap-2">
                  <span>{BLOCK_ICONS[block.name] || "⏰"}</span>
                  <span className="font-semibold text-sm">
                    {block.clock_time}
                  </span>
                  <span className="text-sm text-[var(--color-text-muted)]">
                    — {block.label}
                  </span>
                </div>

                {/* Doses */}
                <div className="divide-y divide-[var(--color-border)]">
                  {block.doses.map((dose) => (
                    <div key={dose.substance_id} className="px-4 py-2.5">
                      <div className="flex items-center gap-2">
                        <span className="text-sm">💊</span>
                        <span className="text-sm font-medium">
                          {dose.substance_name}
                        </span>
                      </div>
                      <p className="text-xs text-[var(--color-text-muted)] mt-0.5 ml-6">
                        {dose.rationale}
                      </p>
                      {dose.food_note && (
                        <p className="text-xs text-green-400 mt-0.5 ml-6">
                          🍽 {dose.food_note}
                        </p>
                      )}
                    </div>
                  ))}
                </div>

                {/* Meal note */}
                {block.meal_note && (
                  <div className="px-4 py-2.5 border-t border-[var(--color-border)] bg-yellow-500/5">
                    <p className="text-xs text-yellow-400">
                      🥗 {block.meal_note}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* General Notes */}
      {timeline.notes.length > 0 && (
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
          <h3 className="text-sm font-semibold mb-2">General Notes</h3>
          <ul className="space-y-1.5">
            {timeline.notes.map((note, i) => (
              <li key={i} className="text-xs text-[var(--color-text-muted)] leading-relaxed">
                • {note}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
