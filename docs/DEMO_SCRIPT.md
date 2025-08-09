# LabOps Metrics Starter Kit - 5-Minute Demo Script

## Opening (30 seconds)
"Welcome to the LabOps Metrics Starter Kit demo. This is a comprehensive laboratory operations monitoring solution that generates synthetic data, provides real-time metrics, and enables proactive alerting. Let me show you how it works."

## Data Generation (1 minute)
"First, let's generate some realistic lab data. I'll run the synthetic data generator to create 3 days of specimen data with 1200 specimens per day."

```bash
python scripts/gen_synthetic_data.py --days 3 --per-day 1200
```

"This creates HIPAA-safe synthetic data with realistic timestamps, error patterns, and processing times. The data is automatically stored in SQLite and also saved as CSV for analysis."

## API Demonstration (1.5 minutes)
"Now let's start the FastAPI backend to see our metrics endpoints in action."

```bash
uvicorn app.main:app --reload
```

"Let me show you the API documentation at localhost:8000/docs. We have endpoints for:
- Turnaround time metrics with P50/P90/P99 percentiles
- Throughput analysis by hour and day
- Error rate breakdowns by machine and error code
- SLA breach monitoring with configurable thresholds

Let me test a quick endpoint:"

```bash
curl http://localhost:8000/api/v1/metrics/tat
```

"This returns real-time TAT metrics calculated from our synthetic data."

## Dashboard Walkthrough (2 minutes)
"Now for the main attraction - our Streamlit dashboard. Let me start it up:"

```bash
streamlit run app/dashboards/streamlit_app.py
```

"Here's our comprehensive dashboard with several key sections:

**KPI Tiles**: Real-time metrics showing TAT P90, today's throughput, error rates, and total specimens.

**Time Series Charts**: Interactive charts showing TAT trends and throughput over time. You can toggle between hourly and daily views.

**Data Breakdowns**: Pie charts and bar charts showing specimen distribution by assay type and machine.

**SLA Monitoring**: Critical section showing SLA breaches with a red alert badge. Notice the 'Trigger Teams Alert' button - this demonstrates our alerting capability."

*[Click the Teams Alert button]*

"Watch this - when I click the alert button, it generates a Teams webhook payload and shows it in this collapsible panel. In production, this would send an actual alert to your Teams channel."

**What-If Analysis**: "This is particularly powerful - you can simulate adding extra machines or reducing failure rates to see projected improvements in TAT and throughput."

## Data Quality & Export (30 seconds)
"Let me quickly show you our data quality engine:"

```bash
python scripts/dq_check.py data/seeds/synthetic_20241201.csv
```

"This validates our data against configurable rules and generates a visualization of any issues.

And for Power BI integration:"

```bash
python scripts/export_for_powerbi.py
```

"This exports consolidated CSV data ready for Power BI import with computed TAT and SLA fields."

## Closing (30 seconds)
"To summarize what we've built:
- HIPAA-safe synthetic data generation
- Real-time metrics API with FastAPI
- Interactive Streamlit dashboard with KPIs and alerts
- Data quality validation
- Power BI export capabilities
- Comprehensive test suite

The entire system is production-ready with proper error handling, logging, and configuration management. You can deploy this immediately and start monitoring your lab operations."

## Demo Tips
- Keep the terminal windows visible to show real-time data generation
- Have the dashboard open in a browser tab ready to switch to
- Prepare a few different date ranges to show filtering capabilities
- Mention that all code is tested and documented
- Emphasize the modular architecture for easy customization
