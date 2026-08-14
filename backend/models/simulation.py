from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.db.database import Base


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    scenario = Column(Text, nullable=False)
    role = Column(String(100), nullable=False)
    difficulty = Column(String(20), nullable=False)
    session_id = Column(String(36), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    nodes = relationship(
        "SimulationNode",
        back_populates="simulation",
        cascade="all, delete-orphan",
    )


class SimulationNode(Base):
    __tablename__ = "simulation_nodes"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(
        Integer,
        ForeignKey("simulations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content = Column(Text, nullable=False)
    is_root = Column(Boolean, default=False, nullable=False)
    is_ending = Column(Boolean, default=False, nullable=False)
    outcome_summary = Column(Text, nullable=True)

    simulation = relationship(
        "Simulation",
        back_populates="nodes",
    )

    outgoing_options = relationship(
        "DecisionOption",
        foreign_keys="DecisionOption.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan",
    )

    incoming_options = relationship(
        "DecisionOption",
        foreign_keys="DecisionOption.target_node_id",
        back_populates="target_node",
    )


class DecisionOption(Base):
    __tablename__ = "decision_options"

    id = Column(Integer, primary_key=True, index=True)
    source_node_id = Column(
        Integer,
        ForeignKey("simulation_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_node_id = Column(
        Integer,
        ForeignKey("simulation_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text = Column(Text, nullable=False)
    priorities = Column(JSON, default=list, nullable=False)
    feedback = Column(Text, nullable=False)

    source_node = relationship(
        "SimulationNode",
        foreign_keys=[source_node_id],
        back_populates="outgoing_options",
    )

    target_node = relationship(
        "SimulationNode",
        foreign_keys=[target_node_id],
        back_populates="incoming_options",
    )
