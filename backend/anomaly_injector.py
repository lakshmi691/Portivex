"""
BACKEND ANOMALY INJECTOR & GROUND TRUTH REGISTRY
Injects the 5 required negative scenarios and writes an isolated ground truth catalog.
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any

from .models import TargetAllocation, Trade, MarketPrice, RebalanceProposal, Instrument


class AnomalyInjector:
    def __init__(
        self,
        target_allocations: List[TargetAllocation],
        trades: List[Trade],
        proposals: List[RebalanceProposal],
        market_prices: List[MarketPrice],
        instruments: List[Instrument],
        valuation_date: str = "2025-12-31"
    ):
        self.target_allocations = target_allocations
        self.trades = trades
        self.proposals = proposals
        self.market_prices = market_prices
        self.instruments = instruments
        self.valuation_date = valuation_date
        self.ground_truth: List[Dict[str, Any]] = []

    def inject_all(self):
        """Inject all 5 required edge cases in a deterministic, controlled fashion"""
        self._inject_anomaly_1_target_weight_mismatch()
        self._inject_anomaly_2_oversell_violation()
        self._inject_anomaly_3_excluded_instrument()
        self._inject_anomaly_4_omitted_fees()
        self._inject_anomaly_5_unflagged_stale_price()

    def _inject_anomaly_1_target_weight_mismatch(self):
        """Case 1: Portfolio target weights fail to sum to 100% (sums to 1.08)"""
        target_port_id = "PORT-INV-000002-01"
        matched = [t for t in self.target_allocations if t.portfolio_id == target_port_id]
        if matched:
            matched[0].target_weight = round(matched[0].target_weight + 0.0800, 4)
            
            # Flag proposal
            prop = next((p for p in self.proposals if p.portfolio_id == target_port_id), None)
            if prop:
                prop.status = "EXCEPTION_FLAGGED"
                prop.decision_code = "REJECTED_WEIGHT_SUM"
                
            self.ground_truth.append({
                "anomaly_id": "ANOM-001",
                "issue_type": "TARGET_WEIGHT_MISMATCH",
                "entity_type": "TargetAllocation",
                "entity_id": target_port_id,
                "description": f"Target weights sum to {sum(t.target_weight for t in matched):.4f} (exceeds 100%)",
                "expected_decision": "REJECTED_WEIGHT_SUM",
                "expected_status": "EXCEPTION_FLAGGED"
            })

    def _inject_anomaly_2_oversell_violation(self):
        """Case 2: Trade exceeds holding quantity (Oversell)"""
        sell_trade = next((t for t in self.trades if t.action == "SELL"), None)
        if sell_trade:
            sell_trade.quantity += 500.0  # Force oversell
            sell_trade.notional = round(sell_trade.quantity * sell_trade.price, 2)
            sell_trade.compliance_status = "FAIL_OVERSELL"
            
            self.ground_truth.append({
                "anomaly_id": "ANOM-002",
                "issue_type": "OVERSELL_VIOLATION",
                "entity_type": "Trade",
                "entity_id": sell_trade.trade_id,
                "description": f"Sell quantity {sell_trade.quantity} exceeds held position",
                "expected_decision": "REJECTED_OVERSOLD",
                "expected_status": "FAIL_OVERSELL"
            })

    def _inject_anomaly_3_excluded_instrument(self):
        """Case 3: Excluded/restricted instrument recommended for trading"""
        restricted_ins = next((i.instrument_id for i in self.instruments if i.is_restricted), "INS-000042")
        buy_trade = next((t for t in self.trades if t.action == "BUY"), None)
        if buy_trade:
            buy_trade.instrument_id = restricted_ins
            buy_trade.compliance_status = "FAIL_RESTRICTED"
            
            self.ground_truth.append({
                "anomaly_id": "ANOM-003",
                "issue_type": "EXCLUDED_INSTRUMENT_RECOMMENDED",
                "entity_type": "Trade",
                "entity_id": buy_trade.trade_id,
                "description": f"Recommended BUY order for restricted ticker {restricted_ins}",
                "expected_decision": "REJECTED_EXCLUDED_ASSET",
                "expected_status": "FAIL_RESTRICTED"
            })

    def _inject_anomaly_4_omitted_fees(self):
        """Case 4: Brokerage transaction fee omitted on fee-applicable account"""
        trade = next((t for t in self.trades if t.notional > 500.0 and t.compliance_status == "PASS"), None)
        if trade:
            trade.estimated_fee = 0.00  # Zero out fee
            
            self.ground_truth.append({
                "anomaly_id": "ANOM-004",
                "issue_type": "OMITTED_TRANSACTION_FEE",
                "entity_type": "Trade",
                "entity_id": trade.trade_id,
                "description": f"Transaction fee omitted ($0.00) on trade notional ${trade.notional}",
                "expected_decision": "RECONCILIATION_FAILURE",
                "expected_status": "FEE_CALCULATION_OMISSION"
            })

    def _inject_anomaly_5_unflagged_stale_price(self):
        """Case 5: Stale market price used without warning flag"""
        px = next((p for p in self.market_prices if p.price_date == self.valuation_date), None)
        if px:
            px.price_date = "2025-12-24"  # 7 days old
            px.is_stale_flag = False      # Intentionally unflagged
            
            self.ground_truth.append({
                "anomaly_id": "ANOM-005",
                "issue_type": "UNFLAGGED_STALE_PRICE",
                "entity_type": "MarketPrice",
                "entity_id": px.price_id,
                "description": f"Price date {px.price_date} is 7 days stale but is_stale_flag is False",
                "expected_decision": "MARKET_DATA_REJECTION",
                "expected_status": "STALE_PRICE_UNFLAGGED"
            })

    def export_ground_truth(self, json_path: Path, csv_path: Path):
        """Export ground truth catalog separately to prevent label leakage"""
        # Save JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.ground_truth, f, indent=2)
            
        # Save CSV
        fields = ["anomaly_id", "issue_type", "entity_type", "entity_id", "description", "expected_decision", "expected_status"]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(self.ground_truth)
