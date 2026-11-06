"""
test_hyderabad_locality_filters.py - Comprehensive Verification Test Suite
Validates the 8 core acceptance criteria for Hyderabad Locality & Region Filters and Display:
1. Gachibowli filter returns only Gachibowli leads.
2. West Hyderabad filter returns only West Hyderabad leads.
3. Madhapur + West Hyderabad combined filter returns 14 leads.
4. All Localities + All Regions returns all active leads.
5. Table formatting displays Locality and Region instead of City.
6. Lead scoring locality verification (20/17/14/12 pts vs 0 for Bangalore/unknown).
7. AI Assistant natural language locality query matching.
8. Non-Hyderabad record segregation (is_service_area = 0).
"""

import sys
import os
import sqlite3

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import database
import hyderabad_geo as hg
import lead_scoring
import db_intelligence
import ai_assistant

def run_tests():
    print("==================================================================")
    print("RUNNING HYDERABAD LOCALITY & REGION VERIFICATION SUITE (8 TESTS)")
    print("==================================================================")

    # ------------------------------------------------------------------
    # TEST 1: Gachibowli filter returns only Gachibowli leads
    # ------------------------------------------------------------------
    print("\n[Test 1] Testing Gachibowli locality filter...")
    gachi_leads = database.get_all_leads(locality="Gachibowli", active_only=True)
    assert len(gachi_leads) == 17, f"Expected 17 Gachibowli leads, got {len(gachi_leads)}"
    for l in gachi_leads:
        assert l["locality"] == "Gachibowli", f"Found non-Gachibowli record: {l['locality']}"
        assert l["region"] == "West Hyderabad", f"Found non-West Hyderabad record: {l['region']}"
        assert l["city"] == "Hyderabad", f"City should be Hyderabad, got {l['city']}"
    print(f"-> Test 1 PASSED: Found exactly {len(gachi_leads)} leads, all in Gachibowli (West Hyderabad).")

    # ------------------------------------------------------------------
    # TEST 2: West Hyderabad filter returns only West Hyderabad leads
    # ------------------------------------------------------------------
    print("\n[Test 2] Testing West Hyderabad region filter...")
    west_leads = database.get_all_leads(region="West Hyderabad", active_only=True)
    assert len(west_leads) == 149, f"Expected 149 West Hyderabad leads, got {len(west_leads)}"
    west_localities_catalog = set(hg.LOCALITY_CATALOG["West Hyderabad"])
    for l in west_leads:
        assert l["region"] == "West Hyderabad", f"Found non-West region: {l['region']}"
        assert l["locality"] in west_localities_catalog, f"Locality {l['locality']} not in West catalog!"
    print(f"-> Test 2 PASSED: Found {len(west_leads)} leads, all strictly inside West Hyderabad.")

    # ------------------------------------------------------------------
    # TEST 3: Madhapur + West Hyderabad combined filter returns 14 leads
    # ------------------------------------------------------------------
    print("\n[Test 3] Testing combined Madhapur + West Hyderabad filter...")
    madhapur_west_leads = database.get_all_leads(locality="Madhapur", region="West Hyderabad", active_only=True)
    assert len(madhapur_west_leads) == 14, f"Expected 14 Madhapur leads, got {len(madhapur_west_leads)}"
    for l in madhapur_west_leads:
        assert l["locality"] == "Madhapur"
        assert l["region"] == "West Hyderabad"

    # Also test contradictory filter: Madhapur + North Hyderabad -> 0 leads
    mismatch_leads = database.get_all_leads(locality="Madhapur", region="North Hyderabad", active_only=True)
    assert len(mismatch_leads) == 0, f"Expected 0 leads for Madhapur in North Hyderabad, got {len(mismatch_leads)}"
    print(f"-> Test 3 PASSED: Combined filter accurately returns 14 leads; mismatched filter returns 0.")

    # ------------------------------------------------------------------
    # TEST 4: All Localities + All Regions returns all active leads
    # ------------------------------------------------------------------
    print("\n[Test 4] Testing All Localities + All Regions baseline...")
    all_active = database.get_all_leads(active_only=True)
    conn = database.get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM LEADS WHERE city = 'Hyderabad' OR is_service_area = 1;")
        db_count = cur.fetchone()[0]
    finally:
        conn.close()

    assert len(all_active) == db_count, f"Mismatch: get_all_leads={len(all_active)} vs DB={db_count}"
    assert len(all_active) >= 355, f"Expected >= 355 active leads, got {len(all_active)}"
    print(f"-> Test 4 PASSED: Successfully retrieved all {len(all_active)} active Hyderabad leads.")

    # ------------------------------------------------------------------
    # TEST 5: Table formatting displays Locality and Region instead of City
    # ------------------------------------------------------------------
    print("\n[Test 5] Testing markdown table column formatting...")
    sample_leads = gachi_leads[:3]
    table_output = db_intelligence.format_leads_table(sample_leads)
    assert "| Locality |" in table_output, "Locality column header missing from table!"
    assert "| Region |" in table_output, "Region column header missing from table!"
    assert "| City |" not in table_output, "City column header should not be present in table!"
    assert "Gachibowli" in table_output, "Locality value missing from rows!"
    assert "West Hyderabad" in table_output, "Region value missing from rows!"

    # Test unmapped / None locality handling
    unmapped_lead = [{"lead_id": "TEST-UNMAPPED", "customer_name": "Test User", "locality": None, "region": None}]
    unmapped_table = db_intelligence.format_leads_table(unmapped_lead)
    assert "Unmapped" in unmapped_table, "None locality should render as 'Unmapped'!"
    assert "Unspecified" in unmapped_table, "None region should render as 'Unspecified'!"
    print("-> Test 5 PASSED: Table headers show Locality and Region; missing values render as Unmapped.")

    # ------------------------------------------------------------------
    # TEST 6: Lead scoring locality verification (Tiers & Non-Hyderabad 0 pts)
    # ------------------------------------------------------------------
    print("\n[Test 6] Testing lead scoring geographic qualification...")
    # Tier 1 (20 pts)
    score_t1, det_t1 = lead_scoring.calculate_location_score("Hyderabad", "Gachibowli")
    assert score_t1 == 20, f"Expected 20 pts for Gachibowli, got {score_t1}"
    assert "Tier 1" in det_t1

    # Tier 2 (17 pts)
    score_t2, det_t2 = lead_scoring.calculate_location_score("Hyderabad", "Kukatpally")
    assert score_t2 == 17, f"Expected 17 pts for Kukatpally, got {score_t2}"
    assert "Tier 2" in det_t2

    # Tier 3 (14 pts)
    score_t3, det_t3 = lead_scoring.calculate_location_score("Hyderabad", "Uppal")
    assert score_t3 == 14, f"Expected 14 pts for Uppal, got {score_t3}"
    assert "Tier 3" in det_t3

    # Tier 4 (12 pts)
    score_t4, det_t4 = lead_scoring.calculate_location_score("Hyderabad", "LB Nagar")
    assert score_t4 == 12, f"Expected 12 pts for LB Nagar, got {score_t4}"
    assert "Tier 4" in det_t4

    # Non-Hyderabad cities -> 0 pts
    for non_hyd_city in ["Bangalore", "Mumbai", "Pune", "Chennai", "Delhi NCR"]:
        score_nh, _ = lead_scoring.calculate_location_score(non_hyd_city)
        assert score_nh == 0, f"Expected 0 pts for {non_hyd_city}, got {score_nh}"

    # Unknown / unverified locality -> 0 pts
    score_unk, det_unk = lead_scoring.calculate_location_score("Hyderabad", "RandomUnregisteredPlace")
    assert score_unk == 0, f"Expected 0 pts for unknown locality, got {score_unk}"
    assert "Unverified" in det_unk
    print("-> Test 6 PASSED: Tiers 1-4 scored accurately (20/17/14/12); Non-Hyderabad and Unknown scored 0.")

    # ------------------------------------------------------------------
    # TEST 7: AI Assistant locality query matching
    # ------------------------------------------------------------------
    print("\n[Test 7] Testing AI Assistant natural language query matching...")
    q1 = "Show leads in Gachibowli"
    ans1 = ai_assistant.answer_crm_query(q1)
    assert "17 active leads in Gachibowli" in ans1, f"Expected 17 leads in Gachibowli query, got: {ans1[:150]}"

    q2 = "How many leads in Kokapet?"
    ans2 = ai_assistant.answer_crm_query(q2)
    assert "18 active leads in Kokapet" in ans2, f"Expected 18 leads in Kokapet query, got: {ans2[:150]}"

    q3 = "Leads in West Hyderabad"
    ans3 = ai_assistant.answer_crm_query(q3)
    assert "149 active leads in West Hyderabad" in ans3, f"Expected 149 leads in West query, got: {ans3[:150]}"

    q4 = "Show leads in Madhapur"
    ans4 = ai_assistant.answer_crm_query(q4)
    assert "14 active leads in Madhapur" in ans4, f"Expected 14 leads in Madhapur query, got: {ans4[:150]}"
    print("-> Test 7 PASSED: AI Assistant natural language locality queries match exact database counts.")

    # ------------------------------------------------------------------
    # TEST 8: Non-Hyderabad record segregation
    # ------------------------------------------------------------------
    print("\n[Test 8] Testing non-Hyderabad record segregation...")
    conn = database.get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM LEADS WHERE is_service_area = 0;")
        archived_count = cur.fetchone()[0]
        cur.execute("SELECT DISTINCT city FROM LEADS WHERE is_service_area = 0;")
        archived_cities = [r[0] for r in cur.fetchall()]
    finally:
        conn.close()

    assert archived_count == 445, f"Expected 445 archived records, got {archived_count}"
    assert any(c in archived_cities for c in ["Bangalore", "Mumbai", "Chennai", "Pune", "Delhi NCR"])

    # Ensure none of these appear in default active queries
    active_leads_all = database.get_all_leads(active_only=True)
    for l in active_leads_all:
        assert l["is_service_area"] == 1 or l["city"] == "Hyderabad", f"Non-Hyderabad lead found in active pool: {l}"
    print(f"-> Test 8 PASSED: All {archived_count} non-Hyderabad leads safely segregated.")

    print("\n==================================================================")
    print("ALL 8 HYDERABAD LOCALITY & REGION TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================================")

if __name__ == "__main__":
    run_tests()
