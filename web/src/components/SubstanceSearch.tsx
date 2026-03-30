"use client";

import { useState, useEffect, useRef } from "react";
import { searchSubstances, type SubstanceSummary } from "@/lib/api";

interface Props {
  onSelect: (substance: SubstanceSummary) => void;
  excludeIds: string[];
}

const TYPE_COLORS: Record<string, string> = {
  prescription: "text-blue-400",
  supplement: "text-green-400",
  otc: "text-yellow-400",
  dietary: "text-orange-400",
};

export function SubstanceSearch({ onSelect, excludeIds }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SubstanceSummary[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [highlightIdx, setHighlightIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (query.length < 1) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const all = await searchSubstances(query);
        const filtered = all.filter((s) => !excludeIds.includes(s.id));
        setResults(filtered);
        setIsOpen(filtered.length > 0);
        setHighlightIdx(0);
      } catch {
        setResults([]);
      }
    }, 150);

    return () => clearTimeout(timer);
  }, [query, excludeIds]);

  const select = (substance: SubstanceSummary) => {
    onSelect(substance);
    setQuery("");
    setIsOpen(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlightIdx((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlightIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && results[highlightIdx]) {
      e.preventDefault();
      select(results[highlightIdx]);
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  return (
    <div className="relative">
      <label className="block text-sm font-medium text-[var(--color-text-muted)] mb-1.5">
        Add to your stack
      </label>
      <input
        ref={inputRef}
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => results.length > 0 && setIsOpen(true)}
        onBlur={() => setTimeout(() => setIsOpen(false), 200)}
        placeholder="Search medications, supplements..."
        className="w-full px-4 py-2.5 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-accent)] transition-colors"
      />

      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute top-full left-0 right-0 mt-1 rounded-lg bg-[var(--color-surface-2)] border border-[var(--color-border)] shadow-xl z-50 max-h-72 overflow-y-auto"
        >
          {results.map((s, i) => (
            <button
              key={s.id}
              onClick={() => select(s)}
              className={`w-full px-4 py-2.5 text-left flex items-center justify-between transition-colors ${
                i === highlightIdx
                  ? "bg-[var(--color-accent)]/10"
                  : "hover:bg-white/5"
              }`}
            >
              <div>
                <div className="font-medium text-sm">{s.name}</div>
                <div className="text-xs text-[var(--color-text-muted)]">
                  {s.category}
                  {s.cyp450.length > 0 && ` · ${s.cyp450.join(", ")}`}
                </div>
              </div>
              <span
                className={`text-xs font-medium ${TYPE_COLORS[s.type] || "text-gray-400"}`}
              >
                {s.type}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
