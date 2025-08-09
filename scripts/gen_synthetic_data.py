#!/usr/bin/env python3
"""
Synthetic lab data generator for LabOps Metrics Starter Kit.

Generates HIPAA-safe synthetic lab events with realistic timestamps and error patterns.
"""

import argparse
import csv
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.db import SessionLocal, create_tables
from app.core.models import Specimen, SpecimenStatus
from app.core.settings import settings


def generate_specimen_id() -> str:
    """Generate a realistic specimen ID."""
    prefix = random.choice(["SP", "BL", "UR", "CS"])
    number = random.randint(100000, 999999)
    return f"{prefix}{number}"


def generate_timestamps(days_back: int) -> tuple[datetime, datetime]:
    """Generate realistic received and processed timestamps."""
    # Generate received timestamp within the last N days
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days_back)
    
    received_at = start_time + timedelta(
        seconds=random.randint(0, int((end_time - start_time).total_seconds()))
    )
    
    # Generate processed timestamp (1-8 hours later, with some errors)
    processing_time = random.randint(30, 480)  # 30 minutes to 8 hours
    processed_at = received_at + timedelta(minutes=processing_time)
    
    return received_at, processed_at


def generate_specimen_data(
    days: int = 3,
    per_day: int = 1200,
    seed: int = None
) -> list[dict]:
    """Generate synthetic specimen data."""
    if seed is not None:
        random.seed(seed)
    
    specimens = []
    total_specimens = days * per_day
    used_ids = set()
    
    for i in range(total_specimens):
        # Generate unique specimen ID
        while True:
            specimen_id = generate_specimen_id()
            if specimen_id not in used_ids:
                used_ids.add(specimen_id)
                break
        
        assay = random.choice(settings.ASSAYS)
        machine_id = random.choice(settings.MACHINES)
        operator_id = random.choice(settings.OPERATORS)
        
        # Generate timestamps
        received_at, processed_at = generate_timestamps(days)
        
        # Determine status and error code
        if random.random() < settings.ERROR_RATE:
            status = SpecimenStatus.ERROR
            error_code = random.choice(settings.ERROR_CODES)
        else:
            status = SpecimenStatus.COMPLETED
            error_code = None
        
        specimen_data = {
            'specimen_id': specimen_id,
            'assay': assay,
            'machine_id': machine_id,
            'operator_id': operator_id,
            'status': status.value,
            'error_code': error_code,
            'received_at': received_at,
            'processed_at': processed_at if status == SpecimenStatus.COMPLETED else None
        }
        
        specimens.append(specimen_data)
    
    return specimens


def save_to_csv(specimens: list[dict], outfile: str):
    """Save specimens data to CSV file."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    
    # Write to CSV
    with open(outfile, 'w', newline='') as csvfile:
        fieldnames = [
            'specimen_id', 'assay', 'machine_id', 'operator_id',
            'status', 'error_code', 'received_at', 'processed_at'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(specimens)
    
    print(f"Saved {len(specimens)} specimens to {outfile}")


def save_to_database(specimens: list[dict], db: Session):
    """Save specimens data to database."""
    # Clear existing data
    db.query(Specimen).delete()
    
    # Create specimen objects
    specimen_objects = []
    for data in specimens:
        specimen = Specimen(
            specimen_id=data['specimen_id'],
            assay=data['assay'],
            machine_id=data['machine_id'],
            operator_id=data['operator_id'],
            status=SpecimenStatus(data['status']),
            error_code=data['error_code'],
            received_at=data['received_at'],
            processed_at=data['processed_at']
        )
        specimen_objects.append(specimen)
    
    # Bulk insert
    db.add_all(specimen_objects)
    db.commit()
    
    print(f"Saved {len(specimens)} specimens to database")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate synthetic lab data")
    parser.add_argument(
        "--days", type=int, default=3,
        help="Number of days of data to generate (default: 3)"
    )
    parser.add_argument(
        "--per-day", type=int, default=1200,
        help="Number of specimens per day (default: 1200)"
    )
    parser.add_argument(
        "--outfile", type=str,
        default=f"data/seeds/synthetic_{datetime.now().strftime('%Y%m%d')}.csv",
        help="Output CSV file path"
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducible data"
    )
    parser.add_argument(
        "--no-db", action="store_true",
        help="Skip database insertion"
    )
    
    args = parser.parse_args()
    
    print(f"Generating {args.days} days of data with {args.per_day} specimens per day...")
    
    # Generate data
    specimens = generate_specimen_data(
        days=args.days,
        per_day=args.per_day,
        seed=args.seed
    )
    
    # Save to CSV
    save_to_csv(specimens, args.outfile)
    
    # Save to database (unless --no-db flag)
    if not args.no_db:
        # Create tables if they don't exist
        create_tables()
        
        db = SessionLocal()
        try:
            save_to_database(specimens, db)
        finally:
            db.close()
    
    # Print summary
    status_counts = {}
    for specimen in specimens:
        status = specimen['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\nData generation summary:")
    print(f"Total specimens: {len(specimens)}")
    for status, count in status_counts.items():
        percentage = (count / len(specimens)) * 100
        print(f"  {status}: {count} ({percentage:.1f}%)")


if __name__ == "__main__":
    main()
