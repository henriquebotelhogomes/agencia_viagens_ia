"""Modelos de domínio persistidos (PRD D8 / ADR-0008).

Um `Execution` é uma rodada de orquestração; ele produz um `Itinerary` e
registra `UsageRecord` com o consumo real de tokens (base do FinOps, item S4).
"""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

# Tipos portáveis: JSONB/UUID nativos no PostgreSQL, equivalentes no SQLite
# (usado pelos testes). Sem isso, o schema não sobe em banco de teste.
JsonType = JSON().with_variant(JSONB(), "postgresql")
UuidType = Uuid(as_uuid=True)


def _utcnow() -> datetime:
    """Timestamp atual em UTC (timezone-aware)."""
    return datetime.now(UTC)


class ExecutionStatus(enum.StrEnum):
    """Ciclo de vida de uma execução."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionKind(enum.StrEnum):
    """Tipo de execução na linhagem de versões (FR-40/FR-41)."""

    INITIAL = "initial"
    REFINE = "refine"
    ROLLBACK = "rollback"


class Execution(Base):
    """Uma rodada de orquestração da equipe de agentes."""

    __tablename__ = "executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UuidType, primary_key=True, default=uuid.uuid4
    )
    status: Mapped[ExecutionStatus] = mapped_column(
        Enum(ExecutionStatus, name="execution_status", native_enum=False),
        default=ExecutionStatus.QUEUED,
        index=True,
    )

    # --- Briefing (entrada do usuário) ---
    origem: Mapped[str] = mapped_column(String(200))
    destino: Mapped[str] = mapped_column(String(200))
    dias: Mapped[int] = mapped_column(Integer)
    interesses: Mapped[str] = mapped_column(String(500), default="")
    moeda: Mapped[str] = mapped_column(String(3))
    idioma: Mapped[str] = mapped_column(String(10))

    # Hash do briefing — habilita idempotência e reuso de cache
    briefing_hash: Mapped[str] = mapped_column(String(64), index=True)
    # Chave de idempotência enviada pelo cliente (Idempotency-Key)
    idempotency_key: Mapped[str | None] = mapped_column(
        String(200), unique=True, default=None
    )

    # --- Resultado e diagnóstico ---
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    # Gateway efetivamente usado: identifica se houve failover (ADR-0002)
    llm_gateway: Mapped[str | None] = mapped_column(String(50), default=None)
    used_fallback: Mapped[bool] = mapped_column(default=False)
    served_from_cache: Mapped[bool] = mapped_column(default=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float, default=None)

    # --- Versionamento / linhagem (FR-40/FR-41) ---
    kind: Mapped[ExecutionKind] = mapped_column(
        Enum(ExecutionKind, name="execution_kind", native_enum=False),
        default=ExecutionKind.INITIAL,
        server_default=ExecutionKind.INITIAL.value,
    )
    parent_execution_id: Mapped[uuid.UUID | None] = mapped_column(
        UuidType,
        ForeignKey("executions.id", ondelete="SET NULL"),
        index=True,
        default=None,
    )
    root_execution_id: Mapped[uuid.UUID | None] = mapped_column(
        UuidType,
        ForeignKey("executions.id", ondelete="SET NULL"),
        index=True,
        default=None,
    )
    refine_instruction: Mapped[str | None] = mapped_column(Text, default=None)

    # --- Auditoria ---
    client_ip_hash: Mapped[str | None] = mapped_column(String(64), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    itinerary: Mapped["Itinerary | None"] = relationship(
        back_populates="execution", cascade="all, delete-orphan", uselist=False
    )
    usage_records: Mapped[list["UsageRecord"]] = relationship(
        back_populates="execution", cascade="all, delete-orphan"
    )
    # Linhagem self-referencial (conveniência ORM)
    parent: Mapped["Execution | None"] = relationship(
        "Execution",
        remote_side="Execution.id",
        foreign_keys=[parent_execution_id],
        back_populates="children",
    )
    children: Mapped[list["Execution"]] = relationship(
        "Execution",
        foreign_keys="Execution.parent_execution_id",
        back_populates="parent",
    )

    __table_args__ = (
        # Consulta típica do painel: execuções recentes por status
        Index("ix_executions_status_created", "status", "created_at"),
    )

    @property
    def is_terminal(self) -> bool:
        """Indica se a execução já chegou a um estado final."""
        return self.status in {
            ExecutionStatus.SUCCEEDED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
        }


class Itinerary(Base):
    """Roteiro produzido por uma execução."""

    __tablename__ = "itineraries"

    id: Mapped[uuid.UUID] = mapped_column(
        UuidType, primary_key=True, default=uuid.uuid4
    )
    execution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("executions.id", ondelete="CASCADE"), index=True
    )

    content_markdown: Mapped[str] = mapped_column(Text)
    # Locais geocodificados no formato GeoJSON FeatureCollection (FR-05)
    locations_geojson: Mapped[dict[str, object] | None] = mapped_column(
        JsonType, default=None
    )
    # Versionamento para refinamento futuro (FR-40)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    execution: Mapped[Execution] = relationship(back_populates="itinerary")


class UsageRecord(Base):
    """Consumo de LLM de uma chamada — base do FinOps real (item S4)."""

    __tablename__ = "usage_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UuidType, primary_key=True, default=uuid.uuid4
    )
    execution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("executions.id", ondelete="CASCADE"), index=True
    )

    model: Mapped[str] = mapped_column(String(120))
    gateway: Mapped[str] = mapped_column(String(50))
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    # Custo calculado por tokens x tabela de preços (USD)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    # Custo hipotético no modelo de referência — narrativa de economia
    baseline_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )

    execution: Mapped[Execution] = relationship(back_populates="usage_records")

    @property
    def total_tokens(self) -> int:
        """Soma de tokens de prompt e completion."""
        return self.prompt_tokens + self.completion_tokens
