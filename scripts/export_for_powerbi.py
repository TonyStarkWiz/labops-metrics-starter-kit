#!/usr/bin/env python3
"""
Power BI Export Script for LabOps Metrics
Exports data in formats suitable for Power BI analysis
"""
import pandas as pd
import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Any


class PowerBIExporter:
    """Handles Power BI data export and PBIX file creation."""
    
    def __init__(self, db_path: str = "labops.db", export_dir: str = "powerbi_exports"):
        """
        Initialize Power BI exporter.
        
        Args:
            db_path: Path to SQLite database
            export_dir: Directory to save exports
        """
        self.db_path = db_path
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
        
        # Power BI data model configuration
        self.data_model = {
            "tables": {
                "specimens": {
                    "columns": [
                        "specimen_id", "patient_id", "assay_type", "status",
                        "received_at", "processed_at", "priority", "lab_technician", "error_code"
                    ],
                    "relationships": []
                },
                "assay_types": {
                    "columns": ["assay_type", "category", "typical_tat_hours", "priority_level"],
                    "relationships": [{"from": "assay_type", "to": "specimens.assay_type"}]
                },
                "machines": {
                    "columns": ["machine_id", "machine_name", "assay_types", "capacity_per_hour", "status"],
                    "relationships": []
                },
                "daily_metrics": {
                    "columns": ["date", "total_specimens", "completed_specimens", "avg_tat_hours", "error_rate"],
                    "relationships": []
                }
            }
        }
    
    def load_data_from_db(self) -> Dict[str, pd.DataFrame]:
        """Load data from SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Load main specimens table
            specimens_df = pd.read_sql_query("SELECT * FROM specimens", conn)
            
            # Create derived tables
            assay_types_df = self._create_assay_types_dimension(specimens_df)
            machines_df = self._create_machines_dimension(specimens_df)
            daily_metrics_df = self._create_daily_metrics(specimens_df)
            
            conn.close()
            
            return {
                "specimens": specimens_df,
                "assay_types": assay_types_df,
                "machines": machines_df,
                "daily_metrics": daily_metrics_df
            }
            
        except Exception as e:
            print(f"❌ Error loading data from database: {e}")
            # Return sample data if database fails
            return self._create_sample_data()
    
    def _create_assay_types_dimension(self, specimens_df: pd.DataFrame) -> pd.DataFrame:
        """Create assay types dimension table."""
        if specimens_df.empty:
            return pd.DataFrame()
        
        assay_stats = specimens_df.groupby('assay_type').agg({
            'specimen_id': 'count',
            'status': lambda x: (x == 'Completed').sum() / len(x) * 100
        }).reset_index()
        
        assay_stats.columns = ['assay_type', 'total_count', 'completion_rate']
        
        # Add typical TAT and priority levels
        typical_tat = {
            'Blood Chemistry': 4,
            'Hematology': 2,
            'Microbiology': 24,
            'Immunology': 8,
            'Molecular': 48
        }
        
        priority_levels = {
            'Blood Chemistry': 'Medium',
            'Hematology': 'High',
            'Microbiology': 'Medium',
            'Immunology': 'High',
            'Molecular': 'Low'
        }
        
        assay_stats['typical_tat_hours'] = assay_stats['assay_type'].map(typical_tat)
        assay_stats['priority_level'] = assay_stats['assay_type'].map(priority_levels)
        assay_stats['category'] = assay_stats['assay_type'].apply(
            lambda x: 'Routine' if x in ['Blood Chemistry', 'Hematology'] else 'Specialized'
        )
        
        return assay_stats
    
    def _create_machines_dimension(self, specimens_df: pd.DataFrame) -> pd.DataFrame:
        """Create machines dimension table."""
        if specimens_df.empty:
            return pd.DataFrame()
        
        # Simulate machine data based on lab technicians
        machines = []
        for i, tech in enumerate(specimens_df['lab_technician'].unique()):
            machine = {
                'machine_id': f'MACHINE_{i+1:03d}',
                'machine_name': f'Analyzer {chr(65+i)}',
                'assay_types': ','.join(specimens_df[specimens_df['lab_technician'] == tech]['assay_type'].unique()),
                'capacity_per_hour': np.random.randint(10, 50),
                'status': 'Active'
            }
            machines.append(machine)
        
        return pd.DataFrame(machines)
    
    def _create_daily_metrics(self, specimens_df: pd.DataFrame) -> pd.DataFrame:
        """Create daily metrics aggregation table."""
        if specimens_df.empty:
            return pd.DataFrame()
        
        # Convert to datetime if needed
        specimens_df['received_at'] = pd.to_datetime(specimens_df['received_at'])
        specimens_df['processed_at'] = pd.to_datetime(specimens_df['processed_at'])
        
        # Group by date
        daily_stats = specimens_df.groupby(specimens_df['received_at'].dt.date).agg({
            'specimen_id': 'count',
            'status': lambda x: (x == 'Completed').sum(),
            'error_code': lambda x: x.notna().sum()
        }).reset_index()
        
        daily_stats.columns = ['date', 'total_specimens', 'completed_specimens', 'error_count']
        
        # Calculate derived metrics
        daily_stats['avg_tat_hours'] = daily_stats.apply(
            lambda row: self._calculate_daily_tat(specimens_df, row['date']), axis=1
        )
        daily_stats['error_rate'] = (daily_stats['error_count'] / daily_stats['total_specimens'] * 100).round(2)
        
        return daily_stats
    
    def _calculate_daily_tat(self, specimens_df: pd.DataFrame, date: datetime.date) -> float:
        """Calculate average TAT for a specific date."""
        daily_specimens = specimens_df[
            (specimens_df['received_at'].dt.date == date) & 
            (specimens_df['status'] == 'Completed')
        ]
        
        if daily_specimens.empty:
            return 0.0
        
        tat_hours = (daily_specimens['processed_at'] - daily_specimens['received_at']).dt.total_seconds() / 3600
        return round(tat_hours.mean(), 2)
    
    def _create_sample_data(self) -> Dict[str, pd.DataFrame]:
        """Create sample data if database is not available."""
        print("📊 Creating sample data for Power BI export...")
        
        # Generate sample specimens
        np.random.seed(42)
        n_samples = 500
        
        base_date = datetime.now() - timedelta(days=30)
        dates = [base_date + timedelta(days=i) for i in range(30)]
        
        specimens_data = []
        for i in range(n_samples):
            received_date = np.random.choice(dates)
            processing_hours = np.random.exponential(6) + 1
            processed_date = received_date + timedelta(hours=min(processing_hours, 72))
            
            specimen = {
                'specimen_id': f'SP{i+1:06d}',
                'patient_id': f'P{i+1:06d}',
                'assay_type': np.random.choice(['Blood Chemistry', 'Hematology', 'Microbiology', 'Immunology', 'Molecular']),
                'status': np.random.choice(['Completed', 'In Progress', 'Pending', 'Failed'], p=[0.8, 0.15, 0.03, 0.02]),
                'received_at': received_date,
                'processed_at': processed_date if np.random.random() > 0.2 else None,
                'priority': np.random.choice(['High', 'Medium', 'Low']),
                'lab_technician': f'Tech{np.random.randint(1, 6)}',
                'error_code': np.random.choice([None, 'E001', 'E002', 'E003'], p=[0.9, 0.05, 0.03, 0.02])
            }
            specimens_data.append(specimen)
        
        specimens_df = pd.DataFrame(specimens_data)
        
        # Create derived tables
        assay_types_df = self._create_assay_types_dimension(specimens_df)
        machines_df = self._create_machines_dimension(specimens_df)
        daily_metrics_df = self._create_daily_metrics(specimens_df)
        
        return {
            "specimens": specimens_df,
            "assay_types": assay_types_df,
            "machines": machines_df,
            "daily_metrics": daily_metrics_df
        }
    
    def export_to_csv(self, data: Dict[str, pd.DataFrame]) -> Dict[str, str]:
        """Export data to CSV files."""
        exported_files = {}
        
        for table_name, df in data.items():
            if not df.empty:
                filename = f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filepath = self.export_dir / filename
                
                # Export to CSV
                df.to_csv(filepath, index=False)
                exported_files[table_name] = str(filepath)
                print(f"✅ Exported {table_name}: {len(df)} rows to {filename}")
            else:
                print(f"⚠️  Skipping {table_name}: No data available")
        
        return exported_files
    
    def create_pbix_template(self, data: Dict[str, pd.DataFrame]) -> str:
        """Create a Power BI template file with data model definition."""
        template = {
            "version": "1.0",
            "name": "LabOps Metrics Dashboard",
            "description": "Laboratory operations metrics and analytics dashboard",
            "created": datetime.now().isoformat(),
            "data_model": self.data_model,
            "sample_data": {
                table: {
                    "row_count": len(df),
                    "columns": list(df.columns) if not df.empty else []
                }
                for table, df in data.items()
            },
            "recommended_visuals": [
                {
                    "name": "Daily Throughput Trend",
                    "type": "line_chart",
                    "data": "daily_metrics",
                    "x_axis": "date",
                    "y_axis": "total_specimens"
                },
                {
                    "name": "Assay Type Distribution",
                    "type": "pie_chart",
                    "data": "assay_types",
                    "values": "total_count",
                    "labels": "assay_type"
                },
                {
                    "name": "TAT Performance by Assay",
                    "type": "bar_chart",
                    "data": "assay_types",
                    "x_axis": "assay_type",
                    "y_axis": "typical_tat_hours"
                },
                {
                    "name": "Error Rate Trend",
                    "type": "line_chart",
                    "data": "daily_metrics",
                    "x_axis": "date",
                    "y_axis": "error_rate"
                }
            ],
            "setup_instructions": [
                "1. Import the CSV files into Power BI Desktop",
                "2. Create relationships between tables using the data model above",
                "3. Build the recommended visuals using the specified data mappings",
                "4. Add filters for date ranges, assay types, and status",
                "5. Create calculated measures for KPIs and trends"
            ]
        }
        
        # Save template
        template_file = self.export_dir / "labops_metrics_template.json"
        with open(template_file, 'w') as f:
            json.dump(template, f, indent=2, default=str)
        
        print(f"✅ Created Power BI template: {template_file}")
        return str(template_file)
    
    def create_sample_pbix_data(self) -> str:
        """Create a sample PBIX-ready dataset."""
        # Generate a smaller, focused dataset for Power BI
        np.random.seed(42)
        n_samples = 200
        
        # Create focused sample data
        assay_types = ['Blood Chemistry', 'Hematology', 'Microbiology', 'Immunology']
        statuses = ['Completed', 'In Progress', 'Pending', 'Failed']
        
        specimens_data = []
        for i in range(n_samples):
            received_date = datetime.now() - timedelta(days=np.random.randint(0, 30))
            processing_hours = np.random.exponential(4) + 1
            processed_date = received_date + timedelta(hours=min(processing_hours, 24))
            
            specimen = {
                'specimen_id': f'SP{i+1:06d}',
                'assay_type': np.random.choice(assay_types),
                'status': np.random.choice(statuses, p=[0.75, 0.15, 0.08, 0.02]),
                'received_at': received_date,
                'processed_at': processed_date if np.random.random() > 0.25 else None,
                'priority': np.random.choice(['High', 'Medium', 'Low']),
                'error_code': np.random.choice([None, 'E001', 'E002'], p=[0.92, 0.05, 0.03])
            }
            specimens_data.append(specimen)
        
        df = pd.DataFrame(specimens_data)
        
        # Export focused dataset
        filename = f"labops_pbix_sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = self.export_dir / filename
        df.to_csv(filepath, index=False)
        
        print(f"✅ Created Power BI sample dataset: {filename}")
        return str(filepath)
    
    def export_all(self) -> Dict[str, Any]:
        """Export all data for Power BI consumption."""
        print("🚀 Starting Power BI export...")
        
        # Load data
        data = self.load_data_from_db()
        
        # Export to CSV
        csv_files = self.export_to_csv(data)
        
        # Create template
        template_file = self.create_pbix_template(data)
        
        # Create sample dataset
        sample_file = self.create_sample_pbix_data()
        
        # Create summary report
        summary = {
            "export_timestamp": datetime.now().isoformat(),
            "csv_files": csv_files,
            "template_file": template_file,
            "sample_file": sample_file,
            "data_summary": {
                table: {
                    "rows": len(df),
                    "columns": list(df.columns) if not df.empty else []
                }
                for table, df in data.items()
            }
        }
        
        # Save summary
        summary_file = self.export_dir / "export_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n🎉 Power BI export completed successfully!")
        print(f"📁 Export directory: {self.export_dir}")
        print(f"📊 Files exported: {len(csv_files)} CSV files")
        print(f"📋 Template: {template_file}")
        print(f"📈 Sample dataset: {sample_file}")
        print(f"📝 Summary: {summary_file}")
        
        return summary


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Export LabOps data for Power BI")
    parser.add_argument("--db", default="labops.db", help="Path to SQLite database")
    parser.add_argument("--output", default="powerbi_exports", help="Output directory")
    parser.add_argument("--sample-only", action="store_true", help="Export only sample data")
    
    args = parser.parse_args()
    
    exporter = PowerBIExporter(db_path=args.db, export_dir=args.output)
    
    if args.sample_only:
        exporter.create_sample_pbix_data()
    else:
        exporter.export_all()


if __name__ == "__main__":
    main()
