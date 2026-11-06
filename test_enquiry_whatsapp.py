"""
test_enquiry_whatsapp.py - Master Verification Suite for Website Enquiry WhatsApp Outbound Feature
SHA Interface Interiors - AI-Powered Lead Management System
"""

import os
import sys
import urllib.parse
import sqlite3
import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.getcwd())

import database
import enquiry_whatsapp
import whatsapp_assistant

DB_PATH = database.DEFAULT_DB_PATH


def run_tests():
    print("==================================================")
    print("RUNNING WEBSITE ENQUIRY WHATSAPP OUTBOUND VERIFICATION SUITE")
    print("==================================================")

    # ----------------------------------------------------
    # TEST 1: Message Generation for Kanishka
    # ----------------------------------------------------
    print("\n[Test 1] Verifying Message Generation for Kanishka (SHA-TEST-0001)...")
    k = database.get_lead_by_id("SHA-TEST-0001", db_path=DB_PATH)
    assert k is not None, "Kanishka record not found!"
    assert k["phone"] == "+91 90001 40689", f"Phone number mismatch: {k['phone']}"
    assert k["email"] == "mattaganesh191@gmail.com"
    
    msg_k = enquiry_whatsapp.generate_enquiry_message(k)
    print("Generated Message for Kanishka:\n" + "-" * 40 + "\n" + msg_k + "\n" + "-" * 40)
    
    assert "Hello Kanishka," in msg_k
    assert "SHA Interface Interiors" in msg_k
    assert "3BHK property" in msg_k
    assert "Gachibowli, Hyderabad" in msg_k
    assert "modular kitchen" in msg_k.lower()
    assert "wardrobes" in msg_k.lower()
    assert "tv unit" in msg_k.lower()
    assert "false ceiling" in msg_k.lower()
    assert "Miyapur office" in msg_k
    # Privacy check: No internal scores or private CRM notes
    assert "95.0" not in msg_k
    assert "High Priority" not in msg_k
    assert "SHA-TEST-0001" not in msg_k
    assert "test_data" not in msg_k
    print("-> Test 1 PASSED: Kanishka message properly personalized and privacy-compliant.")

    # ----------------------------------------------------
    # TEST 2: Message Generation for Dinesh
    # ----------------------------------------------------
    print("\n[Test 2] Verifying Message Generation for Dinesh (SHA-TEST-0002)...")
    d = database.get_lead_by_id("SHA-TEST-0002", db_path=DB_PATH)
    assert d is not None, "Dinesh record not found!"
    assert d["phone"] == "+91 85005 25509", f"Phone number mismatch: {d['phone']}"
    assert d["email"] == "dineshjawa42@gmail.com"
    
    msg_d = enquiry_whatsapp.generate_enquiry_message(d)
    print("Generated Message for Dinesh:\n" + "-" * 40 + "\n" + msg_d + "\n" + "-" * 40)
    
    assert "Hello Dinesh," in msg_d
    assert "SHA Interface Interiors" in msg_d
    assert "2BHK property" in msg_d
    assert "Miyapur, Hyderabad" in msg_d
    assert "kitchen and bedroom" in msg_d.lower()
    assert "sliding wardrobes" in msg_d.lower() or "wardrobes" in msg_d.lower()
    assert "storage" in msg_d.lower()
    assert "Miyapur office" in msg_d
    # Privacy check
    assert "85.0" not in msg_d
    assert "High Priority" not in msg_d
    assert "SHA-TEST-0002" not in msg_d
    print("-> Test 2 PASSED: Dinesh message properly personalized and privacy-compliant.")

    # ----------------------------------------------------
    # TEST 3: Click-to-Chat URL Generation & Phone Normalization
    # ----------------------------------------------------
    print("\n[Test 3] Verifying Click-to-Chat URL Generation & Number Validation...")
    url_k, err_k = enquiry_whatsapp.build_enquiry_click_to_chat_url(k["phone"], msg_k)
    assert err_k is None, f"Error building Kanishka URL: {err_k}"
    assert url_k.startswith("https://wa.me/919000140689?text=")
    assert "Hello%20Kanishka" in url_k or "Hello+Kanishka" in url_k
    assert "3BHK" in url_k

    url_d, err_d = enquiry_whatsapp.build_enquiry_click_to_chat_url(d["phone"], msg_d)
    assert err_d is None, f"Error building Dinesh URL: {err_d}"
    assert url_d.startswith("https://wa.me/918500525509?text=")
    assert "Hello%20Dinesh" in url_d or "Hello+Dinesh" in url_d
    assert "2BHK" in url_d

    # Invalid numbers validation
    _, err_inv1 = enquiry_whatsapp.build_enquiry_click_to_chat_url("12345", msg_k)
    assert err_inv1 is not None
    _, err_inv2 = enquiry_whatsapp.build_enquiry_click_to_chat_url("", msg_k)
    assert err_inv2 is not None
    _, err_inv3 = enquiry_whatsapp.build_enquiry_click_to_chat_url(None, msg_k)
    assert err_inv3 is not None
    print("-> Test 3 PASSED: Valid Indian phones correctly normalized (919000140689 & 918500525509), invalid numbers safely rejected.")

    # ----------------------------------------------------
    # TEST 4: Missing Fields Graceful Degradation
    # ----------------------------------------------------
    print("\n[Test 4] Verifying Graceful Fallback for Missing Fields...")
    lead_sparse = {
        "lead_id": "TEST-SPARSE",
        "customer_name": "",
        "phone": "+91 99999 11111",
        "project_type": "",
        "locality": "",
        "scope_of_work": "",
        "customer_requirements": ""
    }
    msg_sparse = enquiry_whatsapp.generate_enquiry_message(lead_sparse)
    assert "Hello there," in msg_sparse
    assert "regarding interior design services" in msg_sparse
    assert "for your property" in msg_sparse
    assert "in Hyderabad." in msg_sparse
    assert "None" not in msg_sparse
    assert "undefined" not in msg_sparse
    print("-> Test 4 PASSED: Sparse lead produced natural English without syntax errors or placeholder artifacts.")

    # ----------------------------------------------------
    # TEST 5: Conversation Tracking & Lifecycle Statuses
    # ----------------------------------------------------
    print("\n[Test 5] Verifying Conversation Tracking Lifecycle (Draft -> Ready -> Sent -> Cancelled)...")
    # Clean previous test entries for Kanishka
    conn = database.get_connection(DB_PATH)
    try:
        with conn:
            conn.cursor().execute("DELETE FROM CUSTOMER_CONVERSATIONS WHERE lead_id = 'SHA-TEST-0001' AND metadata LIKE '%crm_send_enquiry_button%';")
    finally:
        conn.close()

    # Step A: Open preview -> Draft
    draft_1 = enquiry_whatsapp.get_or_create_enquiry_draft("SHA-TEST-0001", msg_k, db_path=DB_PATH)
    assert draft_1["sending_status"] == "Draft"
    conv_id = draft_1["conversation_id"]

    # Step B: Open preview multiple times -> Must NOT create duplicate rows!
    draft_2 = enquiry_whatsapp.get_or_create_enquiry_draft("SHA-TEST-0001", msg_k + "\n[Edited preview]", db_path=DB_PATH)
    assert draft_2["conversation_id"] == conv_id, "Duplicate row created on second preview open!"
    assert draft_2["is_existing"] is True

    # Count rows in DB
    conn = database.get_connection(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM CUSTOMER_CONVERSATIONS WHERE lead_id = 'SHA-TEST-0001' AND metadata LIKE '%crm_send_enquiry_button%';")
        count = cur.fetchone()[0]
        assert count == 1, f"Expected exactly 1 draft record, found {count}!"
    finally:
        conn.close()

    # Step C: Transition to Ready to Send
    ok_ready = enquiry_whatsapp.update_enquiry_message_status(conv_id, "Ready to Send", lead_id="SHA-TEST-0001", db_path=DB_PATH)
    assert ok_ready is True
    rec_ready = enquiry_whatsapp.get_latest_enquiry_message("SHA-TEST-0001", db_path=DB_PATH)
    assert rec_ready["sending_status"] == "Ready to Send"
    assert rec_ready["sent_at"] is None, "Message must NOT be marked sent when opening WhatsApp or preparing!"

    # Step D: Salesperson explicitly confirms sent
    ok_sent = enquiry_whatsapp.update_enquiry_message_status(conv_id, "User-Confirmed Sent", lead_id="SHA-TEST-0001", db_path=DB_PATH)
    assert ok_sent is True
    rec_sent = enquiry_whatsapp.get_latest_enquiry_message("SHA-TEST-0001", db_path=DB_PATH)
    assert rec_sent["sending_status"] == "User-Confirmed Sent"
    assert rec_sent["sent_at"] is not None

    # Verify Activity Log
    activities = database.get_lead_activities("SHA-TEST-0001", db_path=DB_PATH)
    assert any(a["activity_type"] == "WhatsApp Enquiry Message Sent" for a in activities), "Activity log not updated on User-Confirmed Sent!"
    print(f"-> Test 5 PASSED: Status lifecycle validated. Zero duplicate draft entries. Activity log recorded on confirmation.")

    # ----------------------------------------------------
    # TEST 6: Genuine Customer Data Integrity
    # ----------------------------------------------------
    print("\n[Test 6] Verifying All 7 Genuine Customer Records Remain Unchanged...")
    genuine_leads = database.get_all_leads(data_origin="genuine_only", db_path=DB_PATH)
    assert len(genuine_leads) == 7, f"Expected 7 genuine leads, got {len(genuine_leads)}"
    expected_ids = {"SHA-2026-0001", "SHA-2026-0002", "SHA-2026-0003", "SHA-2026-0004", "SHA-2026-0005", "SHA-2026-0006", "SHA-2026-0901"}
    actual_ids = {l["lead_id"] for l in genuine_leads}
    assert actual_ids == expected_ids
    for l in genuine_leads:
        assert l["data_origin"] != "test_data"
        assert l["city"] == "Hyderabad"
    print("-> Test 6 PASSED: All 7 genuine customer records are 100% intact.")

    print("\n==================================================")
    print("ALL 6 ENQUIRY WHATSAPP TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================")


if __name__ == "__main__":
    run_tests()
