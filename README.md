# Gurukul Code PROVE

PROVE converts a candidate's unstructured experience into an evidence-led proof artifact. It uses an LLM only for extraction; validation, skill decisions, scoring, gaps, guardrails, and persistence are deterministic.

## Features

- FastAPI + Pydantic + SQLite API, React/TypeScript dashboard
- Mock mode for reliable demos and Gemini live-mode provider boundary
- Structured extraction, validated before it reaches business logic
- L0–L5 levels; Proven, Implied, Claimed, and Unproven statuses
- Seven-dimension, transparent quality score and targeted proof plans
- Unsupported numerical claims are clearly flagged and excluded from artifact outcomes
- Artifact persistence/retrieval and AI-use provenance

## Run locally

Use Python 3.11+ and Node 20+.

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
$env:LLM_MODE="mock"
uvicorn app.main:app --reload
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`; API documentation is at `http://localhost:8000/docs`.

## Environment

Copy `.env.example` values into your local environment (never commit an `.env`). `LLM_MODE=mock` is the default. For live Gemini set `LLM_MODE=live`, `LLM_PROVIDER=gemini`, and a local `GEMINI_API_KEY`. A missing live key returns a clear 503 configuration error.

## Tests

```bash
cd backend
pytest -q
```

## API

- `POST /api/proof/analyze` — performs a non-persistent analysis
- `POST /api/proof/build` — analyzes and stores the artifact
- `GET /api/proof/{id}` — retrieves a stored artifact
- `GET /api/health` — health check

Example request:

```json
{"target_role":"Junior Data Analyst","target_domain":"Data Analytics","claimed_skills":["Python","SQL","Excel","Data Analysis"],"experience":"I cleaned sales data in Excel, wrote SQL queries and created a dashboard.","project_description":"Sales dashboard","evidence":[{"name":"GitHub Repository","type":"github"}],"outcome":"Identified declining categories.","ai_usage":"AI-assisted"}
```

## Demo behavior

The pre-filled UI intentionally produces SQL, Excel, and Data Analysis as **Proven** when evidence is supplied; Python is **Claimed** because it is only listed. Add an unsupported statement such as “improved conversion by 40%” to see the guardrail flag it.

## Deterministic rules

Direct skill mention plus work action and supplied evidence → L3 / Proven. Direct mention without evidence → L2 / Implied. A listed but unmatched skill → L0 / Claimed. Scores combine relevance (20%), depth (15%), ownership (15%), outcome (15%), verifiability (15%), recency (10%), and transferability (10%). Recency defaults to 0.7 without dates.

## Limitations and next steps

Mock extraction is intentionally simple and keyword-based for reproducibility. Gemini output is schema-validated, but production should add JSON-schema response mode, retries with telemetry, authentication, rate limits, object storage, PostgreSQL, a work queue, and human evidence review.
