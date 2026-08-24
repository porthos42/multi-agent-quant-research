"""tests/test_accounting.py
Unit tests verifying portfolio accounting invariants and execution timing.
"""

import numpy as np
import pandas as pd
import pytest
from engine.backtest import backtest, metrics


@pytest.fixture
def sample_market_data():
    """Create 5 days of synthetic price returns for 2 assets."""
    dates = pd.date_range("2020-01-01", periods=5, freq="B")
    tickers = ["SPY", "TLT"]
    
    # Predictable returns: SPY gains 1% each day, TLT loses 1%
    ret_data = {
        "SPY": [0.01, 0.01, 0.01, 0.01, 0.01],
        "TLT": [-0.01, -0.01, -0.01, -0.01, -0.01]
    }
    returns = pd.DataFrame(ret_data, index=dates)
    return returns


def test_buy_and_hold_turnover_invariant(sample_market_data):
    """Invariant 1: Single purchase must yield exactly 1.0 total turnover.
    Asset drift across subsequent days must NOT trigger spurious rebalances.
    """
    returns = sample_market_data
    tickers = returns.columns
    
    # Schedule 100% allocation to SPY on day 0
    weights = pd.DataFrame(0.0, index=[returns.index[0]], columns=tickers)
    weights.iloc[0, 0] = 1.0

    bt = backtest(weights, returns, cost_bps=10.0)

    # Day 0: Signal sent, executed on Day 1 (turnover = 1.0)
    # Days 2-4: Drift occurs, turnover must remain 0.0
    total_turnover = float(bt["turnover"].sum())
    assert round(total_turnover, 4) == 1.0, f"Expected 1.0 turnover, got {total_turnover}"


def test_execution_lag_timing(sample_market_data):
    """Invariant 2: Target weight scheduled on day t takes effect on day t+1.
    Day t return must be 0.0.
    """
    returns = sample_market_data
    tickers = returns.columns

    # Signal generated on Day 0 allocating 100% SPY
    weights = pd.DataFrame(0.0, index=[returns.index[0]], columns=tickers)
    weights.iloc[0, 0] = 1.0

    bt = backtest(weights, returns, cost_bps=0.0)

    # On Day 0 (index 0), portfolio was in cash (shifted by 1)
    assert bt["ret"].iloc[0] == 0.0
    # On Day 1 (index 1), position is live and earns SPY's return (0.01)
    assert pytest.approx(bt["ret"].iloc[1], 1e-5) == 0.01


def test_metrics_calculation(sample_market_data):
    """Verify metrics calculation logic with fixed inputs."""
    returns = sample_market_data
    weights = pd.DataFrame(0.0, index=[returns.index[0]], columns=returns.columns)
    weights.iloc[0, 0] = 1.0

    bt = backtest(weights, returns, cost_bps=0.0)
    m = metrics(bt)

    assert "sharpe" in m
    assert "max_dd" in m
    assert "cagr" in m
    assert m["max_dd"] <= 0.0