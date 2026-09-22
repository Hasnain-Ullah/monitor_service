# 🚀 API Monitoring Service

A continuous API monitoring service that tracks health states, creates incidents, and sends alerts.

---

## 📋 Features

- ✅ Periodically checks API endpoints
- ✅ 4 health states: UP, DEGRADED, DOWN, RECOVERED
- ✅ Configurable rules for state transitions
- ✅ SQLite storage for checks and incidents
- ✅ Webhook alerts with deduplication
- ✅ Status summary output
- ✅ Report files (JSON + CSV)

---

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|---------|
| Python 3.8+ | Programming language |
| requests | Send HTTP requests |
| SQLite | Store checks and incidents |
| pyyaml | Read YAML config |
| pytest | Run automated tests |

---

## 📁 Project Structure
monitor_service/
│
├── app/
│ ├── init.py # Makes app a package
│ ├── main.py # Entry point - runs the monitoring loop
│ ├── config_loader.py # Reads configuration
│ ├── checker.py # Sends HTTP requests
│ ├── state_manager.py # Determines states
│ ├── database.py # SQLite storage
│ ├── alerts.py # Webhook alerts
│ ├── reporters.py # Status summary + reports
│ └── calculator.py # Percentile calculations
│
├── configs/
│ └── config.json # Sample configuration
│
├── tests/
│ ├── init.py
│ ├── test_state_manager.py # State transition tests
│ ├── test_checker.py # HTTP checker tests
│ └── test_database.py # Database tests
│
├── reports/ # Auto-generated reports
│
├── requirements.txt
├── README.md
└── .gitignore


---

## 🔧 Setup Instructions

Step 1: Clone or Create Project

```bash
mkdir monitor_service
cd monitor_service

Step 2: Create Virtual Environment
Window:
python -m venv venv
venv\Scripts\activate

Step 3: Install dependencies
pip install -r requirements.txt

Step 4: Start Task 1 API
Open a separate terminal and run:
bash
cd fastapi_project
venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Step 5: Run Monitoring Service
bash
cd monitor_service
venv\Scripts\activate

# Single check
python -m app.main -c configs/config.json --once

# Continuous monitoring
python -m app.main -c configs/config.json

⚙️ Configuration
The service reads a JSON configuration file. Here is a sample:

json
{
  "monitoring": {
    "default_interval": 30,
    "consecutive_failures_for_down": 3,
    "availability_threshold": 95.0,
    "latency_threshold_ms": 500,
    "recovery_successes": 2,
    "window_size": 20
  },
  "endpoints": [
    {
      "name": "Health Check",
      "url": "http://127.0.0.1:8000/health",
      "method": "GET",
      "interval": 30,
      "timeout": 5,
      "expected_status": 200,
      "latency_threshold_ms": 500
    }
  ]
}

📊 Health States
State	Meaning	When It Happens
UP	    =>API is operating normally	No errors
DEGRADED	=>API is responding but slow or unreliable	
DOWN	=>API is unavailable	3 consecutive failures
RECOVERED	=>API has returned to normal after being DOWN/DEGRADED	

🧪 Running Tests
bash
pytest tests/ -v

Expected Output:
tests/test_state_manager.py::test_initial_state_is_up PASSED
tests/test_state_manager.py::test_up_to_down_after_3_failures PASSED
tests/test_state_manager.py::test_down_to_recovered_to_up PASSED
...
============================= 13 passed in 2.34s =======================

Report Files
After running, the reports/ folder contains:
text
reports/
├── status_20260921_143000.json    # Timestamped JSON
├── status_20260921_143000.csv     # Timestamped CSV
├── status_latest.json              # Latest JSON
├── status_latest.csv               # Latest CSV
└── incidents.json                  # All incidents
🚨 Alerts
The service sends alerts only when state changes:

UP → DOWN: Send DOWN alert
UP → DEGRADED: Send DEGRADED alert
DOWN → RECOVERED: Send RECOVERED alert
No state change: No alert

Webhook Configuration
bash
python -m app.main -c configs/config.json --webhook https://hooks.slack.com/...