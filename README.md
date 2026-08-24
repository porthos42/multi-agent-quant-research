\# Multi-Agent Quantitative Trading Research System



A deterministic, multi-agent algorithmic research platform built with LangChain, LangGraph, and Deep Agents.



The system automates the lifecycle of quantitative strategy generation, backtesting, critical review, and holdout evaluation while enforcing strict data hygiene and sandboxed subprocess execution to prevent backtest overfitting and lookahead bias.



\---



\## Architecture Overview



```text

&#x20;              +-------------------------------------------------+

&#x20;              |             Coordinator Agent (LangGraph)       |

&#x20;              +-------------------------------------------------+

&#x20;                        |                             ^

&#x20;      1. Request Spec   |                             | 4. Audit \& Gate

&#x20;                        v                             |

&#x20;              +-------------------+         +-------------------+

&#x20;              | Strategy Engineer |         |  Research Critic  |

&#x20;              +-------------------+         +-------------------+

&#x20;                        |                             ^

&#x20;     2. Generate Code   |                             | 3. Raw Metrics

&#x20;                        v                             |

&#x20;              +-------------------------------------------------+

&#x20;              |         Deterministic Execution Engine          |

&#x20;              |       (Lagged Signals, Slippage, Drift)         |

&#x20;              +-------------------------------------------------+



```



\### Core Components



\* \*\*Deterministic Backtesting Engine (`engine/`):\*\* Shared accounting layer that computes metrics (CAGR, Sharpe, Sortino, Max Drawdown, Turnover) from target weights while shifting execution signals by $t+1$ to prevent lookahead leakage.

\* \*\*Agent Sandboxing (`workspace/`):\*\* Strategy agents only write target portfolio weights. Generated strategies execute inside isolated sub-processes.

\* \*\*Strict Physical Data Partitions:\*\*

\* `dev` (2005–2017): In-sample discovery and initial parameter optimization.

\* `val` (2018–2021): Out-of-sample promotion tournament ($v\_1 \\to v\_2 \\to v\_3$).

\* `holdout` (2022–2025): Quarantined in `private/`. Unlocked strictly once after the final strategy is frozen.







\---



\## Directory Structure



```text

.

├── engine/

│   ├── \_\_init\_\_.py

│   ├── backtest.py           # Deterministic portfolio accounting \& metrics

│   └── runner.py             # Subprocess strategy execution sandbox

├── agents/

│   ├── \_\_init\_\_.py

│   ├── coordinator.py        # LangGraph workflow orchestration

│   ├── engineer.py           # Strategy code generation agent

│   └── critic.py             # Anti-overfitting \& risk reviewer

├── data/

│   ├── download.py           # Market data ingestion \& validation

│   └── partition.py          # Split generation (dev / val / holdout)

├── workspace/                # Agent-accessible workspace (ignored by Git)

│   ├── data/                 # Dev and Val datasets only

│   ├── strategies/           # Generated Python strategy files

│   └── results/              # Backtest outputs \& metrics

├── tests/

│   ├── test\_accounting.py    # Zero-drift and one-trade assertions

│   └── test\_isolation.py     # Subprocess security \& bounds tests

├── .env.example

├── .gitignore

├── requirements.txt

└── README.md



```



\---



\## Prerequisites



\* Python 3.11+

\* API Keys:

\* \*\*EODHD API Key\*\* (for market history)

\* \*\*OpenAI API Key\*\* (for agent inference)

\* \*\*LangSmith API Key\*\* (optional, for tracing)







\---



\## Installation \& Setup



1\. \*\*Clone the repository:\*\*

```bash

git clone https://github.com/<your-username>/multi-agent-quant-research.git

cd multi-agent-quant-research



```





2\. \*\*Set up a virtual environment:\*\*

```bash

python -m venv .venv

source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate

pip install -r requirements.txt



```





3\. \*\*Configure Environment Variables:\*\*

```bash

cp .env.example .env



```





Populate `.env` with your API credentials:

```env

EODHD\_API\_KEY=your\_eodhd\_key\_here

OPENAI\_API\_KEY=your\_openai\_key\_here

LANGSMITH\_API\_KEY=your\_langsmith\_key\_here

LANGSMITH\_TRACING=true

LANGSMITH\_PROJECT=trading-deep-agents



```





4\. \*\*Verify the deterministic test suite:\*\*

```bash

pytest tests/



```







\---



\## Quickstart



\### 1. Ingest and Partition Market Data



Download ETF data and create the isolated `dev`, `val`, and quarantined `holdout` splits:



```bash

python -m data.download

python -m data.partition



```



\### 2. Run the Multi-Agent Research Loop



Execute the sequential research tournament across iterations:



```bash

\# Run v1 baseline generation

python run\_research.py --version 1



\# Run v2 market-regime challenger

python run\_research.py --version 2



\# Run v3 volatility-targeted challenger

python run\_research.py --version 3



```



\### 3. Freeze Champion \& Run Terminal Holdout Audit



Once the coordinator confirms the surviving champion, evaluate on the quarantined holdout dataset:



```bash

python evaluate\_holdout.py --freeze



```



\---



\## Research Workflow Rules



\* \*\*Immutable Accounting:\*\* Agents cannot modify `engine/backtest.py` or write their own metric calculation functions.

\* \*\*Subprocess Execution:\*\* Code generated by agents is run in isolated processes with strict memory and timeout constraints.

\* \*\*Holdout Quarantine:\*\* The agent loop has no file access to `private/holdout\_\*`. Any strategy referencing dates past the validation split is disqualified.

