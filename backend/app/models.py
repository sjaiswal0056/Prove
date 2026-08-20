from datetime import datetime
from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class ProofRecord(Base):
    __tablename__ = "proofs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_role: Mapped[str] = mapped_column(String(120))
    input_data: Mapped[dict] = mapped_column(JSON)
    analysis: Mapped[dict] = mapped_column(JSON)
    artifact: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
