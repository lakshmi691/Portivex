import pymysql
import os
import re

DB_NAME = "portfolio_db"

def run_sql_file(cursor, file_path):
    print(f"Executing {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # Split by semicolon, accounting for multiline statements
    # Simple regex split by ';' followed by newline or end of string
    statements = sql.split(";")
    count = 0
    for stmt in statements:
        stmt = stmt.strip()
        if not stmt:
            continue
        try:
            cursor.execute(stmt)
            count += 1
        except Exception as e:
            # Print error but continue if table already dropped
            if "Unknown table" in str(e) or "doesn't exist" in str(e):
                continue
            print(f"Warning on statement ({str(e)[:120]}):\n{stmt[:80]}...\n")
    print(f"Executed {count} statements from {file_path}.")

conn = pymysql.connect(
    host="127.0.0.1",
    user="root",
    password="root",
    port=3306,
    autocommit=True
)
cur = conn.cursor()

print("Creating database...")
cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
cur.execute(f"USE {DB_NAME};")
cur.execute("SET FOREIGN_KEY_CHECKS = 0;")

schema_file = os.path.join("database", "schema.sql")
seed_file = os.path.join("database", "seed_data.sql")

run_sql_file(cur, schema_file)
run_sql_file(cur, seed_file)

# Create app_user and support_ticket tables
print("Creating app_user and support_ticket tables...")
cur.execute("""
CREATE TABLE IF NOT EXISTS app_user (
    user_id VARCHAR(32) PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(32) NOT NULL,
    portfolio_id VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS support_ticket (
    ticket_id VARCHAR(32) PRIMARY KEY,
    portfolio_id VARCHAR(64) NOT NULL,
    investor_name VARCHAR(100) NOT NULL,
    category VARCHAR(64) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(32) NOT NULL,
    resolution_notes TEXT,
    resolved_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""")

default_users = [
    ("USR-0001", "jane.doe@example.com", "customer123", "Jane Doe", "CUSTOMER", "PORT-INV-000001-01"),
    ("USR-0002", "marcus.vance@vestilo.com", "analyst123", "Marcus Vance", "OPERATIONS_ANALYST", None),
    ("USR-0003", "sarah.jenkins@vestilo.com", "compliance123", "Sarah Jenkins", "COMPLIANCE_REVIEWER", None),
    ("USR-0004", "admin@vestilo.com", "admin123", "Platform Administrator", "SYSTEM_ADMIN", None),
]
for u in default_users:
    cur.execute("""
        INSERT INTO app_user (user_id, email, password_hash, full_name, role, portfolio_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE full_name=VALUES(full_name);
    """, u)

cur.execute("""
INSERT INTO support_ticket (
    ticket_id, portfolio_id, investor_name, category, message, status, resolution_notes, resolved_by, created_at, resolved_at
) VALUES (
    'TKT-2026-000101', 'PORT-INV-000001-01', 'Jane Doe', 'COMPLIANCE_RESTRICTION',
    'Rebalance proposal has orders on restricted ticker INS-000042. Can this restriction be waived or re-evaluated?',
    'RESOLVED',
    'Reviewed and approved by Administrator: One-time corporate transition waiver granted. Rebalance unlocked.',
    'Platform Administrator',
    '2026-11-13 09:30:00',
    '2026-11-13 10:15:00'
) ON DUPLICATE KEY UPDATE status=VALUES(status);
""")

cur.execute("SET FOREIGN_KEY_CHECKS = 1;")

print("\n--- TABLE ROW COUNTS IN MYSQL `portfolio_db` ---")
cur.execute("SHOW TABLES;")
tables = [r[0] for r in cur.fetchall()]
for t in sorted(tables):
    cur.execute(f"SELECT COUNT(*) FROM `{t}`;")
    cnt = cur.fetchone()[0]
    print(f"  {t}: {cnt} rows")

cur.close()
conn.close()
print("\n[SUCCESS] MySQL database `portfolio_db` setup and verified!")
