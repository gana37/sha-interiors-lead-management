"""
test_crm_search.py - Verification Suite for Advanced CRM Search Engine & Multi-Filter Queries
SHA Interface Interiors - Hyderabad Edition
"""

import os
import sys
import unittest

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.getcwd())

import database
import crm_search

DB_PATH = database.DEFAULT_DB_PATH

class TestCRMSearch(unittest.TestCase):

    def test_01_show_all_high_priority_leads(self):
        """Test 1: 'Show all high-priority leads' finds all 5 High Priority leads."""
        res = crm_search.parse_and_search_crm("Show all high-priority leads", db_path=DB_PATH)
        self.assertTrue(res.get("success") or res.get("intent") == "crm_search")
        leads = res.get("leads", [])
        self.assertEqual(len(leads), 5)
        for l in leads:
            self.assertEqual(l["priority"], "High")
        self.assertIn("Kanishka", [l["customer_name"] for l in leads])
        self.assertIn("Dinesh", [l["customer_name"] for l in leads])
        print("-> Test 1 PASSED: 'Show all high-priority leads' successfully returned all 5 High Priority accounts.")

    def test_02_find_customers_in_gachibowli(self):
        """Test 2: 'Find customers in Gachibowli' finds Kanishka."""
        res = crm_search.parse_and_search_crm("Find customers in Gachibowli", db_path=DB_PATH)
        leads = res.get("leads", [])
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]["customer_name"], "Kanishka")
        self.assertEqual(leads[0]["locality"], "Gachibowli")
        print("-> Test 2 PASSED: 'Find customers in Gachibowli' returned Kanishka in Gachibowli.")

    def test_03_show_customers_with_budgets_above_10_lakh(self):
        """Test 3: 'Show customers with budgets above ₹10 lakh' correctly filters."""
        res = crm_search.parse_and_search_crm("Show customers with budgets above ₹10 lakh", db_path=DB_PATH)
        leads = res.get("leads", [])
        # All leads whose budget upper bound is >= 10 Lakh
        self.assertGreaterEqual(len(leads), 4)
        names = [l["customer_name"] for l in leads]
        self.assertIn("Vivek Ankit", names)
        self.assertIn("Dr. Chakravarthy.B El PT", names)
        self.assertIn("Kanishka", names)
        self.assertIn("Aditya", names)
        print(f"-> Test 3 PASSED: 'Show customers with budgets above ₹10 lakh' matched {len(leads)} accounts.")

    def test_04_find_all_3bhk_customers(self):
        """Test 4: 'Find all 3BHK customers' returns all 3BHK leads."""
        res = crm_search.parse_and_search_crm("Find all 3BHK customers", db_path=DB_PATH)
        leads = res.get("leads", [])
        self.assertEqual(len(leads), 4)
        for l in leads:
            self.assertEqual(l["project_type"], "3BHK")
        names = [l["customer_name"] for l in leads]
        self.assertIn("Kanishka", names)
        self.assertIn("Dr. Chakravarthy.B El PT", names)
        self.assertIn("Saikoushik Chavali", names)
        self.assertIn("Aditya", names)
        print("-> Test 4 PASSED: 'Find all 3BHK customers' matched all 4 3BHK accounts.")

    def test_05_show_leads_with_pending_followups(self):
        """Test 5: 'Show leads with pending follow-ups' returns leads with scheduled tasks."""
        res = crm_search.parse_and_search_crm("Show leads with pending follow-ups", db_path=DB_PATH)
        leads = res.get("leads", [])
        self.assertGreaterEqual(len(leads), 1)
        for l in leads:
            self.assertNotEqual(l["next_followup_desc"], "No Task Scheduled")
        print(f"-> Test 5 PASSED: 'Show leads with pending follow-ups' returned {len(leads)} active leads.")

    def test_06_find_customers_who_have_not_converted(self):
        """Test 6: 'Find customers who have not converted' returns active unconverted leads."""
        res = crm_search.parse_and_search_crm("Find customers who have not converted", db_path=DB_PATH)
        leads = res.get("leads", [])
        self.assertEqual(len(leads), 9)
        for l in leads:
            self.assertNotIn(l["lead_status"].lower(), ["converted", "lost"])
        print("-> Test 6 PASSED: 'Find customers who have not converted' returned 9 active pipeline leads.")

    def test_07_compare_leads_from_different_hyderabad_localities(self):
        """Test 7: 'Compare leads from different Hyderabad localities' returns comparison table."""
        res = crm_search.parse_and_search_crm("Compare leads from different Hyderabad localities", db_path=DB_PATH)
        self.assertEqual(res.get("intent"), "locality_comparison")
        md = res.get("markdown", "")
        self.assertIn("Hyderabad Metropolitan Localities Lead Comparison", md)
        self.assertIn("Gachibowli", md)
        self.assertIn("Miyapur", md)
        self.assertIn("Kondapur", md)
        print("-> Test 7 PASSED: 'Compare leads from different Hyderabad localities' produced comparative analytics.")

    def test_08_find_customers_by_name_or_phone(self):
        """Test 8: 'Find customer Kanishka' and phone search work accurately."""
        # Search by name
        res_name = crm_search.parse_and_search_crm("Find customer Kanishka", db_path=DB_PATH)
        leads_name = res_name.get("leads", [])
        self.assertEqual(len(leads_name), 1)
        self.assertEqual(leads_name[0]["customer_name"], "Kanishka")

        # Search by phone number
        res_phone = crm_search.parse_and_search_crm("Find customer 85005 25509", db_path=DB_PATH)
        leads_phone = res_phone.get("leads", [])
        self.assertEqual(len(leads_phone), 1)
        self.assertEqual(leads_phone[0]["customer_name"], "Dinesh")
        print("-> Test 8 PASSED: Customer search by Name and Phone number verified.")

    def test_09_show_customers_with_upcoming_followups(self):
        """Test 9: 'Show customers with upcoming follow-ups' works."""
        res = crm_search.parse_and_search_crm("Show customers with upcoming follow-ups", db_path=DB_PATH)
        leads = res.get("leads", [])
        self.assertGreaterEqual(len(leads), 1)
        print(f"-> Test 9 PASSED: 'Show customers with upcoming follow-ups' returned {len(leads)} leads.")

    def test_10_multi_criteria_search(self):
        """Test 10: Multi-filter combinations work seamlessly together."""
        # 3BHK + High Priority
        filters_1 = {"project_type": "3BHK", "priority": "High"}
        res_1 = crm_search.search_crm_leads(filters_1, db_path=DB_PATH)
        self.assertEqual(res_1["total_count"], 3)  # Kanishka, Dr. Chakravarthy, Aditya
        for l in res_1["leads"]:
            self.assertEqual(l["project_type"], "3BHK")
            self.assertEqual(l["priority"], "High")

        # 3BHK + Gachibowli
        filters_2 = {"project_type": "3BHK", "locality": "Gachibowli"}
        res_2 = crm_search.search_crm_leads(filters_2, db_path=DB_PATH)
        self.assertEqual(res_2["total_count"], 1)
        self.assertEqual(res_2["leads"][0]["customer_name"], "Kanishka")

        # 2BHK + Miyapur
        filters_3 = {"project_type": "2BHK", "locality": "Miyapur"}
        res_3 = crm_search.search_crm_leads(filters_3, db_path=DB_PATH)
        self.assertEqual(res_3["total_count"], 1)
        self.assertEqual(res_3["leads"][0]["customer_name"], "Dinesh")
        print("-> Test 10 PASSED: Multi-criteria structured searches verified with 100% precision.")

    def test_11_empty_search_results_graceful_handling(self):
        """Test 11: Non-matching searches return 0 leads and friendly guidance without crashing."""
        filters = {"locality": "NonExistentCity", "project_type": "Villa"}
        res = crm_search.search_crm_leads(filters, db_path=DB_PATH)
        self.assertEqual(res["total_count"], 0)
        self.assertEqual(len(res["leads"]), 0)
        md = crm_search.format_search_results_markdown(res, query_title="Villa in NonExistentCity")
        self.assertIn("No matching leads found", md)
        self.assertIn("Suggestions", md)
        print("-> Test 11 PASSED: Empty search results handled gracefully.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
