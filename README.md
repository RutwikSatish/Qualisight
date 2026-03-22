🚀 QualiSight – Quality KPI & CAPA Intelligence Tool
📌 Overview
QualiSight is an interactive Streamlit-based quality engineering tool designed for medical device and regulated manufacturing environments.
It transforms raw quality data — including complaints, non-conformances, CAPA, supplier defects, and batch release records — into actionable KPIs, risk insights, and decision-support outputs.
🎯 Problem Statement
In many manufacturing environments, quality data is:
fragmented across systems (complaints, CAPA, supplier logs)
analyzed manually using Excel
reactive instead of predictive
This leads to:
recurring defects
delayed CAPA closures
supplier performance issues
batch release risks (potential stop-ship scenarios)
💡 Solution
QualiSight provides a centralized quality intelligence interface that:
consolidates multiple quality data sources
automates KPI calculation
identifies recurring issues using Pareto analysis
flags high-risk suppliers and batches
generates actionable insights for quality teams
⚙️ Key Features
📊 KPI Dashboard
Complaint count
CAPA closure rate
Repeat non-conformance rate
Supplier PPM (defect rate)
Batch release turnaround time
DHR completeness rate
Overdue CAPA rate
📈 Trends & Pareto Analysis
Defect category Pareto charts
Monthly complaint and NCM trends
Root cause concentration analysis
🏭 Supplier Quality Intelligence
Supplier risk scoring
PPM calculation
SCAR (corrective action) indicators
Supplier ranking based on defect and response metrics
🧾 Batch Release Risk Monitoring
DHR completeness validation
Deviation tracking
Approval delay detection
High-risk batch identification (stop-ship indicators)
🧠 Decision-Support Insights
The tool converts raw data into actionable recommendations, such as:
initiating supplier corrective actions
escalating overdue CAPAs
reviewing recurring defect root causes
flagging high-risk batches for release hold
🔍 Interactive Filtering
Users can filter analysis by:
product
production line
supplier
date range
🧪 Sample Data
The project includes realistic datasets simulating a regulated manufacturing environment:
complaints (RMA)
non-conformance (NCM)
CAPA tracking
supplier quality
batch release records
🖥️ How to Run Locally
# Clone repo
git clone https://github.com/YOUR-USERNAME/qualisight.git
cd qualisight

# Create environment
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Run app
streamlit run app.py
🌐 Live Demo
👉 (Add your Streamlit link here after deployment)
🛠️ Tech Stack
Python
Streamlit
Pandas
NumPy
Matplotlib
🧠 Key Concepts Applied
Root Cause Analysis (5 Why, Fishbone)
CAPA Management
Non-Conformance Tracking
Supplier Quality Engineering
Pareto Analysis (80/20 principle)
Trend Analysis
Risk Scoring Logic
GMP / Quality System Thinking
📈 Business Impact
This tool enables:
faster identification of quality issues
improved CAPA closure effectiveness
better supplier performance monitoring
reduced risk of defective batch release
data-driven continuous improvement
👤 Author
Rutwik Satish
MS Engineering Management – Northeastern University
⭐ Why This Project Matters
This project demonstrates:
real-world quality engineering thinking
ability to translate data into decisions
understanding of regulated manufacturing workflows
practical application of continuous improvement
