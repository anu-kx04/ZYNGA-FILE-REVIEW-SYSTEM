Author: Anushka Singh
Repository: ZYNGA-FILE-REVIEW-SYSTEM

📌 Overview

Keystone is a real-time Command Center for Engineering Design Reviews (EDRs).
It eliminates the chaos of scattered Google Docs, Slack messages, and email threads by automatically tracking, prioritizing, and visualizing design review documents directly from Google Drive.

The system is designed to be zero-friction:

Architects continue working in Google Docs

Managers gain full visibility through a centralized dashboard

No manual updates. No Jira overhead. No lost reviews.

🚨 Problem Statement

In fast-paced engineering organizations, design reviews are essential — yet painful to manage.

Common Issues:

Lost Links: Review requests buried in Slack or email threads

No Visibility: Managers can’t see which documents are Pending, In Review, or Approved

Stagnation: Critical designs remain unreviewed for days or weeks

Context Switching: Architects dislike updating Jira or spreadsheets

This leads to missed SLAs, delayed launches, and review bottlenecks.

💡 Solution

Keystone acts as an intelligent layer over Google Drive, automatically syncing document metadata and surfacing review priorities in a single dashboard.

Key Principles:

No behavior change for architects

Automatic discovery and tracking

Clear prioritization using data, not guesswork

🧠 Core Features
1️⃣ Auto-Discovery (Zero Manual Entry)

A background sync service continuously monitors Google Drive for new or updated design documents.

No form submissions

No manual tracking

No missed files

2️⃣ Priority Engine (Urgency Scoring)

Keystone doesn’t just list documents — it ranks them.

Priority Formula:

Priority Score = (Days Since Creation) + (Days Since Last Edit)


Visual Status Indicators:

🔴 CRITICAL (Score > 10) → Immediate attention required

🟡 HIGH (Score 5–10) → Approaching SLA breach

🟢 NORMAL (Score < 5) → On track

This ensures important reviews never get buried.

3️⃣ Dual-Interface Experience
👩‍💻 Architects

Continue working only in Google Docs

No new tools or workflows to learn

📊 Managers & Leads

Centralized Keystone Dashboard

Real-time visibility into review status and bottlenecks

4️⃣ Bi-Directional Sync

Google Drive → Dashboard
Newly created or updated documents appear automatically

Dashboard → Database
Status changes (Approved / Needs Changes) are instantly synced back

5️⃣ Operational Analytics

Queue Health: Pending vs Completed reviews

Stagnation Timeline: Identify stale reviews visually

Workload Distribution: Detect overloaded architects early

🏗️ System Architecture
![Dashboard Preview](assets/image.png)

🛠️ Tech Stack
Layer	Technology
Frontend	Streamlit (Python)
Backend	Python 3.10+
Database	Google Sheets
APIs	Google Drive API v3, Google Sheets API v4
Analytics	Plotly Express
Scheduling	APScheduler
⚙️ Installation & Setup
🔹 Prerequisites

Python 3.8+

Google Cloud Project

Enabled Drive API and Sheets API

🔹 Clone Repository
git clone https://github.com/anu-kx04/ZYNGA-FILE-REVIEW-SYSTEM.git
cd ZYNGA-FILE-REVIEW-SYSTEM

🔹 Environment Setup
python -m venv venv


Activate virtual environment

Windows:

.\venv\Scripts\activate


Mac / Linux:

source venv/bin/activate


Install dependencies:

pip install -r requirements.txt

🔹 Configuration

Place your Google Cloud credentials file:

credentials.json


Create config.json in the root directory:

{
  "google": {
    "sheet_id": "YOUR_GOOGLE_SHEET_ID"
  },
  "sync": {
    "interval_minutes": 15
  }
}

🔹 Run the System

You will need two terminal windows.

Terminal 1 – Backend Sync Daemon
python sync_daemon.py


Continuously scans Google Drive and updates metadata.

Terminal 2 – Dashboard
streamlit run app.py


Dashboard opens at:

http://localhost:8501

📸 Dashboard Highlights

Priority Queue: Auto-sorted list with critical reviews highlighted

Analytics Tab: Review stagnation and workload distribution

Real-Time Updates: No manual refresh required

🤝 Contributing

Contributions are welcome.

Fork the repository

Create a feature branch

git checkout -b feature/YourFeature


Commit changes

git commit -m "Add YourFeature"


Push and open a Pull Request

👤 Author

Anushka Singh
Software Engineering | Backend Systems | Automation & Dashboards