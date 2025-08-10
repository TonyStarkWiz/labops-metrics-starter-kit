#!/usr/bin/env python3
"""
Data Quality Rules Engine API endpoints
Integrates the DQ rules engine with FastAPI
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import pandas as pd
import yaml
import tempfile
import os
from pathlib import Path
import json
from datetime import datetime

# Import the DQ rules engine
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))
from dq_rules_engine import DQRulesEngine, DQRule, DQViolation

router = APIRouter()

@router.post("/validate-csv")
async def validate_csv_data(
    file: UploadFile = File(...),
    rules_file: Optional[UploadFile] = File(None),
    custom_rules: Optional[str] = Form(None)
):
    """
    Validate CSV data against DQ rules
    
    Args:
        file: CSV file to validate
        rules_file: Optional YAML rules file
        custom_rules: Optional JSON string with custom rules
    """
    try:
        # Read CSV data
        df = pd.read_csv(file.file)
        
        # Load rules
        rules_engine = DQRulesEngine()
        
        if rules_file:
            # Save uploaded rules file temporarily
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
                tmp.write(rules_file.file.read().decode())
                tmp_path = tmp.name
            
            try:
                rules_engine.load_rules(tmp_path)
            finally:
                os.unlink(tmp_path)
        elif custom_rules:
            # Parse custom rules from JSON
            rules_data = json.loads(custom_rules)
            for rule_data in rules_data.get('rules', []):
                rule = DQRule(
                    name=rule_data['name'],
                    description=rule_data['description'],
                    rule_type=rule_data['rule_type'],
                    parameters=rule_data.get('parameters', {}),
                    severity=rule_data.get('severity', 'ERROR')
                )
                rules_engine.rules.append(rule)
        else:
            # Use default sample rules
            sample_rules_path = Path(__file__).parent.parent.parent / "sample_dq_rules.yaml"
            if sample_rules_path.exists():
                rules_engine.load_rules(str(sample_rules_path))
        
        # Validate data
        violations = rules_engine.validate_data(df)
        
        # Generate report
        report = rules_engine.generate_report()
        
        return {
            "status": "success",
            "data_shape": df.shape,
            "rules_applied": len(rules_engine.rules),
            "violations_count": len(violations),
            "violations": [
                {
                    "rule_name": v.rule_name,
                    "description": v.description,
                    "severity": v.severity,
                    "row_indices": v.row_indices,
                    "column": v.column,
                    "value": str(v.value) if v.value is not None else None,
                    "expected": str(v.expected) if v.expected is not None else None
                }
                for v in violations
            ],
            "summary": report.get("summary", {}),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")

@router.get("/rules/templates")
async def get_rule_templates():
    """Get available rule templates and examples"""
    return {
        "rule_types": [
            {
                "type": "required_columns",
                "description": "Check if required columns are present",
                "example": {
                    "name": "Required Columns Check",
                    "rule_type": "required_columns",
                    "parameters": {"columns": ["id", "name", "date"]}
                }
            },
            {
                "type": "timestamp_order",
                "description": "Ensure timestamp order (e.g., received < processed)",
                "example": {
                    "name": "Timestamp Order",
                    "rule_type": "timestamp_order",
                    "parameters": {
                        "received_column": "received_at",
                        "processed_column": "processed_at"
                    }
                }
            },
            {
                "type": "allowed_values",
                "description": "Check if values are in allowed set",
                "example": {
                    "name": "Status Validation",
                    "rule_type": "allowed_values",
                    "parameters": {
                        "column": "status",
                        "allowed_values": ["active", "inactive", "pending"]
                    }
                }
            },
            {
                "type": "data_types",
                "description": "Validate data types of columns",
                "example": {
                    "name": "Data Type Check",
                    "rule_type": "data_types",
                    "parameters": {
                        "columns": {"id": "int", "date": "datetime", "amount": "float"}
                    }
                }
            },
            {
                "type": "uniqueness",
                "description": "Ensure column values are unique",
                "example": {
                    "name": "Unique IDs",
                    "rule_type": "uniqueness",
                    "parameters": {"columns": ["id"]}
                }
            },
            {
                "type": "completeness",
                "description": "Check for missing values",
                "example": {
                    "name": "No Missing Values",
                    "rule_type": "completeness",
                    "parameters": {"columns": ["id", "name"], "threshold": 0.0}
                }
            }
        ],
        "sample_rules_file": "sample_dq_rules.yaml"
    }

@router.post("/rules/validate")
async def validate_rule_syntax(rules: Dict[str, Any]):
    """Validate rule syntax without running against data"""
    try:
        # Test rule parsing
        rules_engine = DQRulesEngine()
        
        # Create temporary rules file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
            yaml.dump(rules, tmp)
            tmp_path = tmp.name
        
        try:
            rules_engine.load_rules(tmp_path)
            return {
                "status": "valid",
                "rules_loaded": len(rules_engine.rules),
                "message": "Rules syntax is valid"
            }
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid rule syntax: {str(e)}")

@router.get("/health")
async def dq_engine_health():
    """Health check for DQ engine"""
    return {
        "status": "healthy",
        "service": "Data Quality Rules Engine",
        "timestamp": datetime.now().isoformat()
    }
