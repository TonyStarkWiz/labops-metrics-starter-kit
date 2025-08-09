"""Unit tests for TAT (turnaround time) metrics calculation."""

import pandas as pd
import pytest
from datetime import datetime, timedelta

from app.metrics.tat import calculate_tat_metrics, calculate_tat_by_assay, calculate_tat_timeseries


class TestTATMetrics:
    """Test cases for TAT metrics calculation."""
    
    def setup_method(self):
        """Set up test data."""
        # Create test data with known TAT values
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        
        self.test_data = [
            # Specimen 1: 60 minutes TAT
            {
                'id': 1,
                'specimen_id': 'SP100001',
                'assay': 'CBC',
                'machine_id': 'M1',
                'operator_id': 'O1',
                'status': 'COMPLETED',
                'error_code': None,
                'received_at': base_time,
                'processed_at': base_time + timedelta(minutes=60)
            },
            # Specimen 2: 120 minutes TAT
            {
                'id': 2,
                'specimen_id': 'SP100002',
                'assay': 'CBC',
                'machine_id': 'M1',
                'operator_id': 'O1',
                'status': 'COMPLETED',
                'error_code': None,
                'received_at': base_time,
                'processed_at': base_time + timedelta(minutes=120)
            },
            # Specimen 3: 180 minutes TAT
            {
                'id': 3,
                'specimen_id': 'SP100003',
                'assay': 'Chem7',
                'machine_id': 'M2',
                'operator_id': 'O2',
                'status': 'COMPLETED',
                'error_code': None,
                'received_at': base_time,
                'processed_at': base_time + timedelta(minutes=180)
            },
            # Specimen 4: 240 minutes TAT
            {
                'id': 4,
                'specimen_id': 'SP100004',
                'assay': 'Chem7',
                'machine_id': 'M2',
                'operator_id': 'O2',
                'status': 'COMPLETED',
                'error_code': None,
                'received_at': base_time,
                'processed_at': base_time + timedelta(minutes=240)
            },
            # Specimen 5: 300 minutes TAT
            {
                'id': 5,
                'specimen_id': 'SP100005',
                'assay': 'PCR',
                'machine_id': 'M3',
                'operator_id': 'O3',
                'status': 'COMPLETED',
                'error_code': None,
                'received_at': base_time,
                'processed_at': base_time + timedelta(minutes=300)
            },
            # Specimen 6: ERROR status (should be excluded)
            {
                'id': 6,
                'specimen_id': 'SP100006',
                'assay': 'PCR',
                'machine_id': 'M3',
                'operator_id': 'O3',
                'status': 'ERROR',
                'error_code': 'E01',
                'received_at': base_time,
                'processed_at': None
            },
            # Specimen 7: IN_PROCESS status (should be excluded)
            {
                'id': 7,
                'specimen_id': 'SP100007',
                'assay': 'PCR',
                'machine_id': 'M3',
                'operator_id': 'O3',
                'status': 'IN_PROCESS',
                'error_code': None,
                'received_at': base_time,
                'processed_at': None
            }
        ]
        
        self.df = pd.DataFrame(self.test_data)
    
    def test_calculate_tat_metrics_overall(self):
        """Test TAT metrics calculation for all completed specimens."""
        result = calculate_tat_metrics(self.df)
        
        # Expected values: [60, 120, 180, 240, 300] minutes
        # P50 = 180, P90 = 300, P99 = 300
        assert result.p50 == 180.0
        assert result.p90 == 300.0
        assert result.p99 == 300.0
        assert result.total_specimens == 5
        assert result.assay is None
    
    def test_calculate_tat_metrics_by_assay(self):
        """Test TAT metrics calculation filtered by assay."""
        result = calculate_tat_metrics(self.df, assay='CBC')
        
        # Expected values: [60, 120] minutes
        # P50 = 90, P90 = 120, P99 = 120
        assert result.p50 == 90.0
        assert result.p90 == 120.0
        assert result.p99 == 120.0
        assert result.total_specimens == 2
        assert result.assay == 'CBC'
    
    def test_calculate_tat_metrics_empty_data(self):
        """Test TAT metrics calculation with empty DataFrame."""
        empty_df = pd.DataFrame(columns=['status', 'received_at', 'processed_at'])
        result = calculate_tat_metrics(empty_df)
        
        assert result.p50 == 0.0
        assert result.p90 == 0.0
        assert result.p99 == 0.0
        assert result.total_specimens == 0
    
    def test_calculate_tat_metrics_no_completed(self):
        """Test TAT metrics calculation with no completed specimens."""
        # Create data with only errors and in-process
        error_data = [
            {
                'id': 1,
                'specimen_id': 'SP100001',
                'assay': 'CBC',
                'machine_id': 'M1',
                'operator_id': 'O1',
                'status': 'ERROR',
                'error_code': 'E01',
                'received_at': datetime(2024, 1, 1, 10, 0, 0),
                'processed_at': None
            }
        ]
        error_df = pd.DataFrame(error_data)
        
        result = calculate_tat_metrics(error_df)
        
        assert result.p50 == 0.0
        assert result.p90 == 0.0
        assert result.p99 == 0.0
        assert result.total_specimens == 0
    
    def test_calculate_tat_metrics_invalid_timestamps(self):
        """Test TAT metrics calculation with invalid timestamps."""
        # Create data with processed_at before received_at
        invalid_data = [
            {
                'id': 1,
                'specimen_id': 'SP100001',
                'assay': 'CBC',
                'machine_id': 'M1',
                'operator_id': 'O1',
                'status': 'COMPLETED',
                'error_code': None,
                'received_at': datetime(2024, 1, 1, 10, 0, 0),
                'processed_at': datetime(2024, 1, 1, 9, 0, 0)  # Before received_at
            }
        ]
        invalid_df = pd.DataFrame(invalid_data)
        
        result = calculate_tat_metrics(invalid_df)
        
        assert result.p50 == 0.0
        assert result.p90 == 0.0
        assert result.p99 == 0.0
        assert result.total_specimens == 0
    
    def test_calculate_tat_by_assay(self):
        """Test TAT metrics calculation for each assay."""
        results = calculate_tat_by_assay(self.df)
        
        assert 'CBC' in results
        assert 'Chem7' in results
        assert 'PCR' in results
        
        # CBC: [60, 120] minutes
        cbc_result = results['CBC']
        assert cbc_result.p50 == 90.0
        assert cbc_result.p90 == 120.0
        assert cbc_result.total_specimens == 2
        
        # Chem7: [180, 240] minutes
        chem7_result = results['Chem7']
        assert chem7_result.p50 == 210.0
        assert chem7_result.p90 == 240.0
        assert chem7_result.total_specimens == 2
        
        # PCR: [300] minutes
        pcr_result = results['PCR']
        assert pcr_result.p50 == 300.0
        assert pcr_result.p90 == 300.0
        assert pcr_result.total_specimens == 1
    
    def test_calculate_tat_timeseries_hour(self):
        """Test TAT time series calculation with hour grain."""
        result = calculate_tat_timeseries(self.df, grain="hour")
        
        assert len(result) > 0
        assert 'time_group' in result.columns
        assert 'p50' in result.columns
        assert 'p90' in result.columns
        assert 'p99' in result.columns
        assert 'count' in result.columns
    
    def test_calculate_tat_timeseries_day(self):
        """Test TAT time series calculation with day grain."""
        result = calculate_tat_timeseries(self.df, grain="day")
        
        assert len(result) > 0
        assert 'time_group' in result.columns
        assert 'p50' in result.columns
        assert 'p90' in result.columns
        assert 'p99' in result.columns
        assert 'count' in result.columns
    
    def test_calculate_tat_timeseries_empty_data(self):
        """Test TAT time series calculation with empty data."""
        empty_df = pd.DataFrame(columns=['status', 'received_at', 'processed_at'])
        result = calculate_tat_timeseries(empty_df, grain="hour")
        
        assert len(result) == 0
    
    def test_calculate_tat_timeseries_no_completed(self):
        """Test TAT time series calculation with no completed specimens."""
        error_data = [
            {
                'id': 1,
                'specimen_id': 'SP100001',
                'assay': 'CBC',
                'machine_id': 'M1',
                'operator_id': 'O1',
                'status': 'ERROR',
                'error_code': 'E01',
                'received_at': datetime(2024, 1, 1, 10, 0, 0),
                'processed_at': None
            }
        ]
        error_df = pd.DataFrame(error_data)
        
        result = calculate_tat_timeseries(error_df, grain="hour")
        
        assert len(result) == 0
