# FarmHub — Microservice Monorepo Platform

FarmHub is a farm and livestock management platform built as a high-performance monorepo splitting domain write operations and read-only analytical aggregations into dedicated microservices.

---

## 🏗️ Architecture Overview

The system is structured as two independent services sharing a single PostgreSQL / SQLite database:

```
FarmHub/
├── core/                          # Django REST Framework (Writes & Domain Logic)
│   ├── config/                    # Settings, SimpleJWT auth, Spectacluar OpenAPI
│   ├── apps/
│   │   ├── accounts/              # Custom User model (SuperAdmin, Agent, Farmer roles)
│   │   ├── farms/                 # Farm CRUD & Agent assignments
│   │   ├── farmers/               # Farmer onboarding & profile management
│   │   ├── cattle/                # Cow registration & tag tracking
│   │   ├── activities/            # Vaccination, Health check & Birth logs
│   │   └── production/            # Daily milk production records
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
├── reporting/                     # FastAPI Service (Read-Only Analytical Aggregations)
│   ├── app/
│   │   ├── main.py                # FastAPI instance & CORS middleware
│   │   ├── config.py              # Pydantic Settings
│   │   ├── db.py                  # Async SQLAlchemy Engine & Session
│   │   ├── models.py              # Read-Only SQLAlchemy Models (mirroring Django tables)
│   │   ├── schemas.py             # Pydantic Response & Request Schemas
│   │   ├── auth.py                # JWT Interop with Django SimpleJWT
│   │   ├── dependencies.py        # Role-based access dependencies
│   │   └── routers/
│   │       └── reports.py         # Aggregated Farm, Farmer & System Summary endpoints
│   ├── tests/                     # Pytest + HTTPX AsyncClient test suite
│   ├── pytest.ini
│   ├── requirements.txt
│   └── .env.example
├── docker-compose.yml             # Local multi-container deployment
└── README.md                      # Comprehensive project documentation
```

---

## 🔐 Key Features & Role-Based Access Control (RBAC)

FarmHub enforces strict role-based data isolation across three user roles:

| Feature / Domain | SuperAdmin 👑 | Agent 🧑‍🌾 | Farmer 🐄 |
| :--- | :---: | :---: | :---: |
| **Agent Management** | Full CRUD | ❌ No Access | ❌ No Access |
| **Farm Management** | Full CRUD | View/Update Managed Farms | View Assigned Farm |
| **Farmer Onboarding** | Onboard Any Farm | Onboard Managed Farms | ❌ No Access |
| **Cow Enrollment** | Enroll Anywhere | Enroll on Managed Farms | Enroll Own Cows |
| **Activities Logging** | All Cows | Managed Farm Cows | Own Cows |
| **Milk Production** | All Cows | Managed Farm Cows | Own Cows |
| **Reports Summary** | Full System | ❌ No Access | ❌ No Access |
| **Farm Reports** | Any Farm | Managed Farm Only (404 for others) | ❌ No Access |
| **Farmer Reports** | Any Farmer | Managed Farmers Only (404 for others) | Own Profile Only |

---

## 🚀 Quickstart Guide

### Prerequisites
- Python 3.12+
- PostgreSQL or SQLite
- Virtual environment (`venv`)

### 1. Environment Configuration

#### Core Service (`core/.env`)
```env
SECRET_KEY=django-insecure-change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,testserver
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

SUPERADMIN_USERNAME=admin
SUPERADMIN_EMAIL=admin@farmhub.com
SUPERADMIN_PASSWORD=adminpassword123
```

#### Reporting Service (`reporting/.env`)
```env
DATABASE_URL=sqlite+aiosqlite:///../core/db.sqlite3
JWT_SECRET_KEY=django-insecure-change-me
JWT_ALGORITHM=HS256
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

> **Note**: `JWT_SECRET_KEY` in `reporting/.env` **must** match `SECRET_KEY` in `core/.env` for SimpleJWT token validation to succeed.

---

### 2. Local Setup & Execution

#### Option A: Running Services Manually

##### Step 1: Initialize Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

##### Step 2: Start Core Django Service (Port 8000)
```bash
cd core
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_superadmin
python manage.py runserver 0.0.0.0:8000
```

##### Step 3: Start Reporting FastAPI Service (Port 8001)
```bash
cd ../reporting
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

