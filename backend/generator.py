"""
BACKEND SYNTHETIC DATA GENERATOR
Creates realistic, deterministic market prices, portfolios, holdings, and targets.
"""

import math
import numpy as np
from datetime import date, timedelta
from typing import List, Dict

from .config import (
    DEFAULT_SEED, SCALE_CONFIGS, ASSET_CLASSES,
    RISK_PROFILES, FEE_SCHEDULES, CONSTRAINTS
)
from .models import (
    InvestorProfile, FeeSchedule, Portfolio, Instrument,
    MarketPrice, TargetAllocation, Holding, Constraint, PortfolioConstraint
)


class DataGenerator:
    def __init__(self, seed: int = DEFAULT_SEED, scale: str = "starter"):
        self.seed = seed
        self.scale = scale
        self.config = SCALE_CONFIGS.get(scale, SCALE_CONFIGS["starter"])
        
        # Pinned random number generator for 100% determinism
        self.rng = np.random.default_rng(seed)
        
        # Data containers
        self.investors: List[InvestorProfile] = []
        self.fee_schedules: List[FeeSchedule] = []
        self.constraints: List[Constraint] = []
        self.instruments: List[Instrument] = []
        self.market_prices: List[MarketPrice] = []
        self.portfolios: List[Portfolio] = []
        self.portfolio_constraints: List[PortfolioConstraint] = []
        self.target_allocations: List[TargetAllocation] = []
        self.holdings: List[Holding] = []
        
        self.start_date = date(2025, 1, 2)
        self.valuation_date = date(2025, 12, 31)

    def generate_all(self):
        """Build data in strict topological order: Master Tables -> Dependent Tables"""
        self._generate_reference_tables()
        self._generate_investors()
        self._generate_instruments()
        self._generate_market_prices()
        self._generate_portfolios()
        self._generate_targets_and_holdings()

    def _generate_reference_tables(self):
        """Create FeeSchedules and Policy Constraints"""
        for f in FEE_SCHEDULES:
            self.fee_schedules.append(FeeSchedule(**f))
            
        for c in CONSTRAINTS:
            self.constraints.append(Constraint(
                constraint_id=c["constraint_id"],
                constraint_name=c["constraint_name"],
                constraint_type=c["constraint_type"],
                parameters_json=str(c)
            ))

    def _generate_investors(self):
        """Generate Investor profiles with deterministic names and risk appetites"""
        names = ["Alexander Sterling", "Sophia Vance", "Liam Mercer", "Emma Chen", 
                 "Noah Kowalski", "Olivia Patel", "Ethan Rodriguez", "Ava Kim",
                 "Mason Blackwood", "Isabella Sinclair", "Lucas Alvarez", "Mia Gupta"]
        risks = ["CONSERVATIVE", "MODERATE", "GROWTH", "AGGRESSIVE"]
        taxes = ["TAXABLE", "TAX_DEFERRED", "TAX_EXEMPT"]
        
        count = self.config["num_investors"]
        for i in range(1, count + 1):
            inv_id = f"INV-{i:06d}"
            name = names[(i - 1) % len(names)]
            email = f"investor{i:04d}@example-fund.test"
            risk = risks[(i - 1) % len(risks)]
            tax = taxes[(i - 1) % len(taxes)]
            
            self.investors.append(InvestorProfile(
                investor_id=inv_id,
                full_name=f"{name} {i}",
                email=email,
                risk_tolerance=risk,
                tax_status=tax,
                onboarding_date="2024-01-15"
            ))

    def _generate_instruments(self):
        """Generate assets across the 5 canonical asset classes"""
        num_instruments = self.config["num_instruments"]
        ac_list = list(ASSET_CLASSES.keys())
        
        # Primary benchmark assets
        benchmarks = [
            ("SPY", "S&P 500 ETF Trust", "EQUITY"),
            ("QQQ", "Invesco QQQ Trust", "EQUITY"),
            ("BND", "Total Bond Market ETF", "FIXED_INCOME"),
            ("TLT", "20+ Year Treasury Bond", "FIXED_INCOME"),
            ("GLD", "SPDR Gold Shares", "COMMODITY"),
            ("VNQ", "Vanguard Real Estate", "REAL_ESTATE"),
            ("BIL", "1-3 Month T-Bill ETF", "CASH_EQUIVALENT"),
        ]
        
        for idx, (sym, name, ac) in enumerate(benchmarks, start=1):
            if idx > num_instruments:
                break
            self.instruments.append(Instrument(
                instrument_id=f"INS-{idx:06d}",
                symbol=sym,
                name=name,
                asset_class=ac,
                sector="BROAD_MARKET"
            ))
            
        # Generate remaining instruments to meet scale
        for i in range(len(self.instruments) + 1, num_instruments + 1):
            ac = ac_list[(i - 1) % len(ac_list)]
            # Controlled restricted ticker for policy testing
            is_restricted = (i == 42 or i == 421)
            
            self.instruments.append(Instrument(
                instrument_id=f"INS-{i:06d}",
                symbol=f"{ac[:2]}{i:04d}",
                name=f"Synthetic {ac.title()} Fund #{i}",
                asset_class=ac,
                sector="DIVERSIFIED",
                is_restricted=is_restricted
            ))

    def _generate_market_prices(self):
        """Simulate daily prices using Geometric Brownian Motion over 250 trading days"""
        num_days = self.config["num_trading_days"]
        trading_dates = []
        cur = self.start_date
        while len(trading_dates) < num_days:
            if cur.weekday() < 5:  # Monday to Friday only
                trading_dates.append(cur)
            cur += timedelta(days=1)
        self.valuation_date = trading_dates[-1]
        
        dt = 1.0 / 252.0  # Daily time increment
        price_counter = 1
        
        for ins in self.instruments:
            params = ASSET_CLASSES[ins.asset_class]
            mu = params["mu"]
            sigma = params["sigma"]
            
            # Starting price around $100
            current_price = 100.0 + (int(ins.instrument_id[-4:]) % 50)
            
            # Daily normal random shocks
            shocks = self.rng.standard_normal(num_days)
            daily_returns = np.exp((mu - 0.5 * sigma**2) * dt + sigma * math.sqrt(dt) * shocks)
            
            for t, p_date in enumerate(trading_dates):
                current_price = current_price * daily_returns[t]
                close_p = round(float(current_price), 4)
                
                self.market_prices.append(MarketPrice(
                    price_id=f"PRC-{price_counter:08d}",
                    instrument_id=ins.instrument_id,
                    price_date=p_date.isoformat(),
                    close_price=close_p,
                    bid_price=round(close_p * 0.9995, 4),
                    ask_price=round(close_p * 1.0005, 4),
                    volume=int(self.rng.integers(50000, 1000000))
                ))
                price_counter += 1

    def _generate_portfolios(self):
        """Create Portfolios linked to Investors, FeeSchedules, and Constraints"""
        num_portfolios = self.config["num_portfolios"]
        types = ["INDIVIDUAL_TAXABLE", "ROTH_IRA", "TRADITIONAL_IRA", "TRUST"]
        
        for i in range(1, num_portfolios + 1):
            inv_idx = (i - 1) % len(self.investors)
            investor = self.investors[inv_idx]
            sub_seq = ((i - 1) // len(self.investors)) + 1
            port_id = f"PORT-{investor.investor_id}-{sub_seq:02d}"
            
            port = Portfolio(
                portfolio_id=port_id,
                investor_id=investor.investor_id,
                portfolio_type=types[(i - 1) % len(types)],
                base_currency="USD",
                cash_balance=round(float(self.rng.uniform(10000.0, 40000.0)), 2),
                fee_schedule_id=self.fee_schedules[(i - 1) % len(self.fee_schedules)].fee_schedule_id
            )
            self.portfolios.append(port)
            
            # Link portfolio to constraints in bridge table
            for c in self.constraints:
                self.portfolio_constraints.append(PortfolioConstraint(
                    bridge_id=f"PC-{port_id}-{c.constraint_id}",
                    portfolio_id=port_id,
                    constraint_id=c.constraint_id
                ))

    def _generate_targets_and_holdings(self):
        """Assign Target Allocations summing strictly to 1.0000, and generate holdings with organic drift"""
        latest_prices = {mp.instrument_id: mp.close_price for mp in self.market_prices if mp.price_date == self.valuation_date.isoformat()}
        
        # Group instruments by asset class
        grouped = {ac: [] for ac in ASSET_CLASSES}
        for ins in self.instruments:
            grouped[ins.asset_class].append(ins)
            
        for p_idx, port in enumerate(self.portfolios):
            inv = next(x for x in self.investors if x.investor_id == port.investor_id)
            model_weights = RISK_PROFILES[inv.risk_tolerance]
            
            # Select 1 representative instrument per asset class
            chosen_assets = []
            for ac, weight in model_weights.items():
                pool = grouped[ac]
                chosen = pool[(p_idx + len(chosen_assets)) % len(pool)]
                chosen_assets.append((chosen, weight))
                
            # Create Target Allocations (strictly summing to 1.0000)
            for ins, target_w in chosen_assets:
                self.target_allocations.append(TargetAllocation(
                    target_id=f"TGT-{port.portfolio_id}-{ins.instrument_id}",
                    portfolio_id=port.portfolio_id,
                    instrument_id=ins.instrument_id,
                    target_weight=round(target_w, 4)
                ))
                
                # Create Holding with organic drift (some gained value, some lost)
                px = latest_prices.get(ins.instrument_id, 100.0)
                ideal_dollars = 100000.0 * target_w
                drift_factor = 0.85 + (float((p_idx * 5 + int(ins.instrument_id[-2:])) % 30) / 100.0)
                actual_dollars = ideal_dollars * drift_factor
                shares = max(1.0, math.floor(actual_dollars / px))
                
                self.holdings.append(Holding(
                    holding_id=f"HOLD-{port.portfolio_id}-{ins.instrument_id}",
                    portfolio_id=port.portfolio_id,
                    instrument_id=ins.instrument_id,
                    quantity=float(shares),
                    cost_basis_per_share=round(px * float(self.rng.uniform(0.9, 1.1)), 2),
                    as_of_date=self.valuation_date.isoformat()
                ))
