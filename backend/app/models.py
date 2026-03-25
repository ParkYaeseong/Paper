from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.artifact_roles import normalize_artifact_role
from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    owner_sub: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    owner_username: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    objective: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)

    artifacts: Mapped[list["Artifact"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    artifact_chunks: Mapped[list["ArtifactChunk"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    dataset_profiles: Mapped[list["DatasetProfile"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    outlines: Mapped[list["Outline"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    draft_sections: Mapped[list["DraftSection"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    citation_slots: Mapped[list["CitationSlot"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    reference_records: Mapped[list["ReferenceRecord"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    evidence_matches: Mapped[list["EvidenceMatch"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    review_decisions: Mapped[list["ReviewDecision"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    export_bundles: Mapped[list["ExportBundle"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    quality_reports: Mapped[list["QualityReport"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    figure_specs: Mapped[list["FigureSpec"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    figure_assets: Mapped[list["FigureAsset"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    job_runs: Mapped[list["JobRun"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Artifact(TimestampMixin, Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(50), default="upload", nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), default="application/octet-stream", nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, default=dict)

    project: Mapped[Project] = relationship(back_populates="artifacts")
    chunks: Mapped[list["ArtifactChunk"]] = relationship(
        back_populates="artifact",
        cascade="all, delete-orphan",
    )
    figure_assets: Mapped[list["FigureAsset"]] = relationship(
        back_populates="artifact",
        cascade="all, delete-orphan",
    )

    @property
    def role(self) -> str:
        return normalize_artifact_role((self.metadata_json or {}).get("role"))

    def set_role(self, role: str | None) -> None:
        metadata = dict(self.metadata_json or {})
        metadata["role"] = normalize_artifact_role(role)
        self.metadata_json = metadata


class ArtifactChunk(TimestampMixin, Base):
    __tablename__ = "artifact_chunks"
    __table_args__ = (UniqueConstraint("artifact_id", "ordinal", name="uq_artifact_chunk_ordinal"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    artifact_id: Mapped[str] = mapped_column(ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    ordinal: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    heading: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)

    project: Mapped[Project] = relationship(back_populates="artifact_chunks")
    artifact: Mapped[Artifact] = relationship(back_populates="chunks")


class DatasetProfile(TimestampMixin, Base):
    __tablename__ = "dataset_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    summary_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    project: Mapped[Project] = relationship(back_populates="dataset_profiles")


class Outline(TimestampMixin, Base):
    __tablename__ = "outlines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    manuscript_type: Mapped[str] = mapped_column(String(100), default="original_article", nullable=False)
    title_candidates_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    outline_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    project: Mapped[Project] = relationship(back_populates="outlines")


class DraftSection(TimestampMixin, Base):
    __tablename__ = "draft_sections"
    __table_args__ = (UniqueConstraint("project_id", "section_key", "version", name="uq_draft_section_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    section_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    heading: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)

    project: Mapped[Project] = relationship(back_populates="draft_sections")


class CitationSlot(TimestampMixin, Base):
    __tablename__ = "citation_slots"
    __table_args__ = (UniqueConstraint("project_id", "slot_key", name="uq_project_slot_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    section_key: Mapped[str] = mapped_column(String(100), nullable=False)
    slot_key: Mapped[str] = mapped_column(String(100), nullable=False)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    context_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)

    project: Mapped[Project] = relationship(back_populates="citation_slots")
    evidence_matches: Mapped[list["EvidenceMatch"]] = relationship(
        back_populates="citation_slot",
        cascade="all, delete-orphan",
    )


class ReferenceRecord(TimestampMixin, Base):
    __tablename__ = "reference_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str] = mapped_column(Text, default="", nullable=False)
    authors_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    venue: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    year: Mapped[int | None] = mapped_column(Integer)
    doi: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    url: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, default=dict)

    project: Mapped[Project] = relationship(back_populates="reference_records")


class EvidenceMatch(TimestampMixin, Base):
    __tablename__ = "evidence_matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    citation_slot_id: Mapped[str] = mapped_column(
        ForeignKey("citation_slots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    queries_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    candidate_reference_ids_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    selected_reference_ids_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    support_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    project: Mapped[Project] = relationship(back_populates="evidence_matches")
    citation_slot: Mapped[CitationSlot] = relationship(back_populates="evidence_matches")


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    citation_slot_id: Mapped[str | None] = mapped_column(ForeignKey("citation_slots.id", ondelete="SET NULL"))
    draft_section_id: Mapped[str | None] = mapped_column(ForeignKey("draft_sections.id", ondelete="SET NULL"))
    reviewed_by_sub: Mapped[str] = mapped_column(String(255), nullable=False)
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    project: Mapped[Project] = relationship(back_populates="review_decisions")


class QualityReport(Base):
    __tablename__ = "quality_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    critical_issues_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    warnings_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    recommended_actions_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    submission_ready: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    project: Mapped[Project] = relationship(back_populates="quality_reports")


class FigureSpec(TimestampMixin, Base):
    __tablename__ = "figure_specs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    section_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    figure_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    figure_number: Mapped[int] = mapped_column(Integer, nullable=False)
    caption_draft: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_excerpt: Mapped[str] = mapped_column(Text, default="", nullable=False)
    visual_intent: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)

    project: Mapped[Project] = relationship(back_populates="figure_specs")
    figure_assets: Mapped[list["FigureAsset"]] = relationship(
        back_populates="figure_spec",
        cascade="all, delete-orphan",
    )


class FigureAsset(TimestampMixin, Base):
    __tablename__ = "figure_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    figure_spec_id: Mapped[str] = mapped_column(
        ForeignKey("figure_specs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artifact_id: Mapped[str] = mapped_column(
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(100), default="paperbanana", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="generated", nullable=False)
    selected: Mapped[bool] = mapped_column(default=False, nullable=False)

    project: Mapped[Project] = relationship(back_populates="figure_assets")
    figure_spec: Mapped[FigureSpec] = relationship(back_populates="figure_assets")
    artifact: Mapped[Artifact] = relationship(back_populates="figure_assets")


class ExportBundle(Base):
    __tablename__ = "export_bundles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    manifest_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    project: Mapped[Project] = relationship(back_populates="export_bundles")


class JobRun(TimestampMixin, Base):
    __tablename__ = "job_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False)
    payload_json: Mapped[dict | None] = mapped_column(JSON, default=dict)
    result_json: Mapped[dict | None] = mapped_column(JSON, default=dict)
    log_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped[Project] = relationship(back_populates="job_runs")
