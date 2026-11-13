# PORTIVEX — Institutional Portfolio Rebalancing & Risk Management Platform

PORTIVEX is an institutional-grade portfolio rebalancing and compliance governance platform. It automates portfolio drift detection, computes optimal trade orders across multi-asset allocations, enforces 7-tier regulatory and business policy constraints, and manages approval workflows across four distinct actors.

---

## 1. System Architecture

```text
portfolio_rebalance_engine/
│
├── frontend/                   # Client-Side User Interface
│   ├── index.html              # Institutional platform SPA for all 4 actors
│   ├── style.css               # Dark navy & teal institutional styling
│   └── app.js                  # Frontend controllers, charts & API integrations
│
├── backend/                    # Python / FastAPI Backend Engine
│   ├── app.py                  # Core server, routing & authentication
│   ├── actors_api.py           # Workspaces for Customer, Analyst, Reviewer & Admin
│   ├── rebalance_engine.py     # Drift RMSE calculation & rebalance optimizer
│   ├── anomaly_injector.py     # Deterministic compliance anomaly generator
│   ├── validator.py            # 7-tier validation & reconciliation engine
│   └── config.py               # Deterministic seed (20261022) & parameters
│
├── database/                   # MySQL 8.0 Persistence Layer
│   ├── schema.sql              # Relational DDL schema with foreign key constraints
│   └── seed_data.sql           # Database initialization scripts
│
├── setup_mysql.py              # MySQL table initialization script
├── setup_default_employees.py  # Seeder for permanent default employee accounts
├── run_pipeline.py             # CLI batch rebalancing execution pipeline
└── test_complete_portivex_system.py # End-to-end integration test suite
```

---

## 2. Default Login Accounts & Role Redirection

All users log in through a single common login interface (`/`). The system authenticates credentials against the MySQL database (`app_user` table) using SHA-256 password hashing and automatically routes each user to their designated workspace:

| Role | Name | Email | Password | Assigned Dashboard |
| :--- | :--- | :--- | :--- | :--- |
| **System Administrator** | Admin | `admin@gmail.com` | `Admin123` | System Administrator Console |
| **Operations Analyst** | Operations Analyst | `operations@portivex.com` | `Ops123` | Operations Analyst Workspace |
| **Risk & Compliance Reviewer** | Risk & Compliance Reviewer | `risk@portivex.com` | `Risk123` | Risk & Compliance Review Queue |
| **Customer (Active)** | Jane Doe | `jane.doe@example.com` | `customer123` | Customer Portal (Live Portfolio) |
| **Customer (New / Unassigned)** | New Investor | `new.customer@portivex.com` | `Customer123` | Customer Portal (Getting Started) |

---

## 3. Core Features by Actor

### Actor 1: Customer Portal
- **Dashboard & Getting Started Wizard**: 3-step setup progress tracker (`Customer account created` $\rightarrow$ `Portfolio creation` $\rightarrow$ `Holdings and market data`).
- **Portfolio Overview**: Live asset allocation, cash balances, and position holdings.
- **Trade Orders**: Execution tracking with filters for asset class, side (BUY/SELL), and status.
- **Support Tickets**: Support ticket submission and inquiry tracking.
- **Account Settings**: Profile management, residential address, security, and notification preference toggles.

### Actor 2: Operations Analyst Workspace
- **Executive Dashboard**: Key metric cards (Total Portfolios, Rebalancing Required, Awaiting Review, Exceptions, Trade Value, Fees), Portfolio Health donut chart, and Risk Profile Drift RMSE bar charts.
- **Rebalancing Workspace**: Interactive worklist, current vs. target allocation comparisons, automated buy/sell recommendations, cash flow validation, fee calculations, and one-click proposal generation.
- **Proposals Pipeline**: KPI status cards, searchable proposal registry, proposed trade breakdowns, validation checklists, reviewer remarks, and lifecycle audit timeline.
- **History & Simulations**: Comprehensive simulation results, turnover analysis, and trade execution logs.

### Actor 3: Risk & Compliance Reviewer
- **Review Dashboard**: Proposal status donut breakdown, pending review queue, and operational review KPIs.
- **Proposal Review Workspace**: Independent pre-trade and post-trade drift verification, proposed trade inspection, and 7-tier compliance policy validations (allocation total 100%, minimum trade size, cash buffer, liquidity, restricted instruments, and price freshness).
- **Decision Engine**: Approve, Reject, or Return for Changes actions with mandatory reviewer remarks and blocking rule enforcement.
- **Audit Trail & Decision History**: Historical log of all regulatory review decisions and transitions.

### Actor 4: System Administrator
- **Platform Dashboard**: System-wide user distribution counts, active portfolio counts, market data records, and health status indicators.
- **User Management**: Create and manage users with role assignments (`Customer`, `Operations Analyst`, `Compliance Reviewer`, `System Administrator`).
- **System Configuration**: Configuration tables for Instruments, Asset Classes, Fee Schedules, Trading Rules, Regulatory Restrictions, and Model Target Allocations.
- **Data Management**: Deterministic synthetic dataset generator utilizing master seed `20261022`, data validation audit engine, and data export.

---

## 4. Setup & Running the Application

### Prerequisites
- Python 3.10+
- MySQL 8.0 Server running on `127.0.0.1:3306` (Database: `portfolio_db`)

### Step 1: Install Dependencies
```bash
pip install fastapi uvicorn pymysql pydantic
```

### Step 2: Initialize Database & Default Accounts
```bash
python setup_mysql.py
python setup_default_employees.py
```

### Step 3: Start the Backend Server
```bash
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser and navigate to: **`http://127.0.0.1:8000`**

### Step 4: Run the Full System Verification Suite
```bash
python test_complete_portivex_system.py
```
