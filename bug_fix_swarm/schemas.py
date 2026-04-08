"""Typed handoff packets — every agent reads/writes structured boundaries (not loose prose)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class BugSummary(BaseModel):
    symptoms: str
    scope: str
    severity: Literal["P0", "P1", "P2", "P3", "unknown"]


class TriageHandoff(BaseModel):
    title: str
    expected_behavior: str
    actual_behavior: str
    environment: dict[str, str]
    hints: list[str]
    hypotheses: list[str] = Field(default_factory=list)
    bug_summary: BugSummary


class LogLineScore(BaseModel):
    line_no: int
    text: str
    salience: float
    tags: list[str] = Field(default_factory=list)
    is_red_herring_risk: bool = False


class LogMiningHandoff(BaseModel):
    stack_frames: list[str]
    error_signatures: list[str]
    correlated_symbols: list[str]
    excerpt_indices: list[int]
    noise_notes: str


class ReproHandoff(BaseModel):
    artifact_path: str
    run_command: list[str]
    failed: bool
    stdout: str
    stderr: str
    exit_code: int | None


class FixPlanHandoff(BaseModel):
    root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    files_impacted: list[str]
    approach: str
    risks: list[str]
    validation_plan: list[str]


class CriticHandoff(BaseModel):
    repro_minimal_ok: bool
    fix_plan_safe: bool
    edge_cases: list[str]
    requests_more_evidence: list[str]


class FinalReport(BaseModel):
    bug_summary: BugSummary
    evidence: dict[str, str | list[str]]
    repro_steps: list[str]
    repro_artifact_path: str
    root_cause_hypothesis: str
    hypothesis_confidence: float
    patch_plan: dict[str, str | list[str]]
    validation_plan: dict[str, list[str]]
    open_questions: list[str]


def model_to_dict(model: BaseModel) -> dict:
    """Pydantic v2: model_dump(); v1: dict()."""
    md = getattr(model, "model_dump", None)
    if callable(md):
        return md()
    return model.dict()
