"""
BACKEND POLICY-CONSTRAINED REBALANCING ENGINE
Calculates drift, filters orders through policy constraints, and simulates post-trade states.
"""

import math
from typing import Dict, List, Optional

from .models import (
    Portfolio, Holding, TargetAllocation, MarketPrice,
    FeeSchedule, RebalanceProposal, Trade, ProposalEventLog
)


class RebalanceEngine:
    def __init__(
        self,
        portfolios: List[Portfolio],
        holdings: List[Holding],
        target_allocations: List[TargetAllocation],
        market_prices: List[MarketPrice],
        fee_schedules: List[FeeSchedule],
        valuation_date: str = "2025-12-31"
    ):
        self.portfolios = {p.portfolio_id: p for p in portfolios}
        self.fee_schedules = {f.fee_schedule_id: f for f in fee_schedules}
        self.valuation_date = valuation_date
        
        # Price lookup for valuation date
        self.prices: Dict[str, float] = {
            mp.instrument_id: mp.close_price 
            for mp in market_prices if mp.price_date == valuation_date
        }
        
        # Group holdings and targets by portfolio
        self.holdings_by_port: Dict[str, List[Holding]] = {}
        for h in holdings:
            self.holdings_by_port.setdefault(h.portfolio_id, []).append(h)
            
        self.targets_by_port: Dict[str, List[TargetAllocation]] = {}
        for t in target_allocations:
            self.targets_by_port.setdefault(t.portfolio_id, []).append(t)
            
        # Results containers
        self.proposals: List[RebalanceProposal] = []
        self.trades: List[Trade] = []
        self.event_logs: List[ProposalEventLog] = []

    def calculate_fee(self, fee_schedule: FeeSchedule, notional: float) -> float:
        """Calculate transaction fee based on fee schedule type (FLAT, BPS, or TIERED)"""
        if notional <= 0:
            return 0.0
            
        if fee_schedule.fee_type == "FLAT":
            fee = fee_schedule.flat_fee
        elif fee_schedule.fee_type == "BPS_NOTIONAL":
            fee = notional * fee_schedule.bps_rate
        elif fee_schedule.fee_type == "TIERED":
            fee = fee_schedule.flat_fee + (notional * fee_schedule.bps_rate)
        else:
            fee = 0.0
            
        fee = max(fee, fee_schedule.min_fee)
        if fee_schedule.max_fee:
            fee = min(fee, fee_schedule.max_fee)
        return round(fee, 2)

    def rebalance_portfolio(self, portfolio_id: str, seq: int) -> Optional[RebalanceProposal]:
        """Perform policy-constrained rebalancing for a single portfolio"""
        port = self.portfolios[portfolio_id]
        holdings = self.holdings_by_port.get(portfolio_id, [])
        targets = self.targets_by_port.get(portfolio_id, [])
        fee_schedule = self.fee_schedules[port.fee_schedule_id]
        
        # 1. Check if Target Weights sum to 100% (Exception Check)
        target_sum = sum(t.target_weight for t in targets)
        is_mismatch = abs(target_sum - 1.0000) > 0.0001
        
        # 2. Calculate current portfolio valuation
        holding_map = {h.instrument_id: h.quantity for h in holdings}
        instrument_ids = list(set(list(holding_map.keys()) + [t.instrument_id for t in targets]))
        
        current_values = {}
        for ins_id in instrument_ids:
            qty = holding_map.get(ins_id, 0.0)
            px = self.prices.get(ins_id, 100.0)
            current_values[ins_id] = qty * px
            
        total_holdings_value = sum(current_values.values())
        pre_total_wealth = total_holdings_value + port.cash_balance
        
        # 3. Calculate current weight and drift per instrument
        target_map = {t.instrument_id: t.target_weight for t in targets}
        current_weights = {ins_id: (current_values[ins_id] / pre_total_wealth) for ins_id in instrument_ids}
        drifts = {ins_id: (current_weights[ins_id] - target_map.get(ins_id, 0.0)) for ins_id in instrument_ids}
        
        # Pre-drift Root Mean Square Error (RMSE)
        pre_rmse = round(math.sqrt(sum(d**2 for d in drifts.values()) / len(drifts)), 6)
        
        proposal_id = f"RB-2026-{seq:06d}"
        
        # Handle Exception 1: Target Weight Mismatch
        if is_mismatch:
            proposal = RebalanceProposal(
                proposal_id=proposal_id,
                portfolio_id=portfolio_id,
                proposal_date=self.valuation_date,
                pre_rebalance_value=round(pre_total_wealth, 2),
                post_rebalance_value=round(pre_total_wealth, 2),
                pre_drift_rmse=pre_rmse,
                post_drift_rmse=pre_rmse,
                total_turnover=0.0,
                estimated_fees=0.0,
                residual_cash=round(port.cash_balance, 2),
                status="EXCEPTION_FLAGGED",
                decision_code="REJECTED_WEIGHT_SUM"
            )
            self._log_event(proposal_id, "NONE", "EXCEPTION_FLAGGED", "SYSTEM", f"Weights sum to {target_sum:.4f}")
            return proposal

        # 4. Generate policy-constrained trades (Sells first to raise cash, then Buys)
        proposed_trades = []
        trade_counter = len(self.trades) + 1
        simulated_quantities = dict(holding_map)
        simulated_cash = port.cash_balance
        total_turnover = 0.0
        total_fees = 0.0
        min_trade_usd = 100.0  # Policy Constraint: minimum order size
        
        # First Pass: SELLS
        for ins_id in instrument_ids:
            delta_val = (target_map.get(ins_id, 0.0) - current_weights[ins_id]) * pre_total_wealth
            px = self.prices.get(ins_id, 100.0)
            
            if delta_val < -min_trade_usd and px > 0:
                shares_to_sell = math.floor(abs(delta_val) / px)
                held_shares = simulated_quantities.get(ins_id, 0.0)
                actual_sell = min(shares_to_sell, held_shares)  # Policy: No Short Selling
                
                if actual_sell > 0:
                    notional = round(actual_sell * px, 2)
                    fee = self.calculate_fee(fee_schedule, notional)
                    
                    trade = Trade(
                        trade_id=f"TRD-2026-{trade_counter:06d}",
                        proposal_id=proposal_id,
                        instrument_id=ins_id,
                        action="SELL",
                        quantity=actual_sell,
                        price=px,
                        notional=notional,
                        estimated_fee=fee,
                        compliance_status="PASS"
                    )
                    proposed_trades.append(trade)
                    trade_counter += 1
                    
                    total_turnover += notional
                    total_fees += fee
                    simulated_quantities[ins_id] -= actual_sell
                    simulated_cash += (notional - fee)
                    
        # Second Pass: BUYS
        for ins_id in instrument_ids:
            delta_val = (target_map.get(ins_id, 0.0) - current_weights[ins_id]) * pre_total_wealth
            px = self.prices.get(ins_id, 100.0)
            
            if delta_val > min_trade_usd and px > 0:
                shares_to_buy = math.floor(delta_val / px)
                notional = round(shares_to_buy * px, 2)
                fee = self.calculate_fee(fee_schedule, notional)
                
                # Policy: Solvency Check (buys cannot exceed available cash)
                if (notional + fee) <= simulated_cash and shares_to_buy > 0:
                    trade = Trade(
                        trade_id=f"TRD-2026-{trade_counter:06d}",
                        proposal_id=proposal_id,
                        instrument_id=ins_id,
                        action="BUY",
                        quantity=shares_to_buy,
                        price=px,
                        notional=notional,
                        estimated_fee=fee,
                        compliance_status="PASS"
                    )
                    proposed_trades.append(trade)
                    trade_counter += 1
                    
                    total_turnover += notional
                    total_fees += fee
                    simulated_quantities[ins_id] = simulated_quantities.get(ins_id, 0.0) + shares_to_buy
                    simulated_cash -= (notional + fee)

        # 5. Post-Trade Simulation Verification
        post_holding_val = sum(simulated_quantities.get(ins_id, 0.0) * self.prices.get(ins_id, 100.0) for ins_id in instrument_ids)
        post_total_wealth = post_holding_val + simulated_cash
        
        # Post-drift RMSE
        post_drifts = [((simulated_quantities.get(ins_id, 0.0) * self.prices.get(ins_id, 100.0) / post_total_wealth) - target_map.get(ins_id, 0.0)) for ins_id in instrument_ids]
        post_rmse = round(math.sqrt(sum(d**2 for d in post_drifts) / len(post_drifts)), 6)
        
        proposal = RebalanceProposal(
            proposal_id=proposal_id,
            portfolio_id=portfolio_id,
            proposal_date=self.valuation_date,
            pre_rebalance_value=round(pre_total_wealth, 2),
            post_rebalance_value=round(post_total_wealth, 2),
            pre_drift_rmse=pre_rmse,
            post_drift_rmse=post_rmse,
            total_turnover=round(total_turnover, 2),
            estimated_fees=round(total_fees, 2),
            residual_cash=round(simulated_cash, 2),
            status="COMPLIANCE_APPROVED",
            decision_code="APPROVED"
        )
        
        self.trades.extend(proposed_trades)
        self._log_event(proposal_id, "NONE", "DRAFT", "SYSTEM", "Automated proposal generated")
        self._log_event(proposal_id, "DRAFT", "COMPLIANCE_APPROVED", "COMPLIANCE_REVIEWER", f"Approved {len(proposed_trades)} orders")
        return proposal

    def _log_event(self, proposal_id: str, from_state: str, to_state: str, actor: str, notes: str):
        evt_id = f"EVT-{len(self.event_logs) + 1:08d}"
        self.event_logs.append(ProposalEventLog(
            event_id=evt_id,
            proposal_id=proposal_id,
            from_state=from_state,
            to_state=to_state,
            actor_role=actor,
            notes=notes
        ))

    def run_all(self):
        """Execute rebalancing across all portfolios"""
        for seq, port_id in enumerate(self.portfolios.keys(), start=1):
            p = self.rebalance_portfolio(port_id, seq)
            if p:
                self.proposals.append(p)
