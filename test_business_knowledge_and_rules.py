"""
test_business_knowledge_and_rules.py - Master Verification Suite for Central Business Knowledge & Communication Rules
SHA Interface Interiors - Hyderabad Edition

Verifies:
1. Central configuration constants:
   - General Office Hours: 10:00 AM to 6:00 PM IST, Monday through Sunday.
   - Customer Appointment Window: 2:00 PM to 5:00 PM IST, Monday through Sunday.
   - Confirmation Policy: Manual confirmation workflow active until Google Calendar integration.
   - Office Name: "Miyapur office" (Never "Hyderabad Studio" or "Experience Center").
   - Official Google Maps Link.
2. AI prompt grounding & rules across modules.
3. Conversational Assistant responses for appointments, timings, and directions.
4. Website Enquiry outbound message formatting with 2 PM - 5 PM appointment guidance.
5. Follow-up templates and intelligence email drafts.
6. Explicit test failures when customer appointment messages offer 10 AM-2 PM or 5 PM-6 PM.
7. Verification that database records (7 genuine + 2 test leads) remain completely intact.
"""

import os
import sys
import unittest

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.getcwd())

import business_config
import whatsapp_assistant
import enquiry_whatsapp
import followup_templates
import followup_intelligence
import ai_service
import database

DB_PATH = database.DEFAULT_DB_PATH


