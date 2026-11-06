"""
test_estimate_datetime.py - Verification Suite for Estimate Date & Time Extraction
SHA Interface Interiors Lead Management System

Covers:
1. Exact parsing of '2319311026' -> 31 October 2026, 11:19 PM
2. Exact parsing of '1907021126' -> 2 November 2026, 7:07 PM
3. References with and without 'EST-' prefix (case-insensitive)
4. Invalid hours and minutes boundaries
5. Invalid dates and months (including leap year validation)
6. Missing reference numbers (graceful handling, warning generation, no silent fallback to now)
7. CSV and Excel imports with estimate fields
8. Existing database records verification, sorting, and date range filtering
"""

import os
import sys
import datetime
import tempfile
import pandas as pd

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import estimate_parser
import database
import data_loader
import reports


def run_tests():
    print("=" * 70)
    print("RUNNING ESTIMATE DATE & TIME EXTRACTION VERIFICATION SUITE")
    print("=" * 70)

    # -------------------------------------------------------------
    # TEST 1: 2319311026 -> 31 October 2026, 11:19 PM
    # -------------------------------------------------------------
    print("\n[Test 1] Testing '2319311026' -> 31 October 2026, 11:19 PM...")
    dt1, iso1, warn1 = estimate_parser.parse_estimate_reference("2319311026")
    assert dt1 is not None, f"Failed to parse 2319311026: {warn1}"
    assert warn1 is None
    assert iso1 == "2026-10-31 23:19:00", f"Expected '2026-10-31 23:19:00', got '{iso1}'"
    assert dt1.year == 2026
    assert dt1.month == 10
    assert dt1.day == 31
    assert dt1.hour == 23
    assert dt1.minute == 19
    disp1 = estimate_parser.format_estimate_display(dt1)
    long1 = estimate_parser.format_estimate_display_long(dt1)
    assert disp1 == "31 Oct 2026 | 11:19 PM", f"Expected '31 Oct 2026 | 11:19 PM', got '{disp1}'"
    assert long1 == "31 October 2026, 11:19 PM", f"Expected '31 October 2026, 11:19 PM', got '{long1}'"
    print(f"-> Test 1 PASSED: ISO='{iso1}' | Display='{disp1}' | Full='{long1}'")

    # -------------------------------------------------------------
    # TEST 2: 1907021126 -> 2 November 2026, 7:07 PM
    # -------------------------------------------------------------
    print("\n[Test 2] Testing '1907021126' -> 2 November 2026, 7:07 PM...")
    dt2, iso2, warn2 = estimate_parser.parse_estimate_reference("1907021126")
    assert dt2 is not None, f"Failed to parse 1907021126: {warn2}"
    assert warn2 is None
    assert iso2 == "2026-11-02 19:07:00", f"Expected '2026-11-02 19:07:00', got '{iso2}'"
    assert dt2.year == 2026
    assert dt2.month == 11
    assert dt2.day == 2
    assert dt2.hour == 19
    assert dt2.minute == 7
    disp2 = estimate_parser.format_estimate_display(dt2)
    long2 = estimate_parser.format_estimate_display_long(dt2)
    assert disp2 == "2 Nov 2026 | 7:07 PM", f"Expected '2 Nov 2026 | 7:07 PM', got '{disp2}'"
    assert long2 == "2 November 2026, 7:07 PM", f"Expected '2 November 2026, 7:07 PM', got '{long2}'"
    print(f"-> Test 2 PASSED: ISO='{iso2}' | Display='{disp2}' | Full='{long2}'")

    # -------------------------------------------------------------
    # TEST 3: References with and without 'EST-' Prefix
    # -------------------------------------------------------------
    print("\n[Test 3] Testing References with and without 'EST-' Prefix...")
    test_cases_prefix = [
        ("EST-2319311026", "2026-10-31 23:19:00"),
        ("est-2319311026", "2026-10-31 23:19:00"),
        ("EST_1907021126", "2026-11-02 19:07:00"),
        ("EST 1907021126", "2026-11-02 19:07:00"),
        ("EST:1804011126", "2026-11-01 18:04:00"),
        ("1804011126", "2026-11-01 18:04:00")
    ]
    for raw_ref, expected_iso in test_cases_prefix:
        dt, iso, warn = estimate_parser.parse_estimate_reference(raw_ref)
        assert iso == expected_iso, f"Failed for '{raw_ref}': Expected {expected_iso}, got {iso}"
        assert warn is None
    print(f"-> Test 3 PASSED: All {len(test_cases_prefix)} prefix variations parsed identically.")

    # -------------------------------------------------------------
    # TEST 4: Invalid Hours and Minutes
    # -------------------------------------------------------------
    print("\n[Test 4] Testing Invalid Hours and Minutes...")
    # Hour 24 (invalid)
    _, _, err_h24 = estimate_parser.parse_estimate_reference("2400010126")
    assert err_h24 is not None and "hour" in err_h24.lower(), f"Expected hour error, got: {err_h24}"

    # Hour 99 (invalid)
    _, _, err_h99 = estimate_parser.parse_estimate_reference("9900010126")
    assert err_h99 is not None and "hour" in err_h99.lower(), f"Expected hour error, got: {err_h99}"

    # Minute 60 (invalid)
    _, _, err_m60 = estimate_parser.parse_estimate_reference("1260010126")
    assert err_m60 is not None and "minute" in err_m60.lower(), f"Expected minute error, got: {err_m60}"

    # Minute 99 (invalid)
    _, _, err_m99 = estimate_parser.parse_estimate_reference("1299010126")
    assert err_m99 is not None and "minute" in err_m99.lower(), f"Expected minute error, got: {err_m99}"
    print("-> Test 4 PASSED: Hours [00-23] and Minutes [00-59] strictly enforced.")

    # -------------------------------------------------------------
    # TEST 5: Invalid Dates and Months (Including Leap Years)
    # -------------------------------------------------------------
    print("\n[Test 5] Testing Invalid Dates and Months (with Leap Year Check)...")
    # Month 00 (invalid)
    _, _, err_m0 = estimate_parser.parse_estimate_reference("1200010026")
    assert err_m0 is not None and "month" in err_m0.lower()

    # Month 13 (invalid)
    _, _, err_m13 = estimate_parser.parse_estimate_reference("1200011326")
    assert err_m13 is not None and "month" in err_m13.lower()

    # Day 32 in January (invalid)
    _, _, err_d32 = estimate_parser.parse_estimate_reference("1200320126")
    assert err_d32 is not None and "calendar date" in err_d32.lower()

    # Day 31 in November (30-day month, invalid)
    _, _, err_nov31 = estimate_parser.parse_estimate_reference("1200311126")
    assert err_nov31 is not None and "calendar date" in err_nov31.lower()

    # Feb 29 in 2026 (non-leap year, invalid)
    _, _, err_feb26 = estimate_parser.parse_estimate_reference("1200290226")
    assert err_feb26 is not None and "calendar date" in err_feb26.lower()

    # Feb 29 in 2024 (leap year, VALID)
    dt_leap, iso_leap, warn_leap = estimate_parser.parse_estimate_reference("1200290224")
    assert dt_leap is not None, f"Feb 29 on leap year 2024 should be valid, got warning: {warn_leap}"
    assert iso_leap == "2024-02-29 12:00:00"

    # Year 26 explicitly decoded as 2026
    dt_yr, iso_yr, _ = estimate_parser.parse_estimate_reference("1000150826")
    assert dt_yr.year == 2026
    print("-> Test 5 PASSED: Calendar validity and leap-year rules verified.")

    # -------------------------------------------------------------
    # TEST 6: Missing and Malformed Reference Numbers
    # -------------------------------------------------------------
    print("\n[Test 6] Testing Missing & Malformed Reference Numbers...")
    missing_samples = [None, "", "   ", "nan", "none", "NULL", "—", "-"]
    for sample in missing_samples:
        dt, iso, warn = estimate_parser.parse_estimate_reference(sample)
        assert dt is None, f"Should return None for '{sample}'"
        assert iso is None, f"Should return None ISO for '{sample}'"
        assert warn is not None, "Warning must be recorded for missing reference"

    # Malformed reference (too short or letters)
    dt_short, iso_short, warn_short = estimate_parser.parse_estimate_reference("12345")
    assert dt_short is None
    assert "expected exactly 10 digits" in warn_short.lower()

    dt_alpha, iso_alpha, warn_alpha = estimate_parser.parse_estimate_reference("ABCDEFGHIJ")
    assert dt_alpha is None
    print("-> Test 6 PASSED: Missing/malformed references never crash and never assign current time.")

    # -------------------------------------------------------------
    # TEST 7: CSV and Excel Imports
    # -------------------------------------------------------------
    print("\n[Test 7] Testing CSV and Excel Import Pipeline...")
    temp_leads_data = [
        {
            "Lead_ID": "TEST-IMP-001",
            "Customer_Name": "Import Test User 1",
            "Phone": "+91 99887 76655",
            "City": "Hyderabad",
            "Budget_Range": "₹10 lakh–₹25 lakh",
            "Project_Type": "3BHK",
            "Property_Status": "Ready to Move",
            "Project_Timeline": "Immediately",
            "Scope_of_Work": "Full Turnkey Interior",
            "Purchase_Readiness": "Ready to Start",
            "Lead_Reference": "EST-2319311026"  # Valid
        },
        {
            "Lead_ID": "TEST-IMP-002",
            "Customer_Name": "Import Test User 2",
            "Phone": "+91 99887 76656",
            "City": "Hyderabad",
            "Budget_Range": "₹5 lakh–₹10 lakh",
            "Project_Type": "2BHK",
            "Property_Status": "Ready to Move",
            "Project_Timeline": "Within 1 month",
            "Scope_of_Work": "Modular Kitchen",
            "Purchase_Readiness": "Comparing Vendors",
            "Lead_Reference": "INVALID-REF"  # Invalid
        },
        {
            "Lead_ID": "TEST-IMP-003",
            "Customer_Name": "Import Test User 3",
            "Phone": "+91 99887 76657",
            "City": "Hyderabad",
            "Budget_Range": "₹3 lakh–₹5 lakh",
            "Project_Type": "1BHK",
            "Property_Status": "Under Construction",
            "Project_Timeline": "Within 3 months",
            "Scope_of_Work": "Wardrobe",
            "Purchase_Readiness": "Budget Planning",
            "Lead_Reference": ""  # Missing
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "test_leads.csv")
        xlsx_path = os.path.join(tmpdir, "test_leads.xlsx")
        test_db = os.path.join(tmpdir, "test_import.db")

        df_test = pd.DataFrame(temp_leads_data)
        df_test.to_csv(csv_path, index=False)
        df_test.to_excel(xlsx_path, index=False)

        # 7a. Test CSV validation
        csv_res = data_loader.validate_and_prepare_csv(csv_path, db_path=test_db)
        assert csv_res["success"] is True
        assert csv_res["valid_count"] == 3
        assert csv_res["decoded_refs_count"] == 1
        assert csv_res["invalid_refs_count"] == 1
        assert csv_res["missing_refs_count"] == 1
        assert len(csv_res["validation_warnings"]) == 1

        rec1 = next(r for r in csv_res["valid_records"] if r["lead_id"] == "TEST-IMP-001")
        assert rec1["estimate_generated_at"] == "2026-10-31 23:19:00"
        assert rec1["lead_reference"] == "EST-2319311026"

        rec2 = next(r for r in csv_res["valid_records"] if r["lead_id"] == "TEST-IMP-002")
        assert rec2["estimate_generated_at"] is None
        assert rec2["lead_reference"] == "INVALID-REF"

        rec3 = next(r for r in csv_res["valid_records"] if r["lead_id"] == "TEST-IMP-003")
        assert rec3["estimate_generated_at"] is None
        assert rec3["lead_reference"] is None

        # 7b. Test Excel validation
        xlsx_res = data_loader.validate_and_prepare_csv(xlsx_path, db_path=test_db)
        assert xlsx_res["success"] is True
        assert xlsx_res["valid_count"] == 3
        assert xlsx_res["decoded_refs_count"] == 1

        # 7c. Test DB Import
        imp_res = data_loader.import_csv_to_db(csv_path, db_path=test_db, data_origin="test_import")
        assert imp_res["success"] is True
        assert imp_res["imported_count"] == 3

        db_leads = database.get_all_leads(db_path=test_db)
        assert len(db_leads) == 3
        l1 = database.get_lead_by_id("TEST-IMP-001", db_path=test_db)
        assert l1["estimate_generated_at"] == "2026-10-31 23:19:00"
        assert l1["lead_reference"] == "EST-2319311026"
    print("-> Test 7 PASSED: CSV and Excel imports validated with graceful warning capture.")

    # -------------------------------------------------------------
    # TEST 8: Existing Database Records, Sorting & Date Filtering
    # -------------------------------------------------------------
    print("\n[Test 8] Testing Active Database Records, Sorting & Date Range Filtering...")
    active_leads = database.get_all_leads(data_origin="genuine_only", order_by="estimate_generated_at DESC")
    assert len(active_leads) == 7, f"Expected 7 genuine leads, found {len(active_leads)}"

    # Check decoded leads
    with_est = [l for l in active_leads if l.get("estimate_generated_at")]
    without_est = [l for l in active_leads if not l.get("estimate_generated_at")]
    assert len(with_est) == 6, f"Expected 6 leads with decoded estimates, got {len(with_est)}"
    assert len(without_est) == 1, f"Expected 1 lead without estimate (Matta GANESH), got {len(without_est)}"
    assert without_est[0]["customer_name"] == "Matta GANESH"

    # Verify order: latest first (Dr. Chakravarthy on Nov 2, then Nov 1, then Oct 31)
    dates_desc = [l["estimate_generated_at"] for l in with_est]
    assert dates_desc == sorted(dates_desc, reverse=True), "Sorting by estimate_generated_at DESC failed"
    assert with_est[0]["customer_name"] == "Dr. Chakravarthy.B El PT"

    # Verify date filtering:
    oct_leads = database.get_all_leads(data_origin="genuine_only", estimate_date_from="2026-10-31", estimate_date_to="2026-10-31")
    assert len(oct_leads) == 2
    oct_names = {l["customer_name"] for l in oct_leads}
    assert "Aditya" in oct_names and "P Das" in oct_names

    nov_leads = database.get_all_leads(data_origin="genuine_only", estimate_date_from="2026-11-01", estimate_date_to="2026-11-02")
    assert len(nov_leads) == 4

    # Analytics verification
    est_analytics = reports.get_estimate_analytics(dataset_scope="genuine_only")
    assert est_analytics["total_with_estimates"] == 6
    assert est_analytics["latest_estimate"]["customer_name"] == "Dr. Chakravarthy.B El PT"
    assert est_analytics["latest_estimate"]["display_time"] == "2 Nov 2026 | 7:07 PM"
    assert len(est_analytics["grouped_by_date"]) == 3
    print("-> Test 8 PASSED: All 7 existing records verified, sorting and date filtering validated.")

    print("\n" + "=" * 70)
    print("ALL 8 ESTIMATE DATE & TIME EXTRACTION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
