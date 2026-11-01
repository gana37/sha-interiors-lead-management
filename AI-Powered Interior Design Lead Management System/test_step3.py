import os
import sys
import sqlite3
import gc
import time
import pandas as pd
import database
import data_loader
import lead_capture

# Set UTF-8 output encoding
sys.stdout.reconfigure(encoding='utf-8')

TEST_DB = "test_sha_leads.db"

def cleanup():
    gc.collect()
    time.sleep(0.1)
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            gc.collect()
            time.sleep(0.5)
            try:
                os.remove(TEST_DB)
            except Exception as e:
                print(f"Note: Cleanup deferred: {e}")

def run_all_tests():
    print("==================================================")
    print("STARTING STEP 3 COMPREHENSIVE TEST SUITE")
    print("==================================================")
    cleanup()
    
    # ----------------------------------------------------
    # TEST 1: Database Initialization
    # ----------------------------------------------------
    print("\n[Test 1] Testing Database Initialization...")
    database.init_db(TEST_DB)
    assert os.path.exists(TEST_DB), "Test DB file was not created!"
    
    with sqlite3.connect(TEST_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='LEADS';")
        assert cursor.fetchone() is not None, "LEADS table does not exist!"
        
        cursor.execute("PRAGMA table_info(LEADS);")
        columns = [row[1] for row in cursor.fetchall()]
        expected_cols = [
            'lead_id', 'customer_name', 'phone', 'email', 'city', 'lead_source',
            'budget_range', 'project_type', 'property_status', 'project_timeline',
            'scope_of_work', 'customer_requirements', 'purchase_readiness',
            'preferred_contact_method', 'lead_status', 'created_at', 'updated_at', 'data_origin'
        ]
        for col in expected_cols:
            assert col in columns, f"Expected column '{col}' missing from LEADS table!"
    print("-> Test 1 PASSED: LEADS table and all 18 schema columns verified.")

    # ----------------------------------------------------
    # TEST 2: Successful CSV Import (Synthetic Dataset)
    # ----------------------------------------------------
    print("\n[Test 2] Testing CSV Import from synthetic dataset...")
    synth_csv = os.path.join("data", "synthetic", "interior_design_leads.csv")
    assert os.path.exists(synth_csv), f"Synthetic dataset {synth_csv} not found!"
    
    import_res = data_loader.import_csv_to_db(synth_csv, db_path=TEST_DB, data_origin="synthetic_import")
    assert import_res["success"], f"CSV Import failed: {import_res.get('error_message')}"
    assert import_res["imported_count"] == 250, f"Expected 250 imported leads, got {import_res['imported_count']}"
    assert import_res["skipped_count"] == 0, f"Expected 0 skipped leads on fresh DB, got {import_res['skipped_count']}"
    print(f"-> Test 2 PASSED: Successfully imported {import_res['imported_count']} synthetic leads.")

    # ----------------------------------------------------
    # TEST 3: Duplicate Lead Prevention
    # ----------------------------------------------------
    print("\n[Test 3] Testing Duplicate Lead Prevention...")
    # Attempting to re-import the same file should skip all records because lead_ids already exist
    reimport_res = data_loader.import_csv_to_db(synth_csv, db_path=TEST_DB, data_origin="synthetic_import")
    assert reimport_res["success"], "Re-import execution failed"
    assert reimport_res["imported_count"] == 0, f"Expected 0 re-imported leads, got {reimport_res['imported_count']}"
    assert reimport_res["skipped_count"] == 250, f"Expected 250 skipped duplicates, got {reimport_res['skipped_count']}"
    print(f"-> Test 3 PASSED: Duplicate prevention active; {reimport_res['skipped_count']} duplicate leads were safely skipped.")

    # ----------------------------------------------------
    # TEST 4: Missing Required Field Validation
    # ----------------------------------------------------
    print("\n[Test 4] Testing Missing Required Field Validation...")
    # Test manual validation logic
    is_valid, errors = lead_capture.validate_lead_inputs(
        customer_name="", # Empty name
        phone="123",      # Invalid phone
        email="notanemail",# Invalid email
        city="",          # Missing city
        budget_range="",  # Missing budget
        project_type="",  # Missing project type
        property_status="",
        project_timeline="",
        scope_of_work="",
        purchase_readiness=""
    )
    assert not is_valid, "Validation should have failed for invalid inputs"
    assert len(errors) >= 5, f"Expected multiple error messages, got: {errors}"
    print(f"-> Test 4 PASSED: Missing/invalid fields properly caught ({len(errors)} errors reported).")

    # ----------------------------------------------------
    # TEST 5: Manual Lead Creation
    # ----------------------------------------------------
    print("\n[Test 5] Testing Manual Lead Creation...")
    manual_data = {
        "customer_name": "Vikram Adiga",
        "phone": "+91 98450 12345",
        "email": "vikram.adiga@example.com",
        "city": "Bangalore",
        "lead_source": "Direct Walk-in",
        "budget_range": "₹10 lakh–₹25 lakh",
        "project_type": "3BHK",
        "property_status": "Ready to Move",
        "project_timeline": "Immediately",
        "scope_of_work": "Full Turnkey Interior",
        "customer_requirements": "Need full interior woodwork for 3BHK flat in Indiranagar.",
        "purchase_readiness": "Ready to Start",
        "preferred_contact_method": "Phone Call"
    }
    success, msg, new_id = lead_capture.create_manual_lead(manual_data, db_path=TEST_DB)
    assert success, f"Manual lead creation failed: {msg}"
    assert new_id is not None and new_id.startswith("SHA-"), f"Unexpected lead_id: {new_id}"
    
    lead_in_db = database.get_lead_by_id(new_id, db_path=TEST_DB)
    assert lead_in_db is not None, "Lead was not found in DB!"
    assert lead_in_db["customer_name"] == "Vikram Adiga"
    assert lead_in_db["lead_status"] == "New", f"Default status should be New, got {lead_in_db['lead_status']}"
    assert lead_in_db["data_origin"] == "manual_entry", f"Expected origin 'manual_entry', got {lead_in_db['data_origin']}"
    print(f"-> Test 5 PASSED: Manual lead created with ID {new_id}, default status 'New', and origin 'manual_entry'.")

    # ----------------------------------------------------
    # TEST 6: Database Persistence After Application Restart
    # ----------------------------------------------------
    print("\n[Test 6] Testing Database Persistence across new connections...")
    # Simulate fresh connection
    conn = sqlite3.connect(TEST_DB)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM LEADS;")
        count = cursor.fetchone()[0]
        # 250 synthetic + 1 manual = 251 leads
        assert count == 251, f"Expected 251 records, found {count}"
    finally:
        conn.close()
    print(f"-> Test 6 PASSED: Database records persist reliably (251 leads verified across fresh connection).")

    # ----------------------------------------------------
    # TEST 7: Filtering and Searching Leads
    # ----------------------------------------------------
    print("\n[Test 7] Testing Filtering and Searching Leads...")
    # Search by customer name
    results_name = database.get_all_leads(db_path=TEST_DB, search_query="Vikram Adiga")
    assert len(results_name) == 1, f"Expected 1 search result, got {len(results_name)}"
    assert results_name[0]["customer_name"] == "Vikram Adiga"
    
    # Filter by City
    results_city = database.get_all_leads(db_path=TEST_DB, city="Bangalore")
    assert len(results_city) > 0, "Expected Bangalore leads, got none"
    for r in results_city:
        assert r["city"] == "Bangalore", f"Mismatched city: {r['city']}"
        
    # Filter by Project Type
    results_villa = database.get_all_leads(db_path=TEST_DB, project_type="Villa")
    for r in results_villa:
        assert r["project_type"] == "Villa", f"Mismatched project type: {r['project_type']}"
    print(f"-> Test 7 PASSED: Search query and categorical multi-filters verified successfully.")

    # ----------------------------------------------------
    # TEST 8: Correct data_origin Assignment
    # ----------------------------------------------------
    print("\n[Test 8] Testing Correct data_origin Assignment...")
    stats = database.get_lead_stats(db_path=TEST_DB)
    origin_counts = stats["origin_counts"]
    assert origin_counts.get("synthetic_import") == 250, f"Expected 250 synthetic_import, got {origin_counts.get('synthetic_import')}"
    assert origin_counts.get("manual_entry") == 1, f"Expected 1 manual_entry, got {origin_counts.get('manual_entry')}"
    print(f"-> Test 8 PASSED: Data origin correctly partitioned ({origin_counts}).")

    # ----------------------------------------------------
    # TEST 9: Education Dataset Import Guardrail
    # ----------------------------------------------------
    print("\n[Test 9] Testing Education Dataset Import Guardrail...")
    edu_csv = os.path.join("data", "raw", "Leads.csv")
    guardrail_res = data_loader.import_csv_to_db(edu_csv, db_path=TEST_DB)
    assert not guardrail_res["success"], "Education dataset should have been rejected by guardrail!"
    assert "Guardrail Triggered" in guardrail_res["error_message"]
    print("-> Test 9 PASSED: Guardrail successfully blocked legacy education dataset from active CRM.")

    cleanup()
    print("\n==================================================")
    print("ALL 9 TEST SUITES COMPLETED AND PASSED WITH 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    run_all_tests()
