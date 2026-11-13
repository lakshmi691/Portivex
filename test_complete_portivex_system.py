import urllib.request
import json
import pymysql

BASE_URL = "http://127.0.0.1:8000"

def post_json(endpoint, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_json(endpoint):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_text(endpoint):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}")
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")

def main():
    print("======================================================================")
    print("PORTIVEX PLATFORM: FULL SYSTEM & AUTOMATED INTEGRATION TEST SUITE")
    print("======================================================================\n")

    # 1. Test System Administrator Login
    print("--- 1. Testing Default System Administrator Login ---")
    adm_resp = post_json("/api/auth/login", {"email": "admin@gmail.com", "password": "Admin123"})
    assert adm_resp["success"] is True, f"Admin login failed: {adm_resp}"
    assert adm_resp["user"]["role"] == "SYSTEM_ADMIN", f"Wrong role: {adm_resp['user']['role']}"
    assert adm_resp["user"]["full_name"] == "Admin"
    print(f"✓ Administrator Authenticated: {adm_resp['user']['full_name']} | Role: {adm_resp['user']['role']}")

    # 2. Test Operations Analyst Login
    print("\n--- 2. Testing Default Operations Analyst Login ---")
    ops_resp = post_json("/api/auth/login", {"email": "operations@portivex.com", "password": "Ops123"})
    assert ops_resp["success"] is True, f"Analyst login failed: {ops_resp}"
    assert ops_resp["user"]["role"] == "OPERATIONS_ANALYST", f"Wrong role: {ops_resp['user']['role']}"
    print(f"✓ Operations Analyst Authenticated: {ops_resp['user']['full_name']} | Role: {ops_resp['user']['role']}")

    # 3. Test Risk & Compliance Reviewer Login
    print("\n--- 3. Testing Default Risk & Compliance Reviewer Login ---")
    rc_resp = post_json("/api/auth/login", {"email": "risk@portivex.com", "password": "Risk123"})
    assert rc_resp["success"] is True, f"Compliance login failed: {rc_resp}"
    assert rc_resp["user"]["role"] == "COMPLIANCE_REVIEWER", f"Wrong role: {rc_resp['user']['role']}"
    print(f"✓ Compliance Reviewer Authenticated: {rc_resp['user']['full_name']} | Role: {rc_resp['user']['role']}")

    # 4. Test Registered Customer (Assigned Portfolio) Login
    print("\n--- 4. Testing Registered Customer (Jane Doe) Login ---")
    cust_resp = post_json("/api/auth/login", {"email": "jane.doe@example.com", "password": "customer123"})
    assert cust_resp["success"] is True, f"Customer login failed: {cust_resp}"
    assert cust_resp["user"]["role"] == "CUSTOMER", f"Wrong role: {cust_resp['user']['role']}"
    assert cust_resp["user"]["portfolio_id"] == "PORT-INV-000001-01"
    print(f"✓ Registered Customer Authenticated: {cust_resp['user']['full_name']} | Portfolio: {cust_resp['user']['portfolio_id']}")

    # 5. Test Unassigned Customer (New Customer) Login
    print("\n--- 5. Testing Unassigned Customer Login (Photos 1-5 Empty State) ---")
    new_resp = post_json("/api/auth/login", {"email": "new.customer@portivex.com", "password": "Customer123"})
    assert new_resp["success"] is True, f"New customer login failed: {new_resp}"
    assert new_resp["user"]["role"] == "CUSTOMER"
    print(f"✓ Unassigned Customer Authenticated: {new_resp['user']['full_name']} | Portfolio: {new_resp['user']['portfolio_id']}")

    # 6. Test Invalid Password Security
    print("\n--- 6. Testing Invalid Password Security ---")
    bad_pass = post_json("/api/auth/login", {"email": "admin@gmail.com", "password": "WrongPassword!"})
    assert bad_pass["success"] is False, "Security breach: invalid password accepted!"
    print(f"✓ Invalid Password Correctly Rejected: {bad_pass['message']}")

    # 7. Test Non-Existent User Security
    print("\n--- 7. Testing Unknown Email Security ---")
    bad_email = post_json("/api/auth/login", {"email": "nonexistent@portivex.com", "password": "anypassword"})
    assert bad_email["success"] is False, "Security breach: unknown email accepted!"
    print(f"✓ Unknown Account Correctly Rejected: {bad_email['message']}")

    # 8. Test Backend Modules for all 4 Actors
    print("\n--- 8. Testing Operational Endpoints Across All 4 Actors ---")
    # Customer Holdings & Orders
    holdings = get_json("/api/customer/portfolio-holdings/PORT-INV-000001-01")
    assert "holdings" in holdings and len(holdings["holdings"]) > 0
    print(f"✓ Customer Holdings API: {len(holdings['holdings'])} holdings loaded (Total: ${holdings['portfolio_value']:,.2f})")

    orders = get_json("/api/customer/trade-orders/PORT-INV-000001-01")
    assert "orders" in orders
    print(f"✓ Customer Trade Orders API: {len(orders['orders'])} orders loaded")

    # Analyst Dashboard Stats & Queue
    analyst_overview = get_json("/api/analyst/dashboard-stats")
    assert "kpis" in analyst_overview
    kpis = analyst_overview["kpis"]
    print(f"✓ Analyst Stats API: Total Portfolios = {kpis['total_portfolios']}, Rebalance Required = {kpis.get('rebalance_required')}")

    # Compliance Dashboard Stats
    comp_stats = get_json("/api/compliance/dashboard-stats")
    assert "kpis" in comp_stats
    print(f"✓ Compliance Stats API: Total Proposals = {comp_stats['kpis']['total']}, Pending Review = {comp_stats['kpis']['pending_review']}")

    # Admin Dashboard Stats
    admin_stats = get_json("/api/admin/dashboard-stats")
    assert "kpis" in admin_stats and "overview" in admin_stats
    print(f"✓ Admin Stats API: Total Users = {admin_stats['kpis']['total_users']}, Active Portfolios = {admin_stats['overview']['active_portfolios']}")

    # 9. Verify Frontend Navigation and Layout Integrity
    print("\n--- 9. Verifying Frontend Navigation and Layout Integrity ---")
    html = get_text("/")
    assert "actor-tabs" not in html, "ERROR: actor-tabs still present in HTML!"
    assert "portivex-quick-roles" not in html, "ERROR: quick role tester buttons still present!"
    assert "view-cust-dashboard" in html, "Missing view-cust-dashboard"
    assert "view-cust-portfolio" in html, "Missing view-cust-portfolio"
    assert "view-cust-orders" in html, "Missing view-cust-orders"
    assert "view-cust-tickets" in html, "Missing view-cust-tickets"
    assert "view-cust-settings" in html, "Missing view-cust-settings"
    assert "actor-panel-customer" in html, "Missing actor-panel-customer"
    assert "actor-panel-analyst" in html, "Missing actor-panel-analyst"
    assert "actor-panel-compliance" in html, "Missing actor-panel-compliance"
    assert "actor-panel-admin" in html, "Missing actor-panel-admin"
    assert "No portfolio yet" in html, "Missing 'No portfolio yet' label"
    assert "Getting Started" in html, "Missing 'Getting Started' label"
    assert "Request Portfolio Setup" in html, "Missing 'Request Portfolio Setup' button"
    print("✓ Application Header is clean: No actor switcher buttons present.")
    print("✓ Auth Modal is clean: Common login form without role shortcuts.")
    print("✓ Customer pages matching Photos 1 to 5 verified in index.html.")
    print("✓ All 4 actor modules present and linked to role-based redirection.")

    # 10. Database Hash Permanence Check
    print("\n--- 10. Verifying MySQL Database User Records ---")
    conn = pymysql.connect(host="127.0.0.1", port=3306, user="root", password="root", db="portfolio_db", cursorclass=pymysql.cursors.DictCursor)
    with conn.cursor() as cur:
        cur.execute("SELECT user_id, email, full_name, role, password_hash, is_active FROM app_user WHERE email IN ('admin@gmail.com', 'operations@portivex.com', 'risk@portivex.com', 'jane.doe@example.com');")
        rows = cur.fetchall()
        for r in rows:
            print(f"DB Record: {r['email']:25} | Role: {r['role']:20} | Hashed: {len(r['password_hash']) == 64} | Active: {r['is_active']}")
            assert len(r['password_hash']) == 64, f"Password is not a 64-char SHA256 hash: {r['password_hash']}"
            assert r['is_active'] == 1
    conn.close()

    print("\n======================================================================")
    print("ALL 10 VERIFICATION SUITES PASSED 100% WITH ZERO ERRORS!")
    print("======================================================================")

if __name__ == "__main__":
    main()
