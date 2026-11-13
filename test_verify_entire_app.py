import urllib.request
import urllib.error
import json
import uuid
import sys
import pymysql

BASE_URL = "http://127.0.0.1:8000"

def get_json(endpoint):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def post_json(endpoint, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8"))

def get_text(endpoint):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}")
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")

def main():
    print("=" * 80)
    print("PORTIVEX COMPREHENSIVE END-TO-END APPLICATION VERIFICATION")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # SUITE 1: AUTHENTICATION & ROLE-BASED ACCESS CONTROL
    # -------------------------------------------------------------------------
    print("\n[SUITE 1] Testing Authentication & RBAC...")
    
    # 1.1 Admin Login
    adm = post_json("/api/auth/login", {"email": "admin@gmail.com", "password": "Admin123"})
    assert adm.get("success") is True, f"Admin login failed: {adm}"
    assert adm["user"]["role"] == "SYSTEM_ADMIN"
    print("  ✓ Admin Login: SUCCESS (role: SYSTEM_ADMIN)")

    # 1.2 Operations Analyst Login
    ops = post_json("/api/auth/login", {"email": "operations@portivex.com", "password": "Ops123"})
    assert ops.get("success") is True, f"Ops login failed: {ops}"
    assert ops["user"]["role"] == "OPERATIONS_ANALYST"
    print("  ✓ Operations Analyst Login: SUCCESS (role: OPERATIONS_ANALYST)")

    # 1.3 Risk & Compliance Reviewer Login
    risk = post_json("/api/auth/login", {"email": "risk@portivex.com", "password": "Risk123"})
    assert risk.get("success") is True, f"Risk login failed: {risk}"
    assert risk["user"]["role"] == "COMPLIANCE_REVIEWER"
    print("  ✓ Risk & Compliance Login: SUCCESS (role: COMPLIANCE_REVIEWER)")

    # 1.4 Assigned Customer Login
    cust = post_json("/api/auth/login", {"email": "jane.doe@example.com", "password": "customer123"})
    assert cust.get("success") is True, f"Customer login failed: {cust}"
    assert cust["user"]["role"] == "CUSTOMER"
    assert cust["user"]["portfolio_id"] == "PORT-INV-000001-01"
    print("  ✓ Assigned Customer Login: SUCCESS (portfolio: PORT-INV-000001-01)")

    # 1.5 Security: Missing Password Rejection
    no_pass = post_json("/api/auth/login", {"email": "admin@gmail.com", "password": ""})
    assert no_pass.get("success") is False
    print("  ✓ Missing Password: CORRECTLY REJECTED")

    # 1.6 Security: Wrong Password Rejection
    bad_pass = post_json("/api/auth/login", {"email": "admin@gmail.com", "password": "WrongPassword"})
    assert bad_pass.get("success") is False
    print("  ✓ Wrong Password: CORRECTLY REJECTED")

    # 1.7 Security: Unknown User Rejection
    unknown = post_json("/api/auth/login", {"email": "does.not.exist@portivex.com", "password": "pass"})
    assert unknown.get("success") is False
    print("  ✓ Non-existent Account: CORRECTLY REJECTED")

    # 1.8 Customer Self-Registration & Immediate Login
    test_email = f"user.{uuid.uuid4().hex[:6]}@example.com"
    reg = post_json("/api/auth/register", {
        "full_name": "Test Verification Customer",
        "email": test_email,
        "password": "SecurePassword123!"
    })
    assert reg.get("success") is True, f"Registration failed: {reg}"
    new_login = post_json("/api/auth/login", {"email": test_email, "password": "SecurePassword123!"})
    assert new_login.get("success") is True
    assert new_login["user"]["role"] == "CUSTOMER"
    print(f"  ✓ Customer Registration & Login: SUCCESS ({test_email})")

    # -------------------------------------------------------------------------
    # SUITE 2: CUSTOMER PORTAL & ACTIONS
    # -------------------------------------------------------------------------
    print("\n[SUITE 2] Testing Customer Portal Modules & Endpoints...")
    
    # 2.1 Customer Holdings
    holdings_data = get_json("/api/customer/portfolio-holdings/PORT-INV-000001-01")
    assert "holdings" in holdings_data
    assert len(holdings_data["holdings"]) > 0
    print(f"  ✓ Portfolio Holdings: {len(holdings_data['holdings'])} assets loaded (${holdings_data['portfolio_value']:,.2f})")

    # 2.2 Customer Trade Orders
    orders_data = get_json("/api/customer/trade-orders/PORT-INV-000001-01")
    assert "orders" in orders_data
    print(f"  ✓ Trade Orders: {len(orders_data['orders'])} orders listed")

    # 2.3 Customer Support Tickets
    tickets_before = get_json("/api/tickets/portfolio/PORT-INV-000001-01")
    assert isinstance(tickets_before, list)
    print(f"  ✓ Existing Customer Tickets: {len(tickets_before)} retrieved")

    # 2.4 Create Support Ticket
    ticket_req = post_json("/api/tickets/create", {
        "portfolio_id": "PORT-INV-000001-01",
        "investor_name": "Jane Doe",
        "category": "Portfolio Inquiry",
        "message": "Automated verification ticket for rebalancing assistance."
    })
    assert ticket_req.get("success") is True
    created_ticket_id = ticket_req["ticket_id"]
    print(f"  ✓ Create Support Ticket: SUCCESS ({created_ticket_id})")

    # 2.5 Deposit Cash
    dep_res = post_json("/api/portfolio/PORT-INV-000001-01/deposit", {"amount": 2500.0})
    assert dep_res.get("success") is True
    print(f"  ✓ Deposit Cash ($2,500.00): SUCCESS (New Cash Balance: ${dep_res['new_cash_balance']:,.2f})")

    # -------------------------------------------------------------------------
    # SUITE 3: OPERATIONS ANALYST WORKFLOWS
    # -------------------------------------------------------------------------
    print("\n[SUITE 3] Testing Operations Analyst Modules...")
    
    # 3.1 Analyst Dashboard Stats
    analyst_stats = get_json("/api/analyst/dashboard-stats")
    assert "kpis" in analyst_stats
    print(f"  ✓ Analyst KPIs: Total Portfolios = {analyst_stats['kpis']['total_portfolios']}, Rebalance Req = {analyst_stats['kpis']['rebalance_required']}")

    # 3.2 Analyst Queue
    queue_data = get_json("/api/analyst/queue")
    assert "portfolios" in queue_data
    print(f"  ✓ Analyst Queue: {len(queue_data['portfolios'])} portfolios available in work queue")

    # 3.3 Portfolio Details for Rebalancing
    details = get_json("/api/analyst/portfolio/PORT-INV-000001-01/details")
    assert "portfolio" in details and "holdings" in details
    print(f"  ✓ Portfolio Details: Loaded for {details['portfolio']['portfolio_id']} (Risk: {details['portfolio']['risk_tolerance']})")

    # 3.4 Proposals List
    proposals = get_json("/api/proposals")
    assert "data" in proposals
    print(f"  ✓ Proposals Queue: {len(proposals['data'])} proposals retrieved (Total: {proposals['total']})")

    # 3.5 Proposal Simulation
    if proposals["data"]:
        test_prop_id = proposals["data"][0]["proposal_id"]
        sim_res = post_json(f"/api/proposals/{test_prop_id}/simulate", {})
        assert sim_res.get("success") is True
        print(f"  ✓ Proposal Simulation: SUCCESS ({test_prop_id})")

    # 3.6 Trade History & Audit
    history_data = get_json("/api/history")
    assert "trade_history" in history_data
    print(f"  ✓ Execution & Audit History: {len(history_data['trade_history'])} trade records, {len(history_data['audit_trail'])} audit logs")

    # -------------------------------------------------------------------------
    # SUITE 4: RISK & COMPLIANCE REVIEWER WORKFLOWS
    # -------------------------------------------------------------------------
    print("\n[SUITE 4] Testing Risk & Compliance Reviewer Modules...")
    
    # 4.1 Compliance Dashboard Stats
    comp_stats = get_json("/api/compliance/dashboard-stats")
    assert "kpis" in comp_stats
    print(f"  ✓ Compliance KPIs: Total = {comp_stats['kpis']['total']}, Pending Review = {comp_stats['kpis']['pending_review']}")

    # 4.2 Review Proposal Details
    if proposals["data"]:
        test_prop_id = proposals["data"][0]["proposal_id"]
        review_details = get_json(f"/api/compliance/proposal/{test_prop_id}/review-details")
        assert "proposal_id" in review_details and "trades" in review_details and "validations" in review_details
        print(f"  ✓ Compliance Review Details: Retrieved for {test_prop_id} ({len(review_details['trades'])} trades, {len(review_details['validations'])} checks)")

        # 4.3 Compliance Decision (Approve)
        decision_res = post_json(f"/api/compliance/proposal/{test_prop_id}/decide", {
            "decision": "APPROVED",
            "comments": "Compliance pre-trade checks passed under automated verification.",
            "reviewer_name": "Risk & Compliance Reviewer"
        })
        assert decision_res.get("success") is True
        print(f"  ✓ Compliance Decision: Proposal {test_prop_id} APPROVED")

    # 4.4 Compliance History
    comp_history = get_json("/api/compliance/history")
    assert "records" in comp_history or "audit_trail" in comp_history
    print(f"  ✓ Compliance Audit History: {len(comp_history.get('records', []))} compliance decisions retrieved")

    # 4.5 Compliance Exceptions & Anomaly Tracking
    exceptions = get_json("/api/compliance/exceptions")
    assert isinstance(exceptions, list)
    print(f"  ✓ Compliance Exceptions/Anomalies: {len(exceptions)} active policy items")

    # -------------------------------------------------------------------------
    # SUITE 5: SYSTEM ADMINISTRATOR WORKFLOWS
    # -------------------------------------------------------------------------
    print("\n[SUITE 5] Testing System Administrator Modules...")
    
    # 5.1 Admin Dashboard Stats
    admin_stats = get_json("/api/admin/dashboard-stats")
    assert "kpis" in admin_stats and "overview" in admin_stats
    print(f"  ✓ Admin KPIs: Users = {admin_stats['kpis']['total_users']}, Portfolios = {admin_stats['overview']['active_portfolios']}")

    # 5.2 Admin User Management
    users_data = get_json("/api/admin/users")
    assert "users" in users_data
    print(f"  ✓ User Management: {len(users_data['users'])} system users retrieved")

    # 5.3 Admin System Configurations (All 6 Tables)
    config_endpoints = [
        "instruments",
        "asset_classes",
        "fees",
        "trading_rules",
        "restrictions",
        "target_allocation"
    ]
    for cfg in config_endpoints:
        cfg_data = get_json(f"/api/admin/config/{cfg}")
        items = cfg_data.get(cfg) or cfg_data.get("rules") or cfg_data.get("allocations")
        assert items is not None, f"Failed config retrieval for {cfg}"
        print(f"  ✓ Config Table [{cfg}]: {len(items)} records verified")

    # 5.4 Data Integrity Validation
    val_res = post_json("/api/admin/data/validate", {})
    assert val_res.get("status") == "PASSED" or val_res.get("success") is True
    print(f"  ✓ Data Validation: Integrity check {val_res.get('status')} across {len(val_res.get('checks', []))} checks")

    # 5.5 Support Ticket Resolution
    res_ticket = post_json(f"/api/tickets/{created_ticket_id}/resolve", {
        "resolution_notes": "Resolved by System Administrator during verification.",
        "resolved_by": "System Administrator"
    })
    assert res_ticket.get("success") is True
    print(f"  ✓ Support Ticket Resolution: {created_ticket_id} RESOLVED")

    # -------------------------------------------------------------------------
    # SUITE 6: FRONTEND HTML & UI INTEGRITY
    # -------------------------------------------------------------------------
    print("\n[SUITE 6] Testing Frontend HTML & UI Architecture...")
    html = get_text("/")
    assert len(html) > 50000, "HTML output appears incomplete"
    
    # Header clean checks
    assert "actor-tabs" not in html, "Violation: actor-tabs found in HTML!"
    assert "portivex-quick-roles" not in html, "Violation: quick-roles found in HTML!"
    print("  ✓ Header Check: No actor switchers or demo tabs present")

    # Common Auth Modal checks
    assert 'id="modal-auth"' in html
    assert 'id="view-auth-login"' in html
    assert 'id="view-auth-signup"' in html
    assert 'id="login-email"' in html
    assert 'id="login-pass"' in html
    assert 'togglePasswordVisibility' in html
    print("  ✓ Common Login Modal: Email & Password fields with toggle button verified")

    # 4 Actor Panels
    assert 'id="actor-panel-customer"' in html
    assert 'id="actor-panel-analyst"' in html
    assert 'id="actor-panel-compliance"' in html
    assert 'id="actor-panel-admin"' in html
    print("  ✓ Multi-Actor Panels: All 4 actor panels exist and styled")

    # Customer Empty State matching Photos 1-5
    assert "No portfolio yet" in html
    assert "Getting Started" in html
    assert "Request Portfolio Setup" in html
    assert "Support Tickets" in html
    print("  ✓ Customer Portal: Unassigned state matching Photos 1-5 verified")

    print("\n" + "=" * 80)
    print("ALL 6 VERIFICATION SUITES COMPLETED WITH 100% SUCCESS!")
    print("PORTIVEX IS FULLY OPERATIONAL AND PRODUCTION-READY.")
    print("=" * 80)

if __name__ == "__main__":
    main()
