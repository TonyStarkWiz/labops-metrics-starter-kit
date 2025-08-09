#!/usr/bin/env python3
"""
Data Quality Check script for LabOps Metrics Starter Kit.

Validates CSV data against configurable rules and generates reports.
"""

import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import yaml

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent.parent))


def load_rules(rules_file: str = None) -> Dict:
    """Load data quality rules from YAML file or use defaults."""
    if rules_file and os.path.exists(rules_file):
        with open(rules_file, 'r') as f:
            return yaml.safe_load(f)
    
    # Default rules
    return {
        'required_columns': [
            'specimen_id', 'assay', 'machine_id', 'operator_id',
            'status', 'received_at', 'processed_at'
        ],
        'allowed_statuses': ['RECEIVED', 'IN_PROCESS', 'COMPLETED', 'ERROR'],
        'allowed_assays': ['CBC', 'Chem7', 'PCR'],
        'allowed_machines': [f'M{i}' for i in range(1, 6)],
        'allowed_operators': [f'O{i}' for i in range(1, 21)],
        'max_tat_hours': 24,  # Maximum reasonable TAT
        'future_date_tolerance_hours': 1  # Allow slight future dates due to timezone issues
    }


def check_required_columns(df: pd.DataFrame, rules: Dict) -> Tuple[List, int]:
    """Check for required columns."""
    missing_columns = []
    for col in rules['required_columns']:
        if col not in df.columns:
            missing_columns.append(col)
    
    return missing_columns, len(missing_columns)


def check_status_values(df: pd.DataFrame, rules: Dict) -> Tuple[List, int]:
    """Check for valid status values."""
    invalid_statuses = []
    if 'status' in df.columns:
        invalid_mask = ~df['status'].isin(rules['allowed_statuses'])
        invalid_statuses = df[invalid_mask]['status'].unique().tolist()
    
    return invalid_statuses, len(invalid_statuses)


def check_assay_values(df: pd.DataFrame, rules: Dict) -> Tuple[List, int]:
    """Check for valid assay values."""
    invalid_assays = []
    if 'assay' in df.columns:
        invalid_mask = ~df['assay'].isin(rules['allowed_assays'])
        invalid_assays = df[invalid_mask]['assay'].unique().tolist()
    
    return invalid_assays, len(invalid_assays)


def check_machine_values(df: pd.DataFrame, rules: Dict) -> Tuple[List, int]:
    """Check for valid machine values."""
    invalid_machines = []
    if 'machine_id' in df.columns:
        invalid_mask = ~df['machine_id'].isin(rules['allowed_machines'])
        invalid_machines = df[invalid_mask]['machine_id'].unique().tolist()
    
    return invalid_machines, len(invalid_machines)


def check_timestamp_ordering(df: pd.DataFrame) -> Tuple[List, int]:
    """Check that processed_at is after received_at."""
    ordering_errors = []
    if 'received_at' in df.columns and 'processed_at' in df.columns:
        # Convert to datetime
        df['received_at_dt'] = pd.to_datetime(df['received_at'], errors='coerce')
        df['processed_at_dt'] = pd.to_datetime(df['processed_at'], errors='coerce')
        
        # Check ordering for completed specimens
        completed_mask = (df['status'] == 'COMPLETED') & df['processed_at_dt'].notna()
        invalid_ordering = df[completed_mask & (df['processed_at_dt'] <= df['received_at_dt'])]
        
        ordering_errors = invalid_ordering['specimen_id'].tolist()
    
    return ordering_errors, len(ordering_errors)


def check_future_dates(df: pd.DataFrame, rules: Dict) -> Tuple[List, int]:
    """Check for future dates."""
    future_dates = []
    tolerance_hours = rules.get('future_date_tolerance_hours', 1)
    now = datetime.now()
    
    for col in ['received_at', 'processed_at']:
        if col in df.columns:
            df[f'{col}_dt'] = pd.to_datetime(df[col], errors='coerce')
            future_mask = df[f'{col}_dt'] > (now + pd.Timedelta(hours=tolerance_hours))
            future_dates.extend(df[future_mask]['specimen_id'].tolist())
    
    return future_dates, len(future_dates)


def check_tat_reasonableness(df: pd.DataFrame, rules: Dict) -> Tuple[List, int]:
    """Check for reasonable TAT values."""
    unreasonable_tat = []
    max_tat_hours = rules.get('max_tat_hours', 24)
    
    if 'received_at' in df.columns and 'processed_at' in df.columns:
        df['received_at_dt'] = pd.to_datetime(df['received_at'], errors='coerce')
        df['processed_at_dt'] = pd.to_datetime(df['processed_at'], errors='coerce')
        
        # Calculate TAT for completed specimens
        completed_mask = (df['status'] == 'COMPLETED') & df['processed_at_dt'].notna()
        df.loc[completed_mask, 'tat_hours'] = (
            df.loc[completed_mask, 'processed_at_dt'] - 
            df.loc[completed_mask, 'received_at_dt']
        ).dt.total_seconds() / 3600
        
        # Check for unreasonable TAT
        unreasonable_mask = completed_mask & (df['tat_hours'] > max_tat_hours)
        unreasonable_tat = df[unreasonable_mask]['specimen_id'].tolist()
    
    return unreasonable_tat, len(unreasonable_tat)


