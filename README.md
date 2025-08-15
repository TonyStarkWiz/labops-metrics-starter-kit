# LabOps Metrics Starter Kit

A comprehensive laboratory operations metrics dashboard with synthetic data generation, FastAPI endpoints, Streamlit visualization, and Microsoft Teams alerts.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Synthetic Data
```bash
python scripts/gen_synthetic_data.py --days 3 --per-day 1200
```

### 3. Start the Services

**FastAPI Backend:**
```bash
uvicorn app.main:app --reload
```
API docs available at: http://localhost:8000/docs

**Streamlit Dashboard:**
```bash
streamlit run app/dashboards/streamlit_app.py
```
Dashboard available at: http://localhost:8501

## 📊 Features

- **HIPAA-safe synthetic lab events** with realistic timestamps and error patterns
- **SQLite storage** with SQLAlchemy ORM
- **FastAPI endpoints** for metrics (TAT, throughput, errors, SLA)
- **Streamlit dashboard** with KPIs, time-series charts, and breakdowns
- **Microsoft Teams alerts** (dry-run + real webhook support)
- **Power BI export** with CSV snapshots and PBIX scaffold
- **Data quality rules engine** with validation and reporting
- **Comprehensive testing** with pytest and coverage

## 🏗️ Architecture

```
labops-metrics-starter-kit/
├── app/
│   ├── api/              # FastAPI routers
│   ├── core/             # models, db, schemas, settings
│   ├── metrics/          # metric calculators
│   ├── alerts/           # Teams webhook integration
│   └── dashboards/       # Streamlit app
├── scripts/              # data generation and export
├── tests/                # pytest test suite
├── data/                 # synthetic data and exports
└── docs/                 # documentation
```

## 📈 Metrics Available

- **Turnaround Time (TAT)**: P50/P90/P99 by assay
- **Throughput**: Completed specimens per hour/day
- **Error Rates**: By machine and error code
- **SLA Breaches**: Configurable SLA monitoring (default: 4 hours)

## 🔧 Configuration

Copy `.env.example` to `.env` and configure:

```bash
DATABASE_URL=sqlite:///./labops.db
SLA_HOURS=4
TEAMS_WEBHOOK_URL=your_teams_webhook_url_here
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run pre-commit hooks
pre-commit run --all-files
```

## 📤 Export for Power BI

```bash
python scripts/export_for_powerbi.py
```

This creates `data/seeds/exports/specimens_latest.csv` ready for Power BI import.

## 🚨 Teams Alerts

The dashboard includes a "Trigger Teams Alert (Dry-Run)" button that:
- Shows the exact JSON payload in a collapsible panel
- Sends to Teams webhook if `TEAMS_WEBHOOK_URL` is configured

## 🧪 Test Data

### Interactive Demo Testing
For testing the interactive features, use the provided test data file:

**`test_lab_data.csv`** - Comprehensive lab data with intentional data quality issues
- **50 specimen records** across 5 days (Jan 15-19, 2024)
- **Multiple test types**: CBC, Chemistry Panel, Blood Culture, HIV Test, Urinalysis, Coagulation Panel, Stool Culture, Lipid Panel, Thyroid Function
- **4 departments**: Hematology, Chemistry, Microbiology, Immunology
- **Data quality issues** for testing validation rules:
  - Missing result values (6 records)
  - Mixed data types in result_value column
  - Various TAT ranges (1.4 to 72.0 hours)

### How to Use Test Data
1. **Download** `test_lab_data.csv` from the repository
2. **Upload to interactive demo** at the Data Quality tab
3. **Add validation rules** and run data quality checks
4. **View violations** and export results

### Alternative Download Methods
- **Direct download**: Click the file in GitHub and use "Raw" button
- **Download page**: Open `download_test_data.html` in your browser
- **Copy-paste**: Copy content and create new CSV file

## 📋 Data Quality

Run data quality checks:

```bash
python scripts/dq_check.py
```

This validates:
- Required columns
- Timestamp ordering
- No future dates
- Allowed status values

## 🎯 What-If Analysis

The dashboard includes a "What-If" panel for capacity planning:
- Add extra machines (0-3)
- Reduce failure rate (0-50%)
- See projected TAT and throughput improvements

## 📚 Documentation

- [Demo Script](docs/DEMO_SCRIPT.md) - 5-minute presentation guide
- [Architecture](docs/ARCHITECTURE.md) - System design and flows
- [Roadmap](docs/ROADMAP.md) - Feature backlog and development plan

## 🛠️ Development

### Code Quality
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **pre-commit** hooks for automated checks

### CI/CD
GitHub Actions runs on every push:
- Python 3.11 compatibility
- Pre-commit hooks
- Pytest with coverage
- Linting and formatting checks

## 📸 Screenshots

*[Screenshots will be added after first run]*

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and pre-commit hooks
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.
