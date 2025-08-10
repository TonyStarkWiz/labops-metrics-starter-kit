#!/usr/bin/env python3
"""
Enhanced LabOps Metrics Dashboard - Streamlit Application

Comprehensive dashboard for laboratory operations metrics with integrated Micro-PoCs:
- Data Quality Rules Engine
- Teams Stand-up Bot
"""

import json
import sys
import io
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots
import yaml

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.alerts.teams import create_sla_alert_payload, send_sla_alert
from app.core.db import SessionLocal
from app.core.models import Specimen
from app.core.settings import settings
from app.metrics.errors import calculate_error_metrics
from app.metrics.sla import calculate_sla_metrics
from app.metrics.tat import calculate_tat_metrics, calculate_tat_timeseries
from app.metrics.throughput import (
    calculate_throughput,
    calculate_throughput_by_assay,
    get_total_throughput_today,
)

# Import Micro-PoCs
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))
from dq_rules_engine import DQRulesEngine, DQRule
from teams_standup_bot import TeamsStandupBot, StandupUpdate, StandupItem

# API base URL
API_BASE_URL = "http://localhost:8000/api/v1"

def get_specimens_dataframe():
    """Get specimens data as DataFrame."""
    db = SessionLocal()
    try:
        specimens = db.query(Specimen).all()
        
        if not specimens:
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = []
        for specimen in specimens:
            data.append({
                'id': specimen.id,
                'specimen_id': specimen.specimen_id,
                'assay': specimen.assay,
                'machine_id': specimen.machine_id,
                'operator_id': specimen.operator_id,
                'status': specimen.status.value,
                'error_code': specimen.error_code,
                'received_at': specimen.received_at,
                'processed_at': specimen.processed_at
            })
        
        return pd.DataFrame(data)
    finally:
        db.close()

def filter_data_by_date_range(df, days_back=72):
    """Filter data by date range."""
    if len(df) == 0:
        return df
    
    cutoff_date = datetime.now() - timedelta(hours=days_back)
    df['received_at'] = pd.to_datetime(df['received_at'])
    return df[df['received_at'] >= cutoff_date]

def create_kpi_metrics(df):
    """Create KPI metrics display."""
    if len(df) == 0:
        return {
            'tat_p90': 0,
            'throughput_today': 0,
            'error_rate': 0,
            'total_specimens': 0
        }
    
    # Calculate TAT P90
    tat_metrics = calculate_tat_metrics(df)
    tat_p90 = tat_metrics.p90
    
    # Calculate throughput today
    throughput_today = get_total_throughput_today(df)
    
    # Calculate error rate
    error_metrics = calculate_error_metrics(df)
    error_rate = error_metrics.overall_error_rate
    
    # Total specimens
    total_specimens = len(df)
    
    return {
        'tat_p90': tat_p90,
        'throughput_today': throughput_today,
        'error_rate': error_rate,
        'total_specimens': total_specimens
    }

def create_tat_chart(df, grain="hour"):
    """Create TAT time series chart."""
    if len(df) == 0:
        return go.Figure().add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
    
    tat_data = calculate_tat_timeseries(df, grain)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tat_data['timestamp'],
        y=tat_data['tat_p90'],
        mode='lines+markers',
        name='TAT P90',
        line=dict(color='blue', width=2)
    ))
    
    fig.update_layout(
        title=f"Turnaround Time P90 by {grain.capitalize()}",
        xaxis_title="Time",
        yaxis_title="TAT (minutes)",
        height=400
    )
    
    return fig

def create_throughput_chart(df, grain="hour"):
    """Create throughput time series chart."""
    if len(df) == 0:
        return go.Figure().add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
    
    throughput_data = calculate_throughput(df, grain)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=throughput_data['timestamp'],
        y=throughput_data['count'],
        name='Throughput',
        marker_color='green'
    ))
    
    fig.update_layout(
        title=f"Throughput by {grain.capitalize()}",
        xaxis_title="Time",
        yaxis_title="Specimens Processed",
        height=400
    )
    
    return fig

