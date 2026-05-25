"""Pydantic DTOs for the v3 workout generation pipeline.

Single source of truth for inter-stage types. Each stage of the pipeline
consumes one type and produces the next:

    onboarding_row  →  ProfileAnalyzer  →  TrainingProfile
    TrainingProfile →  SplitPlanner     →  WeeklySplit
    WeeklySplit     →  VolumePlanner    →  VolumeTargets
    VolumeTargets   →  ExerciseSelector →  SessionCandidates per day
    SessionCandidates → SessionAssembler→  AssembledSession (LLM)
    AssembledSession → Validator        →  ValidationReport
    base_week + AssembledSession → Progression → list[WeekPlan]

Keep these models stable — they're the contract surface between services.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────
#  Lit unions (single source — reuse across schemas, validators, LLM enums)
# ──────────────────────────────────────────────────────────────────────
Goal = Literal["hypertrophy", "strength", "fat_loss", "general", "endurance", "recomp"]
Experience = Literal["beginner", "intermediate", "advanced"]
Gender = Literal["male", "female", "other", "unspecified"]
EquipmentType = Literal[
    "barbell", "dumbbell", "cable", "machine",
    "bodyweight", "kettlebell", "band", "smith",
]
MovementPattern = Literal[
    "horizontal_press", "vertical_press",
    "horizontal_pull", "vertical_pull",
    "squat", "hinge", "lunge", "carry",
    "rotation", "anti_rotation", "anti_extension",
    "iso_curl", "iso_extension", "iso_fly", "iso_raise",
    "iso_shrug", "iso_calf", "iso_wrist",
    "explosive", "gait", "stretch_mobility",
    "other",
]
SplitFamily = Literal["fb", "ul", "ppl", "arnold", "hybrid", "specialization"]

# Standard muscle vocabulary — matches split_templates.day_sessions
MUSCLES = (
    "chest", "back", "shoulder", "rear_delts", "biceps", "triceps",
    "quads", "hamstrings", "glutes", "calves", "core",
)


# ──────────────────────────────────────────────────────────────────────
#  Stage 1 — TrainingProfile
# ──────────────────────────────────────────────────────────────────────
class TrainingProfile(BaseModel):
    """Normalized snapshot of the user's training context. Persisted to
    `training_profiles` table for audit + retrieval."""
    user_id: int
    goal: Goal
    experience: Experience
    days_per_week: int = Field(ge=1, le=7)
    session_duration: int = Field(ge=20, le=180, description="minutes")
    equipment: list[EquipmentType]
    priority_muscles: list[str] = Field(default_factory=list)
    contraindications: list[str] = Field(default_factory=list)
    gender: Gender = "unspecified"
    complexity_cap: int = Field(ge=1, le=5)
    source_onboarding_id: Optional[int] = None
    # filled by SplitPlanner downstream:
    recommended_split: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────
#  Stage 2 — WeeklySplit
# ──────────────────────────────────────────────────────────────────────
class SessionSpec(BaseModel):
    """One training day's plan (muscle targets, ordered)."""
    name: str
    muscles: list[str]      # ['chest','shoulder','triceps']
    day_index: int = Field(ge=0, le=6)   # 0=Mon ... 6=Sun


class WeeklySplit(BaseModel):
    split_id: str
    family: SplitFamily
    sessions: list[SessionSpec]
    rest_day_indices: list[int]    # 0=Mon ... 6=Sun
    rationale: str


# ──────────────────────────────────────────────────────────────────────
#  Stage 3 — VolumeTargets
# ──────────────────────────────────────────────────────────────────────
class MuscleSetTarget(BaseModel):
    """How many sets a given muscle should receive per session."""
    muscle: str
    sets: int = Field(ge=2, le=12)


class SessionTargets(BaseModel):
    """Per-session set distribution."""
    session_name: str
    day_index: int
    per_muscle_sets: list[MuscleSetTarget]   # toplam sets ≈ 18-30 typical
    total_set_budget: int   # toplam set, validator için
    exercise_count_hint: int = Field(ge=4, le=10)  # selector için ~6


class VolumeTargets(BaseModel):
    weekly_per_muscle: dict[str, int]   # {'chest': 12, 'back': 14, ...}
    sessions: list[SessionTargets]


# ──────────────────────────────────────────────────────────────────────
#  Stage 4-5 — Exercise candidate + assembled output
# ──────────────────────────────────────────────────────────────────────
class ExerciseCandidate(BaseModel):
    """Subset of exercise_library row that the selector returns and the
    assembler chooses from. id is the AI-safe handle."""
    id: int
    canonical_name: str
    primary_muscles: list[str]
    movement_pattern: Optional[MovementPattern]
    equipment_type: Optional[EquipmentType]
    equipment_class: Optional[str]
    stability_requirement: Optional[int]
    complexity: Optional[int]
    fatigue_score: Optional[int]


class AssembledExercise(BaseModel):
    """Output of SessionAssembler (LLM-produced). The LLM picks from the
    candidate list — exercise_id is constrained to those ids."""
    exercise_id: int
    sets: int = Field(ge=2, le=6)
    reps: str             # '5-8' | '8-10' | '12-15' | '30 saniye' ...
    rir: int = Field(ge=0, le=5)
    rationale: str = ""


class AssembledSession(BaseModel):
    session_name: str
    day_index: int
    exercises: list[AssembledExercise]


class WeeklyProgram(BaseModel):
    """End-to-end pipeline output for a single week (Week 1 baseline)."""
    profile: TrainingProfile
    split: WeeklySplit
    targets: VolumeTargets
    sessions: list[AssembledSession]


# ──────────────────────────────────────────────────────────────────────
#  Stage 6 — Validation
# ──────────────────────────────────────────────────────────────────────
IssueSeverity = Literal["info", "swap", "regen_session", "fatal"]


class ValidationIssue(BaseModel):
    code: str
    severity: IssueSeverity
    message: str
    session_day_index: Optional[int] = None
    exercise_id: Optional[int] = None


class ValidationReport(BaseModel):
    issues: list[ValidationIssue]
    score: int = Field(ge=0, le=100, description="100=perfect, 0=fatal")
