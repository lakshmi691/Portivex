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
- **Portfolio Overview**: Live asset allocation donut chart, cash balances, and position holdings table with dynamically calculated allocation percentages per holding.
- **Trade Orders**: Execution tracking with filters for asset class, side (BUY/SELL), and status.
- **Support Tickets**: Support ticket submission and inquiry tracking.
- **Account Settings**: Profile management, residential address, security, and notification preference toggles.

### Actor 2: Operations Analyst Workspace
- **Executive Dashboard**: Key metric cards (Total Portfolios, Rebalancing Required, Awaiting Review, Exceptions, Trade Value, Fees), Portfolio Health donut chart, and Risk Profile Drift RMSE bar charts.
- **Rebalancing Queue**: Full-width interactive table with filters by Risk Profile, Status, and Drift. Supports bulk batch proposal generation and CSV export.
- **Rebalancing Workspace**: Interactive worklist, current vs. target allocation comparisons, automated buy/sell recommendations, cash flow validation, fee calculations, and one-click proposal generation.
- **Proposals Pipeline**: KPI status cards, searchable proposal registry, proposed trade breakdowns, validation checklists, reviewer remarks, and lifecycle audit timeline.
- **History & Simulations**: Comprehensive simulation results, turnover analysis, and trade execution logs.

### Actor 3: Risk & Compliance Reviewer
- **Review Dashboard**: Proposal status donut breakdown, pending review queue, and operational review KPIs.
- **Proposal Review Workspace**: Independent pre-trade and post-trade drift verification, proposed trade inspection, and 7-tier compliance policy validations (allocation total 100%, minimum trade size, cash buffer, liquidity, restricted instruments, and price freshness).
- **Decision Engine**: Approve, Reject, or Return for Changes actions with mandatory reviewer remarks and blocking rule enforcement.
- **Audit Trail & Decision History**: Historical log of all regulatory review decisions and transitions.

### Actor 4: System Administrator
- **Platform Dashboard**: Clean header with page title and subtitle only. System-wide user distribution KPI cards (Total Users, Customers, Operations Analysts, Compliance Reviewers, Administrators) and market data health status indicators.
- **Quick Actions Panel**: One-click shortcuts for Add User, Manage Rules, View Users, and Fee Schedule.
- **User Management**: Full user directory with role-based filtering tabs, search, and status filters. Create new users via the **+ Add User** modal which supports all four roles (`Customer`, `Operations Analyst`, `Compliance Reviewer`, `System Administrator`). Adding a user immediately refreshes the user table and dashboard KPI cards.
- **System Configuration**: Configuration tables for Instruments, Asset Classes, Fee Schedules, Trading Rules, Regulatory Restrictions, and Model Target Allocations.

> **Note**: The Data Management module (synthetic dataset generator, data import, data validation, and export) has been removed from the Administrator navigation as part of the final UI cleanup. The three remaining modules are Dashboard, User Management, and System Configuration.

---

## 4. UI & Bug Fixes Applied

The following improvements were applied to the frontend during development:

| Area | Fix Applied |
| :--- | :--- |
| **Admin Header** | Removed bell notification icon, date badge, and duplicate role/user card from the header strip. |
| **Add User Modal** | Expanded role dropdown to support all 4 roles. Button relabelled to `+ Add User`. On success, the user table and dashboard KPI cards refresh instantly without page reload. |
| **Customer Holdings Allocation** | Allocation (%) column now dynamically calculates `(market_value / portfolio_value) × 100` so active holdings never display `0.00%`. |
| **Rebalancing Queue Table** | Expanded to full-width layout (`display: block; width: 100%`) so the queue table uses the entire screen width. |
| **Top Exceptions Box** | Removed the static "Top Exceptions" sidebar box from the Operational Analyst Dashboard to clean up the layout. |
| **Data Management Nav Item** | Removed from Administrator sidebar navigation. The pane and all its sub-tabs were deleted entirely. |
| **JavaScript Syntax Error** | Fixed a stray orphaned HTML snippet outside function scope at line 3810 that was breaking all button interactions on page load. |

---

## 5. Setup & Running the Application

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
