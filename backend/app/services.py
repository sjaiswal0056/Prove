import json
import re
from collections.abc import Callable
from .config import settings
from .schemas import (AnalysisResponse, ClaimCheck, EvidenceQuality, Extraction,
                      ProofArtifact, ProofGap, ProofRequest, SkillResult)


class LLMServiceError(RuntimeError):
    pass


class Extractor:
    """Provider boundary: only this component knows about mock/Gemini."""
    def extract(self, request: ProofRequest) -> Extraction:
        if settings.llm_mode == "mock":
            return self._mock(request)
        if settings.llm_provider != "gemini" or not settings.gemini_api_key:
            raise LLMServiceError("Live LLM is not configured. Set GEMINI_API_KEY or use LLM_MODE=mock.")
        return self._gemini(request)

    def _mock(self, request: ProofRequest) -> Extraction:
        text = " ".join([request.experience, request.project_description, request.outcome])
        actions = re.findall(r"\b(?:built|created|cleaned|wrote|analyzed|analysed|designed|developed|calculated|implemented)\b[^.]*", text, re.I)
        known_tools = ["Python", "SQL", "Excel", "Pandas", "Streamlit", "Tableau", "Power BI", "React", "FastAPI", "GitHub"]
        tools = [tool for tool in known_tools if re.search(rf"\b{re.escape(tool)}\b", text, re.I)]
        outputs = [x for x in ["dashboard" if re.search("dashboard", text, re.I) else "", "repository" if any(e.type == "github" for e in request.evidence) else ""] if x]
        outcomes = [s.strip() for s in re.split(r"[.!]", request.outcome) if s.strip()]
        return Extraction(actions=actions[:8], tools=tools, outputs=outputs,
                          outcomes=outcomes, context=request.experience[:280],
                          contributions=actions[:8], evidence_references=[e.name for e in request.evidence])

    def _gemini(self, request: ProofRequest) -> Extraction:
        last_error: Exception | None = None
        for _ in range(2):  # one bounded retry for malformed/temporary provider output
            try:
                from google import genai
                client = genai.Client(api_key=settings.gemini_api_key)
                prompt = "Extract JSON only with actions, tools, outputs, outcomes, context, contributions, evidence_references. Text: " + request.experience + " " + request.project_description
                response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
                return Extraction.model_validate(json.loads(response.text))
            except Exception as exc:
                last_error = exc
        raise LLMServiceError("The LLM returned unusable structured data after retry. Please retry.") from last_error


def _contains_skill(skill: str, text: str, extraction: Extraction) -> bool:
    normalized = skill.lower()
    aliases = {"data analysis": ["analysis", "analy", "insight", "dashboard", "data"], "excel": ["excel", "spreadsheet"]}
    terms = aliases.get(normalized, [normalized])
    return any(term in text.lower() for term in terms) or any(term in x.lower() for x in extraction.tools for term in terms)


def analyze_skills(request: ProofRequest, extraction: Extraction) -> list[SkillResult]:
    text = " ".join([request.experience, request.project_description, request.outcome, " ".join(e.description or "" for e in request.evidence)])
    has_verifiable = bool(request.evidence)
    results = []
    for skill in request.claimed_skills:
        direct = _contains_skill(skill, text, extraction)
        action_count = len(extraction.actions)
        if direct and action_count >= 1 and has_verifiable:
            level, strength, status = "L3", "Strong", "Proven"
            reason = f"{skill} is directly mentioned alongside work actions and supplied evidence."
        elif direct:
            level, strength, status = "L2", "Moderate", "Implied"
            reason = f"{skill} appears in the narrative, but direct verifiable proof is limited."
        elif skill.lower() in " ".join(request.claimed_skills).lower():
            level, strength, status = "L0", "None", "Claimed"
            reason = f"{skill} is listed but supplied material does not demonstrate meaningful usage."
        else:
            level, strength, status = "L0", "None", "Unproven"
            reason = f"No claim or evidence establishes {skill}."
        matched = [e.name for e in request.evidence] if direct else []
        results.append(SkillResult(skill=skill, level=level, evidence_strength=strength, status=status, reason=reason, matched_evidence=matched))
    return results