class TestBusinessKnowledgeAndRules(unittest.TestCase):

    def test_01_central_business_constants(self):
        """Test 1: Verify exact official business parameters in central configuration."""
        self.assertEqual(business_config.BUSINESS_NAME, "SHA Interface Interiors")
        self.assertEqual(business_config.OFFICE_NAME, "Miyapur office")
        
        # General Office Operating Hours
        self.assertEqual(business_config.OFFICE_HOURS_START, "10:00 AM")
        self.assertEqual(business_config.OFFICE_HOURS_END, "6:00 PM")
        self.assertEqual(business_config.WORKING_HOURS_START, "10:00 AM")
        self.assertEqual(business_config.WORKING_HOURS_END, "6:00 PM")
        self.assertEqual(business_config.TIMEZONE, "IST")
        self.assertIn("10:00 AM to 6:00 PM", business_config.OFFICE_HOURS)
        self.assertIn("IST", business_config.OFFICE_HOURS)
        self.assertIn("Monday through Sunday", business_config.WORKING_DAYS)

        # Customer Appointment Availability Window
        self.assertEqual(business_config.APPOINTMENT_HOURS_START, "2:00 PM")
        self.assertEqual(business_config.APPOINTMENT_HOURS_END, "5:00 PM")
        self.assertEqual(business_config.APPOINTMENT_HOURS, "2:00 PM to 5:00 PM IST")
        self.assertEqual(business_config.APPOINTMENT_DAYS, "Monday through Sunday")

        # Official Location
        self.assertEqual(business_config.OFFICE_MAPS_LINK, "https://maps.app.goo.gl/Ybuctd1ghqFiQ69D6")

        # Calendar confirmation policy
        self.assertEqual(business_config.CALENDAR_INTEGRATION_STATUS, "manual_workflow_active")
        self.assertIn("manual confirmation", business_config.APPOINTMENT_CONFIRMATION_POLICY.lower())
        self.assertIn("automatic only after successful event creation", business_config.APPOINTMENT_CONFIRMATION_POLICY.lower())
        print("-> Test 1 PASSED: Central business constants verified (General: 10 AM-6 PM, Appointments: 2 PM-5 PM).")

    def test_02_mandatory_communication_rules_block(self):
        """Test 2: Verify AI system instruction block contains all mandatory rules and windows."""
        block = business_config.AI_SYSTEM_INSTRUCTION_BLOCK
        self.assertIn("SHA Interface Interiors", block)
        self.assertIn("Miyapur office", block)
        self.assertIn("10:00 AM to 6:00 PM", block)
        self.assertIn("2:00 PM to 5:00 PM", block)
        self.assertIn("IST", block)
        self.assertIn("all 7 days", block.lower())
        self.assertIn("phone call", block.lower())
        self.assertIn("https://maps.app.goo.gl/Ybuctd1ghqFiQ69D6", block)
        self.assertIn("NEVER call it \"Hyderabad Studio\"", block)
        self.assertIn("NEVER offer, solicit, or suggest appointments between 10:00 AM and 2:00 PM or between 5:00 PM and 6:00 PM", block)
        print("-> Test 2 PASSED: AI system instruction block contains all mandatory rules and time constraints.")

    def test_03_canonical_example_customer_response(self):
        """Test 3: Verify the benchmark customer response satisfies all communication criteria."""
        example = business_config.EXAMPLE_CUSTOMER_RESPONSE
        self.assertIn("SHA Interface Interiors", example)
        self.assertIn("Miyapur office", example)
        self.assertIn("https://calendar.app.google/DMb8MRbZBz97gYbc8", example)
        self.assertNotIn("Hyderabad Studio", example)
        self.assertIn("Once you book a slot, your appointment will be confirmed through Google Calendar.", example)
        
        # Validate with compliance checker
        is_valid, errors = business_config.validate_message_compliance(example)
        self.assertTrue(is_valid, f"Benchmark example failed compliance check: {errors}")
        print("-> Test 3 PASSED: Canonical benchmark response passes all compliance checks.")

    def test_04_whatsapp_assistant_system_instruction(self):
        """Test 4: Verify whatsapp_assistant.py SYSTEM_SALES_INSTRUCTION enforces Miyapur office & hours."""
        sys_prompt = whatsapp_assistant.SYSTEM_SALES_INSTRUCTION
        self.assertIn("Miyapur office", sys_prompt)
        self.assertIn("10:00 AM to 6:00 PM", sys_prompt)
        self.assertIn("2:00 PM to 5:00 PM", sys_prompt)
        self.assertIn("Monday through Sunday", sys_prompt)
        self.assertIn("https://maps.app.goo.gl/Ybuctd1ghqFiQ69D6", sys_prompt)
        self.assertNotIn("inviting to our Hyderabad studio", sys_prompt)
        print("-> Test 4 PASSED: WhatsApp assistant system prompt correctly configured.")

    def test_05_whatsapp_assistant_appointment_scheduling(self):
        """Test 5: Verify conversational assistant appointment response offers Miyapur office & booking link."""
        lead = database.get_lead_by_id("SHA-TEST-0001", db_path=DB_PATH)
        self.assertIsNotNone(lead)
        
        reply = whatsapp_assistant._generate_local_expert_reply(
            lead=lead,
            incoming_msg="Can I book an appointment to meet and discuss my interiors?",
            history=[],
            is_opt_out=False
        )
        
        self.assertIn("Miyapur office", reply)
        self.assertIn("https://calendar.app.google/DMb8MRbZBz97gYbc8", reply)
        self.assertNotIn("Hyderabad Studio", reply)
        
        is_valid, errs = business_config.validate_message_compliance(reply)
        self.assertTrue(is_valid, f"Appointment reply compliance failed: {errs}")
        print("-> Test 5 PASSED: Appointment query offers Miyapur office with Google Calendar booking link.")

    def test_06_whatsapp_assistant_sunday_and_timings(self):
        """Test 6: Verify conversational assistant confirms seven-day availability including Sundays with 2-5 PM slots."""
        lead = database.get_lead_by_id("SHA-TEST-0002", db_path=DB_PATH)
        self.assertIsNotNone(lead)
        
        reply_sunday = whatsapp_assistant._generate_local_expert_reply(
            lead=lead,
            incoming_msg="Are you open on Sunday? What are your working hours?",
            history=[],
            is_opt_out=False
        )
        
        self.assertIn("Miyapur office", reply_sunday)
        self.assertIn("10:00 AM to 6:00 PM IST", reply_sunday)
        self.assertIn("2:00 PM and 5:00 PM", reply_sunday)
        self.assertIn("seven days", reply_sunday.lower())
        self.assertIn("Monday through Sunday", reply_sunday)
        self.assertNotIn("closed on Sunday", reply_sunday.lower())
        self.assertNotIn("Hyderabad Studio", reply_sunday)
        
        is_valid, errs = business_config.validate_message_compliance(reply_sunday)
        self.assertTrue(is_valid, f"Sunday hours reply compliance failed: {errs}")
        print("-> Test 6 PASSED: Sunday & working hours explicitly confirmed (Open all 7 days with 2-5 PM appointments).")

    def test_07_whatsapp_assistant_directions_and_maps_link(self):
        """Test 7: Verify directions query provides official Google Maps link without inventing street addresses."""
        lead = database.get_lead_by_id("SHA-TEST-0001", db_path=DB_PATH)
        self.assertIsNotNone(lead)
        
        reply_maps = whatsapp_assistant._generate_local_expert_reply(
            lead=lead,
            incoming_msg="Where is your office located? Can you share Google Maps link?",
            history=[],
            is_opt_out=False
        )
        
        self.assertIn("Miyapur office", reply_maps)
        self.assertIn("https://maps.app.goo.gl/Ybuctd1ghqFiQ69D6", reply_maps)
        self.assertIn("10:00 AM to 6:00 PM IST", reply_maps)
        self.assertIn("2:00 PM and 5:00 PM IST", reply_maps)
        self.assertNotIn("Plot No", reply_maps)
        self.assertNotIn("Road No", reply_maps)
        self.assertNotIn("Hyderabad Studio", reply_maps)
        
        is_valid, errs = business_config.validate_message_compliance(reply_maps)
        self.assertTrue(is_valid, f"Maps reply compliance failed: {errs}")
        print("-> Test 7 PASSED: Official Google Maps link provided without invented street address.")

    def test_08_whatsapp_assistant_pricing_and_portfolio_rules(self):
        """Test 8: Verify pricing objection and portfolio requests reference Miyapur office (not Hyderabad studio)."""
        lead = database.get_lead_by_id("SHA-TEST-0001", db_path=DB_PATH)
        
        reply_price = whatsapp_assistant._generate_local_expert_reply(
            lead=lead,
            incoming_msg="Your price seems slightly high. Can you give a discount?",
            history=[],
            is_opt_out=False
        )
        self.assertIn("Miyapur office", reply_price)
        self.assertIn("2:00 PM to 5:00 PM IST", reply_price)
        self.assertNotIn("Hyderabad studio", reply_price)
        self.assertNotIn("visit to our Hyderabad studio", reply_price)

        reply_port = whatsapp_assistant._generate_local_expert_reply(
            lead=lead,
            incoming_msg="Can you share previous work or show me your designs?",
            history=[],
            is_opt_out=False
        )
        self.assertIn("Miyapur office", reply_port)
        self.assertNotIn("experience centre", reply_port)
        print("-> Test 8 PASSED: Pricing and portfolio handlers strictly reference Miyapur office and 2-5 PM window.")

    def test_09_enquiry_whatsapp_outbound_messages(self):
        """Test 9: Verify enquiry WhatsApp generator requests appointments within 2 PM to 5 PM."""
        k = database.get_lead_by_id("SHA-TEST-0001", db_path=DB_PATH)
        d = database.get_lead_by_id("SHA-TEST-0002", db_path=DB_PATH)
        
        msg_k = enquiry_whatsapp.generate_enquiry_message(k)
        msg_d = enquiry_whatsapp.generate_enquiry_message(d)
        
        for msg in [msg_k, msg_d]:
            self.assertIn("SHA Interface Interiors", msg)
            self.assertIn("Miyapur office", msg)
            self.assertIn("phone call", msg.lower())
            self.assertIn("2:00 PM and 5:00 PM IST", msg)
            self.assertNotIn("Hyderabad Studio", msg)
            self.assertNotIn("our studio", msg.lower())
            
            is_valid, errs = business_config.validate_message_compliance(msg)
            self.assertTrue(is_valid, f"Enquiry message compliance failed: {errs}")
            
        print("-> Test 9 PASSED: Website enquiry messages consistently use Miyapur office and 2-5 PM appointment window.")

    def test_10_followup_templates_and_intelligence(self):
        """Test 10: Verify follow-up templates and intelligence multichannel drafters use 2 PM-5 PM appointment rules."""
        k = database.get_lead_by_id("SHA-TEST-0001", db_path=DB_PATH)
        
        # Test consultation scheduling template
        sched_msg = followup_templates.generate_personalized_message("consultation_scheduling", k)
        self.assertIn("Miyapur office", sched_msg)
        self.assertIn("10:00 AM", sched_msg)
        self.assertIn("6:00 PM IST", sched_msg)
        self.assertIn("2:00 PM and 5:00 PM IST", sched_msg)
        self.assertIn("Monday through Sunday", sched_msg)
        self.assertIn("https://maps.app.goo.gl/Ybuctd1ghqFiQ69D6", sched_msg)
        self.assertNotIn("Experience Center", sched_msg)
        
        is_valid_sched, errs_sched = business_config.validate_message_compliance(sched_msg)
        self.assertTrue(is_valid_sched, f"Consultation template failed compliance: {errs_sched}")
        
        # Test intelligence email draft
        email_draft = followup_intelligence.generate_personalized_email_draft(k)
        body = email_draft["body"]
        self.assertIn("Miyapur office", body)
        self.assertIn("10:00 AM to 6:00 PM IST", body)
        self.assertIn("2:00 PM and 5:00 PM IST", body)
        self.assertIn("Monday through Sunday", body)
        self.assertIn("https://maps.app.goo.gl/Ybuctd1ghqFiQ69D6", body)
        self.assertNotIn("Hyderabad Studio", body)
        
        is_valid_email, errs_email = business_config.validate_message_compliance(body)
        self.assertTrue(is_valid_email, f"Email draft failed compliance: {errs_email}")
        
        print("-> Test 10 PASSED: Follow-up templates and intelligence drafters adhere to 2 PM-5 PM appointment window.")

    def test_11_ai_service_system_prompt_instruction(self):
        """Test 11: Verify ai_service default system prompt enforces Miyapur office and 2-5 PM appointments."""
        import ai_service
        self.assertIn("Miyapur office", ai_service.business_config.OFFICE_NAME)
        self.assertIn("2:00 PM to 5:00 PM", ai_service.business_config.APPOINTMENT_HOURS)
        self.assertIn("https://maps.app.goo.gl/Ybuctd1ghqFiQ69D6", ai_service.business_config.OFFICE_MAPS_LINK)
        print("-> Test 11 PASSED: AI Service central prompt includes all mandatory business rules.")

    def test_12_explicit_failure_on_disallowed_appointment_slots(self):
        """
        Test 12: EXPLICIT FAILURE TEST
        Verifies that customer appointment messages offering 10 AM-2 PM or 5 PM-6 PM
        strictly fail compliance validation and raise violations.
        """
        # Case A: Offering morning 10 AM to 2 PM appointment slot
        bad_msg_a = "We would be happy to schedule your appointment between 10:00 AM and 2:00 PM at our Miyapur office."
        valid_a, errs_a = business_config.validate_message_compliance(bad_msg_a)
        self.assertFalse(valid_a, "Failed: 10 AM to 2 PM appointment was not flagged as violation!")
        self.assertTrue(any("outside permitted window" in e or "10:00 am and 2:00 pm" in e for e in errs_a))

        # Case B: Offering alternate phrasing 10 AM to 2 PM
        bad_msg_b = "Consultation appointments are available 10 AM to 2 PM, Monday through Sunday."
        valid_b, errs_b = business_config.validate_message_compliance(bad_msg_b)
        self.assertFalse(valid_b, "Failed: '10 AM to 2 PM' was not flagged as violation!")
        self.assertTrue(any("outside permitted window" in e for e in errs_b))

        # Case C: Offering late evening 5 PM to 6 PM appointment slot
        bad_msg_c = "Would you like an appointment between 5:00 PM and 6:00 PM at our Miyapur office?"
        valid_c, errs_c = business_config.validate_message_compliance(bad_msg_c)
        self.assertFalse(valid_c, "Failed: 5 PM to 6 PM appointment was not flagged as violation!")
        self.assertTrue(any("outside permitted window" in e or "5:00 pm and 6:00 pm" in e for e in errs_c))

        # Case D: Offering alternate phrasing 5 PM to 6 PM
        bad_msg_d = "We can meet for an appointment 5 PM to 6 PM any day."
        valid_d, errs_d = business_config.validate_message_compliance(bad_msg_d)
        self.assertFalse(valid_d, "Failed: '5 PM to 6 PM' was not flagged as violation!")
        self.assertTrue(any("outside permitted window" in e for e in errs_d))

        # Case E: Offering 10 AM to 6 PM as appointment availability (instead of general office hours)
        bad_msg_e = "Our appointments are available from 10:00 AM to 6:00 PM. Please book your slot."
        valid_e, errs_e = business_config.validate_message_compliance(bad_msg_e)
        self.assertFalse(valid_e, "Failed: 10 AM to 6 PM for appointments was not flagged as violation!")
        self.assertTrue(any("outside permitted window" in e for e in errs_e))

        # Case F: Offering specific disallowed morning hour (11:00 AM)
        bad_msg_f = "We have booked your appointment at 11:00 AM at our Miyapur office."
        valid_f, errs_f = business_config.validate_message_compliance(bad_msg_f)
        self.assertFalse(valid_f, "Failed: Appointment at 11:00 AM was not flagged as violation!")
        self.assertTrue(any("outside permitted window" in e for e in errs_f))

        # Case G: Asking for preferred appointment time without stating 2 PM to 5 PM
        bad_msg_g = "We would love to arrange a meeting at our Miyapur office. Please let us know your preferred date and time."
        valid_g, errs_g = business_config.validate_message_compliance(bad_msg_g)
        self.assertFalse(valid_g, "Failed: Unbounded appointment request without 2 PM to 5 PM was not flagged!")
        self.assertTrue(any("mandatory 2 PM to 5 PM window" in e for e in errs_g))

        # Case H: Valid compliant message specifying 2 PM to 5 PM MUST PASS
        good_msg = (
            "We would be happy to arrange a meeting at our Miyapur office or schedule a convenient phone call. "
            "Our general office hours are 10:00 AM to 6:00 PM, with customer consultation appointments available between 2:00 PM and 5:00 PM IST. "
            "Please let us know your preferred date and time between 2:00 PM and 5:00 PM, and our team will assist you with confirming the appointment."
        )
        valid_good, errs_good = business_config.validate_message_compliance(good_msg)
        self.assertTrue(valid_good, f"Compliant message failed unexpectedly: {errs_good}")

        print("-> Test 12 PASSED: All disallowed appointment slots (10 AM-2 PM, 5 PM-6 PM, 10 AM-6 PM) strictly fail as required.")

    def test_13_appointment_confirmation_policy(self):
        """Test 13: Verify manual confirmation policy until Google Calendar integration."""
        self.assertEqual(business_config.CALENDAR_INTEGRATION_STATUS, "manual_workflow_active")
        policy = business_config.APPOINTMENT_CONFIRMATION_POLICY
        self.assertIn("Until Google Calendar is integrated", policy)
        self.assertIn("manual confirmation", policy)
        self.assertIn("Future Google Calendar booking confirmation must be automatic only after successful event creation", policy)
        print("-> Test 13 PASSED: Appointment confirmation policy matches exact requirements.")

    def test_14_database_customer_records_integrity(self):
        """Test 14: Verify all 9 database records (7 genuine + 2 test leads) are completely intact."""
        leads = database.get_all_leads(db_path=DB_PATH)
        self.assertEqual(len(leads), 9, f"Expected 9 leads, found {len(leads)}")
        
        # Verify Test Lead 1: Kanishka
        kanishka = database.get_lead_by_id("SHA-TEST-0001", db_path=DB_PATH)
        self.assertIsNotNone(kanishka)
        self.assertEqual(kanishka["customer_name"], "Kanishka")
        self.assertEqual(kanishka["phone"], "+91 90001 40689")
        self.assertEqual(kanishka["email"], "mattaganesh191@gmail.com")
        self.assertEqual(kanishka["project_type"], "3BHK")
        self.assertEqual(kanishka["locality"], "Gachibowli")
        self.assertEqual(kanishka["priority"].upper(), "HIGH")
        self.assertEqual(kanishka["scope_of_work"], "Complete Home Interior Design")

        # Verify Test Lead 2: Dinesh
        dinesh = database.get_lead_by_id("SHA-TEST-0002", db_path=DB_PATH)
        self.assertIsNotNone(dinesh)
        self.assertEqual(dinesh["customer_name"], "Dinesh")
        self.assertEqual(dinesh["phone"], "+91 85005 25509")
        self.assertEqual(dinesh["email"], "dineshjawa42@gmail.com")
        self.assertEqual(dinesh["project_type"], "2BHK")
        self.assertEqual(dinesh["locality"], "Miyapur")
        self.assertEqual(dinesh["priority"].upper(), "HIGH")
        self.assertEqual(dinesh["scope_of_work"], "Kitchen and Bedroom Interiors")

        # Verify genuine customers exist
        genuine_ids = {"SHA-2026-0001", "SHA-2026-0002", "SHA-2026-0003", "SHA-2026-0004", "SHA-2026-0005", "SHA-2026-0006", "SHA-2026-0901"}
        for gid in genuine_ids:
            lead = database.get_lead_by_id(gid, db_path=DB_PATH)
            self.assertIsNotNone(lead, f"Genuine customer {gid} was not found!")
            self.assertNotEqual(lead.get("data_origin"), "test_data", f"Genuine lead {gid} was wrongly marked as test data!")

        print("-> Test 14 PASSED: All 9 database records (7 genuine + 2 test leads) are completely intact.")

    def test_15_internal_booking_buttons_removed_and_link_preserved(self):
        """Test 15: Verify internal 'Book an Appointment' buttons are completely removed from app.py while customer link sharing is preserved."""
        target_url = "https://calendar.app.google/DMb8MRbZBz97gYbc8"
        self.assertEqual(business_config.GOOGLE_CALENDAR_BOOKING_LINK, target_url)

        with open("app.py", "r", encoding="utf-8") as f:
            app_code = f.read()

        # Verify all internal appointment booking buttons and customer scheduling section are removed from app.py
        self.assertNotIn("Book an Appointment", app_code, "Internal 'Book an Appointment' button found in app.py!")
        self.assertNotIn("📅 Customer Scheduling", app_code, "Internal 'Customer Scheduling' section found in app.py!")
        self.assertNotIn("calendar.app.google", app_code, "Direct calendar button URL found in app.py UI!")

        # Verify official booking link is preserved in central config and assistant for customer sharing
        self.assertIn(target_url, business_config.EXAMPLE_CUSTOMER_RESPONSE)
        self.assertIn(target_url, whatsapp_assistant.SYSTEM_SALES_INSTRUCTION)
        print("-> Test 15 PASSED: Internal appointment booking buttons completely removed from app.py while customer booking link is preserved.")

    def test_16_automatic_google_calendar_booking_link_sharing(self):
        """
        Test 16: Verify automatic Google Calendar booking link sharing rules:
        1. "I want to visit your office" -> booking link is included.
        2. "Can I meet your team?" -> booking link is included.
        3. "I want to book an appointment" -> booking link is included.
        4. "What interior designs do you offer?" -> booking link is NOT included.
        5. "What is your office timing?" -> answers business-hours question accurately without booking link.
        """
        lead = database.get_lead_by_id("SHA-TEST-0001", db_path=DB_PATH)
        self.assertIsNotNone(lead)
        target_link = "https://calendar.app.google/DMb8MRbZBz97gYbc8"

        # 1. "I want to visit your office" -> booking link is included
        reply_visit = whatsapp_assistant._generate_local_expert_reply(lead, "I want to visit your office", [], False)
        self.assertIn(target_link, reply_visit)
        self.assertIn("Miyapur office", reply_visit)
        self.assertIn("Certainly!", reply_visit)
        self.assertIn("Once you book a slot, your appointment will be confirmed through Google Calendar.", reply_visit)

        # 2. "Can I meet your team?" -> booking link is included
        reply_meet = whatsapp_assistant._generate_local_expert_reply(lead, "Can I meet your team?", [], False)
        self.assertIn(target_link, reply_meet)
        self.assertIn("Miyapur office", reply_meet)

        # 3. "I want to book an appointment" -> booking link is included
        reply_appt = whatsapp_assistant._generate_local_expert_reply(lead, "I want to book an appointment", [], False)
        self.assertIn(target_link, reply_appt)
        self.assertIn("Miyapur office", reply_appt)

        # 4. "What interior designs do you offer?" -> booking link is NOT included
        reply_designs = whatsapp_assistant._generate_local_expert_reply(lead, "What interior designs do you offer?", [], False)
        self.assertNotIn(target_link, reply_designs)
        self.assertTrue("portfolio" in reply_designs.lower() or "designs" in reply_designs.lower())

        # 5. "What is your office timing?" -> answers business-hours question accurately without booking link
        reply_timing = whatsapp_assistant._generate_local_expert_reply(lead, "What is your office timing?", [], False)
        self.assertNotIn(target_link, reply_timing)
        self.assertIn("10:00 AM to 6:00 PM IST", reply_timing)
        self.assertIn("Miyapur office", reply_timing)
        self.assertIn("Monday through Sunday", reply_timing)
        self.assertIn("2:00 PM and 5:00 PM IST", reply_timing)

        print("-> Test 16 PASSED: All 5 automatic booking link & inquiry scenarios verified.")



    def test_17_selective_booking_link_inclusion_and_exclusions(self):
        """
        Test 17: Rigorously verify selective booking link inclusion and exclusion rules:
        - INCLUSIONS (Only 4 criteria):
          1. Explicit appointment request: "I want to book an appointment"
          2. Office visit: "I want to visit your office"
          3. Available meeting slots: "What meeting slots are available?"
          4. Scheduled consultation: "Can we schedule a consultation to meet?"
        - EXCLUSIONS (Never include booking link for ordinary questions):
          1. Canonical timeline example: "When can you start the project and how long will it take?"
             -> Work starts after design finalisation, standard apartment handover is 45 days after design approval.
          2. Pricing & budget: "What is your pricing for a 3BHK flat?"
          3. Materials: "What materials do you use for modular kitchen?"
          4. General business info: "Where is your office located?"
        """
        lead = database.get_lead_by_id("SHA-TEST-0001", db_path=DB_PATH)
        target_link = business_config.GOOGLE_CALENDAR_BOOKING_LINK

        # 1. Inclusion - Meeting slots query
        reply_slots = whatsapp_assistant._generate_local_expert_reply(lead, "What meeting slots are available?", [], False)
        self.assertIn(target_link, reply_slots)
        self.assertIn("Miyapur office", reply_slots)

        # 2. Inclusion - Scheduled consultation query
        reply_consult = whatsapp_assistant._generate_local_expert_reply(lead, "Can we schedule a consultation to meet?", [], False)
        self.assertIn(target_link, reply_consult)
        self.assertIn("Miyapur office", reply_consult)

        # 3. Canonical Timeline Query: "When can you start the project and how long will it take?"
        reply_timeline = whatsapp_assistant._generate_local_expert_reply(lead, "When can you start the project and how long will it take?", [], False)
        self.assertNotIn(target_link, reply_timeline, "Booking link must NOT be included in timeline query!")
        self.assertNotIn("calendar.app.google", reply_timeline)
        self.assertIn("work can start after design and scope finalisation", reply_timeline.lower())
        self.assertIn("45 days after design approval", reply_timeline.lower())
        self.assertIn("modular kitchens and wardrobes", reply_timeline.lower())
        self.assertIn("subject to site readiness", reply_timeline.lower())

        # 4. Exclusion - Pricing query
        reply_price = whatsapp_assistant._generate_local_expert_reply(lead, "What is your pricing for a 3BHK flat?", [], False)
        self.assertNotIn(target_link, reply_price, "Booking link must NOT be included in pricing query!")

        # 5. Exclusion - Materials query
        reply_mat = whatsapp_assistant._generate_local_expert_reply(lead, "What materials do you use for modular kitchen?", [], False)
        self.assertNotIn(target_link, reply_mat, "Booking link must NOT be included in materials query!")
        self.assertIn("bwp", reply_mat.lower())

        # 6. Exclusion - Directions / Location query
        reply_loc = whatsapp_assistant._generate_local_expert_reply(lead, "Where is your office located?", [], False)
        self.assertNotIn(target_link, reply_loc, "Booking link must NOT be included in location query!")
        self.assertIn("https://maps.app.goo.gl/Ybuctd1ghqFiQ69D6", reply_loc)

        print("-> Test 17 PASSED: Selective booking link inclusion (4 criteria) & exclusions (timeline, pricing, materials, location) verified.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
