from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class EvidenceInput(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    type: Literal["github", "certificate", "resume", "portfolio", "document", "link", "other"] = "other"
    url: str | None = None
    description: str | None = Field(default=None, max_length=1000)


class ProofRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=120)
    target_domain: str = Field(min_length=2, max_length=120)
    claimed_skills: list[str] = Field(min_length=1, max_length=20)
    experience: str = Field(min_length=10, max_length=8000)
    project_description: str = Field(default="", max_length=8000)
    evidence: list[EvidenceInput] = Field(default_factory=list, max_length=20)
    outcome: str = Field(default="", max_length=2000)
    ai_usage: Literal["AI-assisted", "AI-generated", "AI-dependent", "Not specified"] = "Not specified"

    @field_validator("claimed_skills")
    @classmethod
    def clean_skills(cls, values: list[str]) -> list[str]:
        cleaned = list(dict.fromkeys(v.strip() for v in values if v.strip()))
        if not cleaned:
            raise ValueError("At least one claimed skill is required")
        return cleaned


class Extraction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actions: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)
    context: str = ""
    contributions: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)


class SkillResult(BaseModel):
    skill: str
    level: Literal["L0", "L1", "L2", "L3", "L4", "L5"]
    evidence_strength: Literal["None", "Weak", "Moderate", "Strong"]
    status: Literal["Proven", "Implied", "Claimed", "Unproven"]
    reason: str
    matched_evidence: list[str] = Field(default_factory=list)


class EvidenceQuality(BaseModel):
    relevance: float
    depth: float
    ownership: float
    outcome: float
    verifiability: float
    recency: float
    transferability: float
    overall: float
    rating: Literal["Low", "Moderate", "High"]


class ClaimCheck(BaseModel):
    claim: str
    status: Literal["supported", "unsupported"]
    reason: str


class ProofGap(BaseModel):
    skill: str
    status: str
    reason: str
    suggested_proof: str
    required_evidence: list[str]


class ProofArtifact(BaseModel):
    title: str
    context: str
    problem: str
    contribution: list[str]
    tools: list[str]
    outcome: list[str]
    skills_demonstrated: list[SkillResult]
    evidence: list[str]
    evidence_quality: str
    ai_provenance: str


class AnalysisResponse(BaseModel):
    extraction: Extraction
    skills: list[SkillResult]
    evidence_quality: EvidenceQuality
    claim_checks: list[ClaimCheck]
    proof_gaps: list[ProofGap]
    artifact: ProofArtifact


class BuildResponse(AnalysisResponse):
    id: int
    created_at: datetime


class StoredProof(BuildResponse):
    input: ProofRequest
