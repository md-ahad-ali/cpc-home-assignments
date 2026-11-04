# Flask + MySQL Intro App

A simple Flask application that connects to MySQL and outputs data through a REST API. Built as a learning exercise following the [Flask quickstart guide](https://flask.palletsprojects.com/en/stable/quickstart/).

This app reuses the **same database schema as the main `backend/` (Eco Pulse) project** — `users`, `buildings`, `rooms`, `energy_logs` — but reads it with Flask + PyMySQL instead of FastAPI + SQLAlchemy, to practice the Flask/MySQL workflow against real project data.

## Author

- **Name:** Ha Vu (hachan140)
- **Course:** Digital Transformation, Semester 1 — Python

## Tech Stack

- **Framework:** Flask
- **Database:** MySQL (via PyMySQL)
- **Config:** python-dotenv / `.env` file

## Project Structure

```
flask-mysql-intro/
├── app.py            # Flask app and routes
├── db.py             # MySQL connection helper
├── sql/schema.sql    # Database schema (same as backend/sql/schema.sql — ecopulse db)
├── requirements.txt
├── .env.example
└── README.md
```

## Database Schema (`ecopulse`)

Identical to [`backend/sql/schema.sql`](../backend/sql/schema.sql):

- `users` — id, username, password_hash, role (`admin` / `building_manager` / `occupant`)
- `buildings` — id, user_id (owner/manager), name, area_sqm
- `rooms` — id, building_id, occupant_id, room_name
- `energy_logs` — id, room_id, timestamp, energy_consumed_kwh, indoor_temp

## 1. Requirements

- Python 3.9+
- MySQL Server running locally (the same instance/database used by `backend/`, or your own copy)

## 2. Set Up a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Create the Database

If you already have the `ecopulse` database from `backend/` running, you can skip this — just point `.env` at it. Otherwise, create it from the schema (and optionally load `backend/sql/data.sql` for sample rows):

```bash
mysql -u root -p < sql/schema.sql
mysql -u root -p < ../backend/sql/data.sql
```

## 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your MySQL credentials (defaults match `backend/config.py`'s default `DATABASE_URL`):

```bash
cp .env.example .env
```

## 5. Run the App

```bash
python app.py
```

The app runs at `http://127.0.0.1:5000`.

## 6. Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Health check / welcome message |
| `/users` | GET | List all users (id, username, role) |
| `/buildings` | GET | List all buildings |
| `/buildings/<id>/rooms` | GET | List rooms in a building |
| `/rooms/<id>/energy-logs` | GET | Latest 100 energy log entries for a room |

### Example

```bash
curl http://127.0.0.1:5000/buildings
```

```json
[
  {"id": 1, "user_id": 1, "name": "Campus Building A", "area_sqm": 800.0},
  {"id": 2, "user_id": 1, "name": "Campus Building B", "area_sqm": 900.0}
]
```

```bash
curl http://127.0.0.1:5000/rooms/1/energy-logs
```

```json
[
  {"id": 1, "room_id": 1, "timestamp": "2026-09-01T00:00:00", "energy_consumed_kwh": 0.21, "indoor_temp": 20.4}
]
```

## Repository

Project source: <ADD_YOUR_GITHUB_REPO_LINK_HERE>
