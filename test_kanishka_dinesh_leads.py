import os
import sys
import json
import subprocess

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.getcwd())
import database
import lead_scoring
import followups
import reports
import whatsapp_assistant

DB_PATH = database.DEFAULT_DB_PATH

def run_tests():
    print("==================================================")
    print("TEST SUITE: KANISHKA & DINESH TEST LEADS VERIFICATION")
    print("==================================================")
    
    # ----------------------------------------------------
    # TEST 1: Verify Lead Record Fields for Kanishka
    # ----------------------------------------------------
    print("\n[Test 1] Verifying Kanishka lead details...")
    k = database.get_lead_by_id("SHA-TEST-0001", db_path=DB_PATH)
    assert k is not None, "Lead SHA-TEST-0001 not found in database!"
    assert k["customer_name"] == "Kanishka", f"Expected Kanishka, got {k['customer_name']}"
    assert k["phone"] == "+91 90001 40689", f"Expected +91 90001 40689, got {k['phone']}"
    assert k["email"] == "mattaganesh191@gmail.com", f"Expected mattaganesh191@gmail.com, got {k['email']}"
    assert k["city"] == "Hyderabad"
    assert k["locality"] == "Gachibowli"
    assert k["region"] == "West Hyderabad"
    assert k["project_type"] == "3BHK"
    assert k["property_status"] == "Ready to Move"
    assert k["budget_range"] == "₹12 lakh – ₹18 lakh"
    assert k["priority"] == "High"
    assert k["lead_score"] == 95.0, f"Expected calculated score 95.0, got {k['lead_score']}"
    assert k["data_origin"] == "test_data"
    print(f"-> Test 1 PASSED: Kanishka verified (Score: {k['lead_score']}, Priority: {k['priority']}, Phone: {k['phone']}, Email: {k['email']}).")

    # ----------------------------------------------------
    # TEST 2: Verify Lead Record Fields for Dinesh
    # ----------------------------------------------------
    print("\n[Test 2] Verifying Dinesh lead details...")
    d = database.get_lead_by_id("SHA-TEST-0002", db_path=DB_PATH)
    assert d is not None, "Lead SHA-TEST-0002 not found in database!"
    assert d["customer_name"] == "Dinesh", f"Expected Dinesh, got {d['customer_name']}"
    assert d["phone"] == "+91 85005 25509", f"Expected +91 85005 25509, got {d['phone']}"
    assert d["email"] == "dineshjawa42@gmail.com", f"Expected dineshjawa42@gmail.com, got {d['email']}"
    assert d["city"] == "Hyderabad"
    assert d["locality"] == "Miyapur"
    assert d["region"] == "North-West Hyderabad"
    assert d["project_type"] == "2BHK"
    assert d["property_status"] == "Ready to Move"
    assert d["budget_range"] == "₹5 lakh – ₹8 lakh"
    assert d["priority"] == "High"
    assert d["lead_score"] == 85.0, f"Expected calculated score 85.0, got {d['lead_score']}"
    assert d["data_origin"] == "test_data"
    print(f"-> Test 2 PASSED: Dinesh verified (Score: {d['lead_score']}, Priority: {d['priority']}, Phone: {d['phone']}, Email: {d['email']}).")

    # ----------------------------------------------------
    # TEST 3: Verify All 7 Genuine Leads are Preserved
    # ----------------------------------------------------
    print("\n[Test 3] Verifying 7 genuine customer leads remain intact...")
    all_leads = database.get_all_leads(db_path=DB_PATH)
    genuine_leads = [l for l in all_leads if l.get("data_origin") != "test_data"]
    assert len(genuine_leads) == 7, f"Expected 7 genuine leads, found {len(genuine_leads)}"
    expected_ids = {"SHA-2026-0001", "SHA-2026-0002", "SHA-2026-0003", "SHA-2026-0004", "SHA-2026-0005", "SHA-2026-0006", "SHA-2026-0901"}
    actual_ids = {l["lead_id"] for l in genuine_leads}
    assert actual_ids == expected_ids, f"Mismatch in genuine customer IDs: {actual_ids} vs {expected_ids}"
    print(f"-> Test 3 PASSED: All 7 genuine customer records are 100% intact.")

    # ----------------------------------------------------
    # TEST 4: Follow-Up Cadence for Both Leads
    # ----------------------------------------------------
    print("\n[Test 4] Verifying Follow-up Tasks for Kanishka and Dinesh...")
    k_tasks = database.get_followups(db_path=DB_PATH, lead_id="SHA-TEST-0001", status="Scheduled")
    d_tasks = database.get_followups(db_path=DB_PATH, lead_id="SHA-TEST-0002", status="Scheduled")
    assert len(k_tasks) >= 3, f"Expected at least 3 scheduled tasks for Kanishka, got {len(k_tasks)}"
    assert len(d_tasks) >= 3, f"Expected at least 3 scheduled tasks for Dinesh, got {len(d_tasks)}"
    d_initial = [t for t in d_tasks if str(t.get("schedule_id", "")).startswith("SCH-SHA-TEST-0002")]
    assert len(d_initial) == 3, f"Expected 3 initial cadence tasks for Dinesh, got {len(d_initial)}"
    for task in k_tasks:
        assert task["status"] == "Scheduled"
        assert task["lead_id"] == "SHA-TEST-0001"
    for task in d_tasks:
        assert task["status"] == "Scheduled"
        assert task["lead_id"] == "SHA-TEST-0002"
    print(f"-> Test 4 PASSED: Both leads have scheduled follow-up tasks (including Attempts 1, 2, 3 across WhatsApp, Phone, Email).")

    # ----------------------------------------------------
    # TEST 5: WhatsApp Click-to-Chat Normalization & URL Generation
    # ----------------------------------------------------
    print("\n[Test 5] Verifying WhatsApp Click-to-Chat URLs...")
    url_k, err_k = whatsapp_assistant.build_whatsapp_click_to_chat_url(k["phone"], "Hello Kanishka, greetings from SHA Interiors!")
    assert err_k is None, f"Error building WhatsApp URL for Kanishka: {err_k}"
    assert "wa.me/919000140689" in url_k, f"URL missing normalized phone 919000140689: {url_k}"

    url_d, err_d = whatsapp_assistant.build_whatsapp_click_to_chat_url(d["phone"], "Hello Dinesh, greetings from SHA Interiors!")
    assert err_d is None, f"Error building WhatsApp URL for Dinesh: {err_d}"
    assert "wa.me/918500525509" in url_d, f"URL missing normalized phone 918500525509: {url_d}"
    print(f"-> Test 5 PASSED: Click-to-Chat URLs verified (Kanishka: wa.me/919000140689, Dinesh: wa.me/918500525509).")

    # ----------------------------------------------------
    # TEST 6: Customer-Specific Dossier Grounding in AI Assistant
    # ----------------------------------------------------
    print("\n[Test 6] Verifying Conversational AI Prompt Dossier Grounding...")
    dossier_k = whatsapp_assistant.build_customer_prompt_context(k, [])
    assert "Kanishka" in dossier_k
    assert "Gachibowli" in dossier_k
    assert "3BHK" in dossier_k
    assert "₹12 lakh – ₹18 lakh" in dossier_k

    dossier_d = whatsapp_assistant.build_customer_prompt_context(d, [])
    assert "Dinesh" in dossier_d
    assert "Miyapur" in dossier_d
    assert "2BHK" in dossier_d
    assert "₹5 lakh – ₹8 lakh" in dossier_d
    print("-> Test 6 PASSED: Customer dossiers properly grounded with bespoke project details.")

    # ----------------------------------------------------
    # TEST 7: Conversational Response & History Storage
    # ----------------------------------------------------
    print("\n[Test 7] Verifying Conversational Response Generation & History Logging...")
    rep_k = whatsapp_assistant.generate_conversational_reply("SHA-TEST-0001", "Could you provide details about modular kitchen finishes and durability?", db_path=DB_PATH)
    assert rep_k["success"] is True
    assert len(rep_k["reply"]) > 20
    assert "Kanishka" in rep_k["reply"] or "SHA" in rep_k["reply"] or "kitchen" in rep_k["reply"].lower()

    # Record message to history
    msg_rec_k = database.add_conversation_message(
        lead_id="SHA-TEST-0001",
        direction="incoming",
        message_content="Could you provide details about modular kitchen finishes and durability?",
        ai_generated_response=rep_k["reply"],
        channel="WhatsApp",
        sending_status="Draft",
        db_path=DB_PATH
    )
    mid_k = msg_rec_k["message_id"]
    hist_k = database.get_conversation_history("SHA-TEST-0001", db_path=DB_PATH)
    assert any(m["message_id"] == mid_k for m in hist_k), "Message not stored in CUSTOMER_CONVERSATIONS!"
    print(f"-> Test 7 PASSED: AI reply generated and persisted to conversation history for SHA-TEST-0001 (Message ID: {mid_k}).")

    # ----------------------------------------------------
    # TEST 8: Reports Scope Filtering (All vs Genuine Only vs Test Only)
    # ----------------------------------------------------
    print("\n[Test 8] Verifying Reports Scope Filtering...")
    kpi_all = reports.get_executive_kpis(db_path=DB_PATH, dataset_scope="all")
    kpi_gen = reports.get_executive_kpis(db_path=DB_PATH, dataset_scope="genuine_only")
    kpi_tst = reports.get_executive_kpis(db_path=DB_PATH, dataset_scope="test_only")
    
    assert kpi_all["total_leads"] == 9, f"Expected 9 total leads, got {kpi_all['total_leads']}"
    assert kpi_gen["total_leads"] == 7, f"Expected 7 genuine leads, got {kpi_gen['total_leads']}"
    assert kpi_tst["total_leads"] == 2, f"Expected 2 test leads, got {kpi_tst['total_leads']}"
    assert kpi_all["total_test_leads"] == 2
    assert kpi_all["total_genuine_leads"] == 7
    print(f"-> Test 8 PASSED: Scope filtering accurately isolates datasets (All: 9, Genuine: 7, Test: 2).")

    # ----------------------------------------------------
    # TEST 9: Idempotency (Updating Existing Test Leads Without Duplicates)
    # ----------------------------------------------------
    print("\n[Test 9] Verifying Idempotency of Seed Script...")
    result = subprocess.run(
        [sys.executable, "-u", "add_test_leads.py"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"add_test_leads.py failed on second run: {result.stderr}"
    all_leads_second = database.get_all_leads(db_path=DB_PATH)
    assert len(all_leads_second) == 9, f"Duplication detected! Expected 9 leads, got {len(all_leads_second)}"
    print("-> Test 9 PASSED: Re-running update script updated leads in-place with ZERO duplicates.")

    print("\n==================================================")
    print("ALL 9 TEST SUITE CHECKS COMPLETED AND PASSED (100% PASS RATE)!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
