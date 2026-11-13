"""
BACKEND DATA MODELS
Simple, clean dataclasses representing the 10 core financial entities.
"""

from dataclasses import dataclass
from typing import Optional


# 1. InvestorProfile: The person owning the investment accounts
@dataclass
class InvestorProfile:
    investor_id: str        # e.g. "INV-000001"
    full_name: str          # e.g. "Alexander Sterling"
    email: str              # e.g. "alexander.sterling@example.com"
    risk_tolerance: str     # "CONSERVATIVE", "MODERATE", "GROWTH", "AGGRESSIVE"
    tax_status: str         # "TAXABLE", "TAX_DEFERRED", "TAX_EXEMPT"
    onboarding_date: str    # "YYYY-MM-DD"
    kyc_status: str = "VERIFIED"
    created_at: str = "2025-01-02T08:00:00Z"


# 2. Portfolio: The specific account owned by an investor
@dataclass
class Portfolio:
    portfolio_id: str       # e.g. "PORT-INV-000001-01"
    investor_id: str        # Links to InvestorProfile.investor_id
    portfolio_type: str     # "INDIVIDUAL_TAXABLE", "ROTH_IRA", "TRADITIONAL_IRA", "TRUST"
    base_currency: str      # "USD"
    cash_balance: float     # Available uninvested cash in dollars
    fee_schedule_id: str    # Links to FeeSchedule.fee_schedule_id
    rebalance_threshold: float = 0.0500  # 5% drift threshold to trigger rebalancing
    status: str = "ACTIVE"
    created_at: str = "2025-01-02T08:30:00Z"


# 3. Instrument: The financial asset (Stock, Bond, Commodity, Real Estate, Cash)
@dataclass
class Instrument:
    instrument_id: str      # e.g. "INS-000001"
    symbol: str             # e.g. "SPY", "BND", "AAPL"
    name: str               # e.g. "SPDR S&P 500 ETF Trust"
    asset_class: str        # "EQUITY", "FIXED_INCOME", "COMMODITY", "REAL_ESTATE", "CASH_EQUIVALENT"
    sector: str = "BROAD_MARKET"
    liquidity_tier: str = "HIGH"
    lot_size: int = 1       # Trading lot size (usually 1 share)
    is_restricted: bool = False  # If True, trade is blocked by compliance policy
    is_active: bool = True


# 4. MarketPrice: Historical and current daily prices for an instrument
@dataclass
class MarketPrice:
    price_id: str           # e.g. "PRC-00000001"
    instrument_id: str      # Links to Instrument.instrument_id
    price_date: str         # "YYYY-MM-DD"
    close_price: float      # Daily closing price in USD
    bid_price: float        # Price buyers are willing to pay
    ask_price: float        # Price sellers are asking for
    volume: int             # Shares traded during the day
    is_stale_flag: bool = False  # Warning flag if price is older than 1 business day


# 5. TargetAllocation: Desired ideal weight percentage for an asset in a portfolio
@dataclass
class TargetAllocation:
    target_id: str          # e.g. "TGT-PORT-INV-000001-01-INS-000001"
    portfolio_id: str       # Links to Portfolio.portfolio_id
    instrument_id: str      # Links to Instrument.instrument_id
    target_weight: float    # Desired weight (0.0 to 1.0), must sum to 1.0000
    tolerance_band: float = 0.0500  # Allowable drift buffer (5%)
    effective_date: str = "2025-01-02"
    is_active: bool = True


# 6. Holding: Actual assets currently owned in the portfolio
@dataclass
class Holding:
    holding_id: str         # e.g. "HOLD-PORT-INV-000001-01-INS-000001"
    portfolio_id: str       # Links to Portfolio.portfolio_id
    instrument_id: str      # Links to Instrument.instrument_id
    quantity: float         # Number of shares held
    cost_basis_per_share: float # Average purchase price per share
    as_of_date: str         # Valuation date ("YYYY-MM-DD")
    last_updated_at: str = "2025-12-31T16:00:00Z"


