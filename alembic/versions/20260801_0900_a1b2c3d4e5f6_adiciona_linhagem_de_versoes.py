"""adiciona linhagem de versoes (kind, parent, root, instruction)

Revision ID: a1b2c3d4e5f6
Revises: 3692c0743c61
Create Date: 2026-08-01 09:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "3692c0743c61"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adiciona colunas de linhagem para versionamento (FR-40/FR-41)."""
    op.add_column(
        "executions",
        sa.Column(
            "kind",
            sa.Enum(
                "INITIAL",
                "REFINE",
                "ROLLBACK",
                name="execution_kind",
                native_enum=False,
            ),
            nullable=False,
            server_default="initial",
        ),
    )
    op.add_column(
        "executions",
        sa.Column("parent_execution_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "executions",
        sa.Column("root_execution_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "executions",
        sa.Column("refine_instruction", sa.Text(), nullable=True),
    )
    op.create_foreign_key(
        "fk_executions_parent_execution_id",
        "executions",
        "executions",
        ["parent_execution_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_executions_root_execution_id",
        "executions",
        "executions",
        ["root_execution_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_executions_parent_execution_id"),
        "executions",
        ["parent_execution_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_executions_root_execution_id"),
        "executions",
        ["root_execution_id"],
        unique=False,
    )


def downgrade() -> None:
    """Reverte as colunas de linhagem."""
    op.drop_index(op.f("ix_executions_root_execution_id"), table_name="executions")
    op.drop_index(op.f("ix_executions_parent_execution_id"), table_name="executions")
    op.drop_constraint(
        "fk_executions_root_execution_id", "executions", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_executions_parent_execution_id", "executions", type_="foreignkey"
    )
    op.drop_column("executions", "refine_instruction")
    op.drop_column("executions", "root_execution_id")
    op.drop_column("executions", "parent_execution_id")
    op.drop_column("executions", "kind")