def run_dq_checks(df: pd.DataFrame, rules: Dict) -> Dict:
    """Run all data quality checks."""
    results = {}
    
    # Required columns
    missing_cols, missing_count = check_required_columns(df, rules)
    results['missing_columns'] = {
        'errors': missing_cols,
        'count': missing_count,
        'failed_rows': []  # All rows fail if columns missing
    }
    
    # Status values
    invalid_statuses, status_count = check_status_values(df, rules)
    status_failed_rows = df[df['status'].isin(invalid_statuses)]['specimen_id'].tolist()
    results['invalid_statuses'] = {
        'errors': invalid_statuses,
        'count': status_count,
        'failed_rows': status_failed_rows
    }
    
    # Assay values
    invalid_assays, assay_count = check_assay_values(df, rules)
    assay_failed_rows = df[df['assay'].isin(invalid_assays)]['specimen_id'].tolist()
    results['invalid_assays'] = {
        'errors': invalid_assays,
        'count': assay_count,
        'failed_rows': assay_failed_rows
    }
    
    # Machine values
    invalid_machines, machine_count = check_machine_values(df, rules)
    machine_failed_rows = df[df['machine_id'].isin(invalid_machines)]['specimen_id'].tolist()
    results['invalid_machines'] = {
        'errors': invalid_machines,
        'count': machine_count,
        'failed_rows': machine_failed_rows
    }
    
    # Timestamp ordering
    ordering_errors, ordering_count = check_timestamp_ordering(df)
    results['timestamp_ordering'] = {
        'errors': ordering_errors,
        'count': ordering_count,
        'failed_rows': ordering_errors
    }
    
    # Future dates
    future_dates, future_count = check_future_dates(df, rules)
    results['future_dates'] = {
        'errors': future_dates,
        'count': future_count,
        'failed_rows': future_dates
    }
    
    # TAT reasonableness
    unreasonable_tat, tat_count = check_tat_reasonableness(df, rules)
    results['unreasonable_tat'] = {
        'errors': unreasonable_tat,
        'count': tat_count,
        'failed_rows': unreasonable_tat
    }
    
    return results


def save_failed_rows(df: pd.DataFrame, results: Dict, output_file: str):
    """Save failed rows to CSV."""
    # Collect all failed specimen IDs
    all_failed_ids = set()
    for check_result in results.values():
        all_failed_ids.update(check_result['failed_rows'])
    
    if all_failed_ids:
        failed_df = df[df['specimen_id'].isin(all_failed_ids)]
        failed_df.to_csv(output_file, index=False)
        print(f"Saved {len(failed_df)} failed rows to {output_file}")
    else:
        print("No failed rows to save")


def create_visualization(results: Dict, output_file: str):
    """Create matplotlib visualization of DQ failures."""
    # Prepare data for plotting
    check_names = []
    failure_counts = []
    
    for check_name, result in results.items():
        check_names.append(check_name.replace('_', ' ').title())
        failure_counts.append(result['count'])
    
    # Create bar chart
    plt.figure(figsize=(12, 6))
    bars = plt.bar(check_names, failure_counts, color='red' if any(failure_counts) else 'green')
    
    # Add value labels on bars
    for bar, count in zip(bars, failure_counts):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                str(count), ha='center', va='bottom')
    
    plt.title('Data Quality Check Results')
    plt.xlabel('Quality Check')
    plt.ylabel('Number of Failures')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save plot
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved visualization to {output_file}")
    plt.close()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run data quality checks")
    parser.add_argument(
        "csv_file", type=str,
        help="Input CSV file to check"
    )
    parser.add_argument(
        "--rules", type=str, default=None,
        help="YAML rules file (optional)"
    )
    parser.add_argument(
        "--output-dir", type=str, default="data/seeds/exports",
        help="Output directory for reports"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file {args.csv_file} not found")
        return
    
    print(f"Running data quality checks on {args.csv_file}...")
    
    # Load data
    df = pd.read_csv(args.csv_file)
    print(f"Loaded {len(df)} rows from CSV")
    
    # Load rules
    rules = load_rules(args.rules)
    
    # Run checks
    results = run_dq_checks(df, rules)
    
    # Print summary
    print("\nData Quality Check Summary:")
    print("=" * 50)
    
    total_failures = 0
    for check_name, result in results.items():
        count = result['count']
        total_failures += count
        status = "❌" if count > 0 else "✅"
        print(f"{status} {check_name.replace('_', ' ').title()}: {count} failures")
    
    print(f"\nTotal failures: {total_failures}")
    
    # Save failed rows
    os.makedirs(args.output_dir, exist_ok=True)
    failed_rows_file = os.path.join(args.output_dir, "dq_failed_rows.csv")
    save_failed_rows(df, results, failed_rows_file)
    
    # Create visualization
    viz_file = os.path.join(args.output_dir, "dq_results.png")
    create_visualization(results, viz_file)
    
    # Save detailed results
    results_file = os.path.join(args.output_dir, "dq_results.yaml")
    with open(results_file, 'w') as f:
        yaml.dump(results, f, default_flow_style=False)
    
    print(f"\nDetailed results saved to {results_file}")
    print(f"All outputs saved to {args.output_dir}")


if __name__ == "__main__":
    main()
