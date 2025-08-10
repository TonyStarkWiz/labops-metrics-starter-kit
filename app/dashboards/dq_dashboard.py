#!/usr/bin/env python3
"""
Data Quality Dashboard for LabOps Metrics
Streamlit interface for visualizing DQ violations and reports
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Data Quality Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .dq-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .violation-card {
        border-left: 4px solid #ff6b6b;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
        border-radius: 5px;
    }
    .warning-card {
        border-left: 4px solid #ffd93d;
    }
    .info-card {
        border-left: 4px solid #6bcf7f;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_dq_report(report_path: str = "dq_reports/dq_report.json"):
    """Load DQ report from JSON file"""
    try:
        if Path(report_path).exists():
            with open(report_path, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        st.error(f"Error loading DQ report: {e}")
        return None

@st.cache_data(ttl=300)
def load_violations_csv(csv_path: str = "dq_reports/dq_violations.csv"):
    """Load violations CSV file"""
    try:
        if Path(csv_path).exists():
            return pd.read_csv(csv_path)
        return None
    except Exception as e:
        st.error(f"Error loading violations CSV: {e}")
        return None

@st.cache_data(ttl=300)
def load_lab_data():
    """Load lab data from SQLite for comparison"""
    try:
        db_path = Path("labops.db")
        if db_path.exists():
            conn = sqlite3.connect("labops.db")
            df = pd.read_sql_query("SELECT * FROM specimens", conn)
            conn.close()
            return df
        return None
    except Exception as e:
        st.error(f"Error loading lab data: {e}")
        return None

def create_dq_summary_chart(report_data):
    """Create summary chart for DQ violations"""
    if not report_data or 'summary' not in report_data:
        return None
    
    summary = report_data['summary']
    
    # Create summary metrics
    fig = go.Figure()
    
    # Add bar chart for violations by severity
    severities = ['ERROR', 'WARNING', 'INFO']
    counts = [summary.get('errors', 0), summary.get('warnings', 0), summary.get('info', 0)]
    colors = ['#ff6b6b', '#ffd93d', '#6bcf7f']
    
    fig.add_trace(go.Bar(
        x=severities,
        y=counts,
        marker_color=colors,
        text=counts,
        textposition='auto',
        name='Violations by Severity'
    ))
    
    fig.update_layout(
        title="Data Quality Violations by Severity",
        xaxis_title="Severity Level",
        yaxis_title="Count",
        height=400,
        showlegend=False
    )
    
    return fig

def create_violations_by_rule_chart(report_data):
    """Create chart showing violations by rule"""
    if not report_data or 'violations_by_rule' not in report_data:
        return None
    
    violations_by_rule = report_data['violations_by_rule']
    
    if not violations_by_rule:
        return None
    
    # Count violations per rule
    rule_counts = {rule: len(violations) for rule, violations in violations_by_rule.items()}
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=list(rule_counts.values()),
        y=list(rule_counts.keys()),
        orientation='h',
        marker_color='#667eea',
        text=list(rule_counts.values()),
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Violations by Rule",
        xaxis_title="Count",
        yaxis_title="Rule Name",
        height=400,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig

def create_violations_by_column_chart(violations_df):
    """Create chart showing violations by column"""
    if violations_df is None or violations_df.empty:
        return None
    
    # Count violations by column
    column_counts = violations_df['column'].value_counts()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=column_counts.index,
        y=column_counts.values,
        marker_color='#764ba2',
        text=column_counts.values,
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Violations by Column",
        xaxis_title="Column Name",
        yaxis_title="Count",
        height=400,
        xaxis={'tickangle': 45}
    )
    
    return fig

def create_severity_distribution_chart(violations_df):
    """Create pie chart for severity distribution"""
    if violations_df is None or violations_df.empty:
        return None
    
    severity_counts = violations_df['severity'].value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=severity_counts.index,
        values=severity_counts.values,
        hole=0.3,
        marker_colors=['#ff6b6b', '#ffd93d', '#6bcf7f']
    )])
    
    fig.update_layout(
        title="Violations by Severity",
        height=400
    )
    
    return fig

def display_violation_details(report_data):
    """Display detailed violation information"""
    if not report_data or 'all_violations' not in report_data:
        st.info("No violation details available")
        return
    
    violations = report_data['all_violations']
    
    st.subheader("📋 Detailed Violation Report")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Summary Table", "Rule Details", "Raw Data"])
    
    with tab1:
        # Summary table
        summary_df = pd.DataFrame(violations)
        if not summary_df.empty:
            st.dataframe(summary_df, use_container_width=True)
    
    with tab2:
        # Group by rule
        if violations:
            rule_groups = {}
            for v in violations:
                rule_name = v['rule_name']
                if rule_name not in rule_groups:
                    rule_groups[rule_name] = []
                rule_groups[rule_name].append(v)
            
            for rule_name, rule_violations in rule_groups.items():
                with st.expander(f"🔍 {rule_name} ({len(rule_violations)} violations)"):
                    for violation in rule_violations:
                        severity_color = {
                            'ERROR': '#ff6b6b',
                            'WARNING': '#ffd93d',
                            'INFO': '#6bcf7f'
                        }.get(violation['severity'], '#6c757d')
                        
                        st.markdown(f"""
                        <div class="violation-card" style="border-left-color: {severity_color}">
                            <strong>{violation['description']}</strong><br>
                            <small>Severity: {violation['severity']} | Column: {violation['column']} | Affected Rows: {violation['affected_rows']}</small>
                        </div>
                        """, unsafe_allow_html=True)
    
    with tab3:
        # Raw violations data
        if violations:
            st.json(violations)

def main():
    """Main dashboard function"""
    # Header
    st.markdown("""
    <div class="dq-header">
        <h1>🔍 Data Quality Dashboard</h1>
        <p>Monitor and analyze data quality issues in LabOps Metrics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for controls
    st.sidebar.header("🎛️ Dashboard Controls")
    
    # Check if DQ reports exist
    dq_reports_dir = Path("dq_reports")
    if not dq_reports_dir.exists():
        st.sidebar.warning("DQ reports directory not found")
        st.sidebar.info("Run the DQ rules engine first to generate reports")
        
        # Show instructions
        st.info("""
        ## 📋 How to Use This Dashboard
        
        This dashboard visualizes data quality analysis results. To get started:
        
        1. **Generate DQ Report**: Run the DQ rules engine on your data
           ```bash
           python scripts/dq_rules_engine.py your_data.csv --rules sample_dq_rules.yaml
           ```
        
        2. **View Results**: The dashboard will automatically load and display the results
        
        3. **Analyze Issues**: Use the charts and tables to understand data quality problems
        """)
        
        # Show sample rules
        st.subheader("📋 Sample DQ Rules")
        with open("sample_dq_rules.yaml", "r") as f:
            st.code(f.read(), language="yaml")
        
        return
    
    # Load data
    report_data = load_dq_report()
    violations_df = load_violations_csv()
    lab_data = load_lab_data()
    
    if not report_data:
        st.error("No DQ report found. Please run the DQ rules engine first.")
        return
    
    # Dashboard metrics
    summary = report_data.get('summary', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📊 Total Violations</h3>
            <h2 style="color: #ff6b6b;">{summary.get('total_violations', 0)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>❌ Errors</h3>
            <h2 style="color: #ff6b6b;">{summary.get('errors', 0)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>⚠️ Warnings</h3>
            <h2 style="color: #ffd93d;">{summary.get('warnings', 0)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>ℹ️ Info</h3>
            <h2 style="color: #6bcf7f;">{summary.get('info', 0)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts section
    st.subheader("📈 Data Quality Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        summary_chart = create_dq_summary_chart(report_data)
        if summary_chart:
            st.plotly_chart(summary_chart, use_container_width=True)
        
        rule_chart = create_violations_by_rule_chart(report_data)
        if rule_chart:
            st.plotly_chart(rule_chart, use_container_width=True)
    
    with col2:
        column_chart = create_violations_by_column_chart(violations_df)
        if column_chart:
            st.plotly_chart(column_chart, use_container_width=True)
        
        severity_chart = create_severity_distribution_chart(violations_df)
        if severity_chart:
            st.plotly_chart(severity_chart, use_container_width=True)
    
    # Violation details
    display_violation_details(report_data)
    
    # Data comparison section
    if lab_data is not None:
        st.subheader("🔍 Data Quality vs. Data Volume")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Records", len(lab_data))
            st.metric("Data Quality Score", f"{max(0, 100 - (summary.get('total_violations', 0) / len(lab_data) * 100)):.1f}%")
        
        with col2:
            # Show sample of problematic data if violations exist
            if violations_df is not None and not violations_df.empty:
                st.subheader("🚨 Sample Problematic Records")
                
                # Get a sample of records with violations
                if 'affected_rows' in violations_df.columns:
                    # This is a simplified approach - in practice you'd want to show actual problematic records
                    st.info("Showing violation summary. Check the detailed report for specific problematic records.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p>🔍 Data Quality Dashboard | LabOps Metrics Starter Kit</p>
        <p>Generated on: {}</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
