import pandas as pd
from typing import List

from app.core.schemas import ErrorRate, ErrorsResponse


def calculate_error_metrics(df: pd.DataFrame) -> ErrorsResponse:
    """
    Calculate error rate metrics by machine and error code.
    
    Args:
        df: DataFrame with specimen data
        
    Returns:
        ErrorsResponse with error metrics
    """
    # Filter for error specimens only
    error_df = df[df['status'] == 'ERROR'].copy()
    total_specimens = len(df)
    total_errors = len(error_df)
    
    if total_specimens == 0:
        return ErrorsResponse(
            by_machine=[],
            by_error_code=[],
            total_errors=0,
            total_specimens=0,
            overall_error_rate=0.0
        )
    
    overall_error_rate = total_errors / total_specimens
    
    # Calculate error rates by machine
    by_machine = []
    if len(error_df) > 0:
        machine_errors = error_df.groupby('machine_id').size()
        for machine_id, count in machine_errors.items():
            rate = count / total_specimens
            by_machine.append(
                ErrorRate(
                    category="machine_id",
                    value=str(machine_id),
                    count=int(count),
                    rate=float(rate)
                )
            )
    
    # Calculate error rates by error code
    by_error_code = []
    if len(error_df) > 0:
        error_code_counts = error_df.groupby('error_code').size()
        for error_code, count in error_code_counts.items():
            if pd.notna(error_code):  # Skip null error codes
                rate = count / total_specimens
                by_error_code.append(
                    ErrorRate(
                        category="error_code",
                        value=str(error_code),
                        count=int(count),
                        rate=float(rate)
                    )
                )
    
    return ErrorsResponse(
        by_machine=by_machine,
        by_error_code=by_error_code,
        total_errors=total_errors,
        total_specimens=total_specimens,
        overall_error_rate=overall_error_rate
    )


def calculate_error_timeseries(df: pd.DataFrame, grain: str = "hour") -> pd.DataFrame:
    """
    Calculate error rates over time.
    
    Args:
        df: DataFrame with specimen data
        grain: Time grain ("hour" or "day")
        
    Returns:
        DataFrame with error rates by time period
    """
    if len(df) == 0:
        return pd.DataFrame()
    
    # Convert received_at to datetime
    df['received_at'] = pd.to_datetime(df['received_at'])
    
    # Group by time grain
    if grain == "hour":
        df['time_group'] = df['received_at'].dt.floor('H')
    else:  # day
        df['time_group'] = df['received_at'].dt.floor('D')
    
    # Calculate error rates by time period
    error_timeseries = df.groupby('time_group').agg({
        'status': lambda x: (x == 'ERROR').sum(),
        'id': 'count'
    }).reset_index()
    
    error_timeseries.columns = ['time_group', 'errors', 'total']
    error_timeseries['error_rate'] = error_timeseries['errors'] / error_timeseries['total']
    
    return error_timeseries


def get_error_rate_by_assay(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate error rates by assay type.
    
    Args:
        df: DataFrame with specimen data
        
    Returns:
        DataFrame with error rates by assay
    """
    if len(df) == 0:
        return pd.DataFrame()
    
    # Calculate error rates by assay
    assay_errors = df.groupby('assay').agg({
        'status': lambda x: (x == 'ERROR').sum(),
        'id': 'count'
    }).reset_index()
    
    assay_errors.columns = ['assay', 'errors', 'total']
    assay_errors['error_rate'] = assay_errors['errors'] / assay_errors['total']
    
    return assay_errors


def get_most_common_errors(df: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    """
    Get the most common error codes.
    
    Args:
        df: DataFrame with specimen data
        limit: Maximum number of error codes to return
        
    Returns:
        DataFrame with most common error codes
    """
    # Filter for error specimens only
    error_df = df[df['status'] == 'ERROR'].copy()
    
    if len(error_df) == 0:
        return pd.DataFrame()
    
    # Count error codes
    error_counts = error_df['error_code'].value_counts().head(limit).reset_index()
    error_counts.columns = ['error_code', 'count']
    
    return error_counts
