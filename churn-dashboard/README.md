# Customer Churn Prediction Dashboard

A lightweight Python + FastAPI portfolio app for D2C brands to track customer inactivity and retention actions.

## Features
- SQLite database with customers, orders, and retention actions
- Risk scoring based on days since last purchase
- Dashboard UI with filtering, color-coded risk levels, and outreach logging
- CSV export for at-risk customers
- Dark theme frontend with vanilla HTML/CSS/JS

## Setup
1. Create a virtual environment:

```powershell
python -m venv venv
```

2. Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r backend\requirements.txt
```

4. Seed the database:

```powershell
python backend\seed.py
```

5. Run the app:

Option 1 - from the root folder:
```powershell
uvicorn main:app --reload
```

Option 2 - directly from the backend folder:
```powershell
uvicorn backend.main:app --reload
```

6. Open your browser at:

`http://127.0.0.1:8000`

## Project Structure

- `backend/` - FastAPI backend, database logic, and seeding
- `frontend/` - dashboard UI assets
- `backend/churn.db` - SQLite database file
- `README.md` - project documentation
