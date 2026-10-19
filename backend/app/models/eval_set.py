import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, DateTime, Float, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.config import settings
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class EvalSet(Base):
    __tablename__ = "eval_sets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(String(64), index=True, default="", server_default="")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    domain: Mapped[str] = mapped_column(String(100), default="General QA")
    eval_type: Mapped[str] = mapped_column(String(50), default="rag_qa")
    target_capability: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    test_cases: Mapped[List["TestCase"]] = relationship(
        "TestCase",
        back_populates="eval_set",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    runs: Mapped[List["EvalRun"]] = relationship(
        "EvalRun",
        back_populates="eval_set",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    eval_set_id: Mapped[str] = mapped_column(String(36), ForeignKey("eval_sets.id"), nullable=False)
    prompt_input: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rubric: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(50), default="medium")
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    assertions: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    eval_set: Mapped["EvalSet"] = relationship("EvalSet", back_populates="test_cases")


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    eval_set_id: Mapped[str] = mapped_column(String(36), ForeignKey("eval_sets.id"), nullable=False)
    model_tested: Mapped[str] = mapped_column(String(100), default=lambda: settings.GEMINI_MODEL)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    passed_count: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    eval_set: Mapped["EvalSet"] = relationship("EvalSet", back_populates="runs")
    results: Mapped[List["EvaluationResult"]] = relationship(
        "EvaluationResult",
        back_populates="eval_run",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    eval_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("eval_runs.id"), nullable=False)
    test_case_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_cases.id"), nullable=False)
    actual_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    eval_run: Mapped["EvalRun"] = relationship("EvalRun", back_populates="results")