def score_evidence(request: ProofRequest, extraction: Extraction, skills: list[SkillResult]) -> EvidenceQuality:
    text = " ".join([request.experience, request.project_description, request.outcome]).lower()
    relevance = round(sum(s.status in ("Proven", "Implied") for s in skills) / len(skills), 2)
    depth = min(1.0, round((len(extraction.actions) + len(extraction.outputs)) / 6, 2))
    ownership = 0.8 if re.search(r"\b(i|my|i built|i wrote|i created)\b", text) else 0.4
    outcome = 0.8 if request.outcome.strip() else (0.5 if extraction.outcomes else 0.2)
    verifiability = min(1.0, 0.25 + 0.25 * len(request.evidence))
    recency = 0.7  # no dates supplied: neutral, explainable default
    transferability = 0.8 if request.target_domain.lower() in text else 0.6
    weights = [0.2, .15, .15, .15, .15, .1, .1]
    values = [relevance, depth, ownership, outcome, verifiability, recency, transferability]
    overall = round(sum(a*b for a, b in zip(values, weights)), 2)
    rating = "High" if overall >= .75 else "Moderate" if overall >= .45 else "Low"
    return EvidenceQuality(relevance=relevance, depth=depth, ownership=ownership, outcome=outcome, verifiability=verifiability, recency=recency, transferability=transferability, overall=overall, rating=rating)


def check_claims(request: ProofRequest) -> list[ClaimCheck]:
    claims = re.findall(r"[^.]*\b\d+(?:\.\d+)?\s*(?:%|percent|rows|users|hours)\b[^.]*", request.experience + "." + request.outcome, re.I)
    names = " ".join(e.name + " " + (e.description or "") for e in request.evidence).lower()
    return [ClaimCheck(claim=c.strip(), status="supported" if any(ch.isdigit() and ch in names for ch in c) else "unsupported", reason="Supplied evidence references the number." if any(ch.isdigit() and ch in names for ch in c) else "No supplied evidence supports this numerical outcome.") for c in claims]


def proof_gaps(request: ProofRequest, skills: list[SkillResult]) -> list[ProofGap]:
    gaps = []
    for item in skills:
        if item.status != "Proven":
            gaps.append(ProofGap(skill=item.skill, status=item.status, reason=item.reason,
                suggested_proof=f"Create a focused {item.skill} mini-project relevant to {request.target_role}, showing your own implementation and decisions.",
                required_evidence=["Public GitHub repository or shareable file", "README describing approach and contribution", "Concrete output or screenshot", "Short reflection on results"]))
    return gaps


def build_artifact(request: ProofRequest, extraction: Extraction, skills: list[SkillResult], quality: EvidenceQuality) -> ProofArtifact:
    safe_outcomes = [o for o in extraction.outcomes if not re.search(r"\d+\s*(%|percent)", o)]
    return ProofArtifact(title=request.project_description[:90] or f"{request.target_role} Evidence Profile", context=extraction.context,
        problem=request.project_description or "Professional experience supplied by the candidate.", contribution=extraction.contributions,
        tools=extraction.tools, outcome=safe_outcomes, skills_demonstrated=[s for s in skills if s.status in ("Proven", "Implied")],
        evidence=[e.name for e in request.evidence], evidence_quality=quality.rating, ai_provenance=request.ai_usage)


def run_analysis(request: ProofRequest, extractor: Extractor | None = None) -> AnalysisResponse:
    extraction = (extractor or Extractor()).extract(request)
    skills = analyze_skills(request, extraction)
    quality = score_evidence(request, extraction, skills)
    return AnalysisResponse(extraction=extraction, skills=skills, evidence_quality=quality,
        claim_checks=check_claims(request), proof_gaps=proof_gaps(request, skills), artifact=build_artifact(request, extraction, skills, quality))
