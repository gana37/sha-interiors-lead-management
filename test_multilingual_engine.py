"""
test_multilingual_engine.py - Verification Suite for Multilingual Intelligence Engine
Tests:
- Language detection across 12 Indian languages (Telugu, Hindi, Tamil, Kannada, Malayalam,
  Marathi, Bengali, Gujarati, Punjabi, Odia, Urdu, English)
- Transliterated language detection (Hinglish, Teluglish, Tanglish)
- Technical interior terminology preservation
- Translation to English (with preserved terms)
- Enforcement of English-only output
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import multilingual_engine


class TestMultilingualEngine(unittest.TestCase):
    """Test suite for multilingual detection, translation, and technical term protection."""

    def test_01_language_detection_native_scripts(self):
        """Verify script and pattern detection for all 12 Indian languages."""
        samples = {
            "te": "మేము 3BHK ఇంటీరియర్ డిజైన్ చేయాలనుకుంటున్నాము",
            "hi": "नमस्ते, क्या आप 3BHK के लिए मॉड्यूलर किचन बनाते हैं?",
            "ta": "நாங்கள் எங்கள் புதிய வீட்டிற்கு உள்துறை வடிவமைப்பு செய்ய விரும்புகிறோம்",
            "kn": "ನಾವು ನಮ್ಮ 3BHK ಮನೆಗೆ ಇಂಟೀರಿಯರ್ ವಿನ್ಯಾಸ ಮಾಡಬೇಕಾಗಿದೆ",
            "ml": "ഞങ്ങളുടെ പുതിയ വീടിന് ഇന്റീരിയർ ഡിസൈൻ ചെയ്യാൻ ആഗ്രഹിക്കുന്നു",
            "mr": "आम्हाला आमच्या नवीन घरासाठी इंटिरियर डिझाइन करायचे आहे",
            "bn": "আমরা আমাদের ফ্ল্যাটের জন্য ইন্টেরিয়র ডিজাইন করতে চাই",
            "gu": "અમે અમારા નવા ઘર માટે ઇન્ટિરિયર ડિઝાઇન કરાવવા માંગીએ છીએ",
            "pa": "ਅਸੀਂ ਆਪਣੇ ਨਵੇਂ ਘਰ ਲਈ ਇੰਟੀਰੀਅਰ ਡਿਜ਼ਾਈਨ ਕਰਵਾਉਣਾ ਚਾਹੁੰਦੇ ਹਾਂ",
            "or": "ଆମେ ଆମର ନୂଆ ଘର ପାଇଁ ଇଣ୍ଟିରିଅର୍ ଡିଜାଇନ୍ କରିବାକୁ ଚାହୁଁଛୁ",
            "ur": "ہم اپنے نئے گھر کے لیے انٹیریئر ڈیزائن کروانا چاہتے ہیں",
            "en": "We are looking for interior design services for our 3BHK flat in Hyderabad.",
        }

        for lang, text in samples.items():
            det = multilingual_engine.detect_language(text)
            self.assertEqual(det["language_code"], lang, f"Failed language detection for {lang}: '{text}' detected as '{det['language_code']}'")
            self.assertFalse(det["is_transliterated"])

    def test_02_language_detection_transliterated(self):
        """Verify detection of transliterated Indian languages (Hinglish, Teluglish, Tanglish)."""
        samples = {
            "hi": "Bhaiya 3BHK modular kitchen ka quotation kitna hoga?",
            "te": "Maku 3BHK flat interiors kavali Miyapur lo, cost entha avtundi?",
            "ta": "Engalukku 2BHK flat interiors pannanum, modular kitchen eppo mudiyum?",
        }

        for lang, text in samples.items():
            det = multilingual_engine.detect_language(text)
            self.assertEqual(det["language_code"], lang, f"Failed transliterated detection for {lang}: '{text}' detected as '{det['language_code']}'")
            self.assertTrue(det["is_transliterated"], f"Expected transliterated to be True for: {text}")

    def test_03_technical_term_protection(self):
        """Verify technical interior terms are extracted and masked properly."""
        text = "Need BWP marine plywood for modular kitchen base and HDHMR with Acrylic finish for cabinets, with Hettich hinges."
        term_map, masked_text = multilingual_engine.extract_and_mask_technical_terms(text)
        
        # Verify term_map contains the terms
        terms_found = list(term_map.values())
        self.assertTrue(any("BWP" in t for t in terms_found))
        self.assertTrue(any("HDHMR" in t for t in terms_found))
        self.assertTrue(any("Acrylic" in t for t in terms_found))
        self.assertTrue(any("Hettich" in t for t in terms_found))
        
        # Test unmasking
        restored = multilingual_engine.restore_technical_terms(masked_text, term_map)
        self.assertIn("BWP", restored)
        self.assertIn("HDHMR", restored)
        self.assertIn("Acrylic", restored)
        self.assertIn("Hettich", restored)

    def test_04_translate_to_english_preserves_terms(self):
        """Verify translation produces clear English text while preserving technical terms."""
        hi_text = "Hume 3BHK ke liye modular kitchen me BWP plywood aur Acrylic finish chahiye."
        res = multilingual_engine.translate_to_english(hi_text, source_lang="hi_latin")
        
        self.assertTrue(res["is_english_output"])
        self.assertIn("BWP", res["translated_text"])
        self.assertIn("Acrylic", res["translated_text"])
        # Technical terms list must include BWP and Acrylic
        self.assertTrue(any("BWP" in term for term in res["preserved_terms"]))

    def test_05_english_passthrough(self):
        """Verify English text passes through unchanged without unnecessary translation overhead."""
        en_text = "Can we book an appointment at your Miyapur office between 2 PM and 5 PM?"
        res = multilingual_engine.translate_to_english(en_text, source_lang="en")
        
        self.assertTrue(res["is_english_output"])
        self.assertEqual(res["source_language"], "en")
        self.assertEqual(res["translated_text"], en_text)


if __name__ == "__main__":
    unittest.main()
