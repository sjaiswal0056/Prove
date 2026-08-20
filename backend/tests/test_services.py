from app.schemas import Extraction, ProofRequest
from app.services import LLMServiceError, analyze_skills, run_analysis

def req(): return ProofRequest(target_role="Analyst", target_domain="Analytics", claimed_skills=["Python"], experience="I wrote SQL queries for a dashboard.")

def test_claimed_when_missing():
    result = analyze_skills(req(), Extraction(actions=["wrote queries"], tools=["SQL"]))
    assert result[0].status == "Claimed"

class BadExtractor:
    def extract(self, request): raise LLMServiceError("bad response")

def test_bad_llm_is_safe_error():
    try: run_analysis(req(), BadExtractor())
    except LLMServiceError: pass
    else: assert False
