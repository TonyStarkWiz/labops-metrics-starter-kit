# LabOps Metrics Starter Kit - Micro-PoCs

This document describes the two Micro-PoCs implemented to showcase additional capabilities of the LabOps Metrics Starter Kit:

1. **Micro-PoC A: Data Quality Rules Engine**
2. **Micro-PoC B: Microsoft Teams Stand-up Bot**

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- FastAPI server running on port 8000
- Streamlit installed
- Required dependencies (see `requirements.txt`)

### Running the Enhanced Dashboard
```bash
# Start the FastAPI server
uvicorn app.main:app --reload --port 8000

# In another terminal, run the enhanced Streamlit dashboard
streamlit run app/dashboards/enhanced_streamlit_app.py --server.port 8501
```

## 🔍 Micro-PoC A: Data Quality Rules Engine

### Overview
A configurable data quality validation engine that can validate CSV data against declarative rules defined in YAML format.

### Features
- **Multiple Rule Types**: required_columns, timestamp_order, allowed_values, data_types, uniqueness, completeness, range_check, no_future_dates
- **Configurable Severity**: ERROR, WARNING, INFO levels
- **Flexible Input**: Upload CSV files, use sample rules, or define custom rules
- **Comprehensive Reporting**: Violation details, summary statistics, downloadable reports
- **API Integration**: RESTful endpoints for programmatic access

### Usage

#### Via Streamlit Dashboard
1. Navigate to the "🔍 Data Quality" tab
2. Upload a CSV file for validation
3. Choose rules source:
   - **Use Sample Rules**: Pre-configured rules for lab data
   - **Upload Custom Rules**: Upload your own YAML rules file
   - **Enter Rules Manually**: Type rules directly in the interface
4. Click "Run Data Quality Validation"
5. Review results and download violation reports

#### Via API
```bash
# Validate CSV data
curl -X POST "http://localhost:8000/api/v1/dq/validate-csv" \
  -F "file=@your_data.csv" \
  -F "custom_rules={\"rules\":[{\"name\":\"Test\",\"rule_type\":\"required_columns\",\"parameters\":{\"columns\":[\"id\"]}}]}"

# Get rule templates
curl "http://localhost:8000/api/v1/dq/rules/templates"

# Validate rule syntax
curl -X POST "http://localhost:8000/api/v1/dq/rules/validate" \
  -H "Content-Type: application/json" \
  -d '{"rules":[{"name":"Test","rule_type":"required_columns","parameters":{"columns":["id"]}}]}'
```

#### Rule Examples
```yaml
rules:
  - name: "Required Columns Check"
    description: "Ensure all required columns are present"
    rule_type: "required_columns"
    parameters:
      columns: ["specimen_id", "received_at", "status"]
    severity: "ERROR"

  - name: "Valid Status Values"
    description: "Ensure status values are valid"
    rule_type: "allowed_values"
    parameters:
      column: "status"
      allowed_values: ["received", "in_process", "completed", "error"]
    severity: "ERROR"

  - name: "No Missing Critical Fields"
    description: "Ensure critical fields have no missing values"
    rule_type: "completeness"
    parameters:
      columns: ["specimen_id", "status"]
      threshold: 0.0
    severity: "ERROR"
```

### API Endpoints
- `POST /api/v1/dq/validate-csv` - Validate CSV data against rules
- `GET /api/v1/dq/rules/templates` - Get available rule templates
- `POST /api/v1/dq/rules/validate` - Validate rule syntax
- `GET /api/v1/dq/health` - Health check

## 🤖 Micro-PoC B: Microsoft Teams Stand-up Bot

### Overview
An automated bot for posting daily stand-up updates to Microsoft Teams channels, supporting both individual and team-wide updates.

### Features
- **Multiple Input Methods**: Manual entry, JSON upload, template-based
- **Rich Stand-up Items**: Status tracking, priority levels, effort estimation, blockers
- **Team Support**: Individual and team-wide stand-up updates
- **Teams Integration**: Native Teams message cards with rich formatting
- **Dry Run Mode**: Test functionality without posting to Teams
- **Flexible Configuration**: Webhook URL configuration and environment variables

### Usage

#### Via Streamlit Dashboard
1. Navigate to the "🤖 Teams Bot" tab
2. Configure your Teams webhook URL
3. Choose input method:
   - **Manual Entry**: Fill out forms for individual stand-ups
   - **Upload JSON**: Upload JSON files with stand-up data
   - **Use Template**: Copy and modify provided templates
4. Set dry run mode for testing
5. Click "Post Stand-up to Teams"

#### Via API
```bash
# Post individual stand-up
curl -X POST "http://localhost:8000/api/v1/teams/standup/post" \
  -H "Content-Type: application/json" \
  -d '{
    "team_member": "John Doe",
    "items": [
      {
        "title": "Complete API docs",
        "status": "completed",
        "description": "Write comprehensive API docs",
        "assignee": "John Doe",
        "priority": "high",
        "effort": "4h"
      }
    ],
    "mood": "😊",
    "availability": "Available"
  }'

# Post team stand-up
curl -X POST "http://localhost:8000/api/v1/teams/standup/team-post" \
  -H "Content-Type: application/json" \
  -d '{
    "team_members": [
      {
        "team_member": "John Doe",
        "items": [{"title": "Task 1", "status": "completed", "description": "Description", "assignee": "John Doe"}]
      }
    ]
  }'

# Upload JSON file
curl -X POST "http://localhost:8000/api/v1/teams/standup/upload-json" \
  -F "file=@standup_data.json"
```

