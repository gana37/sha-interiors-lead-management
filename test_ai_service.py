"""
test_ai_service.py - Comprehensive Test Suite for Gemini AI & CRM Grounding
SHA Interface Interiors - AI-Powered Lead Management System

Tests API key security, SQLite grounding, invalid key handling, quota fallback,
multi-turn context assembly, and requirement summarization.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Ensure UTF-8 output on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import database
import ai_service
import ai_assistant
import followup_templates

TEST_DB = "test_ai_grounding.db"


class TestGeminiAIService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initializes an isolated test database with synthetic leads."""
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except Exception:
                pass
        database.init_db(TEST_DB)

        # Insert a sample of realistic leads
        leads = [
            {
                "lead_id": "SHA-2026-TEST1",
                "customer_name": "Arjun Reddy",
                "phone": "+91 98765 43210",
                "email": "arjun.reddy@example.com",
                "city": "Hyderabad",
                "project_type": "4BHK Villa",
                "scope_of_work": "Complete Turnkey Interiors",
                "budget_range": "₹35 lakh–₹50 lakh",
                "property_status": "Ready for Possession",
                "project_timeline": "Immediate (Within 15 days)",
                "customer_requirements": "Italian marble finishes, smart lighting, high-end modular kitchen.",
                "purchase_readiness": "Ready to Start",
                "lead_score": 96.0,
                "priority": "High",
                "lead_status": "New"
            },
            {
                "lead_id": "SHA-2026-TEST2",
                "customer_name": "Deepika Rao",
                "phone": "+91 98765 43211",
                "email": "deepika.rao@example.com",
                "city": "Hyderabad",
                "project_type": "3BHK",
                "scope_of_work": "Full Home Interiors",
                "budget_range": "₹20 lakh–₹35 lakh",
                "property_status": "Under Construction",
                "project_timeline": "1–3 months",
                "customer_requirements": "Minimalist Scandinavian design, wooden flooring in master bed.",
                "purchase_readiness": "Comparing Vendors",
                "lead_score": 82.0,
                "priority": "High",
                "lead_status": "Qualified"
            },
            {
                "lead_id": "SHA-2026-TEST3",
                "customer_name": "Vikram Seth",
                "phone": "+91 98765 43212",
                "email": "vikram.seth@example.com",
                "city": "Bangalore",
                "project_type": "2BHK",
                "scope_of_work": "Modular Kitchen & Wardrobes",
                "budget_range": "₹10 lakh–₹20 lakh",
                "property_status": "Ready for Possession",
                "project_timeline": "Immediate (Within 15 days)",
                "customer_requirements": "Budget-friendly durable acrylic cabinets and sliding wardrobes.",
                "purchase_readiness": "Budget Planning",
                "lead_score": 68.0,
                "priority": "Medium",
                "lead_status": "Follow-up"
            }
        ]

        for lead in leads:
            database.insert_lead(lead, db_path=TEST_DB)

        # Schedule a follow-up for Arjun
        database.insert_followup_schedule({
            "schedule_id": "FU-TEST-001",
            "lead_id": "SHA-2026-TEST1",
            "scheduled_for": "2026-11-05 10:00:00",
            "message": "Initial outreach message",
            "attempt_number": 1,
            "channel": "WhatsApp",
            "status": "Scheduled"
        }, db_path=TEST_DB)

    @classmethod
    def tearDownClass(cls):
        """Cleans up the test database."""
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except Exception:
                pass

    def test_01_api_key_detection_and_security(self):
        """Tests that invalid placeholders, missing keys, and empty strings are rejected."""
        print("\n[Test 1] Testing API Key Detection & Security Guardrails...")
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            self.assertFalse(ai_service.is_gemini_available())

        with patch.dict(os.environ, {"GEMINI_API_KEY": "your_gemini_api_key_here"}):
            self.assertFalse(ai_service.is_gemini_available())

        with patch.dict(os.environ, {"GEMINI_API_KEY": "short_key"}):
            self.assertFalse(ai_service.is_gemini_available())

        # Verify .env is in .gitignore
        with open(".gitignore", "r", encoding="utf-8") as f:
            gitignore_content = f.read()
            self.assertIn(".env", gitignore_content)

        print("-> Test 1 PASSED: Key validation & .gitignore security verified.")

    def test_02_built_in_engine_fallback_when_unconfigured(self):
        """Tests that natural language queries succeed with accurate data even without an API key."""
        print("\n[Test 2] Testing Built-in Intelligence Engine Fallback (Offline Mode)...")
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            # High priority query
            ans1 = ai_assistant.answer_crm_query("How many high priority leads do we have?", db_path=TEST_DB)
            self.assertIn("High-Priority", ans1)
            self.assertIn("2", ans1)  # Arjun & Deepika

            # Hyderabad city query
            ans2 = ai_assistant.answer_crm_query("Show high-priority leads in Hyderabad", db_path=TEST_DB)
            self.assertIn("Hyderabad", ans2)
            self.assertIn("Arjun Reddy", ans2)

            # Overview query
            ans3 = ai_assistant.answer_crm_query("Give me a summary of all leads", db_path=TEST_DB)
            self.assertIn("Total Active Leads", ans3)
            self.assertIn("3", ans3)

        print("-> Test 2 PASSED: Built-in deterministic intelligence engine returned verified facts.")

    def test_03_sqlite_grounding_context_builder(self):
        """Tests that build_crm_grounding_context extracts verified real data for Gemini."""
        print("\n[Test 3] Testing SQLite Grounding Context Builder (Zero Hallucination)...")
        context_str = ai_assistant.build_crm_grounding_context("Show me leads in Hyderabad", db_path=TEST_DB)
        
        self.assertIn("VERIFIED REAL CRM STATS", context_str)
        self.assertIn("HYDERABAD", context_str)
        self.assertIn("Arjun Reddy", context_str)
        self.assertIn("Deepika Rao", context_str)
        self.assertIn("₹35 lakh–₹50 lakh", context_str)

        # Test specific ID extraction
        context_id = ai_assistant.build_crm_grounding_context("Tell me about SHA-2026-TEST1", db_path=TEST_DB)
        self.assertIn("SHA-2026-TEST1", context_id)
        self.assertIn("Italian marble", context_id)

        print("-> Test 3 PASSED: Context builder extracts precise SQLite ground truth.")

    def test_04_invalid_key_error_handling(self):
        """Tests that invalid API keys are caught gracefully without unhandled exceptions."""
        print("\n[Test 4] Testing Invalid API Key Error Handling...")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaSyFakeKeyForUnitTestingOnly12345"}):
            status = ai_service.verify_connection()
            self.assertFalse(status["connected"])
            self.assertIn("error", status)
            self.assertTrue(len(status["error"]) > 0)

            # Even with an invalid key, answer_crm_query must gracefully fall back to deterministic response
            ans = ai_assistant.answer_crm_query("How many high priority leads do we have?", db_path=TEST_DB)
            self.assertTrue("High" in ans or "High-Priority" in ans)

        print("-> Test 4 PASSED: Invalid API key handled gracefully without crashing CRM.")

    def test_05_quota_and_network_error_fallback(self):
        """Tests that API exceptions (quota limit / network error) trigger deterministic fallback."""
        print("\n[Test 5] Testing Quota Limit & Network Failure Fallback...")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaSyValidLengthKeyForMockTesting1234"}):
            with patch("ai_service.generate_content") as mock_gen:
                # Simulate 429 Quota Exceeded error
                mock_gen.return_value = {
                    "success": False,
                    "text": "",
                    "model": "gemini-1.5-flash",
                    "error": "Google Gemini API rate limit or quota exceeded.",
                    "fallback_used": True
                }

                ans = ai_assistant.answer_crm_query("Which leads need attention?", db_path=TEST_DB)
                self.assertIn("Attention Required", ans)
                self.assertIn("Arjun Reddy", ans)

        print("-> Test 5 PASSED: Rate-limit failure transparently handled via built-in engine.")

    def test_06_customer_requirement_summarization(self):
        """Tests client requirement summarization formatting."""
        print("\n[Test 6] Testing Client Requirement Summarization...")
        lead = database.get_lead_by_id("SHA-2026-TEST1", db_path=TEST_DB)
        summary = ai_assistant.summarize_customer_requirements(lead)
        
        self.assertIn("Arjun Reddy", summary)
        self.assertIn("4BHK Villa", summary)
        self.assertIn("Hyderabad", summary)
        self.assertIn("Italian marble finishes", summary)
        self.assertIn("High Priority", summary)

        print("-> Test 6 PASSED: Requirement summarizer produced crisp structured brief.")

    def test_07_recommend_next_action_logic(self):
        """Tests operational next-action recommendations based on client profile."""
        print("\n[Test 7] Testing Recommended Next Sales Action Logic...")
        # High priority ready to start
        lead_high = database.get_lead_by_id("SHA-2026-TEST1", db_path=TEST_DB)
        act1 = ai_assistant.recommend_next_action(lead_high)
        self.assertIn("Schedule On-Site Measurement", act1["recommended_action"])
        self.assertEqual(act1["urgency"], "Immediate (Same-Day)")

        # Converted lead
        lead_conv = dict(lead_high, lead_status="Converted")
        act2 = ai_assistant.recommend_next_action(lead_conv)
        self.assertIn("Onboard Project to 3D Design Team", act2["recommended_action"])

        # Opted out client
        lead_opt = dict(lead_high, is_opted_out=1)
        act3 = ai_assistant.recommend_next_action(lead_opt)
        self.assertIn("Do Not Contact", act3["recommended_action"])

        print("-> Test 7 PASSED: Next-action business rules validated across all lifecycle states.")

    def test_08_personalized_pitch_drafting(self):
        """Tests personalized message draft generation."""
        print("\n[Test 8] Testing Personalized Message Pitch Drafting...")
        lead = database.get_lead_by_id("SHA-2026-TEST1", db_path=TEST_DB)
        draft = ai_assistant.draft_personalized_pitch(lead, goal="site_visit_invitation", use_gemini=False)
        
        self.assertIn("Arjun Reddy", draft)
        self.assertIn("4BHK Villa", draft)
        self.assertIn("Hyderabad", draft)

        print("-> Test 8 PASSED: Personalized outreach pitch created accurately.")

    def test_09_multi_turn_history_formatting(self):
        """Tests chat prompt formatting with conversation history."""
        print("\n[Test 9] Testing Multi-turn Conversation Context Assembly...")
        history = [
            {"role": "user", "content": "How many leads are in Hyderabad?"},
            {"role": "assistant", "content": "We have 2 leads in Hyderabad: Arjun Reddy and Deepika Rao."}
        ]
        grounding = "SAMPLE GROUNDING CONTEXT"
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaSyMockValidLengthKey123456789012"}):
            with patch("ai_service.generate_content") as mock_gen:
                mock_gen.return_value = {"success": True, "text": "Arjun Reddy is high priority.", "model": "gemini-1.5-flash", "error": None, "fallback_used": False}
                res = ai_service.generate_chat_response("Which one is higher priority?", history, grounding)
                self.assertTrue(res["success"])
                # Verify prompt passed to generate_content contained history turns
                args, kwargs = mock_gen.call_args
                prompt_arg = kwargs.get("prompt", args[0] if args else "")
                self.assertIn("Arjun Reddy and Deepika Rao", prompt_arg)
                self.assertIn("Which one is higher priority?", prompt_arg)

        print("-> Test 9 PASSED: Multi-turn chat context properly assembled.")


def run_tests():
    print("=" * 65)
    print("STARTING GEMINI AI SERVICE & CRM INTEGRATION TEST SUITE")
    print("=" * 65)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGeminiAIService)
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    print("\n" + "=" * 65)
    if result.wasSuccessful():
        print(f"ALL {result.testsRun} GEMINI INTEGRATION TESTS PASSED WITH 100% SUCCESS!")
    else:
        print(f"FAILED: {len(result.failures)} failures, {len(result.errors)} errors out of {result.testsRun} tests.")
    print("=" * 65)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