def create_assay_breakdown(df):
    """Create assay breakdown chart."""
    if len(df) == 0:
        return go.Figure().add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
    
    assay_counts = df['assay'].value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=assay_counts.index,
        values=assay_counts.values,
        hole=0.3
    )])
    
    fig.update_layout(
        title="Specimens by Assay Type",
        height=400
    )
    
    return fig

def create_machine_breakdown(df):
    """Create machine breakdown chart."""
    if len(df) == 0:
        return go.Figure().add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
    
    machine_counts = df['machine_id'].value_counts()
    
    fig = go.Figure(data=[go.Bar(
        x=machine_counts.index,
        y=machine_counts.values,
        marker_color='orange'
    )])
    
    fig.update_layout(
        title="Specimens by Machine",
        xaxis_title="Machine ID",
        yaxis_title="Count",
        height=400
    )
    
    return fig

def create_error_breakdown(df):
    """Create error breakdown chart."""
    if len(df) == 0:
        return go.Figure().add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
    
    error_df = df[df['status'] == 'ERROR']
    if len(error_df) == 0:
        return go.Figure().add_annotation(text="No errors found", x=0.5, y=0.5, showarrow=False)
    
    error_counts = error_df['error_code'].value_counts()
    
    fig = go.Figure(data=[go.Bar(
        x=error_counts.index,
        y=error_counts.values,
        marker_color='red'
    )])
    
    fig.update_layout(
        title="Errors by Error Code",
        xaxis_title="Error Code",
        yaxis_title="Count",
        height=400
    )
    
    return fig

def what_if_analysis(df, extra_machines, reduced_failure_rate):
    """Perform what-if analysis."""
    if len(df) == 0:
        return {
            'projected_tat_p90': 0,
            'projected_throughput': 0,
            'improvement_tat': 0,
            'improvement_throughput': 0
        }
    
    # Current metrics
    current_tat = calculate_tat_metrics(df).p90
    current_throughput = get_total_throughput_today(df)
    
    # Projections (simplified model)
    tat_improvement = extra_machines * 0.15 + (reduced_failure_rate / 100) * 0.1
    throughput_improvement = extra_machines * 0.25 + (reduced_failure_rate / 100) * 0.15
    
    projected_tat = current_tat * (1 - tat_improvement)
    projected_throughput = current_throughput * (1 + throughput_improvement)
    
    return {
        'projected_tat_p90': projected_tat,
        'projected_throughput': projected_throughput,
        'improvement_tat': tat_improvement * 100,
        'improvement_throughput': throughput_improvement * 100
    }

