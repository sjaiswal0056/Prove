# Evaluation / demo cases

| Case | Input | Expected behavior |
|---|---|---|
| Strong evidence | Excel/SQL actions plus GitHub evidence | Both skills Proven, L3 |
| Missing evidence | Python listed but never used | Claimed, L0 and proof gap |
| Unsupported metric | “Improved conversion by 40%” without evidence | `unsupported`; not added to artifact outcome |
| Invalid LLM | Extractor raises malformed output error | Safe 503, no persistence |
| Empty input | Missing required API fields | FastAPI 422 validation |
