"""
LabOps Metrics Starter Kit - Streamlit Dashboard
Deployment-ready version for Streamlit Community Cloud
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="LabOps Metrics Dashboard",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    .stAlert {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load data from SQLite database with caching."""
    try:
        # Try to connect to the database
        db_path = Path("labops.db")
        if not db_path.exists():
            # If no database exists, create sample data
            return create_sample_data()
        
        conn = sqlite3.connect("labops.db")
        specimens_df = pd.read_sql_query("SELECT * FROM specimens", conn)
        conn.close()
        
        if len(specimens_df) == 0:
            return create_sample_data()
        
        return specimens_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return create_sample_data()

def create_sample_data():
    """Create sample data for demonstration purposes."""
    np.random.seed(42)
    
    # Generate sample data
    n_samples = 1000
    base_time = datetime.now() - timedelta(days=7)
    
    data = []
    for i in range(n_samples):
        received_time = base_time + timedelta(
            hours=np.random.randint(0, 168),
            minutes=np.random.randint(0, 60)
        )
        
        # Random processing time between 1-8 hours
        processing_hours = np.random.exponential(3) + 1
        processing_time = timedelta(hours=min(processing_hours, 8))
        processed_time = received_time + processing_time
        
        # Random status
        status = np.random.choice(['completed', 'processing', 'error'], p=[0.8, 0.15, 0.05])
        
        # Random assay type
        assay_type = np.random.choice(['PCR', 'ELISA', 'Western Blot', 'Flow Cytometry'])
        
        # Random machine
        machine = np.random.choice(['Machine A', 'Machine B', 'Machine C'])
        
        data.append({
            'specimen_id': f'SP{i:06d}',
            'assay_type': assay_type,
            'status': status,
            'received_at': received_time,
            'processed_at': processed_time if status == 'completed' else None,
            'machine': machine,
            'priority': np.random.choice(['high', 'medium', 'low']),
            'error_code': np.random.choice(['None', 'QC_FAIL', 'INSUFFICIENT_SAMPLE'], p=[0.95, 0.03, 0.02]) if status == 'error' else 'None'
        })
    
    return pd.DataFrame(data)

def calculate_tat_metrics(df):
    """Calculate TAT metrics."""
    completed = df[df['status'] == 'completed'].copy()
    if len(completed) == 0:
        return {'p50': 0, 'p95': 0, 'avg': 0}
    
    completed['tat_hours'] = (completed['processed_at'] - completed['received_at']).dt.total_seconds() / 3600
    
    return {
        'p50': completed['tat_hours'].quantile(0.5),
        'p95': completed['tat_hours'].quantile(0.95),
        'avg': completed['tat_hours'].mean()
    }

def calculate_throughput(df, grain="hour"):
    """Calculate throughput metrics."""
    if len(df) == 0:
        return pd.DataFrame()
    
    df_copy = df.copy()
    df_copy['processed_date'] = pd.to_datetime(df_copy['processed_at']).dt.date
    
    if grain == "hour":
        df_copy['time_bucket'] = pd.to_datetime(df_copy['processed_at']).dt.floor('H')
    else:
        df_copy['time_bucket'] = pd.to_datetime(df_copy['processed_at']).dt.date
    
    throughput = df_copy.groupby('time_bucket').size().reset_index(name='count')
    throughput['grain'] = grain
    
    return throughput

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔬 LabOps Metrics Dashboard</h1>
        <p>Real-time laboratory operations monitoring and analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Loading lab data..."):
        df = load_data()
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Date range filter
    if len(df) > 0:
        min_date = df['received_at'].min().date()
        max_date = df['received_at'].max().date()
        
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Status filter
        status_filter = st.sidebar.multiselect(
            "Status",
            options=df['status'].unique(),
            default=df['status'].unique()
        )
        
        # Assay type filter
        assay_filter = st.sidebar.multiselect(
            "Assay Type",
            options=df['assay_type'].unique(),
            default=df['assay_type'].unique()
        )
        
        # Apply filters
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = df[
                (df['received_at'].dt.date >= start_date) &
                (df['received_at'].dt.date <= end_date) &
                (df['status'].isin(status_filter)) &
                (df['assay_type'].isin(assay_filter))
            ]
        else:
            filtered_df = df
    else:
        filtered_df = df
    
    # Main content
    col1, col2, col3, col4 = st.columns(4)
    
    # KPI Cards
    with col1:
        total_specimens = len(filtered_df)
        st.markdown(f"""
        <div class="metric-card">
            <h3>📊 Total Specimens</h3>
            <h2>{total_specimens:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        completed = len(filtered_df[filtered_df['status'] == 'completed'])
        completion_rate = (completed / total_specimens * 100) if total_specimens > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>✅ Completion Rate</h3>
            <h2>{completion_rate:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        errors = len(filtered_df[filtered_df['status'] == 'error'])
        error_rate = (errors / total_specimens * 100) if total_specimens > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>❌ Error Rate</h3>
            <h2>{error_rate:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        tat_metrics = calculate_tat_metrics(filtered_df)
        st.markdown(f"""
        <div class="metric-card">
            <h3>⏱️ Avg TAT</h3>
            <h2>{tat_metrics['avg']:.1f}h</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Status Distribution")
        status_counts = filtered_df['status'].value_counts()
        fig_status = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Specimen Status Distribution"
        )
        fig_status.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        st.subheader("🔬 Assay Type Distribution")
        assay_counts = filtered_df['assay_type'].value_counts()
        fig_assay = px.bar(
            x=assay_counts.index,
            y=assay_counts.values,
            title="Specimens by Assay Type"
        )
        st.plotly_chart(fig_assay, use_container_width=True)
    
    # TAT Analysis
    st.markdown("---")
    st.subheader("⏱️ Turnaround Time Analysis")
    
    if len(filtered_df[filtered_df['status'] == 'completed']) > 0:
        completed_df = filtered_df[filtered_df['status'] == 'completed'].copy()
        completed_df['tat_hours'] = (completed_df['processed_at'] - completed_df['received_at']).dt.total_seconds() / 3600
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_tat_hist = px.histogram(
                completed_df,
                x='tat_hours',
                nbins=30,
                title="TAT Distribution (Hours)",
                labels={'tat_hours': 'Turnaround Time (Hours)'}
            )
            st.plotly_chart(fig_tat_hist, use_container_width=True)
        
        with col2:
            fig_tat_by_assay = px.box(
                completed_df,
                x='assay_type',
                y='tat_hours',
                title="TAT by Assay Type"
            )
            st.plotly_chart(fig_tat_by_assay, use_container_width=True)
    
    # Throughput Analysis
    st.markdown("---")
    st.subheader("📊 Throughput Analysis")
    
    if len(filtered_df) > 0:
        throughput_hourly = calculate_throughput(filtered_df, "hour")
        
        if len(throughput_hourly) > 0:
            fig_throughput = px.line(
                throughput_hourly,
                x='time_bucket',
                y='count',
                title="Hourly Throughput",
                labels={'time_bucket': 'Time', 'count': 'Specimens Processed'}
            )
            st.plotly_chart(fig_throughput, use_container_width=True)
    
    # Data Table
    st.markdown("---")
    st.subheader("📋 Raw Data")
    
    # Show sample of data
    st.dataframe(
        filtered_df.head(100),
        use_container_width=True,
        hide_index=True
    )
    
    # Download button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Data as CSV",
        data=csv,
        file_name=f"labops_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>🔬 LabOps Metrics Starter Kit | Built with Streamlit</p>
        <p>Real-time laboratory operations monitoring and analytics platform</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