# Data Quality Functions
def run_dq_validation(df, rules_file=None, custom_rules=None):
    """Run data quality validation."""
    try:
        rules_engine = DQRulesEngine()
        
        if rules_file:
            rules_engine.load_rules(rules_file)
        elif custom_rules:
            # Parse custom rules
            rules_data = yaml.safe_load(custom_rules)
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
            'success': True,
            'violations': violations,
            'report': report,
            'rules_applied': len(rules_engine.rules)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def create_dq_dashboard():
    """Create Data Quality dashboard tab."""
    st.header("🔍 Data Quality Rules Engine")
    st.markdown("Validate your data against configurable quality rules")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload CSV file for validation",
        type=['csv'],
        help="Upload a CSV file to validate against DQ rules"
    )
    
    # Rules selection
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Rules Configuration")
        rules_option = st.radio(
            "Choose rules source:",
            ["Use Sample Rules", "Upload Custom Rules", "Enter Rules Manually"]
        )
    
    with col2:
        st.subheader("Validation Options")
        severity_filter = st.multiselect(
            "Filter violations by severity:",
            ["ERROR", "WARNING", "INFO"],
            default=["ERROR", "WARNING", "INFO"]
        )
    
    # Handle rules input
    custom_rules = None
    rules_file = None
    
    if rules_option == "Upload Custom Rules":
        rules_file_upload = st.file_uploader(
            "Upload YAML rules file",
            type=['yaml', 'yml'],
            help="Upload a YAML file with custom DQ rules"
        )
        if rules_file_upload:
            rules_file = rules_file_upload.name
            # Save temporarily
            with open(f"/tmp/{rules_file}", 'w') as f:
                f.write(rules_file_upload.getvalue().decode())
    
    elif rules_option == "Enter Rules Manually":
        st.subheader("Custom Rules (YAML format)")
        custom_rules = st.text_area(
            "Enter your DQ rules in YAML format:",
            value="""rules:
  - name: "Required Columns Check"
    description: "Ensure all required columns are present"
    rule_type: "required_columns"
    parameters:
      columns: ["id", "name", "date"]
    severity: "ERROR"
  
  - name: "No Missing Values"
    description: "Ensure critical fields have no missing values"
    rule_type: "completeness"
    parameters:
      columns: ["id", "name"]
      threshold: 0.0
    severity: "ERROR"
""",
            height=200,
            help="Enter DQ rules in YAML format"
        )
    
    # Run validation
    if uploaded_file and st.button("🔍 Run Data Quality Validation", type="primary"):
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ Loaded CSV with {df.shape[0]} rows and {df.shape[1]} columns")
            
            # Show data preview
            with st.expander("📊 Data Preview"):
                st.dataframe(df.head(), use_container_width=True)
                st.write(f"**Data Types:**")
                st.write(df.dtypes)
            
            # Run validation
            with st.spinner("Running data quality validation..."):
                result = run_dq_validation(df, rules_file, custom_rules)
            
            if result['success']:
                violations = result['violations']
                report = result['report']
                
                # Filter violations by severity
                filtered_violations = [v for v in violations if v.severity in severity_filter]
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Rules Applied", result['rules_applied'])
                
                with col2:
                    st.metric("Total Violations", len(violations))
                
                with col3:
                    error_count = len([v for v in violations if v.severity == 'ERROR'])
                    st.metric("Error Violations", error_count)
                
                with col4:
                    warning_count = len([v for v in violations if v.severity == 'WARNING'])
                    st.metric("Warning Violations", warning_count)
                
                # Violations table
                if filtered_violations:
                    st.subheader("🚨 Data Quality Violations")
                    
                    violation_data = []
                    for v in filtered_violations:
                        violation_data.append({
                            'Rule': v.rule_name,
                            'Severity': v.severity,
                            'Description': v.description,
                            'Column': v.column or 'N/A',
                            'Value': str(v.value) if v.value is not None else 'N/A',
                            'Expected': str(v.expected) if v.expected is not None else 'N/A',
                            'Rows Affected': len(v.row_indices)
                        })
                    
                    violation_df = pd.DataFrame(violation_data)
                    st.dataframe(violation_df, use_container_width=True)
                    
                    # Download violations
                    csv = violation_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Violations Report",
                        data=csv,
                        file_name="dq_violations.csv",
                        mime="text/csv"
                    )
                else:
                    st.success("🎉 No violations found for the selected severity levels!")
                
                # Show report summary
                if report and 'summary' in report:
                    with st.expander("📋 Detailed Report"):
                        st.json(report['summary'])
                
            else:
                st.error(f"❌ Validation failed: {result['error']}")
                
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
    
    # Rules templates
    with st.expander("📚 DQ Rules Templates"):
        st.markdown("""
        **Available Rule Types:**
        
        - **required_columns**: Check if required columns are present
        - **timestamp_order**: Ensure timestamp order (e.g., received < processed)
        - **allowed_values**: Check if values are in allowed set
        - **data_types**: Validate data types of columns
        - **uniqueness**: Ensure column values are unique
        - **completeness**: Check for missing values
        - **range_check**: Validate numeric ranges
        - **no_future_dates**: Check for future dates
        
        **Example Rule:**
        ```yaml
        - name: "Status Validation"
          description: "Ensure status values are valid"
          rule_type: "allowed_values"
          parameters:
            column: "status"
            allowed_values: ["active", "inactive", "pending"]
          severity: "ERROR"
        ```
        """)

