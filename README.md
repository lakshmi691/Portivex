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
- **Dashboard & Getting Started Wizard**: 3-step setup progress tracker (`Customer account created` → `Portfolio creation` → `Holdings and market data`).
- **Portfolio Overview**: Live asset allocation donut chart, cash balances, and position holdings table showing instrument name, asset class, quantity, market price, market value, and allocation percentage per holding.
- **Trade Orders**: Execution tracking with filters for asset class, side (BUY/SELL), and status (Executed, Pending, Cancelled).
- **Support Tickets**: Support ticket submission and inquiry tracking with real-time status updates.
- **Account Settings**: Profile management, residential address, security settings, and notification preference toggles.

### Actor 2: Operations Analyst Workspace
- **Executive Dashboard**: Six key metric cards (Total Portfolios, Rebalancing Required, Awaiting Review, Exceptions, Total Trade Value, Estimated Fees), Portfolio Health donut chart showing Compliant / Needs Rebalancing / In Review / Exception breakdown, and Risk Profile Drift RMSE bar charts.
- **Rebalancing Queue**: Full-width interactive table listing all client portfolios with Risk Profile, Cash Balance, Current Drift, Trade Value, Estimated Fees, Post-Drift and Status columns. Supports filtering by Risk Profile, Status, and Drift threshold, free-text search, bulk batch proposal generation, and CSV export.
- **Rebalancing Workspace**: Side-by-side worklist and detailed portfolio analysis panel with current vs. target allocation comparisons, automated buy/sell trade recommendations, cash flow validation, fee calculations, and one-click proposal generation.
- **Proposals Pipeline**: KPI status cards (Total, Pending Review, Approved, Returned, Rejected, Simulated), searchable and filterable proposal registry, proposed trade breakdowns, 7-tier validation checklists, reviewer remarks, and lifecycle audit timeline.
- **History & Simulations**: Comprehensive simulation results, turnover analysis, and trade execution logs.

### Actor 3: Risk & Compliance Reviewer
- **Review Dashboard**: Proposal status breakdown with donut chart, pending review queue, and six operational review KPI cards.
- **Proposal Review Workspace**: Independent pre-trade and post-trade drift verification, proposed trade inspection, and 7-tier compliance policy validations covering allocation totals (100%), minimum trade size, cash buffer requirements, liquidity thresholds, restricted instrument lists, and market price freshness.
- **Decision Engine**: Approve, Reject, or Return for Changes actions with mandatory reviewer remarks and automatic blocking rule enforcement.
- **Audit Trail & Decision History**: Complete historical log of all regulatory review decisions with timestamps and actor traceability.

### Actor 4: System Administrator
- **Platform Dashboard**: System-wide KPI cards showing Total Users, Customers, Operations Analysts, Compliance Reviewers, and Administrators. Includes recent admin activity log and quick action shortcuts for Add User, Manage Rules, View Users, and Fee Schedule.
- **User Management**: Full user directory with role-based filtering tabs (All Users, Customers, Operations Analysts, Reviewers, Administrators), free-text search, and status filters. The **Add User** modal supports provisioning accounts for all four roles — Customer, Operations Analyst, Risk & Compliance Reviewer, and System Administrator — with the user table and dashboard KPI counts refreshing instantly upon creation.
- **System Configuration**: Configuration tables for Instruments, Asset Classes, Fee Schedules, Trading Rules, Regulatory Restrictions, and Model Target Allocations with live search and inline data display.

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
