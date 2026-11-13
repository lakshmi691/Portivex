# Source Manifest & Lawful Provenance

## 1. Provenance Statement
* **Dataset Type**: 100% Mathematically Generated Synthetic Financial Dataset.
* **Deterministic Generator Seed**: `20261022`
* **Generator Command**: `python run_pipeline.py --seed 20261022 --scale full`
* **Data Version**: `1.0.0-PROD`
* **Creation Timestamp**: `2026-11-13T13:30:00Z`
* **Legal Notice**: All investor names, emails, portfolio positions, prices, and account numbers are synthetically generated for educational simulation and software verification. They do not represent real persons, actual brokerage accounts, or real trading recommendations.

---

## 2. Public Data Guidance & Licensing
* **No Confidential/Personal Data**: Zero private, proprietary, or personally identifiable information (PII) is collected, scraped, or embedded.
* **No Access Control Bypasses**: No restricted APIs, paywalled websites, or protected market feeds were accessed.
* **Schema Inspiration**: Schema structures and risk profile models are derived from standard academic finance literature:
  * Modern Portfolio Theory (Markowitz, 1952)
  * Black-Litterman Global Portfolio Optimization (1992)
  * SEC Rule 17a-3 / 17a-4 record-keeping requirements for immutable audit event logs.
  * CFA Institute Portfolio Rebalancing Policy Guidelines.

---

## 3. Mathematical Models Used
* **Price Paths**: Correlated Geometric Brownian Motion (GBM) with asset-class specific annual drift ($\mu$) and annual volatility ($\sigma$):
  $$dS_t = \mu S_t dt + \sigma S_t dW_t$$
  * *Equities*: $\mu = 8.5\%$, $\sigma = 18\%$
  * *Fixed Income*: $\mu = 3.5\%$, $\sigma = 5.5\%$
  * *Commodities*: $\mu = 4.0\%$, $\sigma = 22\%$
  * *Real Estate*: $\mu = 6.0\%$, $\sigma = 14\%$
  * *Cash Equivalents*: $\mu = 2.0\%$, $\sigma = 0.5\%$
* **Trading Calendar**: 250 trading days per calendar year.
* **Reproducibility Guarantee**: Given seed `20261022`, the pseudo-random generator generates identical numerical arrays and bitwise identical output CSV, JSON, and SQL files across runs.
