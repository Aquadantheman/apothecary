/**
 * Apothecary API client
 */

const API_BASE = "/api";

export interface SubstanceSummary {
  id: string;
  name: string;
  type: string;
  category: string;
  cyp450: string[];
  serotonin_load: number;
  common_names: string[];
}

export interface Interaction {
  substances: string[];
  type: string;
  severity: "critical" | "high" | "moderate" | "low" | "beneficial";
  confidence: string;
  title: string;
  mechanism: string;
  recommendation: string;
  pathway: string | null;
  timing_relevant: boolean;
  timing_suggestion: string | null;
}

export interface DepletionGap {
  nutrient: string;
  depleted_by: string[];
  mechanism: string;
  confidence: string;
  clinical_significance: string;
  suggestion: string;
  food_sources: string[];
  symptoms: string[];
  lifestyle_tips: string[];
}

export interface AnalysisResult {
  interactions: Interaction[];
  depletion_gaps: DepletionGap[];
  aggregate_serotonin_load: number;
  aggregate_cardiovascular_flags: number;
  counts: Record<string, number>;
}

export interface ScheduledDose {
  substance_id: string;
  substance_name: string;
  rationale: string;
  food_note: string | null;
}

export interface TimeBlock {
  name: string;
  label: string;
  clock_time: string;
  doses: ScheduledDose[];
  meal_note: string | null;
}

export interface Timeline {
  wake_time: string;
  sleep_target: string;
  blocks: TimeBlock[];
  notes: string[];
}

export async function searchSubstances(
  query?: string
): Promise<SubstanceSummary[]> {
  const params = query ? `?q=${encodeURIComponent(query)}` : "";
  const res = await fetch(`${API_BASE}/substances${params}`);
  if (!res.ok) throw new Error("Failed to fetch substances");
  return res.json();
}

export async function getSubstance(id: string) {
  const res = await fetch(`${API_BASE}/substances/${id}`);
  if (!res.ok) throw new Error(`Substance ${id} not found`);
  return res.json();
}

export async function analyzeStack(
  substanceIds: string[],
  wakeTime = "07:00",
  sleepTarget = "23:00"
): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      substance_ids: substanceIds,
      wake_time: wakeTime,
      sleep_target: sleepTarget,
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Analysis failed");
  }
  return res.json();
}

export async function getTimeline(
  substanceIds: string[],
  wakeTime = "07:00",
  sleepTarget = "23:00"
): Promise<Timeline> {
  const res = await fetch(`${API_BASE}/timeline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      substance_ids: substanceIds,
      wake_time: wakeTime,
      sleep_target: sleepTarget,
    }),
  });
  if (!res.ok) throw new Error("Timeline generation failed");
  return res.json();
}
