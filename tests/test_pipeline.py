"""
TEST SUITE: RECONCILIATION & INTEGRITY CHECKS
"""

import pytest
from backend.config import DEFAULT_SEED
from backend.generator import DataGenerator
from backend.rebalance_engine import RebalanceEngine
from backend.anomaly_injector import AnomalyInjector
from backend.validator import SystemValidator


@pytest.fixture(scope="module")
def system_state():
    gen = DataGenerator(seed=DEFAULT_SEED, scale="starter")
    gen.generate_all()

    engine = RebalanceEngine(
        portfolios=gen.portfolios,
        holdings=gen.holdings,
        target_allocations=gen.target_allocations,
        market_prices=gen.market_prices,
        fee_schedules=gen.fee_schedules,
        valuation_date=gen.valuation_date.isoformat()
    )
    engine.run_all()

    injector = AnomalyInjector(
        target_allocations=gen.target_allocations,
        trades=engine.trades,
        proposals=engine.proposals,
        market_prices=gen.market_prices,
        instruments=gen.instruments,
        valuation_date=gen.valuation_date.isoformat()
    )
    injector.inject_all()

    validator = SystemValidator(
        investors=gen.investors,
        fee_schedules=gen.fee_schedules,
        constraints=gen.constraints,
        instruments=gen.instruments,
        market_prices=gen.market_prices,
        portfolios=gen.portfolios,
        portfolio_constraints=gen.portfolio_constraints,
        target_allocations=gen.target_allocations,
        holdings=gen.holdings,
        proposals=engine.proposals,
        trades=engine.trades,
        event_logs=engine.event_logs
    )

    return {"gen": gen, "engine": engine, "injector": injector, "validator": validator}


def test_primary_key_uniqueness(system_state):
    assert system_state["validator"]._check_pk_uniqueness() is True


def test_foreign_key_integrity(system_state):
    assert system_state["validator"]._check_foreign_keys() is True


def test_allowed_enums(system_state):
    assert system_state["validator"]._check_enums() is True


def test_date_ordering(system_state):
    assert system_state["validator"]._check_dates() is True


def test_post_trade_wealth_reconciliation(system_state):
    assert system_state["validator"]._check_arithmetic() is True


def test_five_injected_anomalies_present(system_state):
    gt = system_state["injector"].ground_truth
    assert len(gt) == 5
    types = {x["issue_type"] for x in gt}
    expected = {
        "TARGET_WEIGHT_MISMATCH",
        "OVERSELL_VIOLATION",
        "EXCLUDED_INSTRUMENT_RECOMMENDED",
        "OMITTED_TRANSACTION_FEE",
        "UNFLAGGED_STALE_PRICE"
    }
    assert types == expected
