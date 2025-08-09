from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.models import Specimen
from app.core.schemas import (
    ErrorsResponse,
    SLAResponse,
    TATResponse,
    ThroughputResponse,
)
from app.metrics.errors import calculate_error_metrics
from app.metrics.sla import calculate_sla_metrics
from app.metrics.tat import calculate_tat_metrics
from app.metrics.throughput import calculate_throughput

router = APIRouter()


def get_specimens_df(db: Session) -> pd.DataFrame:
    """Get specimens data as DataFrame."""
    specimens = db.query(Specimen).all()
    
    if not specimens:
        return pd.DataFrame()
    
    # Convert to DataFrame
    data = []
    for specimen in specimens:
        data.append({
            'id': specimen.id,
            'specimen_id': specimen.specimen_id,
            'assay': specimen.assay,
            'machine_id': specimen.machine_id,
            'operator_id': specimen.operator_id,
            'status': specimen.status.value,
            'error_code': specimen.error_code,
            'received_at': specimen.received_at,
            'processed_at': specimen.processed_at
        })
    
    return pd.DataFrame(data)


@router.get("/metrics/tat", response_model=TATResponse)
async def get_tat_metrics(
    assay: Optional[str] = Query(None, description="Filter by assay type"),
    db: Session = Depends(get_db)
):
    """Get turnaround time metrics."""
    df = get_specimens_df(db)
    return calculate_tat_metrics(df, assay=assay)


@router.get("/metrics/throughput", response_model=ThroughputResponse)
async def get_throughput_metrics(
    grain: str = Query("hour", description="Time grain: hour or day"),
    db: Session = Depends(get_db)
):
    """Get throughput metrics."""
    if grain not in ["hour", "day"]:
        grain = "hour"
    
    df = get_specimens_df(db)
    return calculate_throughput(df, grain=grain)


@router.get("/metrics/errors", response_model=ErrorsResponse)
async def get_error_metrics(db: Session = Depends(get_db)):
    """Get error rate metrics."""
    df = get_specimens_df(db)
    return calculate_error_metrics(df)


@router.get("/metrics/sla", response_model=SLAResponse)
async def get_sla_metrics(db: Session = Depends(get_db)):
    """Get SLA breach metrics."""
    df = get_specimens_df(db)
    return calculate_sla_metrics(df)
