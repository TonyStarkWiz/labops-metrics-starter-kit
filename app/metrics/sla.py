import pandas as pd
from typing import List

from app.core.schemas import SLABreach, SLAResponse
from app.core.settings import settings


def calculate_sla_metrics(df: pd.DataFrame) -> SLAResponse:
    """
    Calculate SLA breach metrics.
    
    Args:
        df: DataFrame with specimen data
        
    Returns:
        SLAResponse with SLA metrics and sample breaches
    """
    # Filter for completed specimens only
    completed_df = df[df['status'] == 'COMPLETED'].copy()
    
    if len(completed_df) == 0:
        return SLAResponse(
            breach_count=0,
            total_completed=0,
            breach_rate=0.0,
            sample_breaches=[]
        )
    
    # Calculate turnaround time in minutes
    completed_df['tat_minutes'] = (
        pd.to_datetime(completed_df['processed_at']) - 
        pd.to_datetime(completed_df['received_at'])
    ).dt.total_seconds() / 60
    
    # Remove any invalid TAT values
    completed_df = completed_df[completed_df['tat_minutes'] >= 0]
    
    # Identify SLA breaches (default 4 hours = 240 minutes)
    sla_threshold_minutes = settings.SLA_HOURS * 60
    breach_df = completed_df[completed_df['tat_minutes'] > sla_threshold_minutes]
    
    total_completed = len(completed_df)
    breach_count = len(breach_df)
    breach_rate = breach_count / total_completed if total_completed > 0 else 0.0
    
    # Create sample breach records (limit 20)
    sample_breaches = []
    for _, row in breach_df.head(20).iterrows():
        sample_breaches.append(
            SLABreach(
                specimen_id=row['specimen_id'],
                assay=row['assay'],
                machine_id=row['machine_id'],
                turnaround_time_minutes=float(row['tat_minutes']),
                received_at=row['received_at'],
                processed_at=row['processed_at']
            )
        )
    
    return SLAResponse(
        breach_count=breach_count,
        total_completed=total_completed,
        breach_rate=breach_rate,
        sample_breaches=sample_breaches
    )


def calculate_sla_by_assay(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate SLA breach rates by assay type.
    
    Args:
        df: DataFrame with specimen data
        
    Returns:
        DataFrame with SLA breach rates by assay
    """
    # Filter for completed specimens only
    completed_df = df[df['status'] == 'COMPLETED'].copy()
    
    if len(completed_df) == 0:
        return pd.DataFrame()
    
    # Calculate turnaround time in minutes
    completed_df['tat_minutes'] = (
        pd.to_datetime(completed_df['processed_at']) - 
        pd.to_datetime(completed_df['received_at'])
    ).dt.total_seconds() / 60
    
    # Remove any invalid TAT values
    completed_df = completed_df[completed_df['tat_minutes'] >= 0]
    
    # Identify SLA breaches
    sla_threshold_minutes = settings.SLA_HOURS * 60
    completed_df['is_breach'] = completed_df['tat_minutes'] > sla_threshold_minutes
    
    # Calculate breach rates by assay
    sla_by_assay = completed_df.groupby('assay').agg({
        'is_breach': 'sum',
        'id': 'count'
    }).reset_index()
    
    sla_by_assay.columns = ['assay', 'breaches', 'total']
    sla_by_assay['breach_rate'] = sla_by_assay['breaches'] / sla_by_assay['total']
    
    return sla_by_assay


def calculate_sla_by_machine(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate SLA breach rates by machine.
    
    Args:
        df: DataFrame with specimen data
        
    Returns:
        DataFrame with SLA breach rates by machine
    """
    # Filter for completed specimens only
    completed_df = df[df['status'] == 'COMPLETED'].copy()
    
    if len(completed_df) == 0:
        return pd.DataFrame()
    
    # Calculate turnaround time in minutes
    completed_df['tat_minutes'] = (
        pd.to_datetime(completed_df['processed_at']) - 
        pd.to_datetime(completed_df['received_at'])
    ).dt.total_seconds() / 60
    
    # Remove any invalid TAT values
    completed_df = completed_df[completed_df['tat_minutes'] >= 0]
    
    # Identify SLA breaches
    sla_threshold_minutes = settings.SLA_HOURS * 60
    completed_df['is_breach'] = completed_df['tat_minutes'] > sla_threshold_minutes
    
    # Calculate breach rates by machine
    sla_by_machine = completed_df.groupby('machine_id').agg({
        'is_breach': 'sum',
        'id': 'count'
    }).reset_index()
    
    sla_by_machine.columns = ['machine_id', 'breaches', 'total']
    sla_by_machine['breach_rate'] = sla_by_machine['breaches'] / sla_by_machine['total']
    
    return sla_by_machine


def get_sla_timeseries(df: pd.DataFrame, grain: str = "hour") -> pd.DataFrame:
    """
    Calculate SLA breach rates over time.
    
    Args:
        df: DataFrame with specimen data
        grain: Time grain ("hour" or "day")
        
    Returns:
        DataFrame with SLA breach rates by time period
    """
    # Filter for completed specimens only
    completed_df = df[df['status'] == 'COMPLETED'].copy()
    
    if len(completed_df) == 0:
        return pd.DataFrame()
    
    # Calculate turnaround time in minutes
    completed_df['tat_minutes'] = (
        pd.to_datetime(completed_df['processed_at']) - 
        pd.to_datetime(completed_df['received_at'])
    ).dt.total_seconds() / 60
    
    # Remove any invalid TAT values
    completed_df = completed_df[completed_df['tat_minutes'] >= 0]
    
    # Identify SLA breaches
    sla_threshold_minutes = settings.SLA_HOURS * 60
    completed_df['is_breach'] = completed_df['tat_minutes'] > sla_threshold_minutes
    
    # Group by time grain
    if grain == "hour":
        completed_df['time_group'] = pd.to_datetime(completed_df['processed_at']).dt.floor('H')
    else:  # day
        completed_df['time_group'] = pd.to_datetime(completed_df['processed_at']).dt.floor('D')
    
    # Calculate breach rates by time period
    sla_timeseries = completed_df.groupby('time_group').agg({
        'is_breach': 'sum',
        'id': 'count'
    }).reset_index()
    
    sla_timeseries.columns = ['time_group', 'breaches', 'total']
    sla_timeseries['breach_rate'] = sla_timeseries['breaches'] / sla_timeseries['total']
    
    return sla_timeseries
