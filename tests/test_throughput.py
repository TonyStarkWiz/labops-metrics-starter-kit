"""Unit tests for throughput metrics calculation."""

import pandas as pd
import pytest
from datetime import datetime, timedelta

from app.metrics.throughput import (
    calculate_throughput,
    calculate_throughput_by_assay,
    calculate_throughput_by_machine,
    get_total_throughput_today
)


class TestThroughputMetrics:
    """Test cases for throughput metrics calculation."""
    
    def setup_method(self):
        """Set up test data."""
        # Create test data with known timestamps
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        
        self.test_data = [
            # Hour 10: 2 completed specimens
            {
                'id': 1,
                'specimen_id': 'SP100001',
                'assay': 'CBC',
                'machine_id': 'M1',
                'operator_id': 'O1',
                'status': 'COMPLETED',
                'error_code': None,
                'received_at': base_time,
                'processed_at': base_time + timedelta(minutes=30)
            },
            {
                'id': 2,
                'specimen_id': 'SP100002',
                'assay': 'CBC',
                'machine_id': 'M1',
                'operator_id': 'O1',
                'status': 'COMPLETED',
                'error_code': None,
                'received_at': base_time,
                'processed_at': base_time + timedelta(minutes=45)
            },
            # Hour 11: 3 completed specimens
            {
                'id': 3,
                'specimen_id': 'SP100003',
                'assay': 'Chem7',
                'machine_id': 'M2',
                'operator_id': 'O2',
                'status': 'COMPLETED',
                'error_code': None,
                'received_at': base_time,
                'processed_at': base_time + timedelta(hours=1, minutes=15)
            },
            {
                'id': 4,
                'specimen_id': 'SP100004',
                'assay': 'Chem7',
                'machine_id': 'M2',
                'operator_id': 'O2',
                'status': 'COMPLETED',
                'error_code': None,
                'received_at': base_time,
                'processed_at': base_time + timedelta(hours=1, minutes=30)
            },
            {
                'id': 5,
                'specimen_id': 'SP100005',
                'assay': 'PCR',
                'machine_id': 'M3',
                'operator_id': 'O3',
                'status': 'COMPLETED',
                'error_code': None,
                'received_at': base_time,
                'processed_at': base_time + timedelta(hours=1, minutes=45)
            },
            # Hour 12: 1 completed specimen
            {
                'id': 6,
                'specimen_id': 'SP100006',
                'assay': 'PCR',
                'machine_id': 'M3',
                'operator_id': 'O3',
                'status': 'COMPLETED',
                'error_code': None,
                'received_at': base_time,
                'processed_at': base_time + timedelta(hours=2, minutes=15)
            },
            # ERROR status (should be excluded)
            {
                'id': 7,
                'specimen_id': 'SP100007',
                'assay': 'PCR',
                'machine_id': 'M3',
                'operator_id': 'O3',
                'status': 'ERROR',
                'error_code': 'E01',
                'received_at': base_time,
                'processed_at': None
            },
            # IN_PROCESS status (should be excluded)
            {
                'id': 8,
                'specimen_id': 'SP100008',
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
    
    def test_calculate_throughput_hour(self):
        """Test throughput calculation with hour grain."""
        result = calculate_throughput(self.df, grain="hour")
        
        assert result.grain == "hour"
        assert len(result.data) == 3  # 3 hours with data
        
        # Check data points
        data_dict = {point.timestamp.hour: point.count for point in result.data}
        
        assert data_dict[10] == 2  # Hour 10: 2 specimens
        assert data_dict[11] == 3  # Hour 11: 3 specimens
        assert data_dict[12] == 1  # Hour 12: 1 specimen
    
    def test_calculate_throughput_day(self):
        """Test throughput calculation with day grain."""
        result = calculate_throughput(self.df, grain="day")
        
        assert result.grain == "day"
        assert len(result.data) == 1  # All data on same day
        
        # Check total count
        total_count = sum(point.count for point in result.data)
        assert total_count == 6  # 6 completed specimens
    
    def test_calculate_throughput_empty_data(self):
        """Test throughput calculation with empty DataFrame."""
        empty_df = pd.DataFrame(columns=['status', 'processed_at'])
        result = calculate_throughput(empty_df, grain="hour")
        
        assert result.grain == "hour"
        assert len(result.data) == 0
    
    def test_calculate_throughput_no_completed(self):
        """Test throughput calculation with no completed specimens."""
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
        
        result = calculate_throughput(error_df, grain="hour")
        
        assert result.grain == "hour"
        assert len(result.data) == 0
    
    def test_calculate_throughput_by_assay(self):
        """Test throughput calculation by assay."""
        result = calculate_throughput_by_assay(self.df, grain="hour")
        
        assert len(result) > 0
        assert 'time_group' in result.columns
        assert 'assay' in result.columns
        assert 'count' in result.columns
        
        # Check that we have data for all assays
        assays = result['assay'].unique()
        assert 'CBC' in assays
        assert 'Chem7' in assays
        assert 'PCR' in assays
    
    def test_calculate_throughput_by_machine(self):
        """Test throughput calculation by machine."""
        result = calculate_throughput_by_machine(self.df, grain="hour")
        
        assert len(result) > 0
        assert 'time_group' in result.columns
        assert 'machine_id' in result.columns
        assert 'count' in result.columns
        
        # Check that we have data for all machines
        machines = result['machine_id'].unique()
        assert 'M1' in machines
        assert 'M2' in machines
        assert 'M3' in machines
    
    def test_get_total_throughput_today(self):
        """Test total throughput calculation for today."""
        # Create data with some specimens processed today
        today = datetime.now().date()
        today_time = datetime.combine(today, datetime.min.time()) + timedelta(hours=10)
        
        today_data = [
            {
                'id': 1,
                'specimen_id': 'SP100001',
                'assay': 'CBC',
                'machine_id': 'M1',
                'operator_id': 'O1',
                'status': 'COMPLETED',
                'error_code': None,
                'received_at': today_time,
                'processed_at': today_time + timedelta(minutes=30)
            },
            {
                'id': 2,
                'specimen_id': 'SP100002',
                'assay': 'CBC',
                'machine_id': 'M1',
                'operator_id': 'O1',
                'status': 'COMPLETED',
                'error_code': None,
                'received_at': today_time,
                'processed_at': today_time + timedelta(minutes=45)
            }
        ]
        
        today_df = pd.DataFrame(today_data)
        result = get_total_throughput_today(today_df)
        
        assert result == 2
    
    def test_get_total_throughput_today_no_today_data(self):
        """Test total throughput calculation with no data from today."""
        # Create data with specimens from yesterday
        yesterday = datetime.now().date() - timedelta(days=1)
        yesterday_time = datetime.combine(yesterday, datetime.min.time()) + timedelta(hours=10)
        
        yesterday_data = [
            {
                'id': 1,
                'specimen_id': 'SP100001',
                'assay': 'CBC',
                'machine_id': 'M1',
                'operator_id': 'O1',
                'status': 'COMPLETED',
                'error_code': None,
                'received_at': yesterday_time,
                'processed_at': yesterday_time + timedelta(minutes=30)
            }
        ]
        
        yesterday_df = pd.DataFrame(yesterday_data)
        result = get_total_throughput_today(yesterday_df)
        
        assert result == 0
    
    def test_get_total_throughput_today_empty_data(self):
        """Test total throughput calculation with empty data."""
        empty_df = pd.DataFrame(columns=['status', 'processed_at'])
        result = get_total_throughput_today(empty_df)
        
        assert result == 0
    
    def test_get_total_throughput_today_no_completed(self):
        """Test total throughput calculation with no completed specimens."""
        # Create data with only errors
        today = datetime.now().date()
        today_time = datetime.combine(today, datetime.min.time()) + timedelta(hours=10)
        
        error_data = [
            {
                'id': 1,
                'specimen_id': 'SP100001',
                'assay': 'CBC',
                'machine_id': 'M1',
                'operator_id': 'O1',
                'status': 'ERROR',
                'error_code': 'E01',
                'received_at': today_time,
                'processed_at': None
            }
        ]
        
        error_df = pd.DataFrame(error_data)
        result = get_total_throughput_today(error_df)
        
        assert result == 0
