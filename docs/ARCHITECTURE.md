# LabOps Metrics Starter Kit - Architecture

## System Overview

The LabOps Metrics Starter Kit is a modular, event-driven laboratory operations monitoring system designed for real-time metrics, alerting, and analytics.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Processing    │    │   Presentation  │
│                 │    │                 │    │                 │
│ • Synthetic     │───▶│ • FastAPI       │───▶│ • Streamlit     │
│   Generator     │    │ • SQLAlchemy    │    │   Dashboard     │
│ • CSV Import    │    │ • Metrics Calc  │    │ • Power BI      │
│ • Real-time     │    │ • Alert Engine  │    │ • Teams Alerts  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Components

### 1. Data Layer
- **SQLite Database**: Lightweight, file-based storage for development and small-scale deployments
- **SQLAlchemy ORM**: Database abstraction and model management
- **Specimen Model**: Core entity representing lab test specimens with status tracking

### 2. API Layer (FastAPI)
- **Health Endpoint**: System status monitoring
- **Metrics Endpoints**: RESTful APIs for TAT, throughput, errors, and SLA metrics
- **CORS Support**: Cross-origin resource sharing for web integration
- **Auto-generated Docs**: Interactive API documentation at `/docs`

### 3. Metrics Engine
- **TAT Calculator**: Turnaround time percentiles (P50/P90/P99) by assay
- **Throughput Analyzer**: Specimen completion rates by time grain
- **Error Rate Monitor**: Failure analysis by machine and error code
- **SLA Breach Detector**: Service level agreement violation tracking

### 4. Dashboard (Streamlit)
- **Real-time KPIs**: Live metrics display with auto-refresh
- **Interactive Charts**: Plotly-based visualizations with filtering
- **Alert Integration**: Teams webhook payload generation and display
- **What-If Analysis**: Capacity planning simulation tools

### 5. Alert System
- **Teams Integration**: Microsoft Teams webhook support
- **Dry-Run Mode**: Safe testing without sending actual alerts
- **Configurable Payloads**: Structured alert messages with actionable data

## Data Flow

### 1. Data Generation Flow
```
Synthetic Generator → CSV Files → SQLite Database → Metrics Calculation
```

### 2. Real-time Metrics Flow
```
Database Query → DataFrame Conversion → Metrics Calculation → API Response
```

### 3. Dashboard Flow
```
Database Query → Filtering → Chart Generation → Streamlit Display
```

### 4. Alert Flow
```
SLA Breach Detection → Payload Creation → Teams Webhook → Notification
```

## Database Schema

### Specimens Table
```sql
CREATE TABLE specimens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    specimen_id VARCHAR(50) UNIQUE NOT NULL,
    assay VARCHAR(20) NOT NULL,
    machine_id VARCHAR(10) NOT NULL,
    operator_id VARCHAR(10) NOT NULL,
    status ENUM('RECEIVED', 'IN_PROCESS', 'COMPLETED', 'ERROR') NOT NULL,
    error_code VARCHAR(10),
    received_at DATETIME NOT NULL,
    processed_at DATETIME,
    
    INDEX idx_assay (assay),
    INDEX idx_machine_id (machine_id),
    INDEX idx_received_at (received_at),
    INDEX idx_status (status)
);
```

## Configuration Management

### Environment Variables
- `DATABASE_URL`: Database connection string
- `SLA_HOURS`: Service level agreement threshold (default: 4 hours)
- `TEAMS_WEBHOOK_URL`: Microsoft Teams webhook URL for alerts

### Settings Module
Centralized configuration management with defaults and validation.

## Security Considerations

### Data Privacy
- **HIPAA Compliance**: Synthetic data generation with no real patient information
- **No PII**: All specimen IDs are synthetic and non-identifiable
- **Local Storage**: SQLite database for development (production should use proper database)

### API Security
- **CORS Configuration**: Configurable cross-origin policies
- **Input Validation**: Pydantic models for request/response validation
- **Error Handling**: Graceful error responses without sensitive information

## Scalability Design

### Horizontal Scaling
- **Stateless API**: FastAPI endpoints can be scaled horizontally
- **Database Separation**: Metrics calculation can be moved to background workers
- **Caching Layer**: Redis integration possible for frequently accessed metrics

### Performance Optimization
- **Database Indexing**: Optimized queries with proper indices
- **Pandas Operations**: Efficient data processing with vectorized operations
- **Lazy Loading**: On-demand data loading in dashboard

## Deployment Architecture

### Development Environment
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │   SQLite        │
│   Dashboard     │◄──►│   Backend       │◄──►│   Database      │
│   (Port 8501)   │    │   (Port 8000)   │    │   (File)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Production Considerations
- **Database**: PostgreSQL or MySQL for production workloads
- **Web Server**: Nginx reverse proxy for FastAPI
- **Process Management**: Systemd or Docker containers
- **Monitoring**: Application performance monitoring (APM) integration
- **Logging**: Structured logging with log aggregation

## Integration Points

### External Systems
- **Microsoft Teams**: Webhook integration for alerts
- **Power BI**: CSV export for business intelligence
- **Data Quality Tools**: YAML-based rule engine
- **CI/CD**: GitHub Actions for automated testing

### Extension Points
- **Custom Metrics**: Pluggable metric calculation functions
- **Additional Alerts**: Extensible alert system for other platforms
- **Data Sources**: Adapter pattern for different lab systems
- **Visualizations**: Custom chart components for specific needs

## Error Handling Strategy

### Graceful Degradation
- **Empty Data Handling**: Proper handling of no-data scenarios
- **Invalid Input**: Validation and user-friendly error messages
- **Database Failures**: Connection retry logic and fallback responses

### Monitoring and Alerting
- **Health Checks**: Regular system status monitoring
- **Error Logging**: Structured error logging for debugging
- **Performance Metrics**: Response time and throughput monitoring

## Future Enhancements

### Planned Features
- **Real-time Streaming**: WebSocket support for live updates
- **Advanced Analytics**: Machine learning for predictive insights
- **Multi-tenant Support**: Organization and user management
- **Mobile App**: React Native dashboard for mobile access

### Technical Debt
- **Type Hints**: Complete type annotation coverage
- **Documentation**: API documentation with examples
- **Testing**: Increased test coverage and integration tests
- **Performance**: Query optimization and caching strategies
