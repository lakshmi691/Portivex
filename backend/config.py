"""
BACKEND CONFIGURATION
Contains fixed settings, deterministic random seed, and dataset scales.
"""

from pathlib import Path

# Project paths
BASE_DIR = Path("C:/CandidateWorkspace/portfolio_rebalance_engine")
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
DATABASE_DIR = BASE_DIR / "database"
DOCS_DIR = BASE_DIR / "docs"
DATA_DIR = BASE_DIR / "data"

# Step 4 Requirement: Fixed master seed for 100% reproducibility
DEFAULT_SEED = 20261022

# Dataset Scales: Starter for fast testing, Full for complete benchmark volume
SCALE_CONFIGS = {
    "starter": {
        "num_investors": 20,
        "num_portfolios": 50,
        "num_instruments": 200,
        "num_trading_days": 30,
        "holdings_per_portfolio": 5,
    },
    "full": {
        "num_investors": 400,
        "num_portfolios": 1000,
        "num_instruments": 5000,
        "num_trading_days": 250,
        "holdings_per_portfolio": 10,
    }
}

# The 5 Canonical Asset Classes with annualized drift (mu) and volatility (sigma)
ASSET_CLASSES = {
    "EQUITY": {"mu": 0.085, "sigma": 0.180},
    "FIXED_INCOME": {"mu": 0.035, "sigma": 0.055},
    "COMMODITY": {"mu": 0.040, "sigma": 0.220},
    "REAL_ESTATE": {"mu": 0.060, "sigma": 0.140},
    "CASH_EQUIVALENT": {"mu": 0.020, "sigma": 0.005},
}

# Standard Investor Risk Profile Target Weight Allocations (Sums to 100%)
RISK_PROFILES = {
    "CONSERVATIVE": {
        "EQUITY": 0.20,
        "FIXED_INCOME": 0.60,
        "COMMODITY": 0.05,
        "REAL_ESTATE": 0.05,
        "CASH_EQUIVALENT": 0.10,
    },
    "MODERATE": {
        "EQUITY": 0.45,
        "FIXED_INCOME": 0.40,
        "COMMODITY": 0.05,
        "REAL_ESTATE": 0.05,
        "CASH_EQUIVALENT": 0.05,
    },
    "GROWTH": {
        "EQUITY": 0.65,
        "FIXED_INCOME": 0.20,
        "COMMODITY": 0.05,
        "REAL_ESTATE": 0.05,
        "CASH_EQUIVALENT": 0.05,
    },
    "AGGRESSIVE": {
        "EQUITY": 0.80,
        "FIXED_INCOME": 0.10,
        "COMMODITY": 0.05,
        "REAL_ESTATE": 0.03,
        "CASH_EQUIVALENT": 0.02,
    },
}

# Transaction Fee Schedules
FEE_SCHEDULES = [
    {"fee_schedule_id": "FEE-000001", "name": "RETAIL_FLAT", "fee_type": "FLAT", "flat_fee": 4.95, "bps_rate": 0.0, "min_fee": 4.95, "max_fee": 4.95},
    {"fee_schedule_id": "FEE-000002", "name": "INSTITUTIONAL_BPS", "fee_type": "BPS_NOTIONAL", "flat_fee": 0.0, "bps_rate": 0.0010, "min_fee": 1.0, "max_fee": 150.0},
    {"fee_schedule_id": "FEE-000003", "name": "TIERED_PREMIUM", "fee_type": "TIERED", "flat_fee": 1.50, "bps_rate": 0.0005, "min_fee": 1.50, "max_fee": 75.0},
]

# Policy Constraints
CONSTRAINTS = [
    {"constraint_id": "CST-000001", "constraint_name": "MIN_TRADE_SIZE_100", "constraint_type": "MIN_TRADE_SIZE", "min_usd": 100.0},
    {"constraint_id": "CST-000002", "constraint_name": "RESTRICTED_LIST", "constraint_type": "EXCLUDED_INSTRUMENT", "restricted_tickers": ["INS-000042"]},
    {"constraint_id": "CST-000003", "constraint_name": "NO_SHORT_SELLING", "constraint_type": "NO_SHORT_SELLING", "allow_short": False},
]
