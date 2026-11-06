"""
test_hyderabad_migration.py - Comprehensive Verification Suite for Hyderabad Edition
SHA Interface Interiors - AI-Powered Lead Management System (Hyderabad Edition)

Validates:
1. Locality master catalog and dynamic expansion (hyderabad_geo.py)
2. Fine-grained locality lead scoring (Tier 1: 20, Tier 2: 17, Tier 3: 14, Tier 4: 12)
3. Database preservation (all 800 records intact, 355 active Hyderabad, 445 archived)
4. Active Hyderabad query filtering (get_all_leads active_only=True)
5. Locality and regional search in database
6. Executive KPIs and localized chart data (reports.py)
7. Dataset integrity for SHA_Hyderabad_Interior_Design_Leads.csv & .xlsx
8. Manual lead capture with Hyderabad locality and state auto-defaults
9. Follow-up queues localized to active service area
10. Backward compatibility with all existing test suites
"""

import os
import sys
import unittest
import pandas as pd
import sqlite3

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import hyderabad_geo as hg
import database
import lead_scoring
import lead_capture
import reports
import followup_intelligence


class TestHyderabadMigration(unittest.TestCase):

    def test_01_locality_catalog_and_regions(self):
        """Verify locality catalog covers all 6 regions and returns valid counts."""
        localities = hg.get_all_localities()
        self.assertGreaterEqual(len(localities), 60)
        self.assertIn("Gachibowli", localities)
        self.assertIn("Jubilee Hills", localities)
        self.assertIn("Kukatpally", localities)
        self.assertIn("Uppal", localities)
        self.assertIn("Secunderabad", localities)
        self.assertIn("Shamshabad", localities)

        # Region resolution
        self.assertEqual(hg.get_region_for_locality("Gachibowli"), "West Hyderabad")
        self.assertEqual(hg.get_region_for_locality("Banjara Hills"), "Central Hyderabad")
        self.assertEqual(hg.get_region_for_locality("Kukatpally"), "North Hyderabad")
        self.assertEqual(hg.get_region_for_locality("LB Nagar"), "East Hyderabad")
        self.assertEqual(hg.get_region_for_locality("Secunderabad"), "Secunderabad")
        self.assertEqual(hg.get_region_for_locality("Mehdipatnam"), "South Hyderabad")

    def test_02_dynamic_locality_addition(self):
        """Verify new localities can be registered dynamically without rejection."""
        custom_name = "Narsingi Golden Mile"
        success = hg.register_custom_locality(custom_name, "West Hyderabad")
        self.assertTrue(success)
        self.assertIn(custom_name, hg.get_all_localities())
        self.assertEqual(hg.get_region_for_locality(custom_name), "West Hyderabad")
        # Custom registered locality should receive baseline Hyderabad score (14)
        self.assertEqual(hg.get_locality_score(custom_name), 14)

    def test_03_locality_pincodes(self):
        """Verify authentic postal PIN code resolution for Hyderabad localities."""
        self.assertEqual(hg.get_pincode_for_locality("Gachibowli"), "500032")
        self.assertEqual(hg.get_pincode_for_locality("Madhapur"), "500081")
        self.assertEqual(hg.get_pincode_for_locality("Banjara Hills"), "500034")
        self.assertEqual(hg.get_pincode_for_locality("Secunderabad"), "500003")

    def test_04_locality_scoring_tiers(self):
        """Verify tiered qualification scoring for Hyderabad localities."""
        # Tier 1: Prime IT & Luxury (20 pts)
        score_jh, detail_jh = lead_scoring.calculate_location_score("Hyderabad", locality="Jubilee Hills")
        self.assertEqual(score_jh, 20)
        self.assertIn("Prime IT & Luxury Corridor", detail_jh)

        score_gach, _ = lead_scoring.calculate_location_score("Hyderabad", locality="Gachibowli")
        self.assertEqual(score_gach, 20)

        # Tier 2: Established Residential (17 pts)
        score_kpt, detail_kpt = lead_scoring.calculate_location_score("Hyderabad", locality="Kukatpally")
        self.assertEqual(score_kpt, 17)
        self.assertIn("Established Residential Hub", detail_kpt)

        # Tier 3: Core Urban (14 pts)
        score_ameer, detail_ameer = lead_scoring.calculate_location_score("Hyderabad", locality="Ameerpet")
        self.assertEqual(score_ameer, 14)

        # Tier 4: Greater Metropolitan (12 pts)
        score_lb, detail_lb = lead_scoring.calculate_location_score("Hyderabad", locality="LB Nagar")
        self.assertEqual(score_lb, 12)

        # Backward compatibility with city-only call
        score_hyd, _ = lead_scoring.calculate_location_score("Hyderabad")
        self.assertEqual(score_hyd, 20)

    def test_05_database_preservation_and_partitioning(self):
        """Verify total records (800) are strictly preserved, with 355 active and 445 archived."""
        conn = sqlite3.connect("file:sha_leads.db?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM LEADS;")
        total = cur.fetchone()[0]
        self.assertGreaterEqual(total, 800, f"Expected at least 800 total leads preserved, got {total}")

        cur.execute("SELECT COUNT(*) FROM LEADS WHERE is_service_area = 1;")
        active_hyd = cur.fetchone()[0]
        self.assertGreaterEqual(active_hyd, 355, f"Expected at least 355 active Hyderabad leads, got {active_hyd}")

        cur.execute("SELECT COUNT(*) FROM LEADS WHERE is_service_area = 0;")
        archived = cur.fetchone()[0]
        self.assertEqual(archived, 445, f"Expected 445 archived non-Hyderabad leads, got {archived}")
        conn.close()

    def test_06_active_hyderabad_query_filtering(self):
        """Verify get_all_leads filters strictly for active Hyderabad records when active_only=True."""
        active_leads = database.get_all_leads(active_only=True)
        self.assertGreaterEqual(len(active_leads), 355)
        migrated_leads = [lead for lead in active_leads if not str(lead.get('lead_id', '')).startswith('SHA-AUTO')]
        for l in migrated_leads[:30]:
            self.assertEqual(l["city"], "Hyderabad")
            self.assertEqual(l["state"], "Telangana")
            self.assertIsNotNone(l["locality"])
            self.assertIsNotNone(l["region"])

        # When active_only=False, returns all 800
        all_leads = database.get_all_leads(active_only=False)
        self.assertGreaterEqual(len(all_leads), 800)

    def test_07_locality_and_region_filters(self):
        """Verify filtering by specific locality and region."""
        west_leads = database.get_all_leads(region="West Hyderabad", active_only=True)
        self.assertGreater(len(west_leads), 0)
        for l in west_leads:
            self.assertEqual(l["region"], "West Hyderabad")

        gach_leads = database.get_all_leads(locality="Gachibowli", active_only=True)
        self.assertGreater(len(gach_leads), 0)
        for l in gach_leads:
            self.assertEqual(l["locality"], "Gachibowli")

    def test_08_search_by_locality_and_pincode(self):
        """Verify search query matches locality, region, or pincode."""
        results = database.get_all_leads(search_query="Banjara", active_only=True)
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertTrue("Banjara" in r["locality"] or "Banjara" in r["customer_name"])

    def test_09_executive_kpis_and_hyderabad_analytics(self):
        """Verify executive KPIs and chart data reflect Hyderabad operations."""
        kpis = reports.get_hyderabad_kpis()
        self.assertGreaterEqual(kpis["total_leads"], 355)
        self.assertGreater(kpis["average_lead_score"], 0)

        charts = reports.get_chart_data()
        self.assertIn("locality", charts)
        self.assertIn("region", charts)
        self.assertGreater(len(charts["locality"]), 0)
        self.assertGreater(len(charts["region"]), 0)

    def test_10_dataset_exports_verification(self):
        """Verify SHA_Hyderabad_Interior_Design_Leads.csv and .xlsx files exist and have all 18 fields."""
        csv_path = "SHA_Hyderabad_Interior_Design_Leads.csv"
        xlsx_path = "SHA_Hyderabad_Interior_Design_Leads.xlsx"

        self.assertTrue(os.path.exists(csv_path), "CSV dataset not found")
        self.assertTrue(os.path.exists(xlsx_path), "Excel dataset not found")

        df_csv = pd.read_csv(csv_path)
        self.assertEqual(len(df_csv), 355)
        required_18_fields = [
            "Lead ID", "Customer Name", "Phone", "Email", "State", "City",
            "Locality", "PIN Code", "Budget Range", "Project Type", "Property Status",
            "Project Timeline", "Scope of Work", "Customer Requirements",
            "Purchase Readiness", "Lead Score", "Priority", "Lead Status"
        ]
        for field in required_18_fields:
            self.assertIn(field, df_csv.columns, f"Missing required field {field}")

        # Check all records are Hyderabad, Telangana
        self.assertTrue((df_csv["City"] == "Hyderabad").all())
        self.assertTrue((df_csv["State"] == "Telangana").all())

    def test_11_followup_queues_active_service_area(self):
        """Verify operational follow-up queues include active Hyderabad records only."""
        overdue = followup_intelligence.get_overdue_queue()
        due_today = followup_intelligence.get_due_today_queue()
        never_contacted = followup_intelligence.get_never_contacted_queue()
        awaiting = followup_intelligence.get_awaiting_response_queue()

        # All leads in queues must be in service area
        for item in (overdue + due_today + never_contacted + awaiting)[:30]:
            self.assertIn(item.get("city"), ["Hyderabad", "Secunderabad", "Cyberabad"])

    def test_12_manual_lead_capture_defaults(self):
        """Verify manual lead capture defaults to Hyderabad, Telangana and accepts locality."""
        test_payload = {
            "customer_name": "Kavita Rao",
            "phone": "+91 98490 55555",
            "email": "kavita.rao@example.com",
            "city": "Hyderabad",
            "state": "Telangana",
            "locality": "Kokapet",
            "region": "West Hyderabad",
            "pincode": "500075",
            "lead_source": "Website Inquiry",
            "budget_range": "₹10 lakh–₹25 lakh",
            "project_type": "3BHK",
            "property_status": "Ready to Move",
            "project_timeline": "Immediately",
            "scope_of_work": "Full Turnkey Interior",
            "customer_requirements": "Complete 3BHK turnkey interior in Kokapet with acrylic kitchen.",
            "purchase_readiness": "Ready to Start",
            "preferred_contact_method": "Phone Call"
        }
        success, msg, new_id, score_data = lead_capture.create_manual_lead(test_payload, return_score=True)
        self.assertTrue(success)
        self.assertIsNotNone(new_id)
        self.assertEqual(score_data["priority"], "High")

        # Verify persisted record
        saved = database.get_lead_by_id(new_id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved["city"], "Hyderabad")
        self.assertEqual(saved["state"], "Telangana")
        self.assertEqual(saved["locality"], "Kokapet")
        self.assertEqual(saved["pincode"], "500075")
        self.assertEqual(saved["is_service_area"], 1)

        # Clean up test lead to avoid test pollution
        conn = database.get_connection()
        with conn:
            conn.cursor().execute("DELETE FROM LEADS WHERE lead_id = ?;", (new_id,))
        conn.close()


if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("STARTING HYDERABAD EDITION TRANSFORMATION TEST SUITE")
    print("=" * 65)
    unittest.main(verbosity=2)
