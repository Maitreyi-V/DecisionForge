from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.db.database import Base


class SimulationAttempt(Base):
    __tablename__ = "simulation_attempts"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
    )
    simulation_id = Column(
        Integer,
        ForeignKey("simulations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(String(36), nullable=False, index=True)
    current_node_id = Column(
        Integer,
        ForeignKey("simulation_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )

    status = Column(
        String(20),
        default="active",
        nullable=False,
        index=True,
    )
    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    simulation = relationship("Simulation")
    current_node = relationship(
        "SimulationNode",
        foreign_keys=[current_node_id],
    )
    decision_records = relationship(
        "DecisionRecord",
        back_populates="attempt",
        cascade="all, delete-orphan",
        order_by="DecisionRecord.sequence_number",
    )


class DecisionRecord(Base):
    __tablename__ = "decision_records"
    __table_args__ = (
        UniqueConstraint(
            "simulation_attempt_id",
            "sequence_number",
            name="uq_attempt_decision_sequence",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    simulation_attempt_id = Column(
        Integer,
        ForeignKey("simulation_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_id = Column(
        Integer,
        ForeignKey("decision_options.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence_number = Column(Integer, nullable=False)
    selected_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    attempt = relationship(
        "SimulationAttempt",
        back_populates="decision_records",
    )
    option = relationship("DecisionOption")
