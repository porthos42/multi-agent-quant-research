"""engine/backtest.py
Deterministic backtest engine and standardized metric calculation.

Enforces execution lag, asset drift, dynamic transaction costs,
and standard performance metrics.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd

PERIODS_PER_YEAR = 252
DEFAULT_RF_ANNUAL = 0.0
DEFAULT_MAR_ANNUAL = 0.0


def backtest(weights: pd.DataFrame, returns: pd.DataFrame, cost_bps: float = 10.0) -> pd.DataFrame:
    """Run a deterministic backtest from scheduled target weights.

    Parameters
    ----------
    weights : pd.DataFrame
        Target weights indexed by date, columns matching returns.
    returns : pd.DataFrame
        Asset returns (percentage change) indexed by date.
    cost_bps : float, default 10.0
        Transaction cost in basis points (1 bp = 0.0001).

    Returns
    -------
    pd.DataFrame
        Columns: ['ret', 'turnover', 'cost', 'cash']
    """
    # 1. Align weights with return dates and apply t+1 execution lag
    scheduled = pd.Series(returns.index.isin(weights.index), index=returns.index, dtype=bool)
    w_target = weights.reindex(returns.index).ffill().shift(1).fillna(0.0)
    is_rebalance = scheduled.shift(1, fill_value=False)

    held = pd.Series(0.0, index=returns.columns)
    records = []

    for dt in returns.index:
        # If today is a scheduled rebalance execution, target is updated; otherwise hold previous drifted weights
        target = w_target.loc[dt] if is_rebalance.loc[dt] else held

        # Calculate traded notional turnover and transaction cost
        traded = float((target - held).abs().sum())
        cost = traded * (cost_bps / 10000.0)

        # Asset returns for the day
        r = returns.loc[dt]
        gross_return = float((target * r).sum())
        net_return = gross_return - cost
        cash_weight = float(1.0 - target.sum())

        records.append({
            "ret": net_return,
            "turnover": traded,
            "cost": cost,
            "cash": cash_weight
        })

        denominator = 1.0 + gross_return
        if denominator <= 0:
            raise RuntimeError(f"Portfolio value became non-positive on {dt}: gross return={gross_return}")

        # Update end-of-day holdings subject to individual asset price drift
        held = (target * (1.0 + r)) / denominator

    return pd.DataFrame(records, index=returns.index)


def metrics(bt: pd.DataFrame, benchmark_returns: pd.Series = None,
            rf_annual: float = DEFAULT_RF_ANNUAL, mar_annual: float = DEFAULT_MAR_ANNUAL) -> dict:
    """Compute standard quantitative performance metrics from backtest results."""
    r = bt["ret"]
    n_days = len(r)
    if n_days == 0:
        return {}

    years = n_days / PERIODS_PER_YEAR
    rf_daily = (1.0 + rf_annual) ** (1.0 / PERIODS_PER_YEAR) - 1.0
    mar_daily = (1.0 + mar_annual) ** (1.0 / PERIODS_PER_YEAR) - 1.0

    excess_ret = r - rf_daily
    equity_curve = (1.0 + r).cumprod()

    sd = excess_ret.std(ddof=1)
    downside_diff = np.minimum(r - mar_daily, 0.0)
    downside_dev = np.sqrt((downside_diff ** 2).mean()) * np.sqrt(PERIODS_PER_YEAR)

    ann_ret = float(r.mean() * PERIODS_PER_YEAR)
    vol = float(r.std(ddof=1) * np.sqrt(PERIODS_PER_YEAR))
    cagr = float(equity_curve.iloc[-1] ** (1.0 / years) - 1.0) if years > 0 else 0.0
    sharpe = float((excess_ret.mean() / sd) * np.sqrt(PERIODS_PER_YEAR)) if sd > 0 else 0.0
    sortino = float((ann_ret - mar_annual) / downside_dev) if downside_dev > 0 else 0.0

    drawdown = (equity_curve / equity_curve.cummax()) - 1.0
    max_dd = float(drawdown.min())

    ann_turnover = float(bt["turnover"].sum() / years) if years > 0 else 0.0
    ann_cost = float(bt["cost"].sum() / years) if years > 0 else 0.0
    avg_cash = float(bt["cash"].mean())

    result = {
        "cagr": round(cagr, 4),
        "ann_ret": round(ann_ret, 4),
        "vol": round(vol, 4),
        "sharpe": round(sharpe, 4),
        "sortino": round(sortino, 4),
        "max_dd": round(max_dd, 4),
        "ann_turnover": round(ann_turnover, 4),
        "ann_cost": round(ann_cost, 4),
        "avg_cash": round(avg_cash, 4)
    }

    if benchmark_returns is not None:
        bench_eq = (1.0 + benchmark_returns).cumprod()
        bench_cagr = float(bench_eq.iloc[-1] ** (1.0 / years) - 1.0) if years > 0 else 0.0
        result["bench_cagr"] = round(bench_cagr, 4)

    return result


def load_split(data_dir: str | Path, split_name: str) -> dict:
    """Load parquet data splits and metadata for backtesting."""
    p = Path(data_dir)
    splits_meta = json.load(open(p / "splits.json"))
    
    data = {
        f: pd.read_parquet(p / f"{split_name}_{f}.parquet")
        for f in ["adj_close", "close", "volume"]
    }
    data["returns"] = data["adj_close"].pct_change().fillna(0.0)
    data["eval_start"] = pd.Timestamp(splits_meta[split_name])
    return data