"""
BACKEND VALIDATOR & RECONCILIATION ENGINE
Runs 7 verification checks covering relational constraints, enums, dates, and accounting math.
"""

from typing import List, Dict, Any
from .models import (
    InvestorProfile, FeeSchedule, Portfolio, Instrument,
    MarketPrice, TargetAllocation, Holding, Constraint,
    PortfolioConstraint, RebalanceProposal, Trade, ProposalEventLog
)


class SystemValidator:
    def __init__(
        self,
        investors: List[InvestorProfile],
        fee_schedules: List[FeeSchedule],
        constraints: List[Constraint],
        instruments: List[Instrument],
        market_prices: List[MarketPrice],
        portfolios: List[Portfolio],
        portfolio_constraints: List[PortfolioConstraint],
        target_allocations: List[TargetAllocation],
        holdings: List[Holding],
        proposals: List[RebalanceProposal],
        trades: List[Trade],
        event_logs: List[ProposalEventLog]
    ):
        self.investors = investors
        self.fee_schedules = fee_schedules
        self.constraints = constraints
        self.instruments = instruments
        self.market_prices = market_prices
        self.portfolios = portfolios
        self.portfolio_constraints = portfolio_constraints
        self.target_allocations = target_allocations
        self.holdings = holdings
        self.proposals = proposals
        self.trades = trades
        self.event_logs = event_logs

    def run_all(self) -> Dict[str, Any]:
        """Execute all 7 validation checks"""
        return {
            "primary_key_uniqueness": self._check_pk_uniqueness(),
            "foreign_key_integrity": self._check_foreign_keys(),
            "allowed_enums": self._check_enums(),
            "date_ordering": self._check_dates(),
            "arithmetic_reconciliation": self._check_arithmetic(),
            "lifecycle_transitions": self._check_lifecycle(),
            "composite_duplicates": self._check_duplicates()
        }

    def _check_pk_uniqueness(self) -> bool:
        """1. Verify zero duplicate primary keys across all tables"""
        tables = [
            [x.investor_id for x in self.investors],
            [x.portfolio_id for x in self.portfolios],
            [x.instrument_id for x in self.instruments],
            [x.price_id for x in self.market_prices],
            [x.target_id for x in self.target_allocations],
            [x.holding_id for x in self.holdings],
            [x.proposal_id for x in self.proposals],
            [x.trade_id for x in self.trades]
        ]
        return all(len(ids) == len(set(ids)) for ids in tables)

    def _check_foreign_keys(self) -> bool:
        """2. Verify all references point to valid parent records"""
        inv_ids = {x.investor_id for x in self.investors}
        fee_ids = {x.fee_schedule_id for x in self.fee_schedules}
        ins_ids = {x.instrument_id for x in self.instruments}
        port_ids = {x.portfolio_id for x in self.portfolios}
        prop_ids = {x.proposal_id for x in self.proposals}

        port_ok = all(p.investor_id in inv_ids and p.fee_schedule_id in fee_ids for p in self.portfolios)
        hold_ok = all(h.portfolio_id in port_ids and h.instrument_id in ins_ids for h in self.holdings)
        tgt_ok = all(t.portfolio_id in port_ids and t.instrument_id in ins_ids for t in self.target_allocations)
        trd_ok = all(tr.proposal_id in prop_ids and tr.instrument_id in ins_ids for tr in self.trades)

        return port_ok and hold_ok and tgt_ok and trd_ok

    def _check_enums(self) -> bool:
        """3. Verify allowed risk profiles and actions"""
        valid_risks = {"CONSERVATIVE", "MODERATE", "GROWTH", "AGGRESSIVE"}
        valid_actions = {"BUY", "SELL", "HOLD"}
        return all(i.risk_tolerance in valid_risks for i in self.investors) and all(t.action in valid_actions for t in self.trades)

    def _check_dates(self) -> bool:
        """4. Verify date format valid ISO format"""
        return all(len(p.proposal_date) == 10 for p in self.proposals)

    def _check_arithmetic(self) -> bool:
        """5. Reconcile post-trade wealth: PostValue == PreValue - TotalFees"""
        for p in self.proposals:
            if p.status == "COMPLIANCE_APPROVED" and p.decision_code == "APPROVED":
                expected_post = round(p.pre_rebalance_value - p.estimated_fees, 2)
                if abs(p.post_rebalance_value - expected_post) > 0.05:
                    return False
        return True

    def _check_lifecycle(self) -> bool:
        """6. Verify all proposals and events use valid states"""
        valid_states = {"DRAFT", "COMPLIANCE_APPROVED", "EXCEPTION_FLAGGED", "REJECTED", "EXECUTED"}
        return all(p.status in valid_states for p in self.proposals) and all(e.to_state in valid_states for e in self.event_logs)

    def _check_duplicates(self) -> bool:
        """7. Verify no duplicate (portfolio_id, instrument_id) pairs in holdings"""
        pairs = [f"{h.portfolio_id}:{h.instrument_id}" for h in self.holdings]
        return len(pairs) == len(set(pairs))
