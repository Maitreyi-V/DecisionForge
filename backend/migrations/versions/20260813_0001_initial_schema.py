"""Create the initial DecisionForge schema.

Revision ID: 20260813_0001
Revises:
Create Date: 2026-08-13
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260813_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "simulations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("scenario", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_simulations_id", "simulations", ["id"])
    op.create_index("ix_simulations_title", "simulations", ["title"])
    op.create_index(
        "ix_simulations_session_id",
        "simulations",
        ["session_id"],
    )

    op.create_table(
        "simulation_nodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("simulation_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_root", sa.Boolean(), nullable=False),
        sa.Column("is_ending", sa.Boolean(), nullable=False),
        sa.Column("outcome_summary", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["simulation_id"],
            ["simulations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_simulation_nodes_id", "simulation_nodes", ["id"])
    op.create_index(
        "ix_simulation_nodes_simulation_id",
        "simulation_nodes",
        ["simulation_id"],
    )

    op.create_table(
        "decision_options",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_node_id", sa.Integer(), nullable=False),
        sa.Column("target_node_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("score_delta", sa.Integer(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_node_id"],
            ["simulation_nodes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_node_id"],
            ["simulation_nodes.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_decision_options_id",
        "decision_options",
        ["id"],
    )
    op.create_index(
        "ix_decision_options_source_node_id",
        "decision_options",
        ["source_node_id"],
    )
    op.create_index(
        "ix_decision_options_target_node_id",
        "decision_options",
        ["target_node_id"],
    )

    op.create_table(
        "simulation_generation_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("scenario", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("simulation_id", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["simulation_id"],
            ["simulations.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id"),
        sa.UniqueConstraint("simulation_id"),
    )
    op.create_index(
        "ix_simulation_generation_jobs_id",
        "simulation_generation_jobs",
        ["id"],
    )
    op.create_index(
        "ix_simulation_generation_jobs_job_id",
        "simulation_generation_jobs",
        ["job_id"],
        unique=True,
    )
    op.create_index(
        "ix_simulation_generation_jobs_session_id",
        "simulation_generation_jobs",
        ["session_id"],
    )
    op.create_index(
        "ix_simulation_generation_jobs_status",
        "simulation_generation_jobs",
        ["status"],
    )

    op.create_table(
        "simulation_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.String(length=36), nullable=False),
        sa.Column("simulation_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("current_node_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["current_node_id"],
            ["simulation_nodes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["simulation_id"],
            ["simulations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id"),
    )
    op.create_index(
        "ix_simulation_attempts_attempt_id",
        "simulation_attempts",
        ["attempt_id"],
        unique=True,
    )
    op.create_index(
        "ix_simulation_attempts_id",
        "simulation_attempts",
        ["id"],
    )
    op.create_index(
        "ix_simulation_attempts_session_id",
        "simulation_attempts",
        ["session_id"],
    )
    op.create_index(
        "ix_simulation_attempts_simulation_id",
        "simulation_attempts",
        ["simulation_id"],
    )
    op.create_index(
        "ix_simulation_attempts_status",
        "simulation_attempts",
        ["status"],
    )

    op.create_table(
        "decision_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("simulation_attempt_id", sa.Integer(), nullable=False),
        sa.Column("option_id", sa.Integer(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("score_delta", sa.Integer(), nullable=False),
        sa.Column(
            "selected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["option_id"],
            ["decision_options.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["simulation_attempt_id"],
            ["simulation_attempts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "simulation_attempt_id",
            "sequence_number",
            name="uq_attempt_decision_sequence",
        ),
    )
    op.create_index(
        "ix_decision_records_id",
        "decision_records",
        ["id"],
    )
    op.create_index(
        "ix_decision_records_simulation_attempt_id",
        "decision_records",
        ["simulation_attempt_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_decision_records_simulation_attempt_id",
        table_name="decision_records",
    )
    op.drop_index("ix_decision_records_id", table_name="decision_records")
    op.drop_table("decision_records")

    op.drop_index("ix_simulation_attempts_status", table_name="simulation_attempts")
    op.drop_index(
        "ix_simulation_attempts_simulation_id",
        table_name="simulation_attempts",
    )
    op.drop_index(
        "ix_simulation_attempts_session_id",
        table_name="simulation_attempts",
    )
    op.drop_index("ix_simulation_attempts_id", table_name="simulation_attempts")
    op.drop_index(
        "ix_simulation_attempts_attempt_id",
        table_name="simulation_attempts",
    )
    op.drop_table("simulation_attempts")

    op.drop_index(
        "ix_simulation_generation_jobs_status",
        table_name="simulation_generation_jobs",
    )
    op.drop_index(
        "ix_simulation_generation_jobs_session_id",
        table_name="simulation_generation_jobs",
    )
    op.drop_index(
        "ix_simulation_generation_jobs_job_id",
        table_name="simulation_generation_jobs",
    )
    op.drop_index(
        "ix_simulation_generation_jobs_id",
        table_name="simulation_generation_jobs",
    )
    op.drop_table("simulation_generation_jobs")

    op.drop_index(
        "ix_decision_options_target_node_id",
        table_name="decision_options",
    )
    op.drop_index(
        "ix_decision_options_source_node_id",
        table_name="decision_options",
    )
    op.drop_index("ix_decision_options_id", table_name="decision_options")
    op.drop_table("decision_options")

    op.drop_index(
        "ix_simulation_nodes_simulation_id",
        table_name="simulation_nodes",
    )
    op.drop_index("ix_simulation_nodes_id", table_name="simulation_nodes")
    op.drop_table("simulation_nodes")

    op.drop_index("ix_simulations_session_id", table_name="simulations")
    op.drop_index("ix_simulations_title", table_name="simulations")
    op.drop_index("ix_simulations_id", table_name="simulations")
    op.drop_table("simulations")
