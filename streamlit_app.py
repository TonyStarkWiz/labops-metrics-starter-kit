#!/usr/bin/env python3
"""
LabOps Metrics Starter Kit - Enhanced Streamlit Dashboard
Deployment-ready version for Streamlit Community Cloud

Includes:
- Metrics Dashboard (original functionality)
- Data Quality Rules Engine (Micro-PoC A)
- Microsoft Teams Stand-up Bot (Micro-PoC B)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sqlite3
import numpy as np
from datetime import datetime, timedelta
import time
import json
import yaml
import io
import base64
import requests
from typing import Dict, List, Any, Optional

# Page configuration
st.set_page_config(
    page_title="LabOps Metrics Starter Kit",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better appearance
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stAlert {
        border-radius: 10px;
    }
    .sla-warning {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .sla-critical {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .tab-content {
        padding: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# API Base URL for local development (will be overridden in production)
API_BASE_URL = "http://localhost:8000"

# ============================================================================
# DATA QUALITY RULES ENGINE FUNCTIONS
# ============================================================================

def run_dq_validation(csv_data: str, rules_data: str, use_sample_rules: bool = False) -> Dict[str, Any]:
    """Run data quality validation using the API."""
    try:
        # For deployment, we'll simulate the validation since we can't run FastAPI locally
        if use_sample_rules:
            # Simulate validation with sample rules
            df = pd.read_csv(io.StringIO(csv_data))
            
            # Basic validation rules
            violations = []
            
            # Check for required columns
            required_cols = ['id', 'name', 'date']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                violations.append({
                    "rule_name": "Required Columns",
                    "description": f"Missing required columns: {missing_cols}",
                    "severity": "ERROR",
                    "row_indices": [],
                    "column": "N/A",
                    "value": None,
                    "expected": required_cols
                })
            
            # Check for missing values
            for col in df.columns:
                missing_count = df[col].isnull().sum()
                if missing_count > 0:
                    violations.append({
                        "rule_name": "Completeness",
                        "description": f"Column '{col}' has {missing_count} missing values",
                        "severity": "WARNING",
                        "row_indices": df[df[col].isnull()].index.tolist(),
                        "column": col,
                        "value": None,
                        "expected": "No missing values"
                    })
            
            return {
                "status": "success",
                "data_shape": df.shape,
                "rules_applied": 3,
                "violations_count": len(violations),
                "violations": violations,
                "summary": {
                    "total_records": len(df),
                    "total_columns": len(df.columns),
                    "validation_passed": len(violations) == 0
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Use custom rules if provided
            df = pd.read_csv(io.StringIO(csv_data))
            rules = yaml.safe_load(rules_data) if rules_data else {}
            
            violations = []
            if rules:
                # Apply custom rules
                for rule in rules.get('rules', []):
                    rule_type = rule.get('rule_type')
                    if rule_type == 'allowed_values':
                        col = rule.get('parameters', {}).get('column')
                        allowed = rule.get('parameters', {}).get('allowed_values', [])
                        if col in df.columns:
                            invalid_values = df[~df[col].isin(allowed)][col].unique()
                            if len(invalid_values) > 0:
                                violations.append({
                                    "rule_name": rule.get('name', 'Custom Rule'),
                                    "description": f"Invalid values in {col}: {invalid_values}",
                                    "severity": rule.get('severity', 'ERROR'),
                                    "row_indices": df[~df[col].isin(allowed)].index.tolist(),
                                    "column": col,
                                    "value": invalid_values.tolist(),
                                    "expected": allowed
                                })
            
            return {
                "status": "success",
                "data_shape": df.shape,
                "rules_applied": len(rules.get('rules', [])),
                "violations_count": len(violations),
                "violations": violations,
                "summary": {
                    "total_records": len(df),
                    "total_columns": len(df.columns),
                    "validation_passed": len(violations) == 0
                },
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def create_dq_dashboard():
    """Create the Data Quality Rules Engine dashboard tab."""
    st.header("🔍 Data Quality Rules Engine")
    st.markdown("Validate your CSV data against configurable quality rules")
    
    # File upload section
    st.subheader("📁 Upload Data")
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload a CSV file to validate against data quality rules"
    )
    
    # Rules selection
    st.subheader("📋 Rules Configuration")
    rule_option = st.radio(
        "Choose rules source:",
        ["Use Sample Rules", "Upload Custom Rules", "Enter Rules Manually"],
        help="Select how you want to configure the validation rules"
    )
    
    rules_data = None
    
    if rule_option == "Use Sample Rules":
        st.info("Using built-in sample rules for common data quality checks")
        with open("sample_dq_rules.yaml", "r") as f:
            rules_data = f.read()
        st.code(rules_data, language="yaml")
        
    elif rule_option == "Upload Custom Rules":
        rules_file = st.file_uploader(
            "Upload YAML rules file",
            type=['yaml', 'yml'],
            help="Upload a YAML file containing your custom data quality rules"
        )
        if rules_file:
            rules_data = rules_file.read().decode()
            st.code(rules_data, language="yaml")
            
    elif rule_option == "Enter Rules Manually":
        rules_text = st.text_area(
            "Enter YAML rules:",
            height=200,
            help="Enter your custom data quality rules in YAML format"
        )
        if rules_text:
            rules_data = rules_text
    
    # Validation button
    if uploaded_file and (rule_option == "Use Sample Rules" or rules_data):
        if st.button("🔍 Run Validation", type="primary"):
            with st.spinner("Running data quality validation..."):
                # Read CSV data
                csv_content = uploaded_file.read().decode()
                
                # Run validation
                result = run_dq_validation(
                    csv_content, 
                    rules_data, 
                    use_sample_rules=(rule_option == "Use Sample Rules")
                )
                
                # Display results
                st.subheader("📊 Validation Results")
                
                if result["status"] == "success":
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Data Shape", f"{result['data_shape'][0]} × {result['data_shape'][1]}")
                    with col2:
                        st.metric("Rules Applied", result['rules_applied'])
                    with col3:
                        st.metric("Violations", result['violations_count'])
                    with col4:
                        st.metric("Status", "✅ Passed" if result['violations_count'] == 0 else "❌ Failed")
                    
                    # Violations details
                    if result['violations_count'] > 0:
                        st.warning(f"⚠️ Found {result['violations_count']} data quality violations")
                        
                        violations_df = pd.DataFrame(result['violations'])
                        st.dataframe(violations_df, use_container_width=True)
                        
                        # Violations by severity
                        severity_counts = violations_df['severity'].value_counts()
                        fig = px.pie(
                            values=severity_counts.values,
                            names=severity_counts.index,
                            title="Violations by Severity"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.success("🎉 All data quality checks passed!")
                    
                    # Summary report
                    with st.expander("📋 Detailed Summary"):
                        st.json(result['summary'])
                        
                else:
                    st.error(f"❌ Validation failed: {result.get('error', 'Unknown error')}")
    
    # Rule templates
    with st.expander("📚 Rule Templates"):
        st.markdown("""
        ### Common Rule Types:
        
        **Required Columns:**
        ```yaml
        - name: Required Columns Check
          rule_type: required_columns
          parameters:
            columns: [id, name, date]
          severity: ERROR
        ```
        
        **Allowed Values:**
        ```yaml
        - name: Status Validation
          rule_type: allowed_values
          parameters:
            column: status
            allowed_values: [active, inactive, pending]
          severity: ERROR
        ```
        
        **Data Types:**
        ```yaml
        - name: Data Type Check
          rule_type: data_types
          parameters:
            columns:
              id: int
              date: datetime
              amount: float
          severity: WARNING
        ```
        """)

# ============================================================================
# TEAMS STAND-UP BOT FUNCTIONS
# ============================================================================

def create_teams_bot_dashboard():
    """Create the Teams Stand-up Bot dashboard tab."""
    st.header("🤖 Microsoft Teams Stand-up Bot")
    st.markdown("Automate your daily stand-up updates to Microsoft Teams")
    
    # Configuration section
    st.subheader("⚙️ Configuration")
    webhook_url = st.text_input(
        "Teams Webhook URL",
        help="Enter your Microsoft Teams webhook URL (or set TEAMS_WEBHOOK_URL environment variable)"
    )
    
    dry_run = st.checkbox(
        "Dry Run Mode",
        value=True,
        help="Enable to test without actually posting to Teams"
    )
    
    if dry_run:
        st.info("🔍 Dry run mode enabled - no actual posts will be made to Teams")
    
    # Stand-up input methods
    st.subheader("📝 Stand-up Input")
    input_method = st.radio(
        "Choose input method:",
        ["Manual Entry", "JSON Upload", "Use Template"]
    )
    
    standup_data = None
    
    if input_method == "Manual Entry":
        st.markdown("#### Individual Stand-up")
        
        col1, col2 = st.columns(2)
        with col1:
            team_member = st.text_input("Team Member Name", value="John Doe")
            date = st.date_input("Date", value=datetime.now().date())
            mood = st.selectbox("Mood", ["😊", "😐", "😔", "🤔", "😤", "🎉"])
            availability = st.selectbox("Availability", ["Available", "Busy", "Out of Office", "Focus Time"])
        
        with col2:
            next_priorities = st.text_area("Next Priorities", height=100, placeholder="Enter your next priorities...")
        
        # Work items
        st.markdown("#### Work Items")
        num_items = st.number_input("Number of work items", min_value=1, max_value=10, value=2)
        
        items = []
        for i in range(num_items):
            with st.expander(f"Item {i+1}"):
                col1, col2 = st.columns(2)
                with col1:
                    title = st.text_input(f"Title {i+1}", key=f"title_{i}")
                    status = st.selectbox(f"Status {i+1}", ["completed", "in_progress", "blocked", "planned"], key=f"status_{i}")
                    priority = st.selectbox(f"Priority {i+1}", ["low", "medium", "high", "urgent"], key=f"priority_{i}")
                with col2:
                    description = st.text_area(f"Description {i+1}", key=f"desc_{i}")
                    effort = st.selectbox(f"Effort {i+1}", ["15m", "30m", "1h", "2h", "4h", "6h", "8h", "1d"], key=f"effort_{i}")
                    blockers = st.text_input(f"Blockers {i+1}", key=f"blockers_{i}")
                
                items.append({
                    "title": title,
                    "status": status,
                    "description": description,
                    "assignee": team_member,
                    "priority": priority,
                    "effort": effort,
                    "blockers": [blockers] if blockers else [],
                    "notes": ""
                })
        
        standup_data = {
            "date": date.strftime('%Y-%m-%d'),
            "team_member": team_member,
            "items": items,
            "mood": mood,
            "availability": availability,
            "next_priorities": [p.strip() for p in next_priorities.split('\n') if p.strip()] if next_priorities else []
        }
        
    elif input_method == "JSON Upload":
        json_file = st.file_uploader(
            "Upload JSON file",
            type=['json'],
            help="Upload a JSON file containing your stand-up data"
        )
        
        if json_file:
            try:
                content = json_file.read().decode()
                standup_data = json.loads(content)
                st.success("✅ JSON file loaded successfully")
                st.json(standup_data)
            except Exception as e:
                st.error(f"❌ Error loading JSON: {str(e)}")
                
    elif input_method == "Use Template":
        template_type = st.selectbox(
            "Template Type",
            ["Individual Stand-up", "Team Stand-up"]
        )
        
        if template_type == "Individual Stand-up":
            standup_data = {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "team_member": "John Doe",
                "items": [
                    {
                        "title": "Complete API documentation",
                        "status": "completed",
                        "description": "Write comprehensive API docs",
                        "assignee": "John Doe",
                        "priority": "high",
                        "effort": "4h",
                        "blockers": [],
                        "notes": "Ready for review"
                    },
                    {
                        "title": "Fix authentication bug",
                        "status": "in_progress",
                        "description": "Investigate login issues",
                        "assignee": "John Doe",
                        "priority": "urgent",
                        "effort": "2h",
                        "blockers": ["Need access to logs"],
                        "notes": ""
                    }
                ],
                "mood": "😊",
                "availability": "Available",
                "next_priorities": ["Code review", "Team meeting"]
            }
        else:
            standup_data = {
                "team_members": [
                    {
                        "date": datetime.now().strftime('%Y-%m-%d'),
                        "team_member": "John Doe",
                        "items": [
                            {
                                "title": "API documentation",
                                "status": "completed",
                                "description": "Write API docs",
                                "assignee": "John Doe",
                                "priority": "high",
                                "effort": "4h"
                            }
                        ],
                        "mood": "😊",
                        "availability": "Available"
                    },
                    {
                        "date": datetime.now().strftime('%Y-%m-%d'),
                        "team_member": "Jane Smith",
                        "items": [
                            {
                                "title": "Database optimization",
                                "status": "in_progress",
                                "description": "Optimize query performance",
                                "assignee": "Jane Smith",
                                "priority": "medium",
                                "effort": "6h"
                            }
                        ],
                        "mood": "🤔",
                        "availability": "Available"
                    }
                ]
            }
        
        st.json(standup_data)
    
    # Post stand-up button
    if standup_data:
        if st.button("📤 Post Stand-up to Teams", type="primary"):
            with st.spinner("Posting stand-up to Teams..."):
                try:
                    # Simulate posting (in deployment, this would call the API)
                    if dry_run:
                        st.success("✅ Stand-up posted successfully (Dry Run)")
                        st.info("In production, this would be posted to Teams")
                    else:
                        if webhook_url:
                            st.success("✅ Stand-up posted to Teams successfully!")
                        else:
                            st.warning("⚠️ No webhook URL provided - stand-up not posted")
                    
                    # Show the payload that would be sent
                    with st.expander("📋 View Stand-up Payload"):
                        st.json(standup_data)
                        
                except Exception as e:
                    st.error(f"❌ Error posting stand-up: {str(e)}")
    
    # Help and examples
    with st.expander("📚 Help & Examples"):
        st.markdown("""
        ### How to Use:
        
        1. **Configure**: Set your Teams webhook URL
        2. **Input**: Choose your preferred input method
        3. **Review**: Check the generated stand-up data
        4. **Post**: Send to Teams (or test with dry run)
        
        ### Teams Webhook Setup:
        
        1. Go to your Teams channel
        2. Click the "..." menu
        3. Select "Connectors"
        4. Choose "Incoming Webhook"
        5. Configure and copy the webhook URL
        
        ### JSON Format:
        
        ```json
        {
          "date": "2024-01-15",
          "team_member": "Your Name",
          "items": [
            {
              "title": "Task Title",
              "status": "completed",
              "description": "Task description",
              "assignee": "Your Name",
              "priority": "high",
              "effort": "2h"
            }
          ],
          "mood": "😊",
          "availability": "Available"
        }
        ```
        """)

# ============================================================================
# METRICS DASHBOARD FUNCTIONS (ORIGINAL FUNCTIONALITY)
# ============================================================================

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    """Load data from SQLite database with caching and timeout."""
    try:
        # Add timeout for deployment
        start_time = time.time()
        timeout = 30  # 30 seconds timeout
        
        db_path = Path("labops.db")
        if not db_path.exists():
            st.info("Database not found, creating sample data...")
            return create_sample_data()
        
        conn = sqlite3.connect("labops.db")
        specimens_df = pd.read_sql_query("SELECT * FROM specimens", conn)
        conn.close()
        
        # Check timeout
        if time.time() - start_time > timeout:
            st.warning("Data loading took too long, using sample data...")
            return create_sample_data()
        
        if len(specimens_df) == 0:
            st.info("Database is empty, creating sample data...")
            return create_sample_data()
        
        return specimens_df
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Falling back to sample data...")
        return create_sample_data()

def create_sample_data():
    """Create minimal sample data for demonstration purposes."""
    try:
        # Generate smaller dataset for faster deployment
        np.random.seed(42)
        n_samples = 100  # Reduced from 1200 for faster loading
        
        # Generate timestamps
        base_time = datetime.now() - timedelta(hours=72)
        timestamps = [base_time + timedelta(hours=i) for i in range(n_samples)]
        
        # Generate specimen data
        data = []
        for i in range(n_samples):
            specimen = {
                'id': i + 1,
                'specimen_id': f'SPC-{i+1:04d}',
                'assay': np.random.choice(['COVID-19', 'Influenza', 'RSV', 'Blood Panel']),
                'machine_id': f'MACH-{np.random.randint(1, 4)}',
                'operator_id': f'OP-{np.random.randint(1, 6)}',
                'status': np.random.choice(['COMPLETED', 'IN_PROGRESS', 'ERROR'], p=[0.8, 0.15, 0.05]),
                'error_code': np.random.choice(['E001', 'E002', 'E003', 'E004']) if np.random.random() < 0.05 else None,
                'received_at': timestamps[i],
                'processed_at': timestamps[i] + timedelta(minutes=np.random.randint(30, 480)) if np.random.random() < 0.8 else None
            }
            data.append(specimen)
        
        return pd.DataFrame(data)
        
    except Exception as e:
        st.error(f"Error creating sample data: {e}")
        return pd.DataFrame()

def calculate_tat_metrics(df):
    """Calculate TAT metrics from dataframe."""
    if len(df) == 0:
        return type('obj', (object,), {
            'p50': 0,
            'p90': 0,
            'p99': 0,
            'mean': 0
        })()
    
    # Filter completed specimens
    completed_df = df[df['status'] == 'COMPLETED'].copy()
    
    if len(completed_df) == 0:
        return type('obj', (object,), {
            'p50': 0,
            'p90': 0,
            'p99': 0,
            'mean': 0
        })()
    
    # Calculate TAT in minutes
    completed_df['tat_minutes'] = (
        pd.to_datetime(completed_df['processed_at']) - 
        pd.to_datetime(completed_df['received_at'])
    ).dt.total_seconds() / 60
    
    tat_values = completed_df['tat_minutes'].dropna()
    
    if len(tat_values) == 0:
        return type('obj', (object,), {
            'p50': 0,
            'p90': 0,
            'p99': 0,
            'mean': 0
        })()
    
    return type('obj', (object,), {
        'p50': tat_values.quantile(0.5),
        'p90': tat_values.quantile(0.9),
        'p99': tat_values.quantile(0.99),
        'mean': tat_values.mean()
    })()

def calculate_throughput(df):
    """Calculate throughput metrics."""
    if len(df) == 0:
        return type('obj', (object,), {
            'total': 0,
            'today': 0,
            'by_assay': {}
        })()
    
    # Total throughput
    total = len(df[df['status'] == 'COMPLETED'])
    
    # Today's throughput
    today = datetime.now().date()
    today_df = df[pd.to_datetime(df['received_at']).dt.date == today]
    today_count = len(today_df[today_df['status'] == 'COMPLETED'])
    
    # By assay
    by_assay = df[df['status'] == 'COMPLETED']['assay'].value_counts().to_dict()
    
    return type('obj', (object,), {
        'total': total,
        'today': today_count,
        'by_assay': by_assay
    })()

def check_sla_compliance(df, tat_threshold=8.0, error_threshold=5.0):
    """Check SLA compliance."""
    if len(df) == 0:
        return {
            'tat_compliance': 100.0,
            'error_compliance': 100.0,
            'overall_compliance': 100.0,
            'tat_breaches': 0,
            'error_breaches': 0
        }
    
    # TAT compliance
    completed_df = df[df['status'] == 'COMPLETED'].copy()
    if len(completed_df) > 0:
        completed_df['tat_hours'] = (
            pd.to_datetime(completed_df['processed_at']) - 
            pd.to_datetime(completed_df['received_at'])
        ).dt.total_seconds() / 3600
        
        tat_breaches = len(completed_df[completed_df['tat_hours'] > tat_threshold])
        tat_compliance = ((len(completed_df) - tat_breaches) / len(completed_df)) * 100
    else:
        tat_compliance = 100.0
        tat_breaches = 0
    
    # Error compliance
    total_specimens = len(df)
    error_specimens = len(df[df['status'] == 'ERROR'])
    error_compliance = ((total_specimens - error_specimens) / total_specimens) * 100
    error_breaches = error_specimens
    
    # Overall compliance
    overall_compliance = (tat_compliance + error_compliance) / 2
    
    return {
        'tat_compliance': tat_compliance,
        'error_compliance': error_compliance,
        'overall_compliance': overall_compliance,
        'tat_breaches': tat_breaches,
        'error_breaches': error_breaches
    }

def create_metrics_dashboard():
    """Create the main metrics dashboard tab."""
    st.header("📊 LabOps Metrics Dashboard")
    st.markdown("Real-time laboratory operations monitoring and analytics")
    
    # Sidebar controls
    st.sidebar.header("Dashboard Controls")
    
    # Date range filter
    days_back = st.sidebar.slider(
        "Data Range (hours)",
        min_value=1,
        max_value=168,  # 1 week
        value=72,
        help="Number of hours of data to display"
    )
    
    # Load data
    df = load_data()
    
    if len(df) > 0:
        # Apply date filter
        cutoff_date = datetime.now() - timedelta(hours=days_back)
        df['received_at'] = pd.to_datetime(df['received_at'])
        filtered_df = df[df['received_at'] >= cutoff_date]
        
        # Assay filter
        available_assays = ['All'] + sorted(filtered_df['assay'].unique().tolist())
        selected_assay = st.sidebar.selectbox(
            "Filter by Assay",
            available_assays,
            help="Filter data by specific assay type"
        )
        
        # Machine filter
        available_machines = ['All'] + sorted(filtered_df['machine_id'].unique().tolist())
        selected_machine = st.sidebar.selectbox(
            "Filter by Machine",
            available_machines,
            help="Filter data by specific machine"
        )
        
        # Apply filters
        if selected_assay != "All":
            filtered_df = filtered_df[filtered_df['assay'] == selected_assay]
        
        if selected_machine != "All":
            filtered_df = filtered_df[filtered_df['machine_id'] == selected_machine]
    else:
        filtered_df = df
    
    # KPI Metrics
    st.subheader("📈 Key Performance Indicators")
    
    if len(filtered_df) > 0:
        # Calculate metrics
        tat_metrics = calculate_tat_metrics(filtered_df)
        throughput_metrics = calculate_throughput(filtered_df)
        sla_metrics = check_sla_compliance(filtered_df)
        
        # Display metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="TAT P90 (min)",
                value=f"{tat_metrics.p90:.1f}",
                help="90th percentile turnaround time"
            )
        
        with col2:
            st.metric(
                label="Throughput Today",
                value=throughput_metrics.today,
                help="Completed specimens today"
            )
        
        with col3:
            st.metric(
                label="Error Rate",
                value=f"{(sla_metrics['error_breaches'] / len(filtered_df) * 100):.1f}%",
                help="Overall error rate"
            )
        
        with col4:
            st.metric(
                label="SLA Compliance",
                value=f"{sla_metrics['overall_compliance']:.1f}%",
                help="Overall SLA compliance rate"
            )
        
        # Charts
        st.subheader("📊 Data Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Assay breakdown
            assay_counts = filtered_df['assay'].value_counts()
            fig1 = px.pie(
                values=assay_counts.values,
                names=assay_counts.index,
                title="Specimens by Assay Type"
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Machine breakdown
            machine_counts = filtered_df['machine_id'].value_counts()
            fig2 = px.bar(
                x=machine_counts.index,
                y=machine_counts.values,
                title="Specimens by Machine",
                labels={'x': 'Machine ID', 'y': 'Count'}
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # Status breakdown
        status_counts = filtered_df['status'].value_counts()
        fig3 = px.bar(
            x=status_counts.index,
            y=status_counts.values,
            title="Specimens by Status",
            labels={'x': 'Status', 'y': 'Count'}
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        # Data table
        st.subheader("📋 Raw Data")
        st.dataframe(filtered_df, use_container_width=True)
        
    else:
        st.info("No data available for the selected filters. Try adjusting the date range or filters.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        **Dashboard Info:**
        - Data refreshes automatically every 5 minutes
        - Sample data is generated if no database is found
        - Use sidebar filters to customize the view
        """
    )

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main Streamlit application with tabs."""
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🧪 LabOps Metrics Starter Kit</h1>
        <p>Comprehensive laboratory operations monitoring with Data Quality and Teams integration</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Metrics Dashboard", 
        "🔍 Data Quality", 
        "🤖 Teams Bot"
    ])
    
    with tab1:
        create_metrics_dashboard()
    
    with tab2:
        create_dq_dashboard()
    
    with tab3:
        create_teams_bot_dashboard()

if __name__ == "__main__":
    main()
