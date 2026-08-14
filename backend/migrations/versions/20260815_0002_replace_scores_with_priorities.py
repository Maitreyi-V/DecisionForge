"""Replace numeric decision scores with descriptive priorities.

Revision ID: 20260815_0002
Revises: 20260813_0001
Create Date: 2026-08-15
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260815_0002"
down_revision: str | None = "20260813_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "decision_options",
        sa.Column(
            "priorities",
            sa.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
    )

    with op.batch_alter_table("decision_options") as batch_op:
        batch_op.drop_column("score_delta")

    with op.batch_alter_table("decision_records") as batch_op:
        batch_op.drop_column("score_delta")

    with op.batch_alter_table("simulation_attempts") as batch_op:
        batch_op.drop_column("total_score")


def downgrade() -> None:
    with op.batch_alter_table("decision_options") as batch_op:
        batch_op.add_column(
            sa.Column(
                "score_delta",
                sa.Integer(),
                server_default=sa.text("0"),
                nullable=False,
            )
        )

    with op.batch_alter_table("decision_records") as batch_op:
        batch_op.add_column(
            sa.Column(
                "score_delta",
                sa.Integer(),
                server_default=sa.text("0"),
                nullable=False,
            )
        )

    with op.batch_alter_table("simulation_attempts") as batch_op:
        batch_op.add_column(
            sa.Column(
                "total_score",
                sa.Integer(),
                server_default=sa.text("0"),
                nullable=False,
            )
        )

    op.drop_column("decision_options", "priorities")