# 7. FeeSchedule: Rules defining brokerage transaction costs
@dataclass
class FeeSchedule:
    fee_schedule_id: str    # e.g. "FEE-000001"
    name: str               # e.g. "RETAIL_FLAT"
    fee_type: str           # "FLAT", "BPS_NOTIONAL", "TIERED"
    flat_fee: float         # Dollar flat fee per trade
    bps_rate: float         # Basis points percentage fee (0.0010 = 10 bps)
    min_fee: float          # Minimum fee cap
    max_fee: Optional[float] = None  # Maximum fee ceiling


# 8. Constraint: Policy rules restricting trading
@dataclass
class Constraint:
    constraint_id: str      # e.g. "CST-000001"
    constraint_name: str    # e.g. "MIN_TRADE_SIZE_100"
    constraint_type: str    # "MIN_TRADE_SIZE", "EXCLUDED_INSTRUMENT", "NO_SHORT_SELLING"
    parameters_json: str    # JSON parameters of the rule
    is_mandatory: bool = True


# 9. PortfolioConstraint: Bridge table linking Portfolios to Constraints (Many-to-Many)
@dataclass
class PortfolioConstraint:
    bridge_id: str          # e.g. "PC-PORT-INV-000001-01-CST-000001"
    portfolio_id: str       # Links to Portfolio.portfolio_id
    constraint_id: str      # Links to Constraint.constraint_id
    is_active: bool = True
    created_at: str = "2025-01-02T09:00:00Z"


# 10. RebalanceProposal: The generated proposal with pre and post trade metrics
@dataclass
class RebalanceProposal:
    proposal_id: str        # e.g. "RB-2026-000001"
    portfolio_id: str       # Links to Portfolio.portfolio_id
    proposal_date: str      # "YYYY-MM-DD"
    pre_rebalance_value: float  # Value before rebalance (Holdings + Cash)
    post_rebalance_value: float # Value after rebalance (Pre-Value minus Fees)
    pre_drift_rmse: float   # Drift root-mean-square error before trades
    post_drift_rmse: float  # Drift root-mean-square error after simulated trades
    total_turnover: float   # Total dollar value traded
    estimated_fees: float   # Total brokerage fees incurred
    residual_cash: float    # Cash balance remaining after simulated trades
    status: str             # "DRAFT", "COMPLIANCE_APPROVED", "EXCEPTION_FLAGGED", "REJECTED"
    decision_code: str      # "APPROVED", "DRIFT_WITHIN_TOLERANCE", "REJECTED_WEIGHT_SUM"
    created_at: str = "2025-12-31T16:30:00Z"


# 11. Trade: Individual buy or sell orders recommended by a proposal
@dataclass
class Trade:
    trade_id: str           # e.g. "TRD-2026-000001"
    proposal_id: str        # Links to RebalanceProposal.proposal_id
    instrument_id: str      # Links to Instrument.instrument_id
    action: str             # "BUY", "SELL", "HOLD"
    quantity: float         # Number of shares to trade
    price: float            # Share price used for valuation
    notional: float         # Dollar value of trade (quantity * price)
    estimated_fee: float    # Fee calculated for this order
    compliance_status: str = "PASS"  # "PASS", "FAIL_RESTRICTED", "FAIL_OVERSELL"
    status: str = "PROPOSED"


# 12. ProposalEventLog: Immutable audit ledger tracking state transitions
@dataclass
class ProposalEventLog:
    event_id: str           # e.g. "EVT-00000001"
    proposal_id: str        # Links to RebalanceProposal.proposal_id
    from_state: str         # Prior state (e.g. "DRAFT")
    to_state: str           # New state (e.g. "COMPLIANCE_APPROVED")
    actor_role: str         # "SYSTEM", "OPERATIONS_ANALYST", "COMPLIANCE_REVIEWER"
    notes: Optional[str]    # Explanation or audit note
    occurred_at: str = "2025-12-31T16:35:00Z"
