import pandas as pd
from typing import Optional

from app.core.schemas import TATResponse


def calculate_tat_metrics(df: pd.DataFrame, assay: Optional[str] = None) -> TATResponse:
    """
    Calculate turnaround time metrics (P50, P90, P99).
    
    Args:
        df: DataFrame with specimen data
        assay: Optional assay filter
        
    Returns:
        TATResponse with percentile metrics
    """
    # Filter for completed specimens only
    completed_df = df[df['status'] == 'COMPLETED'].copy()
    
    if assay:
        completed_df = completed_df[completed_df['assay'] == assay]
    
    # Calculate turnaround time in minutes
    completed_df['tat_minutes'] = (
        pd.to_datetime(completed_df['processed_at']) - 
        pd.to_datetime(completed_df['received_at'])
    ).dt.total_seconds() / 60
    
    # Remove any invalid TAT values (negative or null)
    valid_tat = completed_df['tat_minutes'].dropna()
    valid_tat = valid_tat[valid_tat >= 0]
    
    if len(valid_tat) == 0:
        return TATResponse(
            p50=0.0,
            p90=0.0,
            p99=0.0,
            assay=assay,
            total_specimens=0
        )
    
    # Calculate percentiles
    p50 = float(valid_tat.quantile(0.50))
    p90 = float(valid_tat.quantile(0.90))
    p99 = float(valid_tat.quantile(0.99))
    
    return TATResponse(
        p50=p50,
        p90=p90,
        p99=p99,
        assay=assay,
        total_specimens=len(valid_tat)
    )


def calculate_tat_by_assay(df: pd.DataFrame) -> dict[str, TATResponse]:
    """
    Calculate TAT metrics for each assay type.
    
    Args:
        df: DataFrame with specimen data
        
    Returns:
        Dictionary mapping assay to TAT metrics
    """
    assays = df['assay'].unique()
    results = {}
    
    for assay in assays:
        results[assay] = calculate_tat_metrics(df, assay=assay)
    
    return results


def calculate_tat_timeseries(df: pd.DataFrame, grain: str = "hour") -> pd.DataFrame:
    """
    Calculate TAT metrics over time.
    
    Args:
        df: DataFrame with specimen data
        grain: Time grain ("hour" or "day")
        
    Returns:
        DataFrame with timestamp and TAT metrics
    """
    # Filter for completed specimens
    completed_df = df[df['status'] == 'COMPLETED'].copy()
    
    if len(completed_df) == 0:
        return pd.DataFrame()
    
    # Calculate TAT
    completed_df['tat_minutes'] = (
        pd.to_datetime(completed_df['processed_at']) - 
        pd.to_datetime(completed_df['received_at'])
    ).dt.total_seconds() / 60
    
    # Remove invalid TAT values
    completed_df = completed_df[completed_df['tat_minutes'] >= 0]
    
    # Group by time grain
    if grain == "hour":
        completed_df['time_group'] = pd.to_datetime(completed_df['processed_at']).dt.floor('H')
    else:  # day
        completed_df['time_group'] = pd.to_datetime(completed_df['processed_at']).dt.floor('D')
    
    # Calculate percentiles by time group
    tat_timeseries = completed_df.groupby('time_group')['tat_minutes'].agg([
        ('p50', lambda x: x.quantile(0.50)),
        ('p90', lambda x: x.quantile(0.90)),
        ('p99', lambda x: x.quantile(0.99)),
        ('count', 'count')
    ]).reset_index()
    
    return tat_timeseries
