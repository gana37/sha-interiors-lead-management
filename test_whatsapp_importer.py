"""
test_whatsapp_importer.py - Verification Suite for WhatsApp Conversation Importer
Tests:
- Manual message entry
- WhatsApp TXT export parsing (Indian 12h/24h formats, multiline, system messages)
- Duplicate message prevention
- Customer matching by phone and sender name
- Multilingual language tagging & internal translation
- Record integrity and customer isolation
"""

import unittest
import os
import sys
import datetime

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import database
import whatsapp_importer
import multilingual_engine


class TestWhatsAppImporter(unittest.TestCase):
    """Test suite for WhatsApp conversation importer."""

    @classmethod
    def setUpClass(cls):
        database.init_db()
        cls.test_lead_id = "SHA-TEST-0001"  # Kanishka

    def test_01_manual_message_import_and_translation(self):
        """Verify manual message entry with language detection and internal English translation."""
        # 1. Hindi message with technical term BWP
        hindi_msg = "नमस्ते, क्या आप 3BHK के लिए BWP प्लाइवुड इस्तेमाल करते हैं?"
        res_hi = whatsapp_importer.import_manual_message(
            lead_id=self.test_lead_id,
            message_content=hindi_msg,
            direction="incoming",
            sender_name="Kanishka",
            timestamp="2026-11-05 10:15:00"
        )
        self.assertTrue(res_hi["success"])
        conv_id_hi = res_hi["conversation_id"]

        # Verify in database
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM CUSTOMER_CONVERSATIONS WHERE conversation_id = ?;", (conv_id_hi,))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["original_language"], "hi")
        self.assertIn("BWP", row["english_translation"])
        self.assertEqual(row["source_type"], "Manual")

        # 2. Test duplicate detection
        dup_res = whatsapp_importer.import_manual_message(
            lead_id=self.test_lead_id,
            message_content=hindi_msg,
            direction="incoming",
            timestamp="2026-11-05 10:15:00"
        )
        self.assertFalse(dup_res["success"])
        self.assertTrue(dup_res.get("is_duplicate"))

        # Cleanup
        with conn:
            cursor.execute("DELETE FROM CUSTOMER_CONVERSATIONS WHERE conversation_id = ?;", (conv_id_hi,))
            cursor.execute("UPDATE LEADS SET last_customer_response = NULL, last_response_at = NULL WHERE lead_id = ?;", (self.test_lead_id,))
        conn.close()

    def test_02_parse_whatsapp_txt_formats(self):
        """Verify parsing of WhatsApp TXT exports with Indian date formats and multiline messages."""
        sample_chat = """15/01/26, 10:30 am - Messages and calls are end-to-end encrypted. No one outside of this chat can read them.
15/01/26, 10:31 am - Kanishka: Hi SHA Interiors team, we need interior work for our 3BHK apartment in Gachibowli.
15/01/26, 10:32 am - Kanishka: Specifically for modular kitchen and bedrooms.
Here is the requirement details:
- Acrylic finish for kitchen
- BWP marine plywood for base cabinets
- Sliding wardrobes for master bedroom
15/01/26, 10:35 am - SHA Consultant: Hello Kanishka, thank you for reaching out! We would be delighted to assist.
15/01/26, 10:36 am - Kanishka: <Media omitted>
15/01/26, 10:40 am - Kanishka: Please let me know when can we visit your Miyapur office?
"""
        parsed = whatsapp_importer.parse_whatsapp_txt_export(sample_chat)
        # Should have 4 valid messages (system message and media omitted skipped)
        self.assertEqual(len(parsed), 4)

        # Check multiline preservation
        multiline_msg = parsed[1]
        self.assertIn("Acrylic finish", multiline_msg["message_content"])
        self.assertIn("BWP marine plywood", multiline_msg["message_content"])
        self.assertIn("Sliding wardrobes", multiline_msg["message_content"])

        # Check direction
        self.assertEqual(parsed[0]["direction"], "incoming")
        self.assertEqual(parsed[1]["direction"], "incoming")
        self.assertEqual(parsed[2]["direction"], "outgoing")  # SHA Consultant
        self.assertEqual(parsed[3]["direction"], "incoming")

        # Check timestamp ISO formatting
        self.assertIn("2026-01-15 10:31:00", parsed[0]["timestamp"])

    def test_03_customer_matching(self):
        """Verify automatic customer matching using phone number or customer name."""
        # 1. Match by phone (+91 90001 40689 -> Kanishka)
        sample_phone_chat = [
            {"raw_sender": "+91 90001 40689", "direction": "incoming", "message_content": "Hello"}
        ]
        matched_id, conf, rationale = whatsapp_importer.match_lead_from_conversation(sample_phone_chat)
        self.assertEqual(matched_id, "SHA-TEST-0001")
        self.assertEqual(conf, 1.0)
        self.assertIn("Exact Phone Match", rationale)

        # 2. Match by Name ("Dinesh" -> SHA-TEST-0002)
        sample_name_chat = [
            {"raw_sender": "Dinesh", "direction": "incoming", "message_content": "When can I visit office?"}
        ]
        matched_dinesh, conf_d, rationale_d = whatsapp_importer.match_lead_from_conversation(sample_name_chat)
        self.assertEqual(matched_dinesh, "SHA-TEST-0002")
        self.assertGreaterEqual(conf_d, 0.8)

    def test_04_batch_commit_and_customer_isolation(self):
        """Verify committing messages to a customer prevents duplicates and maintains customer isolation."""
        test_messages = [
            {"message_content": "Can we meet at your Miyapur office?", "direction": "incoming", "timestamp": "2026-11-05 11:00:00", "original_language": "en"},
            {"message_content": "Certainly, we would be happy to welcome you!", "direction": "outgoing", "timestamp": "2026-11-05 11:05:00", "original_language": "en"}
        ]

        commit_res = whatsapp_importer.commit_imported_messages(
            lead_id="SHA-TEST-0002",  # Dinesh
            messages_to_import=test_messages,
            file_name="test_dinesh_chat.txt",
            file_type="TXT_Export"
        )
        self.assertTrue(commit_res["success"])
        self.assertEqual(commit_res["imported_count"], 2)

        # Second commit with same messages should be detected as duplicates
        commit_res_2 = whatsapp_importer.commit_imported_messages(
            lead_id="SHA-TEST-0002",
            messages_to_import=test_messages,
            file_name="test_dinesh_chat.txt",
            file_type="TXT_Export"
        )
        self.assertEqual(commit_res_2["duplicate_count"], 2)
        self.assertEqual(commit_res_2["imported_count"], 0)

        # Customer isolation check: ensure these messages are NOT associated with Kanishka
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM CUSTOMER_CONVERSATIONS WHERE lead_id = 'SHA-TEST-0001' AND message_content = 'Can we meet at your Miyapur office?';")
        kanishka_count = cursor.fetchone()[0]
        self.assertEqual(kanishka_count, 0, "Dinesh's message must NOT leak into Kanishka's account")

        # Cleanup test messages
        with conn:
            cursor.execute("DELETE FROM CUSTOMER_CONVERSATIONS WHERE lead_id = 'SHA-TEST-0002' AND message_content IN ('Can we meet at your Miyapur office?', 'Certainly, we would be happy to welcome you!');")
            cursor.execute("DELETE FROM IMPORTED_CONVERSATION_FILES WHERE file_name = 'test_dinesh_chat.txt';")
        conn.close()


if __name__ == "__main__":
    unittest.main()
