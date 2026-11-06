"""
test_voice_assistant.py - Verification Suite for Voice Input and Text-to-Speech Engine
Tests:
- Speech text sanitization (markdown, emojis, URLs, tables)
- Technical terminology preservation in voice synthesis
- Voice transcription processing (multilingual to English)
- HTML5 Web Speech components generation
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import voice_assistant


class TestVoiceAssistant(unittest.TestCase):
    """Test suite for voice input and text-to-speech functionality."""

    def test_01_speech_sanitizer_markdown_and_formatting(self):
        """Verify markdown syntax is stripped into clean spoken words."""
        raw_text = """### Interior Design Recommendation
Here is the proposal for your **3BHK apartment**:
* Modular Kitchen with `BWP Plywood`
* Acrylic Finish for *upper cabinets*
> [!NOTE] All hardware includes Blum soft-close hinges.
"""
        cleaned = voice_assistant.clean_text_for_speech(raw_text)
        self.assertNotIn("###", cleaned)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("`", cleaned)
        self.assertNotIn("*", cleaned)
        self.assertNotIn(">", cleaned)
        self.assertNotIn("[!NOTE]", cleaned)
        # Ensure core contents remain
        self.assertIn("Interior Design Recommendation", cleaned)
        self.assertIn("3BHK apartment", cleaned)
        self.assertIn("BWP Plywood", cleaned)
        self.assertIn("Blum", cleaned)

    def test_02_speech_sanitizer_urls_and_emojis(self):
        """Verify URLs and emojis are converted to natural speech without broken strings."""
        raw_text = """Certainly! We would be happy to welcome you to SHA Interface Interiors at our Miyapur office. 😊
You can check the available appointment slots using our booking link:
https://calendar.app.google/DMb8MRbZBz97gYbc8
Our office location: https://maps.app.goo.gl/Ybuctd1ghqFiQ69D6 👍
"""
        cleaned = voice_assistant.clean_text_for_speech(raw_text)
        self.assertNotIn("😊", cleaned)
        self.assertNotIn("👍", cleaned)
        self.assertNotIn("https://calendar.app.google", cleaned)
        self.assertIn("Google Calendar booking link", cleaned)
        self.assertIn("Miyapur office", cleaned)

    def test_03_speech_sanitizer_tables(self):
        """Verify markdown tables are flattened into spoken sentences."""
        raw_table = """| Material | Recommended Use | Estimated Warranty |
|---|---|---|
| BWP Marine Plywood | Kitchen Base Cabinets | 15 Years |
| HDHMR Board | Wardrobes & Dry Areas | 10 Years |
| Acrylic 1.5mm | Kitchen Wall Shutters | 5 Years |
"""
        cleaned = voice_assistant.clean_text_for_speech(raw_table)
        self.assertNotIn("|", cleaned)
        self.assertNotIn("---|---", cleaned)
        self.assertIn("BWP Marine Plywood", cleaned)
        self.assertIn("Kitchen Base Cabinets", cleaned)
        self.assertIn("15 Years", cleaned)
        self.assertIn("HDHMR Board", cleaned)

    def test_04_process_voice_transcription(self):
        """Verify incoming voice transcriptions are processed and translated to English."""
        # Spoken Telugu transcript
        telugu_voice = "మేము 3BHK కోసం BWP ప్లైవుడ్ మరియు మోడ్యులర్ కిచెన్ కావాలనుకుంటున్నాము"
        res_te = voice_assistant.process_voice_transcription(telugu_voice)
        self.assertEqual(res_te["language_code"], "te")
        self.assertTrue(len(res_te["english_translation"]) > 0)
        self.assertIn("BWP", res_te["english_translation"])

        # Spoken English transcript
        english_voice = "Can I schedule a consultation at your Miyapur office tomorrow at 3 PM?"
        res_en = voice_assistant.process_voice_transcription(english_voice)
        self.assertEqual(res_en["language_code"], "en")
        self.assertEqual(res_en["english_translation"], english_voice)

    def test_05_html_component_generation(self):
        """Verify Web Speech API HTML snippets are well formed."""
        tts_html = voice_assistant.get_tts_html_snippet("Hello, welcome to SHA Interface Interiors.")
        self.assertIn("speechSynthesis", tts_html)
        self.assertIn("SpeechSynthesisUtterance", tts_html)
        self.assertIn("Read Aloud", tts_html)

        stt_html = voice_assistant.get_voice_input_html_snippet("test_stt_01")
        self.assertIn("webkitSpeechRecognition", stt_html)
        self.assertIn("Start Voice Input", stt_html)
        self.assertIn("Copy Transcript", stt_html)



    def test_06_unified_chat_composer_bridge(self):
        """Verify the unified chat composer bridge contains mic integration, multilingual support, and strict no-auto-send."""
        bridge_html = voice_assistant.get_unified_chat_composer_bridge()
        self.assertIn("webkitSpeechRecognition", bridge_html)
        self.assertIn("stChatInput", bridge_html)
        self.assertIn("stChatInputTextArea", bridge_html)
        self.assertIn("sha_voice_mic_btn", bridge_html)
        self.assertIn("sha_voice_lang", bridge_html)
        # Verify Indian languages support
        self.assertIn("te-IN", bridge_html)
        self.assertIn("hi-IN", bridge_html)
        self.assertIn("ta-IN", bridge_html)
        self.assertIn("kn-IN", bridge_html)
        self.assertIn("ml-IN", bridge_html)
        self.assertIn("mr-IN", bridge_html)
        self.assertIn("bn-IN", bridge_html)
        # Verify active listening animation
        self.assertIn("sha-pulse-ring", bridge_html)
        # Verify strict no-auto-send rule (places in editable textarea, does not click submit)
        self.assertIn("setReactInputValue(combinedText)", bridge_html)
        self.assertNotIn("submitBtn.click()", bridge_html)



    def test_07_tts_listen_stop_replay_controls(self):
        """Verify AI voice output contains Listen, Stop, and Replay controls."""
        tts_html = voice_assistant.get_tts_html_snippet("Thank you for contacting SHA Interface Interiors.")
        self.assertIn("Listen", tts_html)
        self.assertIn("Stop", tts_html)
        self.assertIn("Replay", tts_html)
        self.assertIn("btn_play", tts_html)
        self.assertIn("btn_stop", tts_html)
        self.assertIn("btn_replay", tts_html)
        self.assertIn("SpeechSynthesisUtterance", tts_html)


if __name__ == "__main__":
    unittest.main()
