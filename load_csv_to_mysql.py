import os
import csv
import json
import pymysql

DATA_DIR = os.path.join("data", "csv")
TABLES_ORDER = [
    "investor_profile",
    "fee_schedule",
    "portfolio",
    "instrument",
    "market_price",
    "target_allocation",
    "holding",
    "constraint_policy",
    "portfolio_constraint",
    "rebalance_proposal",
    "trade",
    "proposal_event_log"
]

def clean_val(val, col_name):
    if val is None or val == "" or val == "NULL":
        return None
    # Fix Booleans for MySQL TINYINT(1)
    if isinstance(val, str) and val.lower() in ("true", "t"):
        return 1
    if isinstance(val, str) and val.lower() in ("false", "f"):
        return 0
    # Fix ISO 8601 timestamps for MySQL datetime/timestamp
    if isinstance(val, str) and len(val) >= 19 and val[0].isdigit() and ("T" in val):
        v = val.replace("Z", "").replace("T", " ")
        if "+" in v:
            v = v.split("+")[0]
        return v
    # Fix JSON fields
    if "json" in col_name.lower() or col_name in ("parameters", "parameters_json"):
        if isinstance(val, str):
            import ast
            try:
                parsed = json.loads(val)
                return json.dumps(parsed)
            except Exception:
                try:
                    parsed = ast.literal_eval(val)
                    return json.dumps(parsed)
                except Exception:
                    return "{}"
    return val

conn = pymysql.connect(
    host="127.0.0.1",
    user="root",
    password="root",
    database="portfolio_db",
    port=3306,
    autocommit=False
)
cur = conn.cursor()
cur.execute("SET FOREIGN_KEY_CHECKS = 0;")

for table in TABLES_ORDER:
    csv_path = os.path.join(DATA_DIR, f"{table}.csv")
    if not os.path.exists(csv_path):
        print(f"Skipping {table}, file not found: {csv_path}")
        continue

    cur.execute(f"TRUNCATE TABLE `{table}`;")
    cur.execute(f"DESCRIBE `{table}`;")
    cols_desc = cur.fetchall()
    print(f"Schema for {table}: {[c[0] for c in cols_desc]}")

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = []
        for r in reader:
            cleaned_row = [clean_val(cell, headers[idx]) for idx, cell in enumerate(r)]
            rows.append(cleaned_row)

    if rows:
        if table == "constraint_policy":
            print(f"Sample row for constraint_policy: {rows[0]}")
        cols_str = ", ".join([f"`{h}`" for h in headers])
        placeholders = ", ".join(["%s"] * len(headers))
        sql = f"INSERT INTO `{table}` ({cols_str}) VALUES ({placeholders})"
        cur.executemany(sql, rows)
        print(f"✓ Imported {len(rows)} rows into `{table}`")

cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
conn.commit()

print("\n--- FINAL MYSQL TABLE COUNTS ---")
for table in TABLES_ORDER + ["app_user", "support_ticket"]:
    cur.execute(f"SELECT COUNT(*) FROM `{table}`;")
    print(f"  {table}: {cur.fetchone()[0]} rows")

cur.close()
conn.close()
print("\n[SUCCESS] All CSV data loaded into MySQL successfully!")
