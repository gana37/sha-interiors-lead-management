"""
test_advanced_ai.py - Comprehensive Test Suite for SHA Advanced AI CRM & Design Intelligence
SHA Interface Interiors - AI-Powered Lead Management System

Tests:
1. SQL validation and read-only execution safeguards
2. CRM database intelligence queries (counts, filters, pipeline valuation, duplicates, missing data)
3. Interior design styles & room space planning knowledge
4. Materials technical specifications & head-to-head comparisons
5. Parametric interior cost estimation engine & BOQ tiers
6. Lead scoring factor-by-factor explainer & upgradable lead detection
7. Customer 360° consultation dossiers & tailored discovery questions
8. Multichannel follow-up queues & personalized WhatsApp/Email drafting
9. Master natural language query routing across domains
10. Production database integrity verification (250 synthetic leads preserved)
"""

import sys
import os
import unittest

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import database
import db_intelligence
import design_knowledge
import material_knowledge
import cost_estimator
import sales_intelligence
import customer_intelligence
import followup_intelligence
import ai_assistant


class TestAdvancedAICRM(unittest.TestCase):

    def test_01_sql_validation_security_safeguards(self):
        """Verifies that mutating queries and injections are strictly blocked, while SELECT is allowed."""
        print("\n[Test 1] Testing Safe SQL Validator & Security Guardrails...")
        # Valid read-only queries
        ok1, _ = db_intelligence.validate_sql_query("SELECT * FROM LEADS;")
        self.assertTrue(ok1)

        ok2, _ = db_intelligence.validate_sql_query("WITH top_leads AS (SELECT * FROM LEADS WHERE priority='High') SELECT * FROM top_leads;")
        self.assertTrue(ok2)

        # Destructive / mutating queries must be blocked
        bad_queries = [
            "DROP TABLE LEADS;",
            "DELETE FROM LEADS WHERE lead_id='SHA-2026-0001';",
            "UPDATE LEADS SET priority='Low';",
            "INSERT INTO LEADS (lead_id) VALUES ('HACK');",
            "ALTER TABLE LEADS DROP COLUMN phone;",
            "TRUNCATE TABLE LEADS;",
            "ATTACH DATABASE 'evil.db' AS evil;",
            "PRAGMA table_info(LEADS);",
            "SELECT * FROM LEADS; DROP TABLE LEADS;",
            "SELECT * FROM LEADS WHERE 1=1 -- comment injection"
        ]
        for bq in bad_queries:
            valid, err = db_intelligence.validate_sql_query(bq)
            self.assertFalse(valid, f"Failed to block destructive query: {bq}")
            self.assertTrue(len(err) > 0)

        print("-> Test 1 PASSED: Strict read-only query validator blocked all destructive patterns.")

    def test_02_crm_database_intelligence(self):
        """Tests safe analytical queries against actual SQLite database."""
        print("\n[Test 2] Testing CRM Database Intelligence Layer...")
        overview = db_intelligence.get_leads_overview()
        self.assertGreaterEqual(overview["total_leads"], 250)
        self.assertIn("High", overview["priority_counts"])

        # City analytics
        c_analytics = db_intelligence.get_city_lead_analytics()
        self.assertTrue(len(c_analytics) > 0)
        self.assertIn("Bangalore", [c["city"] for c in c_analytics])

        # Top 10 leads
        top10 = db_intelligence.get_top_leads_by_score(limit=10)
        self.assertEqual(len(top10), 10)
        self.assertGreaterEqual(top10[0]["lead_score"], top10[-1]["lead_score"])

        # Pipeline calculation
        pipe = db_intelligence.calculate_sales_pipeline_value()
        self.assertGreater(pipe["nominal_pipeline_inr"], 1000000)
        self.assertIn("₹", pipe["formatted_nominal"])

        # Missing data audit
        audit = db_intelligence.detect_missing_information()
        self.assertGreaterEqual(audit["completeness_score"], 50.0)

        # Tabular formatting
        table_md = db_intelligence.format_leads_table(top10[:3])
        self.assertIn("| Lead ID | Customer Name |", table_md)

        print("-> Test 2 PASSED: CRM intelligence extracted verified factual SQLite analytics.")

    def test_03_interior_design_knowledge_expert(self):
        """Tests design styles, spatial planning, and Vastu guidelines lookup."""
        print("\n[Test 3] Testing Interior Design Knowledge Expert...")
        scandi = design_knowledge.get_style_info("scandinavian")
        self.assertIsNotNone(scandi)
        self.assertIn("Hygge", scandi["description"])
        self.assertIn("Light oak / ash veneer", scandi["materials"])

        # Vastu search
        vastu_text = design_knowledge.search_design_knowledge("What are the Vastu rules for master bedroom?")
        self.assertIn("Vastu", vastu_text)
        self.assertIn("South-West", vastu_text)

        # Kitchen work triangle
        kitchen_text = design_knowledge.search_design_knowledge("modular kitchen layout")
        self.assertIn("Golden Work Triangle", kitchen_text)

        print("-> Test 3 PASSED: Interior design knowledge repository verified.")

    def test_04_materials_and_hardware_consultant(self):
        """Tests materials specifications and comparative intelligence."""
        print("\n[Test 4] Testing Materials, Finishes & Hardware Knowledge...")
        bwp = material_knowledge.CORE_BOARDS.get("bwp_plywood")
        self.assertIsNotNone(bwp)
        self.assertIn("IS:710", bwp["standard"])

        # Comparison: Plywood vs HDHMR
        comp_boards = material_knowledge.compare_materials("bwp_plywood", "hdhmr")
        self.assertIn("BWP Marine Grade Plywood", comp_boards)
        self.assertIn("HDHMR Board", comp_boards)

        # Comparison: Countertops
        comp_counter = material_knowledge.search_material_knowledge("compare quartz vs granite")
        self.assertIn("Engineered Quartz", comp_counter)
        self.assertIn("Natural Granite", comp_counter)

        # Hardware catalog
        blum = material_knowledge.HARDWARE_CATALOG.get("blum")
        self.assertIsNotNone(blum)
        self.assertIn("BLUMOTION", blum["key_products"][0])

        print("-> Test 4 PASSED: Materials technical repository and comparison tool verified.")

    def test_05_interior_cost_estimator(self):
        """Tests parametric cost calculations and 3-tier BOQ breakdowns."""
        print("\n[Test 5] Testing Parametric Cost Estimator Engine...")
        est = cost_estimator.estimate_project_cost(property_type="3BHK", built_up_area=1500, city="Bangalore")
        self.assertEqual(est["property_type"], "3BHK")
        self.assertEqual(est["built_up_area_sqft"], 1500)

        tiers = est["tiers"]
        self.assertIn("essential", tiers)
        self.assertIn("premium", tiers)
        self.assertIn("luxury", tiers)

        # Ensure luxury > premium > essential
        self.assertGreater(tiers["luxury"]["total_estimated_inr"], tiers["premium"]["total_estimated_inr"])
        self.assertGreater(tiers["premium"]["total_estimated_inr"], tiers["essential"]["total_estimated_inr"])

        # Ensure BOQ breakdown matches total cost
        boq = tiers["premium"]["boq_breakdown"]
        boq_sum = sum(boq.values())
        self.assertAlmostEqual(boq_sum, tiers["premium"]["total_estimated_inr"], delta=10)

        # Markdown report
        rep_md = cost_estimator.format_cost_estimate_markdown(est)
        self.assertIn("Cost Estimate for 3BHK", rep_md)
        self.assertIn("Modular Woodwork", rep_md)

        print("-> Test 5 PASSED: Parametric cost estimator computed accurate 3-tier BOQ estimates.")

    def test_06_sales_intelligence_and_score_explainer(self):
        """Tests factor-by-factor score explanations and upgradable lead detection."""
        print("\n[Test 6] Testing Lead Scoring Explainer & Sales Intelligence...")
        leads = database.get_all_leads()
        sample_lead = leads[0]

        expl = sales_intelligence.explain_lead_score(sample_lead)
        self.assertIn("total_score", expl)
        self.assertIn("breakdown", expl)
        self.assertIn("budget", expl["breakdown"])
        self.assertIn("location", expl["breakdown"])
        self.assertIn("requirements", expl["breakdown"])
        self.assertIn("readiness", expl["breakdown"])

        # Upgradable leads (score 70-79)
        upgradable_list = sales_intelligence.find_upgradable_leads()
        self.assertIsInstance(upgradable_list, list)
        if upgradable_list:
            up_sample = upgradable_list[0]
            self.assertGreaterEqual(up_sample["lead_score"], 70.0)
            self.assertLessEqual(up_sample["lead_score"], 79.9)
            self.assertIn("upgrade_recommendations", up_sample)

        print("-> Test 6 PASSED: Score breakdown and upgradable lead intelligence verified.")

    def test_07_customer_360_consultation_dossier(self):
        """Tests Customer 360 profile compilation and tailored consultation questions."""
        print("\n[Test 7] Testing Customer 360° Dossier & Consultation Questions...")
        leads = database.get_all_leads()
        sample_lead_id = leads[0]["lead_id"]

        dossier = customer_intelligence.build_customer_360_dossier(sample_lead_id)
        self.assertIsNotNone(dossier)
        self.assertEqual(dossier["lead_id"], sample_lead_id)
        self.assertIn("consultation_questions", dossier)
        self.assertGreaterEqual(len(dossier["consultation_questions"]), 3)
        self.assertIn("design_recommendations", dossier)

        md = customer_intelligence.format_customer_360_markdown(dossier)
        self.assertIn("Customer 360° Consultation Brief", md)
        self.assertIn(dossier["customer_name"], md)

        print("-> Test 7 PASSED: Customer 360° dossier and consultation questions verified.")

    def test_08_followup_intelligence_and_multichannel_drafts(self):
        """Tests operational queues and personalized WhatsApp/Email drafts."""
        print("\n[Test 8] Testing Follow-Up Intelligence & Multichannel Drafter...")
        overdue = followup_intelligence.get_overdue_queue()
        self.assertIsInstance(overdue, list)

        never_contacted = followup_intelligence.get_never_contacted_queue()
        self.assertIsInstance(never_contacted, list)

        leads = database.get_all_leads()
        lead = leads[0]

        wa = followup_intelligence.generate_personalized_whatsapp_draft(lead, goal="site_visit")
        self.assertIn(lead["customer_name"], wa)
        self.assertIn("SHA Interface Interiors", wa)

        em = followup_intelligence.generate_personalized_email_draft(lead, goal="consultation_invitation")
        self.assertIn("subject", em)
        self.assertIn("body", em)
        self.assertIn(lead["customer_name"], em["body"])

        print("-> Test 8 PASSED: Operational queues and multichannel draft generation verified.")

    def test_09_master_assistant_multi_domain_routing(self):
        """Tests master natural language query routing across CRM, Design, Materials, and Cost domains."""
        print("\n[Test 9] Testing Master Natural Language Query Router...")
        # CRM inquiry
        ans1 = ai_assistant.answer_crm_query("How many high priority leads do we have?")
        self.assertTrue("High" in ans1 or "High-Priority" in ans1)

        # Cost inquiry
        ans2 = ai_assistant.answer_crm_query("Estimate cost for 3BHK in Hyderabad")
        self.assertIn("Interior Project Cost Estimate", ans2)
        self.assertIn("3BHK", ans2)

        # Material inquiry
        ans3 = ai_assistant.answer_crm_query("Compare Plywood vs HDHMR")
        self.assertIn("BWP Marine Grade Plywood", ans3)

        # Pipeline inquiry
        ans4 = ai_assistant.answer_crm_query("Calculate total sales pipeline")
        self.assertIn("Pipeline Valuation", ans4)

        # Vastu inquiry
        ans5 = ai_assistant.answer_crm_query("What are the Vastu rules for master bedroom?")
        self.assertIn("Vastu", ans5)

        print("-> Test 9 PASSED: Master assistant routed inquiries accurately across all 5 knowledge domains.")

    def test_10_database_and_records_preservation(self):
        """Verifies that all 250 synthetic leads remain completely intact in production database."""
        print("\n[Test 10] Testing Database Records & Customer Preservation...")
        leads = database.get_all_leads()
        synth_count = sum(1 for l in leads if l.get("data_origin") == "synthetic_import")
        self.assertEqual(synth_count, 250, "Synthetic import records were altered or lost!")
        self.assertGreaterEqual(len(leads), 251)
        print(f"-> Test 10 PASSED: All {synth_count} synthetic leads strictly preserved in active database.")


def run_tests():
    print("=" * 70)
    print("STARTING ADVANCED AI CRM & INTERIOR DESIGN SUITE VERIFICATION")
    print("=" * 70)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAdvancedAICRM)
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print(f"ALL {result.testsRun} ADVANCED AI TESTS PASSED WITH 100% SUCCESS!")
    else:
        print(f"FAILED: {len(result.failures)} failures, {len(result.errors)} errors out of {result.testsRun} tests.")
    print("=" * 70)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
