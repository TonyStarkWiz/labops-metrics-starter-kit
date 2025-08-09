#!/usr/bin/env python3
"""
LabOps Metrics Dashboard - Streamlit Application

Comprehensive dashboard for laboratory operations metrics with real-time data visualization.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots

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
        return go.Figure()
    
    tat_timeseries = calculate_tat_timeseries(df, grain=grain)
    
    if len(tat_timeseries) == 0:
        return go.Figure()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=tat_timeseries['time_group'],
        y=tat_timeseries['p50'],
        mode='lines+markers',
        name='P50',
        line=dict(color='blue')
    ))
    
    fig.add_trace(go.Scatter(
        x=tat_timeseries['time_group'],
        y=tat_timeseries['p90'],
        mode='lines+markers',
        name='P90',
        line=dict(color='orange')
    ))
    
    fig.add_trace(go.Scatter(
        x=tat_timeseries['time_group'],
        y=tat_timeseries['p99'],
        mode='lines+markers',
        name='P99',
        line=dict(color='red')
    ))
    
    fig.update_layout(
        title=f'Turnaround Time Over Time ({grain.title()})',
        xaxis_title='Time',
        yaxis_title='TAT (minutes)',
        hovermode='x unified'
    )
    
    return fig


def create_throughput_chart(df, grain="hour"):
    """Create throughput time series chart."""
    if len(df) == 0:
        return go.Figure()
    
    throughput_data = calculate_throughput(df, grain=grain)
    
    if not throughput_data.data:
        return go.Figure()
    
    # Convert to DataFrame for plotting
    plot_data = []
    for point in throughput_data.data:
        plot_data.append({
            'timestamp': point.timestamp,
            'count': point.count
        })
    
    plot_df = pd.DataFrame(plot_data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=plot_df['timestamp'],
        y=plot_df['count'],
        name='Throughput',
        marker_color='green'
    ))
    
    fig.update_layout(
        title=f'Throughput Over Time ({grain.title()})',
        xaxis_title='Time',
        yaxis_title='Completed Specimens',
        hovermode='x unified'
    )
    
    return fig


def create_assay_breakdown(df):
    """Create assay breakdown chart."""
    if len(df) == 0:
        return go.Figure()
    
    assay_counts = df['assay'].value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=assay_counts.index,
        values=assay_counts.values,
        hole=0.3
    )])
    
    fig.update_layout(
        title='Specimens by Assay Type',
        showlegend=True
    )
    
    return fig


def create_machine_breakdown(df):
    """Create machine breakdown chart."""
    if len(df) == 0:
        return go.Figure()
    
    machine_counts = df['machine_id'].value_counts()
    
    fig = go.Figure(data=[go.Bar(
        x=machine_counts.index,
        y=machine_counts.values,
        marker_color='lightblue'
    )])
    
    fig.update_layout(
        title='Specimens by Machine',
        xaxis_title='Machine ID',
        yaxis_title='Count'
    )
    
    return fig


def create_error_breakdown(df):
    """Create error breakdown chart."""
    if len(df) == 0:
        return go.Figure()
    
    error_df = df[df['status'] == 'ERROR']
    
    if len(error_df) == 0:
        return go.Figure()
    
    error_counts = error_df['error_code'].value_counts()
    
    fig = go.Figure(data=[go.Bar(
        x=error_counts.index,
        y=error_counts.values,
        marker_color='red'
    )])
    
    fig.update_layout(
        title='Errors by Error Code',
        xaxis_title='Error Code',
        yaxis_title='Count'
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
    current_tat = calculate_tat_metrics(df)
    current_throughput = get_total_throughput_today(df)
    
    # Simple capacity model assumptions:
    # - Each machine can process ~50 specimens per day
    # - Reducing failure rate by X% reduces processing time by X%
    # - Extra machines increase capacity linearly
    
    base_capacity_per_machine = 50
    current_machines = len(df['machine_id'].unique())
    new_machines = current_machines + extra_machines
    
    # Calculate capacity improvement
    capacity_improvement = new_machines / current_machines if current_machines > 0 else 1
    
    # Calculate failure rate improvement
    failure_rate_improvement = 1 - (reduced_failure_rate / 100)
    
    # Projected metrics
    projected_tat_p90 = current_tat.p90 * failure_rate_improvement
    projected_throughput = current_throughput * capacity_improvement
    
    # Calculate improvements
    improvement_tat = ((current_tat.p90 - projected_tat_p90) / current_tat.p90) * 100
    improvement_throughput = ((projected_throughput - current_throughput) / current_throughput) * 100
    
    return {
        'projected_tat_p90': projected_tat_p90,
        'projected_throughput': projected_throughput,
        'improvement_tat': improvement_tat,
        'improvement_throughput': improvement_throughput
    }


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="LabOps Metrics Dashboard",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔬 LabOps Metrics Dashboard")
    st.markdown("Real-time laboratory operations monitoring and analytics")
    
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
    st.header("📊 Key Performance Indicators")
    
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
            delta=f"{projections['improvement_throughput']:.1f}%"
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
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        **Dashboard Info:**
        - Data refreshes automatically
        - API documentation available at `/docs`
        - Export data for Power BI using the export script
        """
    )


if __name__ == "__main__":
    main()
