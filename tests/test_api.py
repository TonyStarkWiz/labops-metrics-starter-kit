"""API tests using FastAPI TestClient."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import get_db
from app.core.models import Base, Specimen, SpecimenStatus


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


class TestAPI:
    """Test cases for API endpoints."""
    
    def setup_method(self):
        """Set up test database and data."""
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Create test data
        db = TestingSessionLocal()
        try:
            # Clear existing data
            db.query(Specimen).delete()
            
            # Add test specimens
            from datetime import datetime, timedelta
            
            base_time = datetime(2024, 1, 1, 10, 0, 0)
            
            test_specimens = [
                Specimen(
                    specimen_id="SP100001",
                    assay="CBC",
                    machine_id="M1",
                    operator_id="O1",
                    status=SpecimenStatus.COMPLETED,
                    error_code=None,
                    received_at=base_time,
                    processed_at=base_time + timedelta(minutes=60)
                ),
                Specimen(
                    specimen_id="SP100002",
                    assay="CBC",
                    machine_id="M1",
                    operator_id="O1",
                    status=SpecimenStatus.COMPLETED,
                    error_code=None,
                    received_at=base_time,
                    processed_at=base_time + timedelta(minutes=120)
                ),
                Specimen(
                    specimen_id="SP100003",
                    assay="Chem7",
                    machine_id="M2",
                    operator_id="O2",
                    status=SpecimenStatus.ERROR,
                    error_code="E01",
                    received_at=base_time,
                    processed_at=None
                )
            ]
            
            db.add_all(test_specimens)
            db.commit()
            
        finally:
            db.close()
    
    def teardown_method(self):
        """Clean up test database."""
        Base.metadata.drop_all(bind=engine)
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
    
    def test_tat_metrics_endpoint(self):
        """Test TAT metrics endpoint."""
        response = client.get("/api/v1/metrics/tat")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "p50" in data
        assert "p90" in data
        assert "p99" in data
        assert "total_specimens" in data
        assert data["total_specimens"] == 2  # Only completed specimens
    
    def test_tat_metrics_with_assay_filter(self):
        """Test TAT metrics endpoint with assay filter."""
        response = client.get("/api/v1/metrics/tat?assay=CBC")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "p50" in data
        assert "p90" in data
        assert "p99" in data
        assert "assay" in data
        assert data["assay"] == "CBC"
        assert data["total_specimens"] == 2  # Both CBC specimens completed
    
    def test_throughput_metrics_endpoint(self):
        """Test throughput metrics endpoint."""
        response = client.get("/api/v1/metrics/throughput")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "grain" in data
        assert data["grain"] == "hour"
        assert len(data["data"]) > 0
    
    def test_throughput_metrics_with_day_grain(self):
        """Test throughput metrics endpoint with day grain."""
        response = client.get("/api/v1/metrics/throughput?grain=day")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "grain" in data
        assert data["grain"] == "day"
    
    def test_error_metrics_endpoint(self):
        """Test error metrics endpoint."""
        response = client.get("/api/v1/metrics/errors")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "by_machine" in data
        assert "by_error_code" in data
        assert "total_errors" in data
        assert "total_specimens" in data
        assert "overall_error_rate" in data
        
        assert data["total_specimens"] == 3
        assert data["total_errors"] == 1
        assert data["overall_error_rate"] == 1/3
    
    def test_sla_metrics_endpoint(self):
        """Test SLA metrics endpoint."""
        response = client.get("/api/v1/metrics/sla")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "breach_count" in data
        assert "total_completed" in data
        assert "breach_rate" in data
        assert "sample_breaches" in data
        
        assert data["total_completed"] == 2
    
    def test_invalid_grain_parameter(self):
        """Test throughput endpoint with invalid grain parameter."""
        response = client.get("/api/v1/metrics/throughput?grain=invalid")
        
        assert response.status_code == 200  # Should default to "hour"
        data = response.json()
        assert data["grain"] == "hour"
    
    def test_nonexistent_assay_filter(self):
        """Test TAT endpoint with nonexistent assay filter."""
        response = client.get("/api/v1/metrics/tat?assay=NONEXISTENT")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_specimens"] == 0
        assert data["p50"] == 0.0
        assert data["p90"] == 0.0
        assert data["p99"] == 0.0
    
    def test_api_docs_available(self):
        """Test that API documentation is available."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_available(self):
        """Test that ReDoc documentation is available."""
        response = client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
