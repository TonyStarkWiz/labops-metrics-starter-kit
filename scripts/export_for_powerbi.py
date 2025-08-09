#!/usr/bin/env python3
"""
Power BI export script for LabOps Metrics Starter Kit.

Exports consolidated CSV data ready for Power BI import.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.db import SessionLocal
from app.core.models import Specimen


def get_specimens_dataframe(db: Session) -> pd.DataFrame:
    """Get specimens data as DataFrame with computed fields."""
    specimens = db.query(Specimen).all()
    
    if not specimens:
        return pd.DataFrame()
    
    # Convert to DataFrame
    data = []
    for specimen in specimens:
        # Calculate TAT in minutes
        tat_minutes = None
        if specimen.status.value == 'COMPLETED' and specimen.processed_at and specimen.received_at:
            tat_minutes = (specimen.processed_at - specimen.received_at).total_seconds() / 60
        
        # Determine if SLA breach
        is_sla_breach = False
        if tat_minutes is not None:
            from app.core.settings import settings
            is_sla_breach = tat_minutes > (settings.SLA_HOURS * 60)
        
        data.append({
            'id': specimen.id,
            'specimen_id': specimen.specimen_id,
            'assay': specimen.assay,
            'machine_id': specimen.machine_id,
            'operator_id': specimen.operator_id,
            'status': specimen.status.value,
            'error_code': specimen.error_code,
            'received_at': specimen.received_at,
            'processed_at': specimen.processed_at,
            'tat_minutes': tat_minutes,
            'is_sla_breach': is_sla_breach,
            'received_date': specimen.received_at.date() if specimen.received_at else None,
            'processed_date': specimen.processed_at.date() if specimen.processed_at else None,
            'received_hour': specimen.received_at.hour if specimen.received_at else None,
            'processed_hour': specimen.processed_at.hour if specimen.processed_at else None,
        })
    
    return pd.DataFrame(data)


def create_summary_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Create summary tables for Power BI."""
    summaries = {}
    
    if len(df) == 0:
        return summaries
    
    # Daily summary
    daily_summary = df.groupby('received_date').agg({
        'id': 'count',
        'status': lambda x: (x == 'COMPLETED').sum(),
        'tat_minutes': 'mean',
        'is_sla_breach': 'sum'
    }).reset_index()
    daily_summary.columns = ['date', 'total_specimens', 'completed_specimens', 'avg_tat_minutes', 'sla_breaches']
    daily_summary['completion_rate'] = daily_summary['completed_specimens'] / daily_summary['total_specimens']
    summaries['daily_summary'] = daily_summary
    
    # Assay summary
    assay_summary = df.groupby('assay').agg({
        'id': 'count',
        'status': lambda x: (x == 'COMPLETED').sum(),
        'tat_minutes': 'mean',
        'is_sla_breach': 'sum'
    }).reset_index()
    assay_summary.columns = ['assay', 'total_specimens', 'completed_specimens', 'avg_tat_minutes', 'sla_breaches']
    assay_summary['completion_rate'] = assay_summary['completed_specimens'] / assay_summary['total_specimens']
    summaries['assay_summary'] = assay_summary
    
    # Machine summary
    machine_summary = df.groupby('machine_id').agg({
        'id': 'count',
        'status': lambda x: (x == 'COMPLETED').sum(),
        'tat_minutes': 'mean',
        'is_sla_breach': 'sum'
    }).reset_index()
    machine_summary.columns = ['machine_id', 'total_specimens', 'completed_specimens', 'avg_tat_minutes', 'sla_breaches']
    machine_summary['completion_rate'] = machine_summary['completed_specimens'] / machine_summary['total_specimens']
    summaries['machine_summary'] = machine_summary
    
    # Error summary
    error_summary = df[df['status'] == 'ERROR'].groupby('error_code').size().reset_index(name='count')
    summaries['error_summary'] = error_summary
    
    return summaries


def export_to_csv(df: pd.DataFrame, summaries: dict[str, pd.DataFrame], output_dir: str):
    """Export data to CSV files."""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Export main specimens data
    specimens_file = os.path.join(output_dir, 'specimens_latest.csv')
    df.to_csv(specimens_file, index=False)
    print(f"Exported {len(df)} specimens to {specimens_file}")
    
    # Export summary tables
    for name, summary_df in summaries.items():
        summary_file = os.path.join(output_dir, f'{name}.csv')
        summary_df.to_csv(summary_file, index=False)
        print(f"Exported {name} to {summary_file}")


def create_pbix_instructions(output_dir: str):
    """Create instructions for Power BI import."""
    instructions_file = os.path.join(output_dir, 'POWERBI_INSTRUCTIONS.md')
    
    instructions = """# Power BI Import Instructions

## Files Available
- `specimens_latest.csv` - Main specimens data with computed TAT and SLA fields
- `daily_summary.csv` - Daily aggregated metrics
- `assay_summary.csv` - Assay-level metrics
- `machine_summary.csv` - Machine-level metrics
- `error_summary.csv` - Error code breakdown

## Import Steps
1. Open Power BI Desktop
2. Click "Get Data" → "Text/CSV"
3. Select `specimens_latest.csv`
4. Click "Load" to import the data
5. Create relationships with summary tables if needed

## Key Fields
- `tat_minutes` - Turnaround time in minutes (for completed specimens)
- `is_sla_breach` - Boolean flag for SLA violations
- `received_date` / `processed_date` - Date dimensions
- `received_hour` / `processed_hour` - Hour dimensions for time analysis

## Suggested Visualizations
1. **TAT Dashboard**: Line chart of average TAT over time
2. **Throughput Chart**: Bar chart of specimens by date
3. **Error Analysis**: Pie chart of error codes
4. **SLA Monitoring**: Gauge showing breach rate
5. **Machine Performance**: Table comparing machine metrics

## Data Refresh
To refresh data, run the export script again and reload in Power BI.
"""
    
    with open(instructions_file, 'w') as f:
        f.write(instructions)
    
    print(f"Created Power BI instructions at {instructions_file}")


def main():
    """Main function."""
    print("Exporting data for Power BI...")
    
    # Get data from database
    db = SessionLocal()
    try:
        df = get_specimens_dataframe(db)
        if len(df) == 0:
            print("No data found in database. Please run the data generation script first.")
            return
        
        # Create summary tables
        summaries = create_summary_tables(df)
        
        # Export to CSV
        output_dir = "data/seeds/exports"
        export_to_csv(df, summaries, output_dir)
        
        # Create instructions
        create_pbix_instructions(output_dir)
        
        print(f"\nExport completed successfully!")
        print(f"Files saved to: {output_dir}")
        print(f"Main data file: {output_dir}/specimens_latest.csv")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
