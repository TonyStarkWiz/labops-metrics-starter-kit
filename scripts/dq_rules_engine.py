#!/usr/bin/env python3
"""
Data Quality Rules Engine for LabOps Metrics
Validates CSV data against declarative rules and generates DQ reports
"""

import pandas as pd
import yaml
import argparse
import sys
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Any, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
import json

@dataclass
class DQRule:
    """Data Quality Rule definition"""
    name: str
    description: str
    rule_type: str
    parameters: Dict[str, Any]
    severity: str = "ERROR"  # ERROR, WARNING, INFO

@dataclass
class DQViolation:
    """Data Quality Violation record"""
    rule_name: str
    description: str
    severity: str
    row_indices: List[int]
    column: str = None
    value: Any = None
    expected: Any = None

class DQRulesEngine:
    """Data Quality Rules Engine for validating CSV data"""
    
    def __init__(self, rules_file: str = None):
        self.rules = []
        self.violations = []
        if rules_file:
            self.load_rules(rules_file)
    
    def load_rules(self, rules_file: str):
        """Load rules from YAML file"""
        try:
            with open(rules_file, 'r') as f:
                rules_data = yaml.safe_load(f)
            
            for rule_data in rules_data.get('rules', []):
                rule = DQRule(
                    name=rule_data['name'],
                    description=rule_data['description'],
                    rule_type=rule_data['rule_type'],
                    parameters=rule_data.get('parameters', {}),
                    severity=rule_data.get('severity', 'ERROR')
                )
                self.rules.append(rule)
                
        except Exception as e:
            print(f"Error loading rules: {e}")
            sys.exit(1)
    
    def validate_data(self, df: pd.DataFrame) -> List[DQViolation]:
        """Validate data against all loaded rules"""
        self.violations = []
        
        for rule in self.rules:
            if rule.rule_type == "required_columns":
                self._check_required_columns(df, rule)
            elif rule.rule_type == "timestamp_order":
                self._check_timestamp_order(df, rule)
            elif rule.rule_type == "no_future_dates":
                self._check_no_future_dates(df, rule)
            elif rule.rule_type == "allowed_values":
                self._check_allowed_values(df, rule)
            elif rule.rule_type == "data_types":
                self._check_data_types(df, rule)
            elif rule.rule_type == "range_check":
                self._check_range_check(df, rule)
            elif rule.rule_type == "uniqueness":
                self._check_uniqueness(df, rule)
            elif rule.rule_type == "completeness":
                self._check_completeness(df, rule)
        
        return self.violations
    
    def _check_required_columns(self, df: pd.DataFrame, rule: DQRule):
        """Check if required columns are present"""
        required_cols = rule.parameters.get('columns', [])
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            violation = DQViolation(
                rule_name=rule.name,
                description=f"Missing required columns: {missing_cols}",
                severity=rule.severity,
                row_indices=[],
                column="schema"
            )
            self.violations.append(violation)
    
    def _check_timestamp_order(self, df: pd.DataFrame, rule: DQRule):
        """Check if received_at < processed_at"""
        received_col = rule.parameters.get('received_column', 'received_at')
        processed_col = rule.parameters.get('processed_column', 'processed_at')
        
        if received_col in df.columns and processed_col in df.columns:
            # Convert to datetime if needed
            df_copy = df.copy()
            for col in [received_col, processed_col]:
                if df_copy[col].dtype == 'object':
                    df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce')
            
            invalid_rows = df_copy[df_copy[received_col] >= df_copy[processed_col]]
            
            if len(invalid_rows) > 0:
                violation = DQViolation(
                    rule_name=rule.name,
                    description=f"Invalid timestamp order: {len(invalid_rows)} rows have received_at >= processed_at",
                    severity=rule.severity,
                    row_indices=invalid_rows.index.tolist(),
                    column=f"{received_col}/{processed_col}"
                )
                self.violations.append(violation)
    
    def _check_no_future_dates(self, df: pd.DataFrame, rule: DQRule):
        """Check for future dates in timestamp columns"""
        timestamp_cols = rule.parameters.get('columns', ['received_at', 'processed_at'])
        today = pd.Timestamp.now().normalize()
        
        for col in timestamp_cols:
            if col in df.columns:
                df_copy = df.copy()
                if df_copy[col].dtype == 'object':
                    df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce')
                
                future_dates = df_copy[df_copy[col] > today]
                
                if len(future_dates) > 0:
                    violation = DQViolation(
                        rule_name=rule.name,
                        description=f"Future dates found in {col}: {len(future_dates)} rows",
                        severity=rule.severity,
                        row_indices=future_dates.index.tolist(),
                        column=col
                    )
                    self.violations.append(violation)
    
    def _check_allowed_values(self, df: pd.DataFrame, rule: DQRule):
        """Check if column values are in allowed list"""
        column = rule.parameters.get('column')
        allowed_values = rule.parameters.get('allowed_values', [])
        
        if column and column in df.columns:
            invalid_values = df[~df[column].isin(allowed_values)]
            
            if len(invalid_values) > 0:
                unique_invalid = invalid_values[column].unique()
                violation = DQViolation(
                    rule_name=rule.name,
                    description=f"Invalid values in {column}: {list(unique_invalid)}",
                    severity=rule.severity,
                    row_indices=invalid_values.index.tolist(),
                    column=column,
                    value=list(unique_invalid),
                    expected=allowed_values
                )
                self.violations.append(violation)
    
    def _check_data_types(self, df: pd.DataFrame, rule: DQRule):
        """Check if columns have expected data types"""
        type_checks = rule.parameters.get('columns', {})
        
        for col, expected_type in type_checks.items():
            if col in df.columns:
                if expected_type == 'datetime':
                    try:
                        pd.to_datetime(df[col], errors='raise')
                    except:
                        violation = DQViolation(
                            rule_name=rule.name,
                            description=f"Column {col} cannot be converted to datetime",
                            severity=rule.severity,
                            row_indices=df.index.tolist(),
                            column=col,
                            expected=expected_type
                        )
                        self.violations.append(violation)
                elif expected_type == 'numeric':
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        violation = DQViolation(
                            rule_name=rule.name,
                            description=f"Column {col} is not numeric",
                            severity=rule.severity,
                            row_indices=df.index.tolist(),
                            column=col,
                            expected=expected_type
                        )
                        self.violations.append(violation)
    
    def _check_range_check(self, df: pd.DataFrame, rule: DQRule):
        """Check if numeric values are within specified range"""
        column = rule.parameters.get('column')
        min_val = rule.parameters.get('min')
        max_val = rule.parameters.get('max')
        
        if column and column in df.columns and pd.api.types.is_numeric_dtype(df[column]):
            if min_val is not None:
                below_min = df[df[column] < min_val]
                if len(below_min) > 0:
                    violation = DQViolation(
                        rule_name=rule.name,
                        description=f"Values below minimum {min_val} in {column}: {len(below_min)} rows",
                        severity=rule.severity,
                        row_indices=below_min.index.tolist(),
                        column=column,
                        value=f"< {min_val}"
                    )
                    self.violations.append(violation)
            
            if max_val is not None:
                above_max = df[df[column] > max_val]
                if len(above_max) > 0:
                    violation = DQViolation(
                        rule_name=rule.name,
                        description=f"Values above maximum {max_val} in {column}: {len(above_max)} rows",
                        severity=rule.severity,
                        row_indices=above_max.index.tolist(),
                        column=column,
                        value=f"> {max_val}"
                    )
                    self.violations.append(violation)
    
    def _check_uniqueness(self, df: pd.DataFrame, rule: DQRule):
        """Check if specified columns have unique values"""
        columns = rule.parameters.get('columns', [])
        
        if columns:
            duplicates = df[df.duplicated(subset=columns, keep=False)]
            
            if len(duplicates) > 0:
                violation = DQViolation(
                    rule_name=rule.name,
                    description=f"Duplicate values found in columns {columns}: {len(duplicates)} rows",
                    severity=rule.severity,
                    row_indices=duplicates.index.tolist(),
                    column=", ".join(columns)
                )
                self.violations.append(violation)
    
    def _check_completeness(self, df: pd.DataFrame, rule: DQRule):
        """Check for missing values in specified columns"""
        columns = rule.parameters.get('columns', [])
        threshold = rule.parameters.get('threshold', 0.0)  # 0.0 = no missing values allowed
        
        for col in columns:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                missing_pct = missing_count / len(df)
                
                if missing_pct > threshold:
                    violation = DQViolation(
                        rule_name=rule.name,
                        description=f"Missing values in {col}: {missing_count} ({missing_pct:.1%})",
                        severity=rule.severity,
                        row_indices=df[df[col].isna()].index.tolist(),
                        column=col,
                        value=f"{missing_count} missing ({missing_pct:.1%})",
                        expected=f"≤ {threshold:.1%} missing"
                    )
                    self.violations.append(violation)
    
    def generate_report(self, output_dir: str = "dq_reports") -> Dict[str, Any]:
        """Generate comprehensive DQ report"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Summary statistics
        total_violations = len(self.violations)
        error_count = len([v for v in self.violations if v.severity == "ERROR"])
        warning_count = len([v for v in self.violations if v.severity == "WARNING"])
        info_count = len([v for v in self.violations if v.severity == "INFO"])
        
        # Group violations by rule
        violations_by_rule = {}
        for violation in self.violations:
            if violation.rule_name not in violations_by_rule:
                violations_by_rule[violation.rule_name] = []
            violations_by_rule[violation.rule_name].append(violation)
        
        # Create detailed report
        report = {
            "summary": {
                "total_violations": total_violations,
                "errors": error_count,
                "warnings": warning_count,
                "info": info_count,
                "timestamp": datetime.now().isoformat()
            },
            "violations_by_rule": violations_by_rule,
            "all_violations": [
                {
                    "rule_name": v.rule_name,
                    "description": v.description,
                    "severity": v.severity,
                    "column": v.column,
                    "value": v.value,
                    "expected": v.expected,
                    "affected_rows": len(v.row_indices)
                }
                for v in self.violations
            ]
        }
        
        # Save JSON report
        report_file = output_path / "dq_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Save CSV report
        violations_df = pd.DataFrame(report["all_violations"])
        if not violations_df.empty:
            csv_file = output_path / "dq_violations.csv"
            violations_df.to_csv(csv_file, index=False)
        
        # Generate visualization
        self._create_visualization(output_path)
        
        return {
            "report_file": str(report_file),
            "csv_file": str(output_path / "dq_violations.csv") if not violations_df.empty else None,
            "summary": report["summary"]
        }
    
    def _create_visualization(self, output_path: Path):
        """Create DQ visualization charts"""
        if not self.violations:
            return
        
        # Set style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Data Quality Analysis Report', fontsize=16, fontweight='bold')
        
        # 1. Violations by severity
        severity_counts = {}
        for violation in self.violations:
            severity_counts[violation.severity] = severity_counts.get(violation.severity, 0) + 1
        
        if severity_counts:
            ax1.pie(severity_counts.values(), labels=severity_counts.keys(), autopct='%1.1f%%', startangle=90)
            ax1.set_title('Violations by Severity')
        
        # 2. Violations by rule
        rule_counts = {}
        for violation in self.violations:
            rule_counts[violation.rule_name] = rule_counts.get(violation.rule_name, 0) + 1
        
        if rule_counts:
            rules = list(rule_counts.keys())
            counts = list(rule_counts.values())
            ax2.barh(rules, counts, color='skyblue')
            ax2.set_title('Violations by Rule')
            ax2.set_xlabel('Count')
        
        # 3. Violations by column
        column_counts = {}
        for violation in self.violations:
            if violation.column:
                column_counts[violation.column] = column_counts.get(violation.column, 0) + 1
        
        if column_counts:
            columns = list(column_counts.keys())
            counts = list(column_counts.values())
            ax3.bar(columns, counts, color='lightcoral')
            ax3.set_title('Violations by Column')
            ax3.set_ylabel('Count')
            plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 4. Affected rows distribution
        row_counts = [len(v.row_indices) for v in self.violations if v.row_indices]
        if row_counts:
            ax4.hist(row_counts, bins=min(10, len(row_counts)), color='lightgreen', alpha=0.7)
            ax4.set_title('Distribution of Affected Rows per Violation')
            ax4.set_xlabel('Number of Affected Rows')
            ax4.set_ylabel('Frequency')
        
        plt.tight_layout()
        
        # Save chart
        chart_file = output_path / "dq_visualization.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Visualization saved to: {chart_file}")

def create_sample_rules():
    """Create sample DQ rules for lab data"""
    rules = {
        "rules": [
            {
                "name": "Required Columns Check",
                "description": "Ensure all required columns are present",
                "rule_type": "required_columns",
                "parameters": {
                    "columns": ["specimen_id", "received_at", "processed_at", "status", "assay_type"]
                },
                "severity": "ERROR"
            },
            {
                "name": "Timestamp Order Validation",
                "description": "Ensure received_at < processed_at",
                "rule_type": "timestamp_order",
                "parameters": {
                    "received_column": "received_at",
                    "processed_column": "processed_at"
                },
                "severity": "ERROR"
            },
            {
                "name": "No Future Dates",
                "description": "Check for future dates in timestamp columns",
                "rule_type": "no_future_dates",
                "parameters": {
                    "columns": ["received_at", "processed_at"]
                },
                "severity": "WARNING"
            },
            {
                "name": "Valid Status Values",
                "description": "Ensure status values are valid",
                "rule_type": "allowed_values",
                "parameters": {
                    "column": "status",
                    "allowed_values": ["received", "in_process", "completed", "error", "cancelled"]
                },
                "severity": "ERROR"
            },
            {
                "name": "Valid Assay Types",
                "description": "Ensure assay types are valid",
                "rule_type": "allowed_values",
                "parameters": {
                    "column": "assay_type",
                    "allowed_values": ["blood_chemistry", "hematology", "microbiology", "molecular", "immunology"]
                },
                "severity": "ERROR"
            },
            {
                "name": "Timestamp Data Types",
                "description": "Ensure timestamp columns are datetime",
                "rule_type": "data_types",
                "parameters": {
                    "columns": {
                        "received_at": "datetime",
                        "processed_at": "datetime"
                    }
                },
                "severity": "ERROR"
            },
            {
                "name": "Unique Specimen IDs",
                "description": "Ensure specimen IDs are unique",
                "rule_type": "uniqueness",
                "parameters": {
                    "columns": ["specimen_id"]
                },
                "severity": "ERROR"
            },
            {
                "name": "No Missing Critical Fields",
                "description": "Ensure critical fields have no missing values",
                "rule_type": "completeness",
                "parameters": {
                    "columns": ["specimen_id", "status", "assay_type"],
                    "threshold": 0.0
                },
                "severity": "ERROR"
            }
        ]
    }
    
    return rules

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Data Quality Rules Engine for LabOps Metrics")
    parser.add_argument("csv_file", help="Path to CSV file to validate")
    parser.add_argument("--rules", "-r", help="Path to YAML rules file")
    parser.add_argument("--output", "-o", default="dq_reports", help="Output directory for reports")
    parser.add_argument("--create-sample-rules", action="store_true", help="Create sample rules file")
    
    args = parser.parse_args()
    
    # Create sample rules if requested
    if args.create_sample_rules:
        sample_rules_file = "sample_dq_rules.yaml"
        with open(sample_rules_file, 'w') as f:
            yaml.dump(create_sample_rules(), f, default_flow_style=False, indent=2)
        print(f"Sample rules created: {sample_rules_file}")
        return
    
    # Check if CSV file exists
    if not Path(args.csv_file).exists():
        print(f"Error: CSV file '{args.csv_file}' not found")
        sys.exit(1)
    
    # Load data
    print(f"Loading data from: {args.csv_file}")
    try:
        df = pd.read_csv(args.csv_file)
        print(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    except Exception as e:
        print(f"Error loading CSV: {e}")
        sys.exit(1)
    
    # Initialize rules engine
    engine = DQRulesEngine()
    
    if args.rules:
        print(f"Loading rules from: {args.rules}")
        engine.load_rules(args.rules)
    else:
        print("No rules file specified, using default lab data rules")
        # Create temporary rules file
        temp_rules = "temp_dq_rules.yaml"
        with open(temp_rules, 'w') as f:
            yaml.dump(create_sample_rules(), f, default_flow_style=False, indent=2)
        engine.load_rules(temp_rules)
        # Clean up
        Path(temp_rules).unlink()
    
    print(f"Loaded {len(engine.rules)} rules")
    
    # Validate data
    print("Validating data...")
    violations = engine.validate_data(df)
    
    # Generate report
    print("Generating report...")
    report_info = engine.generate_report(args.output)
    
    # Display summary
    summary = report_info["summary"]
    print("\n" + "="*50)
    print("DATA QUALITY REPORT SUMMARY")
    print("="*50)
    print(f"Total Violations: {summary['total_violations']}")
    print(f"Errors: {summary['errors']}")
    print(f"Warnings: {summary['warnings']}")
    print(f"Info: {summary['info']}")
    print(f"Report saved to: {report_info['report_file']}")
    
    if report_info['csv_file']:
        print(f"Violations CSV: {report_info['csv_file']}")
    
    if summary['total_violations'] == 0:
        print("\n✅ All data quality checks passed!")
    else:
        print(f"\n❌ Found {summary['total_violations']} data quality issues")
        print("Check the detailed report for more information")

if __name__ == "__main__":
    main()