#### Stand-up Data Structure
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
      "notes": "Ready for review",
      "blockers": []
    }
  ],
  "mood": "😊",
  "availability": "Available",
  "next_priorities": ["Code review", "Team meeting"]
}
```

#### Team Stand-up Structure
```json
{
  "team_members": [
    {
      "date": "2024-01-15",
      "team_member": "John Doe",
      "items": [...],
      "mood": "😊",
      "availability": "Available"
    },
    {
      "date": "2024-01-15",
      "team_member": "Jane Smith",
      "items": [...],
      "mood": "🤔",
      "availability": "Available"
    }
  ]
}
```

### API Endpoints
- `POST /api/v1/teams/standup/post` - Post individual stand-up
- `POST /api/v1/teams/standup/team-post` - Post team stand-up
- `POST /api/v1/teams/standup/upload-json` - Post stand-up from JSON file
- `GET /api/v1/teams/standup/templates` - Get stand-up templates
- `GET /api/v1/teams/health` - Health check

### Configuration
Set the `TEAMS_WEBHOOK_URL` environment variable or provide it in the webhook URL field:
```bash
export TEAMS_WEBHOOK_URL="https://your-org.webhook.office.com/webhookb2/..."
```

## 📊 Enhanced Dashboard Features

The enhanced Streamlit dashboard provides three main tabs:

### 1. 📊 Metrics Dashboard
- Original lab operations metrics
- Real-time KPI monitoring
- Time series analysis
- SLA monitoring and alerting
- What-if analysis

### 2. 🔍 Data Quality
- CSV file upload and validation
- Configurable DQ rules
- Violation reporting and filtering
- Downloadable reports
- Rule templates and examples

### 3. 🤖 Teams Bot
- Stand-up input forms
- Multiple input methods
- Teams integration
- Dry run testing
- Status monitoring

## 🛠️ Development and Customization

### Adding New DQ Rule Types
1. Extend the `DQRulesEngine` class in `scripts/dq_rules_engine.py`
2. Add new rule type handling in the `validate_data` method
3. Update the API templates endpoint
4. Add examples to the Streamlit dashboard

### Extending Teams Bot Functionality
1. Modify the `TeamsStandupBot` class in `scripts/teams_standup_bot.py`
2. Add new message card formats
3. Extend the API endpoints
4. Update the Streamlit interface

### API Integration
Both Micro-PoCs are fully integrated with the FastAPI application:
- Automatic route registration
- Swagger documentation at `/docs`
- Health check endpoints
- Error handling and validation

## 🔧 Troubleshooting

### Common Issues

#### Data Quality Engine
- **Import errors**: Ensure the scripts directory is in the Python path
- **YAML parsing errors**: Check rule syntax and indentation
- **File upload issues**: Verify file format and size limits

#### Teams Bot
- **Webhook errors**: Verify Teams webhook URL and permissions
- **Message formatting**: Check Teams message card format requirements
- **Rate limiting**: Teams has rate limits for webhook calls

#### Dashboard
- **Port conflicts**: Change ports if 8000 or 8501 are in use
- **Database connection**: Ensure the database is accessible
- **Dependencies**: Install all required packages from `requirements.txt`

### Debug Mode
Enable debug logging by setting environment variables:
```bash
export LOG_LEVEL=DEBUG
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## 📚 Additional Resources

- **API Documentation**: Available at `http://localhost:8000/docs`
- **Sample Data**: Use the data generation scripts in the `scripts/` directory
- **Configuration**: Modify `app/core/settings.py` for custom settings
- **Testing**: Run tests with `pytest tests/`

## 🚀 Deployment

### Production Considerations
- Secure webhook URLs and API keys
- Implement proper authentication and authorization
- Set up monitoring and logging
- Configure rate limiting for Teams webhooks
- Use production-grade databases

### Docker Deployment
```bash
# Build and run with Docker
docker build -t labops-metrics .
docker run -p 8000:8000 -p 8501:8501 labops-metrics
```

### Cloud Deployment
- **Streamlit Cloud**: Deploy the enhanced dashboard
- **Heroku**: Deploy the FastAPI backend
- **Azure**: Use Azure Functions for Teams integration
- **AWS**: Deploy with Lambda and API Gateway

## 🤝 Contributing

To extend the Micro-PoCs:

1. **Fork the repository**
2. **Create a feature branch**
3. **Implement your changes**
4. **Add tests and documentation**
5. **Submit a pull request**

### Development Guidelines
- Follow the existing code style
- Add type hints and docstrings
- Include error handling
- Write unit tests
- Update documentation

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Examine the sample code and templates
4. Open an issue on GitHub

---

**Happy LabOps Monitoring! 🔬📊🤖**
