import sys
sys.stdout.reconfigure(encoding="utf-8")
import os
import sqlite3
import datetime
import pandas as pd
import database
import reports
import hyderabad_geo as hg

def run_tests():
    print("==================================================================")
    print("RUNNING COMPREHENSIVE DASHBOARD TEST SUITE (HYDERABAD CRM)")
    print("==================================================================")

    db_path = database.DEFAULT_DB_PATH
    conn = database.get_connection(db_path)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_date = datetime.date.today().isoformat()
    where_active = "WHERE (city = 'Hyderabad' OR is_service_area = 1)"

    # -------------------------------------------------------------
    # TEST 1: Dashboard Title & Structural Markers in app.py
    # -------------------------------------------------------------
    print("\n[Test 1] Verifying Official Dashboard Title & Branding...")
    with open("app.py", "r", encoding="utf-8") as f:
        app_source = f.read()
    
    assert "SHA Interiors" in app_source, "Official title 'SHA Interiors' not found in app.py"
    assert "Lead Management Dashboard" in app_source, "Official title 'Lead Management Dashboard' not found in app.py"
    assert "Hyderabad Metropolitan Edition" in app_source, "Hyderabad branding subtitle not found in app.py"
    assert "Total Active Hyderabad Leads" in app_source, "Card label 'Total Active Hyderabad Leads' missing"
    assert "Upcoming Follow-ups" in app_source, "Card label 'Upcoming Follow-ups' missing"
    print("-> Test 1 PASSED: Official title, subtitle, and branding verified in app.py.")

    # -------------------------------------------------------------
    # TEST 2: Dashboard Overview Cards (8 Metrics) vs SQLite
    # -------------------------------------------------------------
    print("\n[Test 2] Verifying All 8 Overview Metric Cards against SQLite...")
    kpis = reports.get_hyderabad_kpis(db_path)
    c = conn.cursor()

    # Query DB directly
    c.execute(f"SELECT COUNT(*) FROM LEADS {where_active}")
    db_total = c.fetchone()[0]
    assert kpis["total_leads"] == db_total, f"Expected {db_total} active leads, got kpi={kpis['total_leads']}"
    assert db_total >= 355, f"Expected at least 355 active leads, got {db_total}"

    c.execute(f"SELECT COUNT(*) FROM LEADS {where_active} AND lead_status = 'New'")
    db_new = c.fetchone()[0]
    assert kpis["new_leads"] == db_new, f"Expected {db_new} new leads, got kpi={kpis['new_leads']}"

    c.execute(f"SELECT COUNT(*) FROM LEADS {where_active} AND lead_status = 'Qualified'")
    db_qual = c.fetchone()[0]
    assert kpis["qualified_leads"] == db_qual, f"Expected {db_qual} qualified leads, got kpi={kpis['qualified_leads']}"

    c.execute(f"SELECT COUNT(*) FROM LEADS {where_active} AND priority = 'High'")
    db_high = c.fetchone()[0]
    assert kpis["high_priority_leads"] == db_high, f"Expected {db_high} high priority leads, got kpi={kpis['high_priority_leads']}"

    c.execute(f"SELECT COUNT(*) FROM LEADS {where_active} AND lead_status = 'Converted'")
    db_conv = c.fetchone()[0]
    assert kpis["converted_leads"] == db_conv, f"Expected {db_conv} converted leads, got kpi={kpis['converted_leads']}"

    c.execute(f"SELECT COUNT(*) FROM LEADS {where_active} AND lead_status = 'Lost'")
    db_lost = c.fetchone()[0]
    assert kpis["lost_leads"] == db_lost, f"Expected {db_lost} lost leads, got kpi={kpis['lost_leads']}"

    expected_conv_rate = round((db_conv / db_total * 100), 2)
    assert kpis["overall_conversion_rate"] == expected_conv_rate, f"Expected {expected_conv_rate}%, got {kpis['overall_conversion_rate']}%"

    c.execute("""
        SELECT COUNT(*) FROM FOLLOW_UP_SCHEDULE f 
        JOIN LEADS l ON f.lead_id = l.lead_id 
        WHERE (l.city = 'Hyderabad' OR l.is_service_area = 1) 
          AND f.status = 'Scheduled' 
          AND f.scheduled_for > ?
    """, (now_str,))
    db_upcoming_fu = c.fetchone()[0]
    assert kpis["upcoming_followups"] == db_upcoming_fu, f"Expected {db_upcoming_fu} upcoming followups, got kpi={kpis['upcoming_followups']}"

    print(f"-> Test 2 PASSED: All 8 overview cards verified against database queries:")
    print(f"   Total Active: {kpis['total_leads']}, New: {kpis['new_leads']}, Qualified: {kpis['qualified_leads']}, High Priority: {kpis['high_priority_leads']}")
    print(f"   Converted: {kpis['converted_leads']}, Lost: {kpis['lost_leads']}, Conversion Rate: {kpis['overall_conversion_rate']}%, Upcoming Follow-ups: {kpis['upcoming_followups']}")

    # -------------------------------------------------------------
    # TEST 3: Hyderabad Geographical Analytics
    # -------------------------------------------------------------
    print("\n[Test 3] Verifying Hyderabad Geographical Analytics...")
    charts = reports.get_chart_data(db_path)

    # Top 10 localities
    df_loc = charts["locality"]
    assert len(df_loc) == 10, f"Expected 10 top localities, got {len(df_loc)}"
    assert "Locality" in df_loc.columns and "Count" in df_loc.columns
    top_locality = df_loc.iloc[0]["Locality"]
    assert top_locality == "Banjara Hills", f"Expected Banjara Hills as top locality, got {top_locality}"

    # Full locality list
    df_loc_all = charts["locality_all"]
    assert len(df_loc_all) >= 40, f"Expected at least 40 active localities, got {len(df_loc_all)}"
    assert "PIN Code" in df_loc_all.columns and "Region" in df_loc_all.columns

    # Region distribution
    df_reg = charts["region"]
    assert len(df_reg) == 6, f"Expected 6 metropolitan regions, got {len(df_reg)}"
    assert set(df_reg["Region"]).issubset(set(hg.HYDERABAD_REGIONS))
    c.execute(f"SELECT COUNT(*) FROM LEADS {where_active} AND region IS NOT NULL")
    db_reg_total = c.fetchone()[0]
    assert df_reg["Count"].sum() == db_reg_total, f"Expected regional sum of {db_reg_total}, got {df_reg['Count'].sum()}"

    print(f"-> Test 3 PASSED: Top 10 Localities, Directory of {len(df_loc_all)} localities, and 6 Regions verified.")

    # -------------------------------------------------------------
    # TEST 4: Business Analytics
    # -------------------------------------------------------------
    print("\n[Test 4] Verifying Business Analytics Datasets...")
    # Priority
    df_prio = charts["priority"]
    assert df_prio["Count"].sum() == db_total, f"Expected priority sum of {db_total}, got {df_prio['Count'].sum()}"

    # Budget
    df_budget = charts["budget"]
    assert df_budget["Count"].sum() == db_total, f"Expected budget sum of {db_total}, got {df_budget['Count'].sum()}"

    # Project Type
    df_pt = charts["project_type"]
    assert df_pt["Count"].sum() == db_total, f"Expected project type sum of {db_total}, got {df_pt['Count'].sum()}"

    # Property Status
    df_prop = charts["property_status"]
    assert "Property Status" in df_prop.columns
    assert df_prop["Count"].sum() == db_total, f"Expected property status sum of {db_total}, got {df_prop['Count'].sum()}"

    # Purchase Readiness
    df_ready = charts["purchase_readiness"]
    assert "Purchase Readiness" in df_ready.columns
    assert df_ready["Count"].sum() == db_total, f"Expected purchase readiness sum of {db_total}, got {df_ready['Count'].sum()}"

    # Monthly Generation
    df_month = charts["monthly_generation"]
    assert "Month" in df_month.columns and "Leads Created" in df_month.columns
    assert df_month["Leads Created"].sum() == db_total, f"Expected monthly lead sum of {db_total}, got {df_month['Leads Created'].sum()}"

    # Conversion Trends
    df_conv = charts["conversion_trends"]
    assert "Month" in df_conv.columns and "Total Leads" in df_conv.columns and "Conversion Rate (%)" in df_conv.columns
    assert df_conv["Total Leads"].sum() == db_total

    print(f"-> Test 4 PASSED: Priority, Budget, Project Type, Property Status, Purchase Readiness, Monthly Trends verified.")

    # -------------------------------------------------------------
    # TEST 5: Follow-Up Overview & Hyderabad Queue
    # -------------------------------------------------------------
    print("\n[Test 5] Verifying Follow-up Overview & Action Queue...")
    c.execute("""
        SELECT COUNT(*) FROM FOLLOW_UP_SCHEDULE f 
        JOIN LEADS l ON f.lead_id = l.lead_id 
        WHERE (l.city = 'Hyderabad' OR l.is_service_area = 1) 
          AND f.status IN ('Scheduled', 'Due') 
          AND substr(f.scheduled_for, 1, 10) = ?
    """, (today_date,))
    db_today_fu = c.fetchone()[0]
    assert kpis["today_followups"] == db_today_fu

    c.execute("""
        SELECT COUNT(*) FROM FOLLOW_UP_SCHEDULE f 
        JOIN LEADS l ON f.lead_id = l.lead_id 
        WHERE (l.city = 'Hyderabad' OR l.is_service_area = 1) 
          AND f.status IN ('Scheduled', 'Due') 
          AND f.scheduled_for < ?
    """, (now_str,))
    db_overdue_fu = c.fetchone()[0]
    assert kpis["overdue_followups"] == db_overdue_fu

    c.execute("""
        SELECT COUNT(*) FROM FOLLOW_UP_SCHEDULE f 
        JOIN LEADS l ON f.lead_id = l.lead_id 
        WHERE (l.city = 'Hyderabad' OR l.is_service_area = 1)
    """)
    db_total_fu = c.fetchone()[0]
    assert kpis["total_followups"] == db_total_fu

    # Verify queue returns only Hyderabad leads
    df_queue = reports.get_hyderabad_followup_queue("all", limit=2000)
    assert len(df_queue) == db_total_fu, f"Expected {db_total_fu} total Hyderabad followups, got {len(df_queue)}"

    # Check non-Hyderabad follow-ups are excluded
    c.execute("SELECT COUNT(*) FROM FOLLOW_UP_SCHEDULE;")
    total_db_fu = c.fetchone()[0]
    assert len(df_queue) < total_db_fu, "Non-Hyderabad followups were not segregated from Hyderabad queue"

    print(f"-> Test 5 PASSED: Follow-up stats (Today: {kpis['today_followups']}, Overdue: {kpis['overdue_followups']}, Upcoming: {kpis['upcoming_followups']}, Total: {kpis['total_followups']}) strictly isolated to Hyderabad.")

    # -------------------------------------------------------------
    # TEST 6: Strict Non-Hyderabad Exclusion Verification
    # -------------------------------------------------------------
    print("\n[Test 6] Verifying Non-Hyderabad Lead Exclusion from Dashboard...")
    c.execute("SELECT COUNT(*) FROM LEADS WHERE is_service_area = 0;")
    archived_leads = c.fetchone()[0]
    assert archived_leads == 445, f"Expected 445 archived leads in DB, got {archived_leads}"

    # Verify no archived cities appear in Hyderabad chart data
    archived_cities = {"Pune", "Chennai", "Delhi NCR", "Mumbai", "Bangalore", "Ahmedabad", "Coimbatore", "Jaipur", "Kochi"}
    city_chart = charts["city"]
    cities_in_chart = set(city_chart["City"].unique())
    assert not (cities_in_chart & archived_cities), f"Archived cities found in Hyderabad chart: {cities_in_chart & archived_cities}"
    assert cities_in_chart == {"Hyderabad"}, f"Expected only Hyderabad, got {cities_in_chart}"

    print(f"-> Test 6 PASSED: All 445 non-Hyderabad leads safely segregated; 0 appeared in dashboard analytics.")

    conn.close()
    print("\n==================================================================")
    print("ALL 6 DASHBOARD VERIFICATION TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================================")

if __name__ == "__main__":
    run_tests()
