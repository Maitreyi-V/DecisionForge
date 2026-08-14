from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.db.database import Base

class SimulationGenerationJob(Base):
    __tablename__ = "simulation_generation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
    )
    session_id = Column(String(36), nullable=False, index=True)

    scenario = Column(Text, nullable=False)
    role = Column(String(100), nullable=False)
    difficulty = Column(String(20), nullable=False)

    status = Column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
    )

    simulation_id = Column(
        Integer,
        ForeignKey("simulations.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )

    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    simulation = relationship("Simulation")
