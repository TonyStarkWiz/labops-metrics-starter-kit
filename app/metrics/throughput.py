import pandas as pd
from typing import List

from app.core.schemas import ThroughputPoint, ThroughputResponse


def calculate_throughput(df: pd.DataFrame, grain: str = "hour") -> ThroughputResponse:
    """
    Calculate throughput metrics (completed specimens per time period).
    
    Args:
        df: DataFrame with specimen data
        grain: Time grain ("hour" or "day")
        
    Returns:
        ThroughputResponse with time series data
    """
    # Filter for completed specimens only
    completed_df = df[df['status'] == 'COMPLETED'].copy()
    
    if len(completed_df) == 0:
        return ThroughputResponse(data=[], grain=grain)
    
    # Convert processed_at to datetime
    completed_df['processed_at'] = pd.to_datetime(completed_df['processed_at'])
    
    # Group by time grain
    if grain == "hour":
        completed_df['time_group'] = completed_df['processed_at'].dt.floor('H')
    else:  # day
        completed_df['time_group'] = completed_df['processed_at'].dt.floor('D')
    
    # Count specimens per time period
    throughput_data = completed_df.groupby('time_group').size().reset_index(name='count')
    
    # Convert to list of ThroughputPoint objects
    data_points = []
    for _, row in throughput_data.iterrows():
        data_points.append(
            ThroughputPoint(
                timestamp=row['time_group'],
                count=int(row['count'])
            )
        )
    
    return ThroughputResponse(data=data_points, grain=grain)


def calculate_throughput_by_assay(df: pd.DataFrame, grain: str = "hour") -> pd.DataFrame:
    """
    Calculate throughput metrics by assay type.
    
    Args:
        df: DataFrame with specimen data
        grain: Time grain ("hour" or "day")
        
    Returns:
        DataFrame with throughput by assay and time
    """
    # Filter for completed specimens only
    completed_df = df[df['status'] == 'COMPLETED'].copy()
    
    if len(completed_df) == 0:
        return pd.DataFrame()
    
    # Convert processed_at to datetime
    completed_df['processed_at'] = pd.to_datetime(completed_df['processed_at'])
    
    # Group by time grain
    if grain == "hour":
        completed_df['time_group'] = completed_df['processed_at'].dt.floor('H')
    else:  # day
        completed_df['time_group'] = completed_df['processed_at'].dt.floor('D')
    
    # Count specimens by assay and time period
    throughput_by_assay = completed_df.groupby(['time_group', 'assay']).size().reset_index(name='count')
    
    return throughput_by_assay


def calculate_throughput_by_machine(df: pd.DataFrame, grain: str = "hour") -> pd.DataFrame:
    """
    Calculate throughput metrics by machine.
    
    Args:
        df: DataFrame with specimen data
        grain: Time grain ("hour" or "day")
        
    Returns:
        DataFrame with throughput by machine and time
    """
    # Filter for completed specimens only
    completed_df = df[df['status'] == 'COMPLETED'].copy()
    
    if len(completed_df) == 0:
        return pd.DataFrame()
    
    # Convert processed_at to datetime
    completed_df['processed_at'] = pd.to_datetime(completed_df['processed_at'])
    
    # Group by time grain
    if grain == "hour":
        completed_df['time_group'] = completed_df['processed_at'].dt.floor('H')
    else:  # day
        completed_df['time_group'] = completed_df['processed_at'].dt.floor('D')
    
    # Count specimens by machine and time period
    throughput_by_machine = completed_df.groupby(['time_group', 'machine_id']).size().reset_index(name='count')
    
    return throughput_by_machine


def get_total_throughput_today(df: pd.DataFrame) -> int:
    """
    Get total throughput for today.
    
    Args:
        df: DataFrame with specimen data
        
    Returns:
        Total completed specimens today
    """
    # Filter for completed specimens only
    completed_df = df[df['status'] == 'COMPLETED'].copy()
    
    if len(completed_df) == 0:
        return 0
    
    # Convert processed_at to datetime
    completed_df['processed_at'] = pd.to_datetime(completed_df['processed_at'])
    
    # Filter for today
    today = pd.Timestamp.now().floor('D')
    today_completed = completed_df[completed_df['processed_at'].dt.floor('D') == today]
    
    return len(today_completed)
