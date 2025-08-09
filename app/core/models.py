from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Index, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SpecimenStatus(str, Enum):
    """Specimen processing status enumeration."""
    RECEIVED = "RECEIVED"
    IN_PROCESS = "IN_PROCESS"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class Specimen(Base):
    """Specimen model representing lab test specimens."""
    
    __tablename__ = "specimens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    specimen_id = Column(String(50), unique=True, nullable=False, index=True)
    assay = Column(String(20), nullable=False, index=True)
    machine_id = Column(String(10), nullable=False, index=True)
    operator_id = Column(String(10), nullable=False)
    status = Column(SQLEnum(SpecimenStatus), nullable=False, default=SpecimenStatus.RECEIVED)
    error_code = Column(String(10), nullable=True)
    received_at = Column(DateTime, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    
    # Create indices for performance
    __table_args__ = (
        Index("idx_assay", "assay"),
        Index("idx_machine_id", "machine_id"),
        Index("idx_received_at", "received_at"),
        Index("idx_status", "status"),
    )
    
    def __repr__(self):
        return f"<Specimen(id={self.id}, specimen_id='{self.specimen_id}', assay='{self.assay}', status='{self.status}')>"
    
    @property
    def turnaround_time_minutes(self) -> float:
        """Calculate turnaround time in minutes."""
        if self.status == SpecimenStatus.COMPLETED and self.processed_at and self.received_at:
            return (self.processed_at - self.received_at).total_seconds() / 60
        return None
    
    @property
    def is_sla_breach(self) -> bool:
        """Check if specimen breached SLA (default 4 hours)."""
        tat = self.turnaround_time_minutes
        if tat is not None:
            from app.core.settings import settings
            return tat > (settings.SLA_HOURS * 60)
        return False
