from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base

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



class StoryJob(Base):
    __tablename__ = "story_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique = True, index=True)
    session_id = Column(String, index=True)
    theme = Column(String, index=True)
    status = Column(String, index=True)
    story_id= Column(Integer, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)