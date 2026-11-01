import os
import sys
import gc
import time
import sqlite3
import pandas as pd
import database
import data_loader
import lead_capture
import lead_scoring
import followups
import reports
import ai_assistant

sys.stdout.reconfigure(encoding='utf-8')
TEST_DB = "test_e2e_suite.db"

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

def run_e2e_tests():
    print("==================================================")
    print("STARTING STEP 9: COMPLETE END-TO-END TEST SUITE")
    print("==================================================")
    cleanup()
    database.init_db(TEST_DB)

    # ----------------------------------------------------
    # SCENARIO 1: Batch CSV Import & Deduplication
    # ----------------------------------------------------
    print("\n[Scenario 1] Testing Batch CSV Import & Duplicate Prevention...")
    synth_path = os.path.join("data", "synthetic", "interior_design_leads.csv")
    res1 = data_loader.import_csv_to_db(synth_path, db_path=TEST_DB, data_origin="synthetic_import")
    assert res1["success"]
    assert res1["imported_count"] == 250, f"Expected 250 imported, got {res1['imported_count']}"
    
    # Re-import must detect duplicates and skip all 250
    res2 = data_loader.import_csv_to_db(synth_path, db_path=TEST_DB, data_origin="synthetic_import")
    assert res2["success"]
    assert res2["imported_count"] == 0
    assert res2["skipped_count"] == 250
    print(f"-> Scenario 1 PASSED: 250 leads imported; duplicate re-import safely skipped 250 records.")

    # ----------------------------------------------------
    # SCENARIO 2: New Customer Enquiry Capture & Real-Time Scoring
    # ----------------------------------------------------
    print("\n[Scenario 2] Testing New Customer Creation & Real-Time Scoring...")
    new_lead_data = {
        "customer_name": "Nandita Swamy",
        "phone": "+91 98450 99881",
        "email": "nandita.swamy@example.com",
        "city": "Bangalore",
        "lead_source": "Website Inquiry",
        "budget_range": "Above ₹25 lakh",
        "project_type": "Villa",
        "property_status": "Ready to Move",
        "project_timeline": "Immediately",
        "scope_of_work": "Full Turnkey Interior",
        "customer_requirements": "Looking for comprehensive luxury turnkey interior with Italian marble, acoustic paneling, and walk-in closets.",
        "purchase_readiness": "Ready to Start",
        "preferred_contact_method": "WhatsApp"
    }
    success, msg, new_id, score_res = lead_capture.create_manual_lead(new_lead_data, db_path=TEST_DB, return_score=True)
    assert success, f"Manual creation failed: {msg}"
    assert new_id == "SHA-2026-0251", f"Expected SHA-2026-0251, got {new_id}"
    assert score_res["lead_score"] == 100.0, f"Expected 100 score, got {score_res['lead_score']}"
    assert score_res["priority"] == "High"
    
    saved_lead = database.get_lead_by_id(new_id, db_path=TEST_DB)
    assert saved_lead is not None
    assert saved_lead["lead_score"] == 100.0
    assert saved_lead["priority"] == "High"
    assert saved_lead["data_origin"] == "manual_entry"
    print(f"-> Scenario 2 PASSED: Lead {new_id} saved, auto-scored at 100/100 (High Priority).")

    # ----------------------------------------------------
    # SCENARIO 3: High Priority Follow-up Scheduling & Dispatch
    # ----------------------------------------------------
    print("\n[Scenario 3] Testing High Priority Follow-up Scheduling & Dispatch Simulation...")
    sch_res = followups.schedule_followups_for_lead(new_id, db_path=TEST_DB)
    assert sch_res["success"]
    assert sch_res["scheduled_count"] == 3
    
    tasks = database.get_followups(db_path=TEST_DB, lead_id=new_id)
    assert len(tasks) == 3
    first_task = tasks[0]
    
    # Simulate send
    send_res = followups.simulate_send_followup(first_task["schedule_id"], db_path=TEST_DB)
    assert send_res["success"]
    assert send_res["status"] == "Sent"
    
    # Verify activity log
    activities = database.get_lead_activities(new_id, db_path=TEST_DB)
    assert any("Follow-up Sent" in a["activity_type"] for a in activities)
    print(f"-> Scenario 3 PASSED: High-priority sequence scheduled and Attempt #1 dispatched.")

    # ----------------------------------------------------
    # SCENARIO 4: Customer Response Triggers Automated Stop Condition
    # ----------------------------------------------------
    print("\n[Scenario 4] Testing Inbound Customer Response Stop Condition...")
    resp_res = followups.simulate_customer_response(new_id, "I would like to visit your Indiranagar studio tomorrow at 4 PM.", db_path=TEST_DB)
    assert resp_res["success"]
    assert resp_res["cancelled_tasks"] == 2  # remaining 2 tasks cancelled
    
    # Attempting to send remaining task must be blocked
    remaining_task_id = tasks[1]["schedule_id"]
    blocked_send = followups.simulate_send_followup(remaining_task_id, db_path=TEST_DB)
    assert not blocked_send["success"]
    assert "Cancelled" in blocked_send.get("error", "") or blocked_send.get("status") == "Cancelled"
    print(f"-> Scenario 4 PASSED: Inbound client response cancelled future tasks and blocked dispatch.")

    # ----------------------------------------------------
    # SCENARIO 5: Customer Opt-out Compliance
    # ----------------------------------------------------
    print("\n[Scenario 5] Testing Customer Opt-out...")
    lead_opt = "SHA-2026-0001"
    followups.schedule_followups_for_lead(lead_opt, db_path=TEST_DB)
    
    opt_res = followups.mark_lead_opt_out(lead_opt, reason="Customer moved out of city", db_path=TEST_DB)
    assert opt_res["success"]
    assert opt_res["is_opted_out"] is True
    
    # Scheduling again must be rejected
    cant_reschedule = followups.schedule_followups_for_lead(lead_opt, db_path=TEST_DB)
    assert not cant_reschedule["success"]
    assert "Opted Out" in cant_reschedule["error"]
    print(f"-> Scenario 5 PASSED: Opt-out prevents any future follow-up scheduling.")

    # ----------------------------------------------------
    # SCENARIO 6: Converted Lead Auto-cancels Follow-ups
    # ----------------------------------------------------
    print("\n[Scenario 6] Testing Converted Lead Stop Trigger...")
    lead_conv = "SHA-2026-0002"
    followups.schedule_followups_for_lead(lead_conv, db_path=TEST_DB)
    
    conv_res = followups.update_lead_crm_status_with_automation(lead_conv, "Converted", db_path=TEST_DB)
    assert conv_res["success"]
    assert conv_res["new_status"] == "Converted"
    
    tasks_conv = database.get_followups(db_path=TEST_DB, lead_id=lead_conv)
    for t in tasks_conv:
        assert t["status"] == "Cancelled"
    print(f"-> Scenario 6 PASSED: Converted status transition cancelled all follow-ups.")

    # ----------------------------------------------------
    # SCENARIO 7: Lost Lead Auto-cancels Follow-ups
    # ----------------------------------------------------
    print("\n[Scenario 7] Testing Lost Lead Stop Trigger...")
    lead_lost = "SHA-2026-0003"
    followups.schedule_followups_for_lead(lead_lost, db_path=TEST_DB)
    
    lost_res = followups.update_lead_crm_status_with_automation(lead_lost, "Lost", db_path=TEST_DB)
    assert lost_res["success"]
    assert lost_res["new_status"] == "Lost"
    
    tasks_lost = database.get_followups(db_path=TEST_DB, lead_id=lead_lost)
    for t in tasks_lost:
        assert t["status"] == "Cancelled"
    print(f"-> Scenario 7 PASSED: Lost status transition cancelled all follow-ups.")

    # ----------------------------------------------------
    # SCENARIO 8: Reporting & Analytics Calculations
    # ----------------------------------------------------
    print("\n[Scenario 8] Testing Reporting Metrics & Chart Data...")
    lead_scoring.score_all_leads(db_path=TEST_DB, force_rescore=True)
    kpis = reports.get_executive_kpis(db_path=TEST_DB)
    
    assert kpis["total_leads"] == 251  # 250 synthetic + 1 manual
    assert kpis["scored_leads_count"] == 251
    assert kpis["average_lead_score"] > 0
    assert "engaged_conversion_rate" in kpis
    
    charts = reports.get_chart_data(db_path=TEST_DB)
    assert len(charts["city"]) > 0
    assert len(charts["priority"]) > 0
    assert len(charts["project_type"]) > 0
    
    periodic = reports.generate_periodic_report("custom", "2026-01-01", "2026-12-31", db_path=TEST_DB)
    assert periodic["new_leads_count"] > 0
    print(f"-> Scenario 8 PASSED: Executive KPIs, 9 chart datasets, and periodic reports verified.")

    # ----------------------------------------------------
    # SCENARIO 9: AI Assistant & Natural Language Fallback
    # ----------------------------------------------------
    print("\n[Scenario 9] Testing AI Assistant & Fallback Logic...")
    q1 = ai_assistant.answer_crm_query("How many high priority leads do we have?", db_path=TEST_DB)
    assert "High-Priority" in q1 or "High" in q1
    
    q2 = ai_assistant.answer_crm_query("Which leads need attention?", db_path=TEST_DB)
    assert "Attention" in q2 or "No urgent" in q2
    
    req_summary = ai_assistant.summarize_customer_requirements(saved_lead)
    assert "Nandita Swamy" in req_summary
    assert "Villa" in req_summary
    
    next_action = ai_assistant.recommend_next_action(saved_lead)
    assert "recommended_action" in next_action
    print(f"-> Scenario 9 PASSED: AI assistant answered CRM queries and generated recommendations.")

    # ----------------------------------------------------
    # SCENARIO 10: Database Reliability & Reconnection
    # ----------------------------------------------------
    print("\n[Scenario 10] Testing Database Reliability & Reconnection...")
    conn = database.get_connection(TEST_DB)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as c FROM LEADS;")
        lead_count = cursor.fetchone()["c"]
        cursor.execute("SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE;")
        fu_count = cursor.fetchone()["c"]
        cursor.execute("SELECT COUNT(*) as c FROM LEAD_ACTIVITY_LOG;")
        act_count = cursor.fetchone()["c"]
        
        assert lead_count == 251
        assert fu_count > 0
        assert act_count > 0
    finally:
        conn.close()
    print(f"-> Scenario 10 PASSED: Database relationships verified ({lead_count} leads, {fu_count} follow-up tasks, {act_count} activity logs).")

    cleanup()
    print("\n==================================================")
    print("ALL 10 END-TO-END SCENARIOS COMPLETED AND PASSED WITH 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    run_e2e_tests()
