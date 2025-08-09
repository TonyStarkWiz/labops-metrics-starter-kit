from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    timestamp: datetime


class TATResponse(BaseModel):
    """Turnaround time metrics response."""
    p50: float
    p90: float
    p99: float
    assay: Optional[str] = None
    total_specimens: int


class ThroughputPoint(BaseModel):
    """Single throughput data point."""
    timestamp: datetime
    count: int


class ThroughputResponse(BaseModel):
    """Throughput metrics response."""
    data: List[ThroughputPoint]
    grain: str  # "hour" or "day"


class ErrorRate(BaseModel):
    """Error rate for a specific category."""
    category: str  # "machine_id" or "error_code"
    value: str
    count: int
    rate: float


class ErrorsResponse(BaseModel):
    """Error metrics response."""
    by_machine: List[ErrorRate]
    by_error_code: List[ErrorRate]
    total_errors: int
    total_specimens: int
    overall_error_rate: float


class SLABreach(BaseModel):
    """Individual SLA breach record."""
    specimen_id: str
    assay: str
    machine_id: str
    turnaround_time_minutes: float
    received_at: datetime
    processed_at: datetime


class SLAResponse(BaseModel):
    """SLA metrics response."""
    breach_count: int
    total_completed: int
    breach_rate: float
    sample_breaches: List[SLABreach]


class TeamsAlertPayload(BaseModel):
    """Microsoft Teams alert payload."""
    title: str
    breaches: int
    top_assays: List[dict]
    window: str
    link: str


class WhatIfScenario(BaseModel):
    """What-if analysis scenario."""
    extra_machines: int
    reduced_failure_rate: float
    projected_tat_p90: float
    projected_throughput: float
    improvement_tat: float
    improvement_throughput: float
