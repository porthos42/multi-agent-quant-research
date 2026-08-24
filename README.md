# Multi-Agent Quantitative Trading Research System

A deterministic, multi-agent algorithmic research platform built with LangChain, LangGraph, and Deep Agents. 

The system automates the lifecycle of quantitative strategy generation, backtesting, critical review, and holdout evaluation while enforcing strict data hygiene and sandboxed subprocess execution to prevent backtest overfitting and lookahead bias.

---

## Architecture Overview

```text
               +-------------------------------------------------+
               |             Coordinator Agent (LangGraph)       |
               +-------------------------------------------------+
                         |                             ^
       1. Request Spec   |                             | 4. Audit & Gate
                         v                             |
               +-------------------+         +-------------------+
               | Strategy Engineer |         |  Research Critic  |
               +-------------------+         +-------------------+
                         |                             ^
      2. Generate Code   |                             | 3. Raw Metrics
                         v                             |
               +-------------------------------------------------+
               |         Deterministic Execution Engine          |
               |       (Lagged Signals, Slippage, Drift)         |
               +-------------------------------------------------+