---

#### Option B: Running via Docker Compose

```bash
docker-compose up --build
```
This provisions:
- PostgreSQL database container on port `5432`
- Core Django service on `http://localhost:8000`
- Reporting FastAPI service on `http://localhost:8001`

---

## 📡 API Reference

### 🌐 Core Django API (`http://localhost:8000/api/`)

#### Authentication (`/api/auth/`)
- `POST /api/auth/login/` — Obtain JWT access and refresh token.
- `POST /api/auth/refresh/` — Refresh expired access token.
- `POST /api/auth/logout/` — Blacklist refresh token.

#### Agent Management (`/api/agents/`)
- `GET/POST /api/agents/` — List/create Agents (SuperAdmin only).
- `GET/PUT/PATCH/DELETE /api/agents/{id}/` — Manage specific Agent.

#### Farm Management (`/api/farms/`)
- `GET/POST /api/farms/` — List/create Farms.
- `GET/PUT/PATCH/DELETE /api/farms/{id}/` — Manage Farm details.

#### Farmer Onboarding (`/api/farmers/`)
- `GET/POST /api/farmers/` — Onboard new Farmer (creates User + FarmerProfile in atomic transaction).
- `GET/PUT/PATCH/DELETE /api/farmers/{id}/` — View/update Farmer profile.

#### Cow Enrollment (`/api/cows/`)
- `GET/POST /api/cows/` — List and enroll cows.
- `GET/PUT/PATCH/DELETE /api/cows/{id}/` — Manage cow details.

#### Activity Logging (`/api/cows/{cow_id}/activities/`)
- `GET/POST /api/cows/{cow_id}/activities/` — Log vaccination, health check, or birth activity.
- `GET/PATCH/DELETE /api/cows/{cow_id}/activities/{id}/` — Manage specific activity.

#### Daily Milk Production (`/api/cows/{cow_id}/milk-records/`)
- `GET/POST /api/cows/{cow_id}/milk-records/` — Record morning/evening milk production in liters.
- `GET/PATCH/DELETE /api/cows/{cow_id}/milk-records/{id}/` — Manage milk record.

---

### 📊 Reporting FastAPI (`http://localhost:8001/api/v1/`)

Interactive Swagger UI documentation is available at `http://localhost:8001/docs`.

#### Endpoints
- `GET /health` — Health check endpoint (`{"status": "ok"}`).
- `GET /api/v1/reports/farm/{farm_id}?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`
  - **Permission**: SuperAdmin or Managing Agent.
  - **Returns**: Farm metadata, total liters, record count, and per-cow breakdown.
- `GET /api/v1/reports/farmer/{farmer_id}?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`
  - **Permission**: SuperAdmin, Managing Agent, or Self Farmer.
  - **Returns**: Farmer metadata, farm name, total liters, record count, and per-cow breakdown.
- `GET /api/v1/reports/summary?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`
  - **Permission**: SuperAdmin only.
  - **Returns**: System-wide total liters, record count, and per-farm breakdown ordered by volume.

---

## 🧪 Running Automated Tests

### 1. Test Core Django Service
```bash
cd core
../venv/bin/python manage.py test
```
*Executes unit tests covering JWT auth, Agent CRUD, Farm CRUD, Farmer onboarding, Cow enrollment, Activity logging, and Milk production.*

### 2. Test Reporting FastAPI Service
```bash
cd reporting
../venv/bin/python -m pytest
```
*Executes async Pytest suite testing token decoding, RBAC authorization boundaries, 404 security hiding, and date range aggregation filtering.*
