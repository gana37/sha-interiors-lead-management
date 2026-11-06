"""
test_intelligent_followups.py - Comprehensive Verification Suite
Intelligent Follow-up Management, Customer Conversation Understanding,
Task Lifecycle & Mandatory SHA Business Rules Compliance.
"""

import unittest
import datetime
import os
import sys
import sqlite3

# Ensure current working directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import database
import business_config
import followup_intelligence


class TestIntelligentFollowups(unittest.TestCase):
    """Test suite for Intelligent Follow-up Management and Task Lifecycle."""

    @classmethod
    def setUpClass(cls):
        database.init_db()

    def test_01_business_config_constants_and_policies(self):
        """Verify business_config includes website, instagram, and 3D quotation policy."""
        self.assertEqual(business_config.OFFICIAL_WEBSITE, "https://www.sha-interiors-hyderabad.com")
        self.assertEqual(business_config.OFFICIAL_INSTAGRAM, "https://www.instagram.com/madhusudhan_gonepelly/")
        self.assertIn("3D design finalisation", business_config.QUOTATION_POLICY)
        self.assertIn("preliminary budget", business_config.QUOTATION_POLICY.lower())

        info = business_config.get_business_info()
        self.assertEqual(info["official_website"], "https://www.sha-interiors-hyderabad.com")
        self.assertEqual(info["official_instagram"], "https://www.instagram.com/madhusudhan_gonepelly/")
        self.assertIn("3D design finalisation", info["quotation_policy"])

    def test_02_database_schema_and_lead_records_integrity(self):
        """Verify database schema additions in LEADS and FOLLOW_UP_SCHEDULE without record loss."""
        conn = database.get_connection()
        cursor = conn.cursor()

        # Check LEADS columns
        cursor.execute("PRAGMA table_info(LEADS);")
        leads_cols = {row[1] for row in cursor.fetchall()}
        required_lead_cols = [
            "expected_handover_date", "current_project_stage", "property_area_sqft",
            "pending_customer_question", "pending_team_action", "last_interaction_date",
            "last_interaction_summary"
        ]
        for col in required_lead_cols:
            self.assertIn(col, leads_cols, f"Column {col} missing in LEADS table")

        # Check FOLLOW_UP_SCHEDULE columns
        cursor.execute("PRAGMA table_info(FOLLOW_UP_SCHEDULE);")
        sched_cols = {row[1] for row in cursor.fetchall()}
        required_sched_cols = [
            "followup_reason", "next_action", "completion_notes", "priority",
            "rescheduled_from", "rescheduled_reason", "task_summary"
        ]
        for col in required_sched_cols:
            self.assertIn(col, sched_cols, f"Column {col} missing in FOLLOW_UP_SCHEDULE table")

        # Check all 9 leads are present and intact
        leads = database.get_all_leads()
        self.assertEqual(len(leads), 9, f"Expected 9 leads, found {len(leads)}")
        lead_ids = {l["lead_id"] for l in leads}
        self.assertIn("SHA-TEST-0001", lead_ids, "Test lead Kanishka must be present")
        self.assertIn("SHA-TEST-0002", lead_ids, "Test lead Dinesh must be present")

        # Check conversation history count is preserved (at least 19 records from baseline backup)
        cursor.execute("SELECT COUNT(*) FROM CUSTOMER_CONVERSATIONS;")
        conv_count = cursor.fetchone()[0]
        self.assertGreaterEqual(conv_count, 19, "Conversation records must be preserved")
        conn.close()

    def test_03_conversation_understanding_for_existing_leads(self):
        """Verify customer conversation understanding extracts correct profile, configuration, and stage."""
        # Test Dinesh (SHA-TEST-0002)
        analysis_dinesh = followup_intelligence.analyze_customer_conversation_and_status("SHA-TEST-0002")
        self.assertTrue(analysis_dinesh["success"])
        self.assertEqual(analysis_dinesh["customer_name"], "Dinesh")
        self.assertIn("2BHK", analysis_dinesh["project_type"])
        self.assertEqual(analysis_dinesh["locality"], "Miyapur")
        self.assertEqual(analysis_dinesh["scenario"], "office_visit_requested")

        # Test Kanishka (SHA-TEST-0001)
        analysis_kanishka = followup_intelligence.analyze_customer_conversation_and_status("SHA-TEST-0001")
        self.assertTrue(analysis_kanishka["success"])
        self.assertEqual(analysis_kanishka["customer_name"], "Kanishka")
        self.assertIn("kitchen", analysis_kanishka["customer_requirements"].lower())
        self.assertEqual(analysis_kanishka["locality"], "Gachibowli")

    def test_04_scenario_floor_plan_shared(self):
        """Scenario: Customer shared floor plan -> review layout, high priority, compliant draft."""
        test_id = "SHA-TEST-0001"
        conn = database.get_connection()
        with conn:
            # Add simulated floor plan message
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO CUSTOMER_CONVERSATIONS (conversation_id, lead_id, message_id, direction, message_content, created_at)
                VALUES ('TEST-CONV-FP', ?, 'MSG-FP', 'incoming', 'Hi team, I have attached our 3BHK architectural floor plan drawing. Please check room dimensions and layout.', '2026-11-05 20:00:00');
            """, (test_id,))

        try:
            rec = followup_intelligence.generate_intelligent_followup_recommendation(test_id)
            self.assertTrue(rec["success"])
            self.assertEqual(rec["scenario"], "floor_plan_shared")
            self.assertEqual(rec["priority"], "High")
            self.assertIn("floor plan", rec["followup_reason"].lower())
            self.assertIn("layout", rec["next_action"].lower())
            self.assertTrue(rec["is_compliant"])
            self.assertIn("Miyapur office", rec["suggested_whatsapp_message"])
            self.assertNotIn("Hyderabad Studio", rec["suggested_whatsapp_message"])
        finally:
            with conn:
                conn.cursor().execute("DELETE FROM CUSTOMER_CONVERSATIONS WHERE conversation_id = 'TEST-CONV-FP';")
            conn.close()

    def test_05_scenario_quotation_requested_and_3d_policy(self):
        """Scenario: Customer requested quote -> explains 3D design policy, preliminary budget clarity, high priority."""
        test_id = "SHA-TEST-0001"
        conn = database.get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO CUSTOMER_CONVERSATIONS (conversation_id, lead_id, message_id, direction, message_content, created_at)
                VALUES ('TEST-CONV-QT', ?, 'MSG-QT', 'incoming', 'Can you send the final quotation and discount for our apartment woodwork?', '2026-11-05 20:00:00');
            """, (test_id,))

        try:
            rec = followup_intelligence.generate_intelligent_followup_recommendation(test_id)
            self.assertTrue(rec["success"])
            self.assertEqual(rec["scenario"], "quotation_requested")
            self.assertEqual(rec["priority"], "High")
            self.assertIn("quotation", rec["followup_reason"].lower())
            self.assertIn("3D design finalisation", rec["suggested_whatsapp_message"])
            self.assertTrue(rec["is_compliant"])
            self.assertIn("Miyapur office", rec["suggested_whatsapp_message"])
            self.assertNotIn("Hyderabad Studio", rec["suggested_whatsapp_message"])
        finally:
            with conn:
                conn.cursor().execute("DELETE FROM CUSTOMER_CONVERSATIONS WHERE conversation_id = 'TEST-CONV-QT';")
            conn.close()

    def test_06_scenario_postponed_possession_handover(self):
        """Scenario: Customer postponed possession -> update expected date, future follow-up, medium priority."""
        test_id = "SHA-TEST-0001"
        conn = database.get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO CUSTOMER_CONVERSATIONS (conversation_id, lead_id, message_id, direction, message_content, created_at)
                VALUES ('TEST-CONV-PP', ?, 'MSG-PP', 'incoming', 'Our builder has delayed handover by 3 months. Possession is postponed until March.', '2026-11-05 20:00:00');
            """, (test_id,))

        try:
            rec = followup_intelligence.generate_intelligent_followup_recommendation(test_id)
            self.assertTrue(rec["success"])
            self.assertEqual(rec["scenario"], "postponed_possession")
            self.assertEqual(rec["priority"], "Medium")
            self.assertIn("postponed", rec["followup_reason"].lower())
            self.assertIn("possession", rec["next_action"].lower())
            self.assertTrue(rec["is_compliant"])
            self.assertIn("Miyapur office", rec["suggested_whatsapp_message"])
        finally:
            with conn:
                conn.cursor().execute("DELETE FROM CUSTOMER_CONVERSATIONS WHERE conversation_id = 'TEST-CONV-PP';")
            conn.close()

    def test_07_scenario_office_visit_requested_booking_link(self):
        """Scenario: Customer asked to visit office -> official Google Calendar link, Miyapur office, 2-5 PM slots."""
        test_id = "SHA-TEST-0001"
        conn = database.get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO CUSTOMER_CONVERSATIONS (conversation_id, lead_id, message_id, direction, message_content, created_at)
                VALUES ('TEST-CONV-OV', ?, 'MSG-OV', 'incoming', 'I want to visit your office to meet the design team and see material finishes.', '2026-11-05 20:00:00');
            """, (test_id,))

        try:
            rec = followup_intelligence.generate_intelligent_followup_recommendation(test_id)
            self.assertTrue(rec["success"])
            self.assertEqual(rec["scenario"], "office_visit_requested")
            self.assertEqual(rec["priority"], "High")
            self.assertIn(business_config.GOOGLE_CALENDAR_BOOKING_LINK, rec["suggested_whatsapp_message"])
            self.assertIn("Miyapur office", rec["suggested_whatsapp_message"])
            self.assertIn("2:00 PM to 5:00 PM", rec["suggested_whatsapp_message"])
            self.assertTrue(rec["is_compliant"])
        finally:
            with conn:
                conn.cursor().execute("DELETE FROM CUSTOMER_CONVERSATIONS WHERE conversation_id = 'TEST-CONV-OV';")
            conn.close()

    def test_08_scenario_technical_question_specialist_flag(self):
        """Scenario: Customer asked technical question -> flag for specialist review, no ungrounded speculation."""
        test_id = "SHA-TEST-0001"
        conn = database.get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO CUSTOMER_CONVERSATIONS (conversation_id, lead_id, message_id, direction, message_content, created_at)
                VALUES ('TEST-CONV-TQ', ?, 'MSG-TQ', 'incoming', 'Do you use calibrated BWP marine plywood for the sink unit and what warranty does Hettich hardware carry?', '2026-11-05 20:00:00');
            """, (test_id,))

        try:
            rec = followup_intelligence.generate_intelligent_followup_recommendation(test_id)
            self.assertTrue(rec["success"])
            self.assertEqual(rec["scenario"], "technical_question")
            self.assertEqual(rec["priority"], "High")
            self.assertIn("technical", rec["followup_reason"].lower())
            self.assertIn("specialist", rec["next_action"].lower())
            self.assertTrue(rec["is_compliant"])
            self.assertIn("Miyapur office", rec["suggested_whatsapp_message"])
        finally:
            with conn:
                conn.cursor().execute("DELETE FROM CUSTOMER_CONVERSATIONS WHERE conversation_id = 'TEST-CONV-TQ';")
            conn.close()

    def test_09_scenario_silent_customer_no_response(self):
        """Scenario: No customer reply -> polite non-repetitive check-in referencing project scope."""
        test_id = "SHA-TEST-0001"
        conn = database.get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO CUSTOMER_CONVERSATIONS (conversation_id, lead_id, message_id, direction, message_content, created_at, sending_status)
                VALUES ('TEST-CONV-NR', ?, 'MSG-NR', 'outgoing', 'Hello Kanishka, lookbook shared for your kitchen requirements.', '2026-11-05 20:00:00', 'User-Confirmed Sent');
            """, (test_id,))

        try:
            rec = followup_intelligence.generate_intelligent_followup_recommendation(test_id)
            self.assertTrue(rec["success"])
            self.assertEqual(rec["scenario"], "no_response")
            self.assertIn("no customer response", rec["followup_reason"].lower())
            self.assertTrue(rec["is_compliant"])
            self.assertNotIn("Hyderabad Studio", rec["suggested_whatsapp_message"])
        finally:
            with conn:
                conn.cursor().execute("DELETE FROM CUSTOMER_CONVERSATIONS WHERE conversation_id = 'TEST-CONV-NR';")
            conn.close()

    def test_10_task_management_full_lifecycle(self):
        """Verify scheduling, retrieving, editing, rescheduling, and completing tasks with notes."""
        test_lead = "SHA-TEST-0002"
        now_dt = datetime.datetime.now().strftime("%Y-%m-%d 15:00:00")

        # 1. Schedule
        sched_res = database.schedule_single_followup(
            lead_id=test_lead,
            scheduled_for=now_dt,
            channel="WhatsApp",
            message="Meeting follow up at Miyapur office",
            followup_reason="Customer expressed meeting interest",
            next_action="Share booking link",
            priority="High",
            task_summary="Office Consultation Booking"
        )
        self.assertTrue(sched_res["success"])
        sched_id = sched_res["schedule_id"]

        # 2. Retrieve
        task = database.get_followup_by_id(sched_id)
        self.assertIsNotNone(task)
        self.assertEqual(task["lead_id"], test_lead)
        self.assertEqual(task["priority"], "High")
        self.assertEqual(task["followup_reason"], "Customer expressed meeting interest")
        self.assertEqual(task["next_action"], "Share booking link")
        self.assertEqual(task["status"], "Scheduled")

        # 3. Edit
        edit_ok = database.edit_followup_task(
            schedule_id=sched_id,
            message="Updated meeting invitation message",
            priority="High",
            task_summary="Consultation Finalization"
        )
        self.assertTrue(edit_ok)
        task_edited = database.get_followup_by_id(sched_id)
        self.assertEqual(task_edited["message"], "Updated meeting invitation message")
        self.assertEqual(task_edited["task_summary"], "Consultation Finalization")

        # 4. Reschedule
        new_due = "2026-11-20 16:30:00"
        resched_res = database.reschedule_followup_task(
            schedule_id=sched_id,
            new_scheduled_for=new_due,
            reschedule_reason="Customer requested weekend appointment",
            new_channel="Phone Call"
        )
        self.assertTrue(resched_res["success"])
        task_resched = database.get_followup_by_id(sched_id)
        self.assertEqual(task_resched["scheduled_for"], new_due)
        self.assertEqual(task_resched["rescheduled_from"], now_dt)
        self.assertEqual(task_resched["rescheduled_reason"], "Customer requested weekend appointment")
        self.assertEqual(task_resched["channel"], "Phone Call")

        # 5. Complete
        comp_ok = database.complete_followup_task(
            schedule_id=sched_id,
            completion_notes="Consultation confirmed. Customer scheduled via Google Calendar."
        )
        self.assertTrue(comp_ok)
        task_completed = database.get_followup_by_id(sched_id)
        self.assertEqual(task_completed["status"], "Completed")
        self.assertIsNotNone(task_completed["completed_at"])
        self.assertEqual(task_completed["completion_notes"], "Consultation confirmed. Customer scheduled via Google Calendar.")

        # Clean up test task
        conn = database.get_connection()
        with conn:
            conn.cursor().execute("DELETE FROM FOLLOW_UP_SCHEDULE WHERE schedule_id = ?;", (sched_id,))
            conn.cursor().execute("DELETE FROM LEAD_ACTIVITY_LOG WHERE activity_description LIKE ?;", (f"%{sched_id}%",))
        conn.close()

    def test_11_customer_data_isolation(self):
        """Verify strict customer data isolation: Dinesh's Kokapet 2BHK details never leak to Kanishka or Aditya."""
        dinesh_rec = followup_intelligence.generate_intelligent_followup_recommendation("SHA-TEST-0002")
        kanishka_rec = followup_intelligence.generate_intelligent_followup_recommendation("SHA-TEST-0001")
        aditya_rec = followup_intelligence.generate_intelligent_followup_recommendation("SHA-2026-0005")

        # Assert no leak in messages or summaries
        self.assertNotIn("Dinesh", kanishka_rec["suggested_whatsapp_message"])
        self.assertNotIn("Kokapet", kanishka_rec["suggested_whatsapp_message"])
        self.assertNotIn("Kanishka", dinesh_rec["suggested_whatsapp_message"])
        self.assertNotIn("Aditya", dinesh_rec["suggested_whatsapp_message"])
        self.assertNotIn("Aditya", kanishka_rec["suggested_whatsapp_message"])

    def test_12_disallowed_appointment_slots_fail_compliance(self):
        """Verify compliance validator explicitly rejects appointments outside 2 PM - 5 PM IST."""
        # Forbidden offerings
        bad_msg_1 = "We can meet you at our Miyapur office between 10:00 AM and 2:00 PM tomorrow."
        ok_1, violations_1 = business_config.validate_message_compliance(bad_msg_1)
        self.assertFalse(ok_1)
        self.assertTrue(any("outside permitted window" in v.lower() for v in violations_1))

        bad_msg_2 = "Would you like an appointment between 5:00 PM and 6:00 PM at our Miyapur office?"
        ok_2, violations_2 = business_config.validate_message_compliance(bad_msg_2)
        self.assertFalse(ok_2)
        self.assertTrue(any("outside permitted window" in v.lower() for v in violations_2))

        bad_msg_3 = "Visit our Hyderabad Studio for your 3D design consultation."
        ok_3, violations_3 = business_config.validate_message_compliance(bad_msg_3)
        self.assertFalse(ok_3)
        self.assertTrue(any("hyderabad studio" in v.lower() for v in violations_3))


if __name__ == "__main__":
    unittest.main()
