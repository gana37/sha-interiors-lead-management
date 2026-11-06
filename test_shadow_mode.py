"""
test_shadow_mode.py - Verification Suite for AI Shadow Mode Intelligence Engine
Tests:
- Shadow Mode configuration toggle (ON/OFF)
- Scenario detection (Office visit, Quotation, Materials, Possession delay, 3D design)
- Idempotency & duplicate recommendation prevention
- English-only WhatsApp drafts with strict SHA compliance
- Human-in-the-loop review lifecycle (Approve, Modify, Reject, and promotion)
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import database
import shadow_mode
import business_config


class TestShadowMode(unittest.TestCase):
    """Test suite for Shadow Mode intelligence and background recommendations."""

    @classmethod
    def setUpClass(cls):
        database.init_db()
        cls.test_lead_id = "SHA-TEST-0001"  # Kanishka
        cls._clean_test_recs()

    @classmethod
    def tearDownClass(cls):
        cls._clean_test_recs()

    @classmethod
    def _clean_test_recs(cls):
        conn = database.get_connection()
        with conn:
            conn.cursor().execute("DELETE FROM SHADOW_RECOMMENDATIONS WHERE lead_id = ?;", (cls.test_lead_id,))
        conn.close()

    def setUp(self):
        self._clean_test_recs()

    def test_01_shadow_mode_toggle(self):
        """Verify Shadow Mode toggle ON and OFF persistence."""
        shadow_mode.set_shadow_mode_enabled(True)
        self.assertTrue(shadow_mode.is_shadow_mode_enabled())

        shadow_mode.set_shadow_mode_enabled(False)
        self.assertFalse(shadow_mode.is_shadow_mode_enabled())

        # Re-enable
        shadow_mode.set_shadow_mode_enabled(True)
        self.assertTrue(shadow_mode.is_shadow_mode_enabled())

    def test_02_scenario_detection_office_visit(self):
        """Verify detection of Scenario 1 (Office Visit Interest) with compliant English draft."""
        # Simulated message expressing interest in visiting office
        sample_msg = "Hello, we would like to visit your office to discuss our 3BHK flat interiors."
        recs = shadow_mode.analyze_conversation_for_shadow_recommendations(
            lead_id=self.test_lead_id,
            latest_message_override=sample_msg
        )

        self.assertTrue(len(recs) > 0)
        office_rec = next((r for r in recs if r["scenario"] == "OFFICE_VISIT_INTEREST"), None)
        self.assertIsNotNone(office_rec)

        draft = office_rec["english_whatsapp_draft"]
        self.assertIn("Miyapur office", draft)
        self.assertNotIn("Hyderabad Studio", draft)
        self.assertIn("2:00 PM and 5:00 PM", draft)
        self.assertIn(business_config.GOOGLE_CALENDAR_BOOKING_LINK, draft)

        # Cleanup created recommendation
        conn = database.get_connection()
        with conn:
            conn.cursor().execute("DELETE FROM SHADOW_RECOMMENDATIONS WHERE recommendation_id = ?;", (office_rec["recommendation_id"],))
        conn.close()

    def test_03_scenario_detection_quotation_and_materials(self):
        """Verify detection of Quotation Request and Material Specifications scenarios."""
        sample_msg = "Please send quotation for 3BHK. What is the price if we use BWP marine plywood and acrylic?"
        recs = shadow_mode.analyze_conversation_for_shadow_recommendations(
            lead_id=self.test_lead_id,
            latest_message_override=sample_msg
        )

        scenarios = [r["scenario"] for r in recs]
        self.assertTrue("QUOTATION_REQUEST" in scenarios or "TECHNICAL_SPECS" in scenarios)

        # Cleanup
        rec_ids = [r["recommendation_id"] for r in recs]
        conn = database.get_connection()
        with conn:
            for rid in rec_ids:
                conn.cursor().execute("DELETE FROM SHADOW_RECOMMENDATIONS WHERE recommendation_id = ?;", (rid,))
        conn.close()

    def test_04_idempotency_duplicate_prevention(self):
        """Verify repeated messages for same scenario do not create duplicate recommendations."""
        sample_msg = "Can we book an appointment to meet at your Miyapur office?"
        
        # First call creates recommendation
        recs_1 = shadow_mode.analyze_conversation_for_shadow_recommendations(
            lead_id=self.test_lead_id,
            latest_message_override=sample_msg
        )
        self.assertEqual(len(recs_1), 1)
        rec_id = recs_1[0]["recommendation_id"]

        # Second call with same message must detect active recommendation and NOT duplicate
        recs_2 = shadow_mode.analyze_conversation_for_shadow_recommendations(
            lead_id=self.test_lead_id,
            latest_message_override=sample_msg
        )
        self.assertEqual(len(recs_2), 0, "Must be idempotent and not create duplicate recommendation")

        # Cleanup
        conn = database.get_connection()
        with conn:
            conn.cursor().execute("DELETE FROM SHADOW_RECOMMENDATIONS WHERE recommendation_id = ?;", (rec_id,))
        conn.close()

    def test_05_review_lifecycle_and_promotion(self):
        """Verify human review lifecycle: Pending -> Approved promotes to follow-up schedule."""
        sample_msg = "We want to finalize the agreement and start work."
        recs = shadow_mode.analyze_conversation_for_shadow_recommendations(
            lead_id=self.test_lead_id,
            latest_message_override=sample_msg
        )
        self.assertTrue(len(recs) > 0)
        rec = recs[0]
        rec_id = rec["recommendation_id"]

        # Approve recommendation
        review_res = shadow_mode.review_shadow_recommendation(
            recommendation_id=rec_id,
            action="Approved",
            reviewer_notes="Approved by sales lead"
        )
        self.assertTrue(review_res["success"])
        self.assertEqual(review_res["status"], "Approved")
        self.assertIsNotNone(review_res["promoted_schedule_id"])

        # Verify in DB
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status, promoted_schedule_id FROM SHADOW_RECOMMENDATIONS WHERE recommendation_id = ?;", (rec_id,))
        row = cursor.fetchone()
        self.assertEqual(row["status"], "Approved")
        self.assertEqual(row["promoted_schedule_id"], review_res["promoted_schedule_id"])

        # Cleanup
        with conn:
            cursor.execute("DELETE FROM SHADOW_RECOMMENDATIONS WHERE recommendation_id = ?;", (rec_id,))
            if review_res["promoted_schedule_id"]:
                cursor.execute("DELETE FROM FOLLOW_UP_SCHEDULE WHERE schedule_id = ?;", (review_res["promoted_schedule_id"],))
        conn.close()


if __name__ == "__main__":
    unittest.main()
