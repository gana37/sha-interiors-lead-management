import os
import sys
import gc
import time
import json
import sqlite3
import database
import data_loader
import lead_scoring

sys.stdout.reconfigure(encoding='utf-8')
TEST_DB = "test_lead_scoring.db"

def cleanup():
    gc.collect()
    time.sleep(0.1)
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            gc.collect()
            time.sleep(0.4)
            try:
                os.remove(TEST_DB)
            except Exception as e:
                print(f"Cleanup note: {e}")

def run_tests():
    print("==================================================")
    print("STARTING STEP 4: LEAD SCORING TEST SUITE")
    print("==================================================")
    cleanup()
    
    # ----------------------------------------------------
    # TEST 1: Maximum Score is 100
    # ----------------------------------------------------
    print("\n[Test 1] Testing Maximum Score is 100...")
    perfect_lead = {
        "lead_id": "TEST-MAX",
        "customer_name": "Perfect Prospect",
        "city": "Bangalore",  # 20 pts
        "budget_range": "Above ₹25 lakh",  # 30 pts
        "project_type": "Villa",  # 4 pts
        "property_status": "Ready to Move",  # 4 pts
        "project_timeline": "Immediately",  # 4 pts
        "scope_of_work": "Full Turnkey Interior",  # 4 pts
        "customer_requirements": "Looking for high-end luxury turnkey Italian marble interior with home automation.",  # 4 pts (>30 chars)
        "purchase_readiness": "Ready to Start"  # 30 pts
    }
    res_max = lead_scoring.score_lead(perfect_lead)
    assert res_max["lead_score"] == 100.0, f"Expected 100.0, got {res_max['lead_score']}"
    assert res_max["priority"] == "High", f"Expected High, got {res_max['priority']}"
    print("-> Test 1 PASSED: Maximum score is 100 with High Priority.")

    # ----------------------------------------------------
    # TEST 2: Minimum Score is 0
    # ----------------------------------------------------
    print("\n[Test 2] Testing Minimum Score is 0...")
    empty_lead = {
        "lead_id": "TEST-MIN",
        "customer_name": "Incomplete Prospect",
        "city": "Unknown / Far City",  # 0 pts
        "budget_range": None,  # 0 pts
        "project_type": "",  # 0 pts
        "property_status": "",  # 0 pts
        "project_timeline": "",  # 0 pts
        "scope_of_work": "",  # 0 pts
        "customer_requirements": "",  # 0 pts
        "purchase_readiness": ""  # 0 pts
    }
    res_min = lead_scoring.score_lead(empty_lead)
    assert res_min["lead_score"] == 0.0, f"Expected 0.0, got {res_min['lead_score']}"
    assert res_min["priority"] == "Low", f"Expected Low, got {res_min['priority']}"
    print("-> Test 2 PASSED: Minimum score is 0 with Low Priority.")

    # ----------------------------------------------------
    # TEST 3: Budget Scoring (0 to 30)
    # ----------------------------------------------------
    print("\n[Test 3] Testing Budget Scoring across categories...")
    budget_tests = [
        ("Above ₹25 lakh", 30),
        ("₹10 lakh–₹25 lakh", 25),
        ("₹5 lakh–₹10 lakh", 18),
        ("₹3 lakh–₹5 lakh", 10),
        ("Below ₹3 lakh", 2),
        ("Unlisted / Custom", 0)
    ]
    for b_tier, expected_pts in budget_tests:
        pts, detail = lead_scoring.calculate_budget_score(b_tier)
        assert pts == expected_pts, f"Budget {b_tier}: expected {expected_pts}, got {pts}"
    print("-> Test 3 PASSED: All budget tiers scored accurately.")

    # ----------------------------------------------------
    # TEST 4: Location Scoring (0 to 20)
    # ----------------------------------------------------
    print("\n[Test 4] Testing Location Scoring across tiers...")
    loc_tests = [
        ("Bangalore", 20),
        ("Hyderabad", 20),
        ("Chennai", 14),
        ("Mumbai", 14),
        ("Pune", 14),
        ("Delhi NCR", 8),
        ("Kolkata", 0),
        ("RandomTown", 0)
    ]
    for city, expected_pts in loc_tests:
        pts, detail = lead_scoring.calculate_location_score(city)
        assert pts == expected_pts, f"City {city}: expected {expected_pts}, got {pts}"
    print("-> Test 4 PASSED: Tier 1, Tier 2, Tier 3, and Out-of-service locations verified.")

    # ----------------------------------------------------
    # TEST 5: Requirements Completeness Scoring (0 to 20)
    # ----------------------------------------------------
    print("\n[Test 5] Testing Requirements Completeness Scoring...")
    partial_lead = {
        "project_type": "2BHK",                 # 4 pts
        "property_status": "Ready to Move",     # 4 pts
        "project_timeline": "Within 1 month",   # 4 pts
        "scope_of_work": "Modular Kitchen",     # 4 pts
        "customer_requirements": "Short note"   # 2 pts (10-25 chars)
    }
    pts, subdict, detail = lead_scoring.calculate_requirements_score(partial_lead)
    assert pts == 18, f"Expected 18 pts, got {pts}"
    
    # Test with placeholders
    placeholder_lead = {
        "project_type": "InvalidType",
        "property_status": "Select",
        "project_timeline": "",
        "scope_of_work": "",
        "customer_requirements": "None"
    }
    pts_zero, _, _ = lead_scoring.calculate_requirements_score(placeholder_lead)
    assert pts_zero == 0, f"Expected 0 pts for placeholders, got {pts_zero}"
    print("-> Test 5 PASSED: Requirements completeness handles valid details and placeholders.")

    # ----------------------------------------------------
    # TEST 6: Purchase Readiness Scoring (0 to 30)
    # ----------------------------------------------------
    print("\n[Test 6] Testing Purchase Readiness Scoring...")
    readiness_tests = [
        ("Ready to Start", 30),
        ("Comparing Vendors", 22),
        ("Budget Planning", 12),
        ("Just Exploring", 4),
        ("Unknown", 0)
    ]
    for r_opt, expected_pts in readiness_tests:
        pts, detail = lead_scoring.calculate_readiness_score(r_opt)
        assert pts == expected_pts, f"Readiness {r_opt}: expected {expected_pts}, got {pts}"
    print("-> Test 6 PASSED: Purchase readiness categories scored properly.")

    # ----------------------------------------------------
    # TEST 7: Correct Priority Classification
    # ----------------------------------------------------
    print("\n[Test 7] Testing Priority Classification Thresholds...")
    assert lead_scoring.classify_priority(100.0) == "High"
    assert lead_scoring.classify_priority(80.0) == "High"
    assert lead_scoring.classify_priority(79.9) == "Medium"
    assert lead_scoring.classify_priority(50.0) == "Medium"
    assert lead_scoring.classify_priority(49.9) == "Low"
    assert lead_scoring.classify_priority(0.0) == "Low"
    print("-> Test 7 PASSED: High (80-100), Medium (50-79), Low (0-49) boundaries verified.")

    # ----------------------------------------------------
    # TEST 8: Missing or Unknown Values Handling
    # ----------------------------------------------------
    print("\n[Test 8] Testing Missing or Unknown Values Handling...")
    null_lead = {
        "lead_id": "TEST-NULL",
        "customer_name": "Null Fields",
        "city": None,
        "budget_range": None,
        "project_type": None,
        "property_status": None,
        "project_timeline": None,
        "scope_of_work": None,
        "customer_requirements": None,
        "purchase_readiness": None
    }
    res_null = lead_scoring.score_lead(null_lead)
    assert res_null["lead_score"] == 0.0
    assert res_null["priority"] == "Low"
    assert "0/100" in res_null["scoring_reason"]
    print("-> Test 8 PASSED: None/null values handled gracefully without exceptions.")

    # ----------------------------------------------------
    # TEST 9: Score Breakdown Correctness
    # ----------------------------------------------------
    print("\n[Test 9] Testing Score Breakdown Mathematical Consistency...")
    sample_lead = {
        "lead_id": "TEST-BREAKDOWN",
        "customer_name": "Breakdown Test",
        "city": "Chennai",                      # 14 pts
        "budget_range": "₹10 lakh–₹25 lakh",     # 25 pts
        "project_type": "3BHK",                 # 4 pts
        "property_status": "Ready to Move",     # 4 pts
        "project_timeline": "Within 1 month",   # 4 pts
        "scope_of_work": "Full Turnkey Interior",# 4 pts
        "customer_requirements": "Complete woodwork, false ceiling, and wallpaper accents.", # 4 pts
        "purchase_readiness": "Comparing Vendors" # 22 pts
    }
    res_sample = lead_scoring.score_lead(sample_lead)
    b = res_sample["score_breakdown"]
    total_calculated = b["budget_score"] + b["location_score"] + b["requirements_score"] + b["readiness_score"]
    assert total_calculated == res_sample["lead_score"], f"Sum mismatch: {total_calculated} vs {res_sample['lead_score']}"
    assert res_sample["lead_score"] == 81.0, f"Expected 81.0, got {res_sample['lead_score']}"
    assert res_sample["priority"] == "High"
    print(f"-> Test 9 PASSED: Breakdown sum ({total_calculated}) strictly equals lead_score (81.0).")

    # ----------------------------------------------------
    # TEST 10: Rescoring After Lead Updates in SQLite
    # ----------------------------------------------------
    print("\n[Test 10] Testing Rescoring After Lead Updates...")
    database.init_db(TEST_DB)
    # Insert initial lead: Low budget, Just Exploring
    initial_lead = {
        "lead_id": "SHA-UPDATE-01",
        "customer_name": "Arun Kumar",
        "phone": "+91 98450 11111",
        "city": "Bangalore",
        "lead_source": "Website Inquiry",
        "budget_range": "Below ₹3 lakh",
        "project_type": "1BHK",
        "property_status": "Under Construction",
        "project_timeline": "Within 6 months",
        "scope_of_work": "Wardrobe",
        "customer_requirements": "Basic wardrobe.",
        "purchase_readiness": "Just Exploring",
        "lead_status": "New",
        "data_origin": "manual_entry"
    }
    database.insert_lead(initial_lead, db_path=TEST_DB)
    res1 = lead_scoring.score_and_save_lead("SHA-UPDATE-01", db_path=TEST_DB)
    score1 = res1["lead_score"]
    assert score1 < 50.0, f"Initial score should be low, got {score1}"
    assert res1["priority"] == "Low"

    # Customer updates requirement to turnkey villa with high budget
    conn = database.get_connection(TEST_DB)
    try:
        with conn:
            conn.execute("""
            UPDATE LEADS SET
                budget_range = 'Above ₹25 lakh',
                project_type = 'Villa',
                property_status = 'Ready to Move',
                project_timeline = 'Immediately',
                scope_of_work = 'Full Turnkey Interior',
                purchase_readiness = 'Ready to Start',
                customer_requirements = 'Upgraded to full turnkey villa interior; immediate site inspection requested.'
            WHERE lead_id = 'SHA-UPDATE-01';
            """)
    finally:
        conn.close()

    res2 = lead_scoring.score_and_save_lead("SHA-UPDATE-01", db_path=TEST_DB)
    score2 = res2["lead_score"]
    assert score2 == 100.0, f"Updated score should be 100, got {score2}"
    assert res2["priority"] == "High"
    print(f"-> Test 10 PASSED: Rescoring updated lead score from {score1:.0f} (Low) to {score2:.0f} (High).")

    # ----------------------------------------------------
    # TEST 11: Existing CRM lead_status Remains Unchanged
    # ----------------------------------------------------
    print("\n[Test 11] Testing lead_status Immobility during Scoring...")
    test_lead_status = {
        "lead_id": "SHA-STATUS-PRESERVE",
        "customer_name": "Status Check",
        "phone": "+91 98450 22222",
        "city": "Hyderabad",
        "lead_source": "Architect Referral",
        "budget_range": "₹10 lakh–₹25 lakh",
        "project_type": "3BHK",
        "property_status": "Ready to Move",
        "project_timeline": "Immediately",
        "scope_of_work": "Full Turnkey Interior",
        "customer_requirements": "Complete turnkey flat interior requirements.",
        "purchase_readiness": "Ready to Start",
        "lead_status": "Follow-up",  # Established CRM status
        "data_origin": "manual_entry"
    }
    database.insert_lead(test_lead_status, db_path=TEST_DB)
    lead_scoring.score_and_save_lead("SHA-STATUS-PRESERVE", db_path=TEST_DB)
    
    lead_after_score = database.get_lead_by_id("SHA-STATUS-PRESERVE", db_path=TEST_DB)
    assert lead_after_score["lead_status"] == "Follow-up", f"lead_status was mutated to {lead_after_score['lead_status']}!"
    assert lead_after_score["priority"] == "High"
    print("-> Test 11 PASSED: CRM lead_status 'Follow-up' preserved unchanged after scoring.")

    # ----------------------------------------------------
    # TEST 12: Synthetic Historical Status Does Not Influence Score
    # ----------------------------------------------------
    print("\n[Test 12] Testing Independence from Historical Lead_Status...")
    # Two identical leads: one with historical status 'Lost', one with 'Converted'
    base_lead = {
        "customer_name": "Identical Lead",
        "phone": "+91 98450 33333",
        "city": "Pune",
        "lead_source": "Instagram Ad",
        "budget_range": "₹5 lakh–₹10 lakh",
        "project_type": "2BHK",
        "property_status": "Possession within 30 days",
        "project_timeline": "Within 1 month",
        "scope_of_work": "Modular Kitchen",
        "customer_requirements": "Need L-shaped modular kitchen with acrylic finish.",
        "purchase_readiness": "Comparing Vendors"
    }
    lead_lost = dict(base_lead, lead_id="SHA-LOST-01", lead_status="Lost")
    lead_converted = dict(base_lead, lead_id="SHA-CONV-01", lead_status="Converted")
    
    score_lost = lead_scoring.score_lead(lead_lost)["lead_score"]
    score_conv = lead_scoring.score_lead(lead_converted)["lead_score"]
    assert score_lost == score_conv, f"Scores differ based on historical status: {score_lost} vs {score_conv}"
    print(f"-> Test 12 PASSED: Historical status ('Lost' vs 'Converted') has 0 influence on score ({score_lost:.0f} vs {score_conv:.0f}).")

    cleanup()
    print("\n==================================================")
    print("ALL 12 STEP 4 TESTS COMPLETED AND PASSED WITH 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
