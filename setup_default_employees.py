import hashlib
import pymysql

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def main():
    conn = pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="root",
        db="portfolio_db",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )
    with conn.cursor() as cur:
        # 1. Ensure is_active column exists in app_user
        try:
            cur.execute("ALTER TABLE app_user ADD COLUMN is_active TINYINT DEFAULT 1;")
            print("Added is_active column to app_user.")
        except Exception as e:
            print("Column is_active check:", e)

        # 2. Add or update the 3 default employee accounts
        # System Administrator: Name: Admin, Email: admin@gmail.com, Password: Admin123, Role: SYSTEM_ADMIN
        # Operations Analyst: Name: Operations Analyst, Email: operations@portivex.com, Password: Ops123, Role: OPERATIONS_ANALYST
        # Risk & Compliance Reviewer: Name: Risk & Compliance Reviewer, Email: risk@portivex.com, Password: Risk123, Role: COMPLIANCE_REVIEWER
        employees = [
            ("USR-ADM-001", "admin@gmail.com", hash_password("Admin123"), "Admin", "SYSTEM_ADMIN"),
            ("USR-OPS-001", "operations@portivex.com", hash_password("Ops123"), "Operations Analyst", "OPERATIONS_ANALYST"),
            ("USR-RC-001", "risk@portivex.com", hash_password("Risk123"), "Risk & Compliance Reviewer", "COMPLIANCE_REVIEWER")
        ]

        for uid, email, pwd_hash, name, role in employees:
            cur.execute("SELECT user_id, email FROM app_user WHERE LOWER(email) = LOWER(%s);", (email,))
            existing = cur.fetchone()
            if existing:
                cur.execute("""
                    UPDATE app_user 
                    SET password_hash = %s, full_name = %s, role = %s, is_active = 1
                    WHERE LOWER(email) = LOWER(%s);
                """, (pwd_hash, name, role, email))
                print(f"Updated employee account: {email} -> {role}")
            else:
                cur.execute("""
                    INSERT INTO app_user (user_id, email, password_hash, full_name, role, is_active)
                    VALUES (%s, %s, %s, %s, %s, 1);
                """, (uid, email, pwd_hash, name, role))
                print(f"Created default employee account: {email} ({role})")

        # 3. Ensure test customer account with hashed password
        cur.execute("SELECT user_id, email FROM app_user WHERE LOWER(email) = 'jane.doe@example.com';")
        cust = cur.fetchone()
        if cust:
            cur.execute("""
                UPDATE app_user 
                SET password_hash = %s, full_name = 'Jane Doe', role = 'CUSTOMER', portfolio_id = 'PORT-INV-000001-01', is_active = 1
                WHERE LOWER(email) = 'jane.doe@example.com';
            """, (hash_password("customer123"),))
            print("Updated test customer jane.doe@example.com with hashed password.")
        else:
            cur.execute("""
                INSERT INTO app_user (user_id, email, password_hash, full_name, role, portfolio_id, is_active)
                VALUES ('USR-0001', 'jane.doe@example.com', %s, 'Jane Doe', 'CUSTOMER', 'PORT-INV-000001-01', 1);
            """, (hash_password("customer123"),))
            print("Created test customer jane.doe@example.com.")

        # 4. Create a test "New Customer" without portfolio to test "No Portfolio Yet" state
        cur.execute("SELECT user_id, email FROM app_user WHERE LOWER(email) = 'new.customer@portivex.com';")
        new_cust = cur.fetchone()
        if not new_cust:
            cur.execute("""
                INSERT INTO app_user (user_id, email, password_hash, full_name, role, portfolio_id, is_active)
                VALUES ('USR-NEW-001', 'new.customer@portivex.com', %s, 'New Investor', 'CUSTOMER', NULL, 1);
            """, (hash_password("Customer123"),))
            print("Created test unassigned customer new.customer@portivex.com.")

        # Verify users
        cur.execute("SELECT user_id, email, full_name, role, is_active FROM app_user WHERE email IN ('admin@gmail.com', 'operations@portivex.com', 'risk@portivex.com', 'jane.doe@example.com', 'new.customer@portivex.com');")
        rows = cur.fetchall()
        print("\nVerified Core Accounts:")
        for r in rows:
            print(r)

    conn.close()

if __name__ == "__main__":
    main()
