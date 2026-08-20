from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import ProofRecord
from .schemas import AnalysisResponse, BuildResponse, ProofRequest, StoredProof
from .services import LLMServiceError, run_analysis

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Gurukul PROVE API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health(): return {"status": "ok"}


@app.post("/api/proof/analyze", response_model=AnalysisResponse, summary="Analyze evidence without storing it")
def analyze(request: ProofRequest):
    try: return run_analysis(request)
    except LLMServiceError as exc: raise HTTPException(status_code=503, detail=str(exc))


@app.post("/api/proof/build", response_model=BuildResponse, summary="Analyze and persist a proof artifact")
def build(request: ProofRequest, db: Session = Depends(get_db)):
    try: result = run_analysis(request)
    except LLMServiceError as exc: raise HTTPException(status_code=503, detail=str(exc))
    record = ProofRecord(target_role=request.target_role, input_data=request.model_dump(mode="json"), analysis=result.model_dump(mode="json"), artifact=result.artifact.model_dump(mode="json"))
    db.add(record); db.commit(); db.refresh(record)
    return BuildResponse(id=record.id, created_at=record.created_at, **result.model_dump())


@app.get("/api/proof/{proof_id}", response_model=StoredProof, summary="Retrieve a stored proof artifact")
def get_proof(proof_id: int, db: Session = Depends(get_db)):
    record = db.get(ProofRecord, proof_id)
    if not record: raise HTTPException(status_code=404, detail="Proof artifact not found")
    return StoredProof(id=record.id, created_at=record.created_at, input=record.input_data, **record.analysis)
