"""Apothecary API — FastAPI backend for the web frontend."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from apothecary.data.loader import SubstanceDatabase
from apothecary.engine.interaction_engine import analyze_stack
from apothecary.engine.timing_engine import generate_timeline
from apothecary.models.interaction import Severity

# === Load Database ===

DATA_DIR = Path(__file__).parent.parent / "data" / "curated"
db = SubstanceDatabase()
db.load_directory(DATA_DIR)

# === App ===

app = FastAPI(
    title="Apothecary API",
    description="Drug-supplement interaction analysis, timing optimization, and mechanism explanation.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Response Models ===

class SubstanceSummary(BaseModel):
    id: str
    name: str
    type: str
    category: str
    cyp450: list[str]
    serotonin_load: float
    common_names: list[str]
    data_tier: str


class InteractionResponse(BaseModel):
    substances: list[str]
    type: str
    severity: str
    confidence: str
    title: str
    mechanism: str
    recommendation: str
    pathway: str | None = None
    timing_relevant: bool = False
    timing_suggestion: str | None = None


class DepletionGapResponse(BaseModel):
    nutrient: str
    depleted_by: list[str]
    mechanism: str
    confidence: str
    clinical_significance: str
    suggestion: str


class AnalysisResponse(BaseModel):
    interactions: list[InteractionResponse]
    depletion_gaps: list[DepletionGapResponse]
    aggregate_serotonin_load: float
    aggregate_cardiovascular_flags: int
    counts: dict[str, int]


class ScheduledDoseResponse(BaseModel):
    substance_id: str
    substance_name: str
    rationale: str
    food_note: str | None = None


class TimeBlockResponse(BaseModel):
    name: str
    label: str
    clock_time: str
    doses: list[ScheduledDoseResponse]
    meal_note: str | None = None


class TimelineResponse(BaseModel):
    wake_time: str
    sleep_target: str
    blocks: list[TimeBlockResponse]
    notes: list[str]


class AnalyzeRequest(BaseModel):
    substance_ids: list[str]
    wake_time: str = "07:00"
    sleep_target: str = "23:00"


# === Endpoints ===

@app.get("/api/substances", response_model=list[SubstanceSummary])
def list_substances(q: str | None = None):
    """List all substances, optionally filtered by search query."""
    if q:
        results = db.search(q)
    else:
        results = db.all()

    return [
        SubstanceSummary(
            id=s.id,
            name=s.name,
            type=s.type.value,
            category=s.category,
            cyp450=[
                f"{e.enzyme}({e.role.value[0]})" for e in s.metabolism.cyp450
            ],
            serotonin_load=s.safety.serotonin_load,
            common_names=s.common_names,
            data_tier=s.metadata.data_tier.value if hasattr(s.metadata, 'data_tier') else "tier_1",
        )
        for s in sorted(results, key=lambda x: x.name)
    ]


@app.get("/api/substances/{substance_id}")
def get_substance(substance_id: str):
    """Get full substance profile."""
    s = db.get(substance_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"Substance '{substance_id}' not found")
    return s.model_dump()


@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze(request: AnalyzeRequest):
    """Run full interaction analysis on a list of substances."""
    substances = []
    missing = []
    for sid in request.substance_ids:
        s = db.get(sid)
        if s:
            substances.append(s)
        else:
            missing.append(sid)

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Substances not found: {', '.join(missing)}",
        )

    if len(substances) < 1:
        raise HTTPException(status_code=400, detail="At least one substance required")

    result = analyze_stack(substances)

    return AnalysisResponse(
        interactions=[
            InteractionResponse(
                substances=i.substances,
                type=i.type.value,
                severity=i.severity.value,
                confidence=i.confidence.value,
                title=i.title,
                mechanism=i.mechanism,
                recommendation=i.recommendation,
                pathway=i.pathway,
                timing_relevant=i.timing_relevant,
                timing_suggestion=i.timing_suggestion,
            )
            for i in result.interactions
        ],
        depletion_gaps=[
            DepletionGapResponse(
                nutrient=g.nutrient,
                depleted_by=g.depleted_by,
                mechanism=g.mechanism,
                confidence=g.confidence.value,
                clinical_significance=g.clinical_significance,
                suggestion=g.suggestion,
            )
            for g in result.depletion_gaps
        ],
        aggregate_serotonin_load=result.aggregate_serotonin_load,
        aggregate_cardiovascular_flags=result.aggregate_cardiovascular_flags,
        counts=result.interaction_count_by_severity,
    )


@app.post("/api/timeline", response_model=TimelineResponse)
def timeline(request: AnalyzeRequest):
    """Generate optimized daily timing schedule."""
    substances = []
    for sid in request.substance_ids:
        s = db.get(sid)
        if s:
            substances.append(s)

    if not substances:
        raise HTTPException(status_code=400, detail="No valid substances found")

    tl = generate_timeline(
        substances,
        wake_time=request.wake_time,
        sleep_target=request.sleep_target,
    )

    return TimelineResponse(
        wake_time=tl.wake_time,
        sleep_target=tl.sleep_target,
        blocks=[
            TimeBlockResponse(
                name=b.name,
                label=b.label,
                clock_time=b.clock_time,
                doses=[
                    ScheduledDoseResponse(
                        substance_id=d.substance_id,
                        substance_name=d.substance_name,
                        rationale=d.rationale,
                        food_note=d.food_note,
                    )
                    for d in b.doses
                ],
                meal_note=b.meal_note,
            )
            for b in tl.active_blocks
        ],
        notes=tl.notes,
    )


@app.get("/api/check/{substance_a}/{substance_b}", response_model=AnalysisResponse)
def check_pair(substance_a: str, substance_b: str):
    """Quick pairwise interaction check."""
    a = db.get(substance_a)
    b = db.get(substance_b)
    if not a:
        raise HTTPException(status_code=404, detail=f"Substance '{substance_a}' not found")
    if not b:
        raise HTTPException(status_code=404, detail=f"Substance '{substance_b}' not found")

    result = analyze_stack([a, b])

    return AnalysisResponse(
        interactions=[
            InteractionResponse(
                substances=i.substances,
                type=i.type.value,
                severity=i.severity.value,
                confidence=i.confidence.value,
                title=i.title,
                mechanism=i.mechanism,
                recommendation=i.recommendation,
                pathway=i.pathway,
                timing_relevant=i.timing_relevant,
                timing_suggestion=i.timing_suggestion,
            )
            for i in result.interactions
        ],
        depletion_gaps=[
            DepletionGapResponse(
                nutrient=g.nutrient,
                depleted_by=g.depleted_by,
                mechanism=g.mechanism,
                confidence=g.confidence.value,
                clinical_significance=g.clinical_significance,
                suggestion=g.suggestion,
            )
            for g in result.depletion_gaps
        ],
        aggregate_serotonin_load=result.aggregate_serotonin_load,
        aggregate_cardiovascular_flags=result.aggregate_cardiovascular_flags,
        counts=result.interaction_count_by_severity,
    )


@app.get("/health")
def health():
    return {"status": "ok", "substances": db.count}
