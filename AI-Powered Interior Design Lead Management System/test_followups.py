import os
import sys
import gc
import time
import database
import followups

sys.stdout.reconfigure(encoding='utf-8')
TEST_DB = "test_followups.db"

def cleanup():
    gc.collect()
    time.sleep(0.1)
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except Exception:
            gc.collect()
            time.sleep(0.4)
            try:
                os.remove(TEST_DB)
            except Exception as e:
                print(f"Cleanup note: {e}")

def run_tests():
    print("==================================================")
    print("STARTING STEP 5: AUTOMATED FOLLOW-UPS TEST SUITE")
    print("==================================================")
    cleanup()
    database.init_db(TEST_DB)
    
    # ----------------------------------------------------
    # TEST 1: Scheduling Sequences across Priorities
    # ----------------------------------------------------
    print("\n[Test 1] Testing Scheduling Sequences for High, Medium, Low Priority...")
    leads = [
        {"lead_id": "LEAD-HP", "customer_name": "High Priority Client", "phone": "+91 98450 11111", "city": "Bangalore",
         "lead_source": "Website", "budget_range": "Above ₹25 lakh", "project_type": "Villa", "property_status": "Ready to Move",
         "project_timeline": "Immediately", "scope_of_work": "Full Turnkey Interior", "purchase_readiness": "Ready to Start",
         "priority": "High", "lead_status": "Qualified"},
        {"lead_id": "LEAD-MP", "customer_name": "Medium Priority Client", "phone": "+91 98450 22222", "city": "Mumbai",
         "lead_source": "Instagram", "budget_range": "₹5 lakh–₹10 lakh", "project_type": "2BHK", "property_status": "Ready to Move",
         "project_timeline": "Within 1 month", "scope_of_work": "Modular Kitchen", "purchase_readiness": "Comparing Vendors",
         "priority": "Medium", "lead_status": "New"},
        {"lead_id": "LEAD-LP", "customer_name": "Low Priority Client", "phone": "+91 98450 33333", "city": "Pune",
         "lead_source": "Search", "budget_range": "Below ₹3 lakh", "project_type": "1BHK", "property_status": "Under Construction",
         "project_timeline": "Within 6 months", "scope_of_work": "Wardrobe", "purchase_readiness": "Just Exploring",
         "priority": "Low", "lead_status": "New"}
    ]
    for l in leads:
        database.insert_lead(l, db_path=TEST_DB)
        
    res_hp = followups.schedule_followups_for_lead("LEAD-HP", db_path=TEST_DB)
    res_mp = followups.schedule_followups_for_lead("LEAD-MP", db_path=TEST_DB)
    res_lp = followups.schedule_followups_for_lead("LEAD-LP", db_path=TEST_DB)
    
    assert res_hp["scheduled_count"] == 3, f"Expected 3 tasks for High Priority, got {res_hp['scheduled_count']}"
    assert res_mp["scheduled_count"] == 3, f"Expected 3 tasks for Medium Priority, got {res_mp['scheduled_count']}"
    assert res_lp["scheduled_count"] == 2, f"Expected 2 tasks for Low Priority, got {res_lp['scheduled_count']}"
    print(f"-> Test 1 PASSED: High (3), Medium (3), Low (2) follow-up tasks scheduled.")

    # ----------------------------------------------------
    # TEST 2: Stop Condition - Converted Lead
    # ----------------------------------------------------
    print("\n[Test 2] Testing Stop Condition: Converted Lead...")
    lead_conv = {"lead_id": "LEAD-CONV", "customer_name": "Converted Client", "phone": "+91 98450 44444", "city": "Bangalore",
                 "lead_source": "Referral", "budget_range": "₹10 lakh–₹25 lakh", "project_type": "3BHK", "property_status": "Ready",
                 "project_timeline": "Immediately", "scope_of_work": "Full Turnkey", "purchase_readiness": "Ready to Start",
                 "priority": "High", "lead_status": "Converted"}
    database.insert_lead(lead_conv, db_path=TEST_DB)
    res_conv = followups.schedule_followups_for_lead("LEAD-CONV", db_path=TEST_DB)
    assert not res_conv["success"], "Should not schedule follow-up for Converted lead!"
    assert "Converted" in res_conv["error"]
    print("-> Test 2 PASSED: Converted lead rejected from scheduling.")

    # ----------------------------------------------------
    # TEST 3: Stop Condition - Lost Lead
    # ----------------------------------------------------
    print("\n[Test 3] Testing Stop Condition: Lost Lead...")
    lead_lost = {"lead_id": "LEAD-LOST", "customer_name": "Lost Client", "phone": "+91 98450 55555", "city": "Chennai",
                 "lead_source": "Search", "budget_range": "₹3 lakh–₹5 lakh", "project_type": "1BHK", "property_status": "Under Construction",
                 "project_timeline": "Within 6 months", "scope_of_work": "Wardrobe", "purchase_readiness": "Just Exploring",
                 "priority": "Low", "lead_status": "Lost"}
    database.insert_lead(lead_lost, db_path=TEST_DB)
    res_lost = followups.schedule_followups_for_lead("LEAD-LOST", db_path=TEST_DB)
    assert not res_lost["success"], "Should not schedule follow-up for Lost lead!"
    assert "Lost" in res_lost["error"]
    print("-> Test 3 PASSED: Lost lead rejected from scheduling.")

    # ----------------------------------------------------
    # TEST 4: Stop Condition - Customer Opt-out
    # ----------------------------------------------------
    print("\n[Test 4] Testing Stop Condition: Customer Opt-out...")
    # LEAD-HP has 3 scheduled tasks. Now mark opted-out:
    opt_res = followups.mark_lead_opt_out("LEAD-HP", reason="Customer chose alternate vendor", db_path=TEST_DB)
    assert opt_res["success"], "Opt-out failed"
    assert opt_res["cancelled_tasks"] == 3, f"Expected 3 cancelled tasks, got {opt_res['cancelled_tasks']}"
    
    # Verify tasks are marked Cancelled in DB
    hp_tasks = database.get_followups(db_path=TEST_DB, lead_id="LEAD-HP")
    for t in hp_tasks:
        assert t["status"] == "Cancelled"
        assert "Opted Out" in t["stop_reason"]
    print("-> Test 4 PASSED: Opt-out cancelled all 3 pending tasks and updated audit log.")

    # ----------------------------------------------------
    # TEST 5: Stop Condition - Customer Inbound Response
    # ----------------------------------------------------
    print("\n[Test 5] Testing Stop Condition: Customer Inbound Response...")
    # LEAD-MP has 3 scheduled tasks. Simulate customer WhatsApp response:
    resp_res = followups.simulate_customer_response("LEAD-MP", "Hi! Yes, I want a site visit this Saturday at 11 AM.", db_path=TEST_DB)
    assert resp_res["success"], "Customer response simulation failed"
    assert resp_res["cancelled_tasks"] == 3, f"Expected 3 cancelled tasks, got {resp_res['cancelled_tasks']}"
    
    # Try sending next task - should be blocked
    mp_tasks = database.get_followups(db_path=TEST_DB, lead_id="LEAD-MP")
    first_task = mp_tasks[0]
    send_res = followups.simulate_send_followup(first_task["schedule_id"], db_path=TEST_DB)
    assert not send_res["success"], "Cancelled task should not be sent!"
    print("-> Test 5 PASSED: Inbound customer response cancelled all future tasks and blocked further automated sends.")

    # ----------------------------------------------------
    # TEST 6: Terminal Status Transition Automatically Cancels Tasks
    # ----------------------------------------------------
    print("\n[Test 6] Testing Status Transition to Converted Cancels Tasks...")
    # LEAD-LP has 2 scheduled tasks. Transition to Converted:
    status_res = followups.update_lead_crm_status_with_automation("LEAD-LP", "Converted", db_path=TEST_DB)
    assert status_res["success"]
    assert status_res["cancelled_tasks"] == 2
    
    lp_tasks = database.get_followups(db_path=TEST_DB, lead_id="LEAD-LP")
    for t in lp_tasks:
        assert t["status"] == "Cancelled"
        assert "Converted" in t["stop_reason"]
    print("-> Test 6 PASSED: Transitioning to 'Converted' cancelled 2 scheduled tasks.")

    # ----------------------------------------------------
    # TEST 7: Idempotency - Prevent Duplicate Sending
    # ----------------------------------------------------
    print("\n[Test 7] Testing Idempotency on Send Simulation...")
    # Create fresh lead and single scheduled follow-up
    lead_idemp = {"lead_id": "LEAD-IDEMP", "customer_name": "Idempotency Client", "phone": "+91 98450 66666", "city": "Bangalore",
                  "lead_source": "Website", "budget_range": "₹10 lakh–₹25 lakh", "project_type": "3BHK", "property_status": "Ready",
                  "project_timeline": "Immediately", "scope_of_work": "Full Turnkey", "purchase_readiness": "Ready to Start",
                  "priority": "High", "lead_status": "New"}
    database.insert_lead(lead_idemp, db_path=TEST_DB)
    followups.schedule_followups_for_lead("LEAD-IDEMP", db_path=TEST_DB)
    
    idemp_tasks = database.get_followups(db_path=TEST_DB, lead_id="LEAD-IDEMP")
    t1 = idemp_tasks[0]["schedule_id"]
    
    # First send -> Should succeed
    send1 = followups.simulate_send_followup(t1, db_path=TEST_DB)
    assert send1["success"], f"First send failed: {send1.get('error')}"
    assert send1["status"] == "Sent"
    
    # Second send -> MUST fail due to Idempotency Guard!
    send2 = followups.simulate_send_followup(t1, db_path=TEST_DB)
    assert not send2["success"], "Second send must be rejected by idempotency guard!"
    assert "Idempotency Guard" in send2["error"]
    print("-> Test 7 PASSED: Idempotency guard successfully blocked duplicate message dispatch.")

    # ----------------------------------------------------
    # TEST 8: Activity Log Verification
    # ----------------------------------------------------
    print("\n[Test 8] Testing Lead Activity Log Audit Trail...")
    activities = database.get_lead_activities("LEAD-IDEMP", db_path=TEST_DB)
    assert len(activities) >= 2, f"Expected at least 2 activity logs, got {len(activities)}"
    types = [a["activity_type"] for a in activities]
    assert any("Follow-up Sent" in t for t in types)
    assert any("Scheduled" in t for t in types)
    print(f"-> Test 8 PASSED: Comprehensive activity log entries verified ({len(activities)} recorded events).")

    cleanup()
    print("\n==================================================")
    print("ALL 8 STEP 5 FOLLOW-UP TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
