import pymysql
import json
from datetime import datetime, timedelta

conn = pymysql.connect(
    host="127.0.0.1",
    user="root",
    password="root",
    database="portfolio_db",
    autocommit=True
)
cur = conn.cursor()

# 1. Create simulation_record table
cur.execute("""
CREATE TABLE IF NOT EXISTS simulation_record (
    simulation_id VARCHAR(32) PRIMARY KEY,
    proposal_id VARCHAR(32) NOT NULL,
    portfolio_id VARCHAR(64) NOT NULL,
    pre_value DECIMAL(18, 4) NOT NULL,
    post_value DECIMAL(18, 4) NOT NULL,
    pre_drift DECIMAL(8, 6) NOT NULL,
    post_drift DECIMAL(8, 6) NOT NULL,
    drift_reduction_pct DECIMAL(8, 4) NOT NULL,
    turnover DECIMAL(18, 4) NOT NULL,
    fees DECIMAL(10, 4) NOT NULL,
    reconciliation_status VARCHAR(32) NOT NULL DEFAULT 'RECONCILED',
    simulated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""")

# 2. Enrich proposal statuses for realistic operational pipeline
cur.execute("SELECT proposal_id, portfolio_id, pre_rebalance_value, post_rebalance_value, pre_drift_rmse, post_drift_rmse, total_turnover, estimated_fees FROM rebalance_proposal ORDER BY proposal_id ASC;")
proposals = cur.fetchall()

status_assignments = [
    ("DRAFT", "DRIFT_WITHIN_TOLERANCE"),
    ("PENDING_REVIEW", "APPROVED"),
    ("RETURNED", "REJECTED_EXCLUDED_ASSET"),
    ("APPROVED", "APPROVED"),
    ("SIMULATED", "APPROVED"),
    ("EXCEPTION_FLAGGED", "REJECTED_OVERSOLD"),
]

for idx, p in enumerate(proposals):
    prop_id = p[0]
    port_id = p[1]
    pre_val = float(p[2])
    post_val = float(p[3])
    pre_drift = float(p[4])
    post_drift = float(p[5])
    turnover = float(p[6])
    fees = float(p[7])

    # Assign diverse statuses
    if idx < 5:
        st, dec = "DRAFT", "DRIFT_WITHIN_TOLERANCE"
    elif idx < 15:
        st, dec = "PENDING_REVIEW", "APPROVED"
    elif idx < 20:
        st, dec = "RETURNED", "REJECTED_EXCLUDED_ASSET"
    elif idx < 35:
        st, dec = "APPROVED", "APPROVED"
    elif idx < 45:
        st, dec = "SIMULATED", "APPROVED"
        # Insert simulation record
        sim_id = f"SIM-2026-{(idx + 1):04d}"
        drift_red = round(((pre_drift - post_drift) / pre_drift) * 100, 2) if pre_drift > 0 else 99.0
        cur.execute("""
            INSERT IGNORE INTO simulation_record (
                simulation_id, proposal_id, portfolio_id, pre_value, post_value, pre_drift, post_drift, drift_reduction_pct, turnover, fees, reconciliation_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'RECONCILED');
        """, (sim_id, prop_id, port_id, pre_val, post_val, pre_drift, post_drift, drift_red, turnover, fees))
    elif idx == 45:
        st, dec = "EXCEPTION_FLAGGED", "REJECTED_OVERSOLD"
    else:
        st, dec = "APPROVED", "APPROVED"

    cur.execute("UPDATE rebalance_proposal SET status = %s, decision_code = %s WHERE proposal_id = %s;", (st, dec, prop_id))

# Verify counts
print("\n--- UPDATED PROPOSAL STATUS COUNTS ---")
cur.execute("SELECT status, count(*) FROM rebalance_proposal GROUP BY status;")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

print("\n--- SIMULATION RECORDS COUNT ---")
cur.execute("SELECT count(*) FROM simulation_record;")
print(f"  Total Simulations: {cur.fetchone()[0]}")

cur.close()
conn.close()
print("\n[SUCCESS] Operations Analyst data enriched!")