# Teams Bot Functions
def create_teams_bot_dashboard():
    """Create Teams Stand-up Bot dashboard tab."""
    st.header("🤖 Microsoft Teams Stand-up Bot")
    st.markdown("Automate your daily stand-up updates and team communications")
    
    # Configuration
    st.subheader("⚙️ Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        webhook_url = st.text_input(
            "Teams Webhook URL",
            value=st.secrets.get("TEAMS_WEBHOOK_URL", ""),
            help="Enter your Teams webhook URL or set TEAMS_WEBHOOK_URL in secrets",
            type="password"
        )
    
    with col2:
        dry_run = st.checkbox(
            "Dry Run Mode",
            value=True,
            help="Enable to test without actually posting to Teams"
        )
    
    # Stand-up input
    st.subheader("📝 Stand-up Input")
    
    input_method = st.radio(
        "Choose input method:",
        ["Manual Entry", "Upload JSON", "Use Template"]
    )
    
    if input_method == "Manual Entry":
        # Single stand-up entry
        st.subheader("Individual Stand-up")
        
        col1, col2 = st.columns(2)
        
        with col1:
            team_member = st.text_input("Team Member Name", value="John Doe")
            date = st.date_input("Date", value=datetime.now().date())
            mood = st.selectbox("Mood", ["😊", "🤔", "😐", "😟", "😤"], index=0)
        
        with col2:
            availability = st.selectbox("Availability", ["Available", "Busy", "Away", "Do Not Disturb"])
            next_priorities = st.text_area("Next Priorities (one per line)", value="Code review\nTeam meeting")
        
        # Stand-up items
        st.subheader("Stand-up Items")
        
        items = []
        num_items = st.number_input("Number of items", min_value=1, max_value=10, value=3)
        
        for i in range(num_items):
            with st.expander(f"Item {i+1}", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    title = st.text_input(f"Title {i+1}", value=f"Task {i+1}", key=f"title_{i}")
                    status = st.selectbox(f"Status {i+1}", ["completed", "in_progress", "blocked", "planned"], key=f"status_{i}")
                    assignee = st.text_input(f"Assignee {i+1}", value=team_member, key=f"assignee_{i}")
                
                with col2:
                    priority = st.selectbox(f"Priority {i+1}", ["low", "medium", "high", "urgent"], key=f"priority_{i}")
                    effort = st.selectbox(f"Effort {i+1}", ["15m", "30m", "1h", "2h", "4h", "6h", "8h", "1d"], key=f"effort_{i}")
                    blockers = st.text_input(f"Blockers {i+1}", key=f"blockers_{i}")
                
                description = st.text_area(f"Description {i+1}", value=f"Description for task {i+1}", key=f"desc_{i}")
                notes = st.text_area(f"Notes {i+1}", key=f"notes_{i}")
                
                items.append({
                    'title': title,
                    'status': status,
                    'description': description,
                    'assignee': assignee,
                    'priority': priority,
                    'effort': effort,
                    'blockers': [blockers] if blockers else [],
                    'notes': notes
                })
        
        # Post stand-up
        if st.button("📤 Post Stand-up to Teams", type="primary"):
            try:
                # Create stand-up update
                update = StandupUpdate(
                    date=date.strftime('%Y-%m-%d'),
                    team_member=team_member,
                    items=items,
                    mood=mood,
                    availability=availability,
                    next_priorities=next_priorities.split('\n') if next_priorities else []
                )
                
                # Initialize bot
                bot = TeamsStandupBot(webhook_url=webhook_url, dry_run=dry_run)
                
                # Post stand-up
                success = bot.post_standup(update)
                
                if success:
                    st.success("✅ Stand-up posted successfully!")
                    
                    # Show preview
                    with st.expander("📋 View Stand-up Preview"):
                        st.json({
                            'date': update.date,
                            'team_member': update.team_member,
                            'items_count': len(update.items),
                            'mood': update.mood,
                            'availability': update.availability,
                            'next_priorities': update.next_priorities
                        })
                else:
                    st.error("❌ Failed to post stand-up")
                    
            except Exception as e:
                st.error(f"❌ Error posting stand-up: {str(e)}")
    
    elif input_method == "Upload JSON":
        st.subheader("Upload JSON File")
        
        json_file = st.file_uploader(
            "Upload JSON file with stand-up data",
            type=['json'],
            help="Upload a JSON file with stand-up data"
        )
        
        if json_file:
            try:
                data = json.loads(json_file.getvalue().decode())
                st.success("✅ JSON file loaded successfully!")
                
                # Show preview
                with st.expander("📋 JSON Preview"):
                    st.json(data)
                
                # Post stand-up
                if st.button("📤 Post Stand-up from JSON", type="primary"):
                    try:
                        bot = TeamsStandupBot(webhook_url=webhook_url, dry_run=dry_run)
                        
                        if 'team_members' in data:
                            # Team stand-up
                            updates = []
                            for member_data in data['team_members']:
                                update = StandupUpdate(
                                    date=member_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                                    team_member=member_data['team_member'],
                                    items=[
                                        StandupItem(
                                            title=item['title'],
                                            status=item['status'],
                                            description=item['description'],
                                            assignee=item['assignee'],
                                            priority=item.get('priority', 'medium'),
                                            effort=item.get('effort', '1-2h'),
                                            blockers=item.get('blockers', []),
                                            notes=item.get('notes', '')
                                        )
                                        for item in member_data.get('items', [])
                                    ],
                                    mood=member_data.get('mood', '😊'),
                                    availability=member_data.get('availability', 'Available'),
                                    next_priorities=member_data.get('next_priorities', [])
                                )
                                updates.append(update)
                            
                            success = bot.post_team_standup(updates)
                            message = f"Team stand-up posted for {len(updates)} members"
                        else:
                            # Single stand-up
                            update = StandupUpdate(
                                date=data.get('date', datetime.now().strftime('%Y-%m-%d')),
                                team_member=data['team_member'],
                                items=[
                                    StandupItem(
                                        title=item['title'],
                                        status=item['status'],
                                        description=item['description'],
                                        assignee=item['assignee'],
                                        priority=item.get('priority', 'medium'),
                                        effort=item.get('effort', '1-2h'),
                                        blockers=item.get('blockers', []),
                                        notes=item.get('notes', '')
                                    )
                                    for item in data.get('items', [])
                                ],
                                mood=data.get('mood', '😊'),
                                availability=data.get('availability', 'Available'),
                                next_priorities=data.get('next_priorities', [])
                            )
                            
                            success = bot.post_standup(update)
                            message = "Stand-up posted successfully"
                        
                        if success:
                            st.success(f"✅ {message}!")
                        else:
                            st.error("❌ Failed to post stand-up")
                            
                    except Exception as e:
                        st.error(f"❌ Error posting stand-up: {str(e)}")
                        
        else:
            st.info("📁 Please upload a JSON file to continue")
    
    else:  # Use Template
        st.subheader("Template-based Stand-up")
        
        template_type = st.selectbox(
            "Choose template:",
            ["Individual Stand-up", "Team Stand-up"]
        )
        
        if template_type == "Individual Stand-up":
            st.markdown("""
            **Individual Stand-up Template:**
            ```json
            {
              "date": "2024-01-15",
              "team_member": "John Doe",
              "items": [
                {
                  "title": "Complete API documentation",
                  "status": "completed",
                  "description": "Write comprehensive API docs",
                  "assignee": "John Doe",
                  "priority": "high",
                  "effort": "4h",
                  "notes": "Ready for review"
                }
              ],
              "mood": "😊",
              "availability": "Available",
              "next_priorities": ["Code review", "Team meeting"]
            }
            ```
            """)
        else:
            st.markdown("""
            **Team Stand-up Template:**
            ```json
            {
              "team_members": [
                {
                  "date": "2024-01-15",
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
                }
              ]
            }
            ```
            """)
        
        st.info("💡 Copy the template, modify it with your data, and use the 'Upload JSON' option to post your stand-up!")
    
    # Status and health
    st.subheader("🔍 Bot Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        webhook_status = "✅ Configured" if webhook_url else "❌ Not configured"
        st.metric("Webhook Status", webhook_status)
    
    with col2:
        run_mode = "🧪 Dry Run" if dry_run else "🚀 Live Mode"
        st.metric("Run Mode", run_mode)
    
    if not webhook_url:
        st.warning("⚠️ Please configure a Teams webhook URL to post stand-ups")

def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Enhanced LabOps Metrics Dashboard",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔬 Enhanced LabOps Metrics Dashboard")
    st.markdown("Real-time laboratory operations monitoring with integrated Micro-PoCs")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Metrics Dashboard", 
        "🔍 Data Quality", 
        "🤖 Teams Bot"
    ])
    
    with tab1:
        # Original dashboard content
        st.header("📊 Key Performance Indicators")
        
        # Sidebar
        st.sidebar.header("Dashboard Controls")
        
        # Date range filter
        days_back = st.sidebar.slider(
            "Data Range (hours)",
            min_value=1,
            max_value=168,  # 1 week
            value=72,
            help="Number of hours of data to display"
        )
        
        # Assay filter
        df = get_specimens_dataframe()
        if len(df) > 0:
            available_assays = ['All'] + sorted(df['assay'].unique().tolist())
            selected_assay = st.sidebar.selectbox(
                "Filter by Assay",
                available_assays,
                help="Filter data by specific assay type"
            )
            
            # Machine filter
            available_machines = ['All'] + sorted(df['machine_id'].unique().tolist())
            selected_machine = st.sidebar.selectbox(
                "Filter by Machine",
                available_machines,
                help="Filter data by specific machine"
            )
        else:
            selected_assay = "All"
            selected_machine = "All"
        
        # Apply filters
        df = filter_data_by_date_range(df, days_back)
        
        if selected_assay != "All" and len(df) > 0:
            df = df[df['assay'] == selected_assay]
        
        if selected_machine != "All" and len(df) > 0:
            df = df[df['machine_id'] == selected_machine]
        
        # KPI Metrics
        kpi_metrics = create_kpi_metrics(df)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="TAT P90 (min)",
                value=f"{kpi_metrics['tat_p90']:.1f}",
                help="90th percentile turnaround time"
            )
        
        with col2:
            st.metric(
                label="Throughput Today",
                value=kpi_metrics['throughput_today'],
                help="Completed specimens today"
            )
        
        with col3:
            st.metric(
                label="Error Rate",
                value=f"{kpi_metrics['error_rate']:.1%}",
                help="Overall error rate"
            )
        
        with col4:
            st.metric(
                label="Total Specimens",
                value=kpi_metrics['total_specimens'],
                help="Total specimens in selected range"
            )
        
        # Time Series Charts
        st.header("📈 Time Series Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            grain = st.selectbox("Time Grain", ["hour", "day"], key="tat_grain")
            tat_fig = create_tat_chart(df, grain)
            st.plotly_chart(tat_fig, use_container_width=True)
        
        with col2:
            grain2 = st.selectbox("Time Grain", ["hour", "day"], key="throughput_grain")
            throughput_fig = create_throughput_chart(df, grain2)
            st.plotly_chart(throughput_fig, use_container_width=True)
        
        # Breakdowns
        st.header("🔍 Data Breakdowns")
        
        col1, col2 = st.columns(2)
        
        with col1:
            assay_fig = create_assay_breakdown(df)
            st.plotly_chart(assay_fig, use_container_width=True)
        
        with col2:
            machine_fig = create_machine_breakdown(df)
            st.plotly_chart(machine_fig, use_container_width=True)
        
        # Error Analysis
        if len(df) > 0 and len(df[df['status'] == 'ERROR']) > 0:
            st.header("⚠️ Error Analysis")
            error_fig = create_error_breakdown(df)
            st.plotly_chart(error_fig, use_container_width=True)
        
        # SLA Monitoring
        st.header("🚨 SLA Monitoring")
        
        sla_metrics = calculate_sla_metrics(df)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="SLA Breaches",
                value=sla_metrics.breach_count,
                delta=f"{sla_metrics.breach_rate:.1%}",
                delta_color="inverse"
            )
        
        with col2:
            st.metric(
                label="Total Completed",
                value=sla_metrics.total_completed
            )
        
        with col3:
            st.metric(
                label="Breach Rate",
                value=f"{sla_metrics.breach_rate:.1%}"
            )
        
        # SLA Alert Button
        if sla_metrics.breach_count > 0:
            st.warning(f"⚠️ {sla_metrics.breach_count} SLA breaches detected!")
            
            if st.button("🚨 Trigger Teams Alert (Dry-Run)", type="primary"):
                # Create alert payload
                top_assays = []
                if len(df) > 0:
                    sla_by_assay = df[df['status'] == 'COMPLETED'].copy()
                    if len(sla_by_assay) > 0:
                        sla_by_assay['tat_minutes'] = (
                            pd.to_datetime(sla_by_assay['processed_at']) - 
                            pd.to_datetime(sla_by_assay['received_at'])
                        ).dt.total_seconds() / 60
                        
                        sla_threshold = settings.SLA_HOURS * 60
                        breaches_by_assay = sla_by_assay[sla_by_assay['tat_minutes'] > sla_threshold].groupby('assay').size()
                        
                        for assay, count in breaches_by_assay.head(3).items():
                            top_assays.append({'assay': assay, 'breaches': int(count)})
                
                payload = create_sla_alert_payload(
                    breach_count=sla_metrics.breach_count,
                    top_assays=top_assays,
                    window=f"last {days_back} hours"
                )
                
                # Send alert (dry-run)
                success = send_sla_alert(payload, dry_run=True)
                
                if success:
                    st.success("✅ Teams alert payload generated successfully!")
                    
                    # Show payload in expander
                    with st.expander("📋 View Alert Payload"):
                        st.json(payload)
                else:
                    st.error("❌ Failed to generate alert payload")
        
        # Sample SLA breaches table
        if sla_metrics.sample_breaches:
            st.subheader("Sample SLA Breaches")
            breach_data = []
            for breach in sla_metrics.sample_breaches:
                breach_data.append({
                    'Specimen ID': breach.specimen_id,
                    'Assay': breach.assay,
                    'Machine': breach.machine_id,
                    'TAT (min)': f"{breach.turnaround_time_minutes:.1f}",
                    'Received': breach.received_at.strftime('%Y-%m-%d %H:%M'),
                    'Processed': breach.processed_at.strftime('%Y-%m-%d %H:%M')
                })
            
            breach_df = pd.DataFrame(breach_data)
            st.dataframe(breach_df, use_container_width=True)
        
        # What-If Analysis
        st.header("🎯 What-If Analysis")
        st.markdown("Explore the impact of capacity changes on performance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            extra_machines = st.slider(
                "Add Extra Machines",
                min_value=0,
                max_value=3,
                value=0,
                help="Number of additional machines to add"
            )
        
        with col2:
            reduced_failure_rate = st.slider(
                "Reduce Failure Rate (%)",
                min_value=0,
                max_value=50,
                value=0,
                help="Percentage reduction in failure rate"
            )
        
        # Calculate projections
        projections = what_if_analysis(df, extra_machines, reduced_failure_rate)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Projected TAT P90",
                value=f"{projections['projected_tat_p90']:.1f} min",
                delta=f"{projections['improvement_tat']:.1f}%",
                delta_color="inverse"
            )
        
        with col2:
            st.metric(
                label="Projected Throughput",
                value=f"{projections['projected_throughput']:.0f}",
                value_color="green"
            )
        
        with col3:
            st.metric(
                label="TAT Improvement",
                value=f"{projections['improvement_tat']:.1f}%"
            )
        
        with col4:
            st.metric(
                label="Throughput Improvement",
                value=f"{projections['improvement_throughput']:.1f}%"
            )
    
    with tab2:
        create_dq_dashboard()
    
    with tab3:
        create_teams_bot_dashboard()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        **Enhanced Dashboard Features:**
        - 📊 **Metrics Dashboard**: Real-time lab operations monitoring
        - 🔍 **Data Quality Engine**: Validate data against configurable rules
        - 🤖 **Teams Bot**: Automate stand-up updates and team communications
        - 📈 **Advanced Analytics**: What-if analysis and SLA monitoring
        - 🚨 **Alerting**: Teams integration for SLA breaches
        
        **API Endpoints:**
        - Data Quality: `/api/v1/dq/*`
        - Teams Bot: `/api/v1/teams/*`
        - Metrics: `/api/v1/*`
        
        **Documentation:** Available at `/docs`
        """
    )

if __name__ == "__main__":
    main()
