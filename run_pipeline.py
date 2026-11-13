"""
MASTER CLI PIPELINE ORCHESTRATOR
Runs synthetic data generation, policy-constrained rebalancing, anomaly injection, validation, and multi-format exports.
"""

import argparse
import csv
import json
import hashlib
import time
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Any

from backend.config import DEFAULT_SEED, DATA_DIR, DATABASE_DIR, DOCS_DIR
from backend.generator import DataGenerator
from backend.rebalance_engine import RebalanceEngine
from backend.anomaly_injector import AnomalyInjector
from backend.validator import SystemValidator


def export_all_formats(gen, engine, val_results):
    """Export datasets to CSV, JSON, MySQL seed script, and SQLite DB"""
    csv_dir = DATA_DIR / "csv"
    json_dir = DATA_DIR / "json"
    csv_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    tables = {
        "investor_profile": gen.investors,
        "fee_schedule": gen.fee_schedules,
        "constraint_policy": gen.constraints,
        "instrument": gen.instruments,
        "market_price": gen.market_prices,
        "portfolio": gen.portfolios,
        "portfolio_constraint": gen.portfolio_constraints,
        "target_allocation": gen.target_allocations,
        "holding": gen.holdings,
        "rebalance_proposal": engine.proposals,
        "trade": engine.trades,
        "proposal_event_log": engine.event_logs
    }

    # 1. Export CSV & JSON
    for name, records in tables.items():
        if not records:
            continue
        rows = [asdict(r) for r in records]
        
        # Write CSV
        with open(csv_dir / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
            
        # Write JSON
        with open(json_dir / f"{name}.json", "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2)

    # 2. Export MySQL 8.0 Seed Script (database/seed_data.sql)
    sql_path = DATABASE_DIR / "seed_data.sql"
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write("-- SEED DATA: POLICY-CONSTRAINED REBALANCING SYSTEM\n")
        f.write("-- Dialect: MySQL 8.0 (InnoDB) / ANSI SQL\n\n")
        f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")
        
        for name, records in tables.items():
            if not records:
                continue
            rows = [asdict(r) for r in records]
            cols = ", ".join(f"`{k}`" for k in rows[0].keys())
            f.write(f"-- Table: {name} ({len(rows)} rows)\n")
            
            # Batch inserts in chunks of 500
            for i in range(0, len(rows), 500):
                batch = rows[i:i + 500]
                f.write(f"INSERT INTO `{name}` ({cols}) VALUES\n")
                line_vals = []
                for r in batch:
                    vals = []
                    for val in r.values():
                        if val is None:
                            vals.append("NULL")
                        elif isinstance(val, (int, float)):
                            vals.append(str(val))
                        elif isinstance(val, bool):
                            vals.append("1" if val else "0")
                        else:
                            clean_str = str(val).replace("'", "''")
                            vals.append(f"'{clean_str}'")
                    line_vals.append(f"  ({', '.join(vals)})")
                f.write(",\n".join(line_vals) + ";\n\n")
                
        f.write("SET FOREIGN_KEY_CHECKS = 1;\n")

    # 3. MySQL Database Sync
    try:
        import pymysql
        my_conn = pymysql.connect(
            host="127.0.0.1",
            user="root",
            password="root",
            database="portfolio_db",
            port=3306,
            autocommit=True
        )
        my_cur = my_conn.cursor()
        my_cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        for name, records in tables.items():
            if not records:
                continue
            rows = [asdict(r) for r in records]
            col_names = list(rows[0].keys())
            cols_str = ", ".join([f"`{c}`" for c in col_names])
            placeholders = ", ".join(["%s"] * len(col_names))
            my_cur.execute(f"TRUNCATE TABLE `{name}`;")
            data_to_insert = []
            for r in rows:
                cleaned = []
                for c in col_names:
                    val = r[c]
                    if isinstance(val, bool):
                        cleaned.append(1 if val else 0)
                    elif isinstance(val, str) and len(val) >= 19 and val[0].isdigit() and "T" in val:
                        v = val.replace("Z", "").replace("T", " ")
                        if "+" in v: v = v.split("+")[0]
                        cleaned.append(v)
                    elif isinstance(val, dict):
                        cleaned.append(json.dumps(val))
                    else:
                        cleaned.append(val)
                data_to_insert.append(cleaned)
            my_cur.executemany(f"INSERT INTO `{name}` ({cols_str}) VALUES ({placeholders})", data_to_insert)
        my_cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        my_cur.close()
        my_conn.close()
    except Exception as e:
        pass

    # 4. Write docs/VALIDATION_SUMMARY.md
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    with open(DOCS_DIR / "VALIDATION_SUMMARY.md", "w", encoding="utf-8") as f:
        f.write("# Validation Summary & Acceptance Verification\n\n")
        f.write("## 7-Tier Validation Results\n\n")
        f.write("| Verification Check | Status |\n| :--- | :---: |\n")
        for k, v in val_results.items():
            f.write(f"| **{k.replace('_', ' ').title()}** | `{'PASS' if v else 'FAIL'}` |\n")
        f.write("\n## Exported Table Row Counts\n\n")
        f.write("| Table Name | Record Count |\n| :--- | :--- |\n")
        for k, v in tables.items():
            f.write(f"| `{k}` | {len(v):,} |\n")


def get_dataset_fingerprint() -> Dict[str, Any]:
    """Calculate SHA-256 hashes of all exported CSV files"""
    fingerprint = {}
    for cf in sorted(list((DATA_DIR / "csv").glob("*.csv"))):
        sha256 = hashlib.sha256()
        with open(cf, "rb") as f:
            while chunk := f.read(65536):
                sha256.update(chunk)
        with open(cf, "r", encoding="utf-8") as f:
            lines = len(f.readlines()) - 1
        fingerprint[cf.name] = {"rows": lines, "hash": sha256.hexdigest()}
    return fingerprint


def run(seed: int, scale: str):
    start = time.time()
    print("=" * 70)
    print(" POLICY-CONSTRAINED PORTFOLIO REBALANCING SYSTEM")
    print(f" Master Seed: {seed} | Scale: '{scale}'")
    print("=" * 70)

    # 1. Master Data Generation
    gen = DataGenerator(seed=seed, scale=scale)
    gen.generate_all()

    # 2. Rebalancing Engine
    engine = RebalanceEngine(
        portfolios=gen.portfolios,
        holdings=gen.holdings,
        target_allocations=gen.target_allocations,
        market_prices=gen.market_prices,
        fee_schedules=gen.fee_schedules,
        valuation_date=gen.valuation_date.isoformat()
    )
    engine.run_all()

    # 3. Anomaly Injection
    injector = AnomalyInjector(
        target_allocations=gen.target_allocations,
        trades=engine.trades,
        proposals=engine.proposals,
        market_prices=gen.market_prices,
        instruments=gen.instruments,
        valuation_date=gen.valuation_date.isoformat()
    )
    injector.inject_all()
    injector.export_ground_truth(DATA_DIR / "ground_truth.json", DATA_DIR / "ground_truth.csv")

    # 4. Multi-Tier Validation
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
    val_results = validator.run_all()

    # 5. Export multi-format
    export_all_formats(gen, engine, val_results)
    
    elapsed = time.time() - start
    print(f"[✓] Pipeline complete in {elapsed:.2f}s.")
    return val_results


def main():
    parser = argparse.ArgumentParser(description="Policy-Constrained Portfolio Rebalancing Pipeline")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Fixed deterministic seed (20261022)")
    parser.add_argument("--scale", type=str, choices=["starter", "full"], default="starter", help="starter vs full")
    parser.add_argument("--verify-reproducibility", action="store_true", help="Demonstrate bitwise SHA-256 reproducibility")
    args = parser.parse_args()

    if args.verify_reproducibility:
        print("\n>>> EXECUTION RUN 1 <<<")
        run(seed=args.seed, scale=args.scale)
        fp1 = get_dataset_fingerprint()

        print("\n>>> EXECUTION RUN 2 <<<")
        run(seed=args.seed, scale=args.scale)
        fp2 = get_dataset_fingerprint()

        print("\n" + "=" * 70)
        print(" REPRODUCIBILITY AUDIT RESULTS (SHA-256 BITWISE VERIFICATION)")
        print("=" * 70)
        match = True
        for fname in sorted(list(fp1.keys())):
            r1, h1 = fp1[fname]["rows"], fp1[fname]["hash"]
            r2, h2 = fp2[fname]["rows"], fp2[fname]["hash"]
            if r1 != r2 or h1 != h2:
                print(f"[FAIL] {fname} mismatch!")
                match = False
            else:
                print(f"  ✓ {fname:25s} | Rows: {r1:5d} | Hash: {h1[:16]}... (MATCH)")
        if match:
            print("\n[SUCCESS] 100% BITWISE DETERMINISM DEMONSTRATED.")
    else:
        run(seed=args.seed, scale=args.scale)


if __name__ == "__main__":
    main()
