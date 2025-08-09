"""
LabOps Metrics Starter Kit - Streamlit Dashboard
Deployment-ready version for Streamlit Community Cloud
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

# Page configuration
st.set_page_config(
    page_title="LabOps Metrics Dashboard",
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
</style>
""", unsafe_allow_html=True)

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
        
        # Generate dates for the last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        date_range = pd.date_range(start=start_date, end=end_date, freq='H')
        
        # Sample data
        assay_types = ['Blood Chemistry', 'Hematology', 'Microbiology', 'Immunology', 'Molecular']
        statuses = ['Completed', 'In Progress', 'Pending', 'Failed']
        
        data = []
        for i in range(n_samples):
            received_at = np.random.choice(date_range)
            processing_time = np.random.randint(1, 48)  # 1-48 hours
            processed_at = received_at + timedelta(hours=processing_time)
            
            specimen = {
                'specimen_id': f'SP{i+1:06d}',
                'patient_id': f'P{i+1:06d}',
                'assay_type': np.random.choice(assay_types),
                'status': np.random.choice(statuses),
                'received_at': received_at,
                'processed_at': processed_at,
                'priority': np.random.choice(['High', 'Medium', 'Low']),
                'lab_technician': f'Tech{np.random.randint(1, 6)}',
                'error_code': np.random.choice([None, 'E001', 'E002', 'E003'], p=[0.8, 0.1, 0.05, 0.05])
            }
            data.append(specimen)
        
        return pd.DataFrame(data)
        
    except Exception as e:
        st.error(f"Error creating sample data: {e}")
        # Return minimal fallback data
        return pd.DataFrame({
            'specimen_id': ['SP000001'],
            'patient_id': ['P000001'],
            'assay_type': ['Blood Chemistry'],
            'status': ['Completed'],
            'received_at': [datetime.now() - timedelta(hours=1)],
            'processed_at': [datetime.now()],
            'priority': ['Medium'],
            'lab_technician': ['Tech1'],
            'error_code': [None]
        })

def calculate_tat_metrics(df):
    """Calculate TAT metrics with error handling."""
    try:
        if df.empty:
            return 0, 0, 0
        
        # Filter completed specimens
        completed = df[df['status'] == 'Completed'].copy()
        if completed.empty:
            return 0, 0, 0
        
        # Calculate TAT in hours
        completed['tat_hours'] = (completed['processed_at'] - completed['received_at']).dt.total_seconds() / 3600
        
        avg_tat = completed['tat_hours'].mean()
        median_tat = completed['tat_hours'].median()
        max_tat = completed['tat_hours'].max()
        
        return round(avg_tat, 2), round(median_tat, 2), round(max_tat, 2)
        
    except Exception as e:
        st.error(f"Error calculating TAT metrics: {e}")
        return 0, 0, 0

def calculate_throughput(df):
    """Calculate throughput metrics with error handling."""
    try:
        if df.empty:
            return 0, 0
        
        # Today's throughput
        today = datetime.now().date()
        today_specimens = df[df['processed_at'].dt.date == today]
        today_throughput = len(today_specimens)
        
        # Weekly throughput
        week_ago = today - timedelta(days=7)
        weekly_specimens = df[df['processed_at'].dt.date >= week_ago]
        weekly_throughput = len(weekly_specimens)
        
        return today_throughput, weekly_throughput
        
    except Exception as e:
        st.error(f"Error calculating throughput: {e}")
        return 0, 0

def main():
    """Main Streamlit application."""
    st.markdown('<h1 class="main-header">🧪 LabOps Metrics Dashboard</h1>', unsafe_allow_html=True)
    
    # Load data with progress indicator
    with st.spinner("Loading data..."):
        df = load_data()
    
    if df is None or df.empty:
        st.error("Failed to load data. Please check the application.")
        return
    
    # Display basic info
    st.success(f"✅ Data loaded successfully! {len(df)} specimens available.")
    
    # Calculate metrics
    avg_tat, median_tat, max_tat = calculate_tat_metrics(df)
    today_throughput, weekly_throughput = calculate_throughput(df)
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Avg TAT (hrs)", f"{avg_tat}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Today's Throughput", f"{today_throughput}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Weekly Throughput", f"{weekly_throughput}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        error_rate = len(df[df['error_code'].notna()]) / len(df) * 100
        st.metric("Error Rate", f"{error_rate:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Status Distribution")
        status_counts = df['status'].value_counts()
        fig_status = px.pie(values=status_counts.values, names=status_counts.index, title="Specimen Status")
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        st.subheader("🧬 Assay Type Distribution")
        assay_counts = df['assay_type'].value_counts()
        fig_assay = px.bar(x=assay_counts.index, y=assay_counts.values, title="Assay Types")
        st.plotly_chart(fig_assay, use_container_width=True)
    
    # TAT Timeline
    st.subheader("⏱️ Turnaround Time Timeline")
    completed_df = df[df['status'] == 'Completed'].copy()
    if not completed_df.empty:
        completed_df['tat_hours'] = (completed_df['processed_at'] - completed_df['received_at']).dt.total_seconds() / 3600
        fig_tat = px.scatter(completed_df, x='received_at', y='tat_hours', 
                            title="TAT by Receipt Date", labels={'tat_hours': 'TAT (hours)'})
        st.plotly_chart(fig_tat, use_container_width=True)
    
    # Data Table
    st.subheader("📋 Specimen Data")
    st.dataframe(df.head(20), use_container_width=True)
    
    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Data as CSV",
        data=csv,
        file_name="labops_metrics.csv",
        mime="text/csv"
    )
    
    # Footer
    st.markdown("---")
    st.markdown("**LabOps Metrics Starter Kit** - Built with Streamlit and FastAPI")

if __name__ == "__main__":
    main()
