"""Evidence rating and source tracking models."""

from enum import Enum
from pydantic import BaseModel


class ConfidenceTier(str, Enum):
    """How confident we are in a claim, based on evidence quality."""

    ESTABLISHED = "established"  # Human RCTs, FDA labels, PK studies
    PROBABLE = "probable"  # Human observational, consistent case reports
    POSSIBLE = "possible"  # Animal studies, mechanistic reasoning + partial human data
    THEORETICAL = "theoretical"  # Inferred from pharmacology, no direct study
    ANECDOTAL = "anecdotal"  # Community reports, no formal study


class StudyType(str, Enum):
    """Type of study backing a claim."""

    RCT = "rct"
    SYSTEMATIC_REVIEW = "systematic_review"
    PHARMACOKINETIC = "pharmacokinetic"
    OBSERVATIONAL = "observational"
    CASE_REPORT = "case_report"
    ANIMAL = "animal"
    IN_VITRO = "in_vitro"
    FDA_LABEL = "fda_label"
    EXPERT_CONSENSUS = "expert_consensus"
    MECHANISTIC = "mechanistic"
    COMMUNITY = "community"


class EvidenceSource(BaseModel):
    """A single source backing a claim."""

    type: StudyType
    reference: str  # Human-readable citation
    pmid: str | None = None  # PubMed ID if applicable
    url: str | None = None
    sample_size: int | None = None
    year: int | None = None
    summary: str | None = None  # Brief description of finding


class EvidencedClaim(BaseModel):
    """A claim with its confidence rating and sources.

    Used as a mixin pattern — other models reference this
    when they need to attach evidence to a specific assertion.
    """

    confidence: ConfidenceTier
    sources: list[EvidenceSource] = []
    notes: str | None = None
