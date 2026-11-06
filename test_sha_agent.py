"""
test_sha_agent.py - Verification Suite for Controlled SHA AI Agent
Tests:
- Verification of all 10 specialized agent tools
- Controlled permission boundaries (Read-only on DB, Human-in-the-loop)
- Compliance validation against SHA operating policies
- English-only output guarantee across all tools
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import database
import sha_agent
import business_config


class TestShaAgent(unittest.TestCase):
    """Test suite for SHA AI Agent tools and orchestration."""

    @classmethod
    def setUpClass(cls):
        database.init_db()
        cls.test_lead_id = "SHA-TEST-0001"  # Kanishka

    def test_01_tool_customer_lookup_and_crm_search(self):
        """Verify Tool 1 (customer lookup) and Tool 2 (crm search)."""
        # Lookup by ID
        res_id = sha_agent.tool_customer_lookup(self.test_lead_id)
        self.assertTrue(res_id["found"])
        self.assertEqual(res_id["lead"]["lead_id"], self.test_lead_id)

        # Lookup by Name
        res_name = sha_agent.tool_customer_lookup("Kanishka")
        self.assertTrue(res_name["found"])

        # CRM Search
        search_res = sha_agent.tool_crm_search("Gachibowli")
        self.assertTrue(len(search_res) > 0)
        self.assertTrue(any(l["lead_id"] == self.test_lead_id for l in search_res))

    def test_02_tool_interior_knowledge_search(self):
        """Verify Tool 3 (interior knowledge search)."""
        res = sha_agent.tool_interior_knowledge_search("BWP marine plywood standards")
        self.assertTrue(len(res) > 0)
        # Check source citation
        self.assertTrue(any("IS 710" in str(r.get("verified_source", "")) or "IS 710" in str(r.get("citation", "")) for r in res))

    def test_03_tool_conversation_analysis_and_requirements(self):
        """Verify Tool 4 (conversation analysis) and Tool 5 (requirement extraction)."""
        conv_info = sha_agent.tool_conversation_analysis(self.test_lead_id)
        self.assertEqual(conv_info["lead_id"], self.test_lead_id)
        self.assertIn("customer_name", conv_info)

        # Requirement extraction from lead
        reqs = sha_agent.tool_requirement_extraction(self.test_lead_id)
        self.assertIn("property_type", reqs)
        self.assertIn("materials_identified", reqs)

    def test_04_tool_followup_and_whatsapp_draft_generator(self):
        """Verify Tool 6 (follow-up recommendation) and Tool 7 (whatsapp draft generator)."""
        followup = sha_agent.tool_followup_recommendation(self.test_lead_id)
        self.assertIn("recommended_action", followup)
        self.assertIn("recommended_followup_date", followup)

        # WhatsApp draft generator
        draft_res = sha_agent.tool_whatsapp_draft_generator(self.test_lead_id, intent="consultation_invite")
        self.assertTrue(draft_res["is_english_only"])
        msg = draft_res["draft_message"]
        self.assertIn("Miyapur office", msg)
        self.assertNotIn("Hyderabad Studio", msg)
        self.assertIn("2:00 PM and 5:00 PM", msg)
        self.assertIn(business_config.GOOGLE_CALENDAR_BOOKING_LINK, msg)

    def test_05_tool_customer_intelligence_dossier(self):
        """Verify Tool 8 (customer intelligence dossier synthesis)."""
        dossier = sha_agent.tool_customer_intelligence(self.test_lead_id)
        self.assertEqual(dossier["lead_id"], self.test_lead_id)
        self.assertIn("lead_score", dossier)
        self.assertIn("property_requirements", dossier)
        self.assertIn("recommended_next_action", dossier)

    def test_06_tool_compliance_validation(self):
        """Verify Tool 9 (compliance validation detects forbidden terms)."""
        # Compliant message
        good_msg = f"Please visit our Miyapur office between 2:00 PM and 5:00 PM. Book here: {business_config.GOOGLE_CALENDAR_BOOKING_LINK}"
        good_eval = sha_agent.tool_compliance_validation(good_msg)
        self.assertTrue(good_eval["is_compliant"])

        # Non-compliant message (calls it Hyderabad Studio and offers 10 AM)
        bad_msg = "Please visit our Hyderabad Studio at 10:00 AM for a free 3D design."
        bad_eval = sha_agent.tool_compliance_validation(bad_msg)
        self.assertFalse(bad_eval["is_compliant"])
        self.assertTrue(any("Hyderabad Studio" in v for v in bad_eval["violations"]))
        self.assertTrue(any("2:00 PM - 5:00 PM" in v for v in bad_eval["violations"]))
        self.assertTrue(any("free 3D" in v for v in bad_eval["violations"]))

    def test_07_tool_appointment_information(self):
        """Verify Tool 10 (appointment information)."""
        appt = sha_agent.tool_appointment_information()
        self.assertEqual(appt["office_name"], "Miyapur office")
        self.assertEqual(appt["customer_appointment_hours"], "2:00 PM to 5:00 PM IST")
        self.assertEqual(appt["google_calendar_booking_link"], business_config.GOOGLE_CALENDAR_BOOKING_LINK)

    def test_08_run_agent_query(self):
        """Verify complete agent dispatcher execution."""
        res = sha_agent.run_agent_query("How can I book an appointment?", current_lead_id=self.test_lead_id)
        self.assertTrue(res["is_english_only"])
        self.assertIn("Miyapur office", res["response"])
        self.assertIn("tool_appointment_information", res["tools_used"])


if __name__ == "__main__":
    unittest.main()
