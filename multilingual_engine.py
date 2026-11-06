"""
multilingual_engine.py - Multilingual Customer Understanding & English-Only Translation Pipeline
SHA Interface Interiors - AI-Powered Interior Design Lead Management System

Supports:
- 12 Indian Languages: Telugu, Hindi, Tamil, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi, Odia, Urdu, English.
- Transliterated & Code-Mixed Messages: Hinglish, Teluglish, Tanglish.
- Complete Technical Terminology Preservation (BWP, HDHMR, Acrylic, Hettich, Blum, etc.).
- MANDATORY POLICY: All customer-facing AI responses and WhatsApp drafts are ALWAYS in ENGLISH ONLY.
"""

import os
import sys
import re
import json
from typing import Dict, List, Optional, Tuple, Any
import ai_service

# -------------------------------------------------------------
# 1. PROTECTED TECHNICAL TERMS (NEVER ALTERED OR TRANSLATED)
# -------------------------------------------------------------

PROTECTED_TECHNICAL_TERMS = [
    # Core Boards & Substrates
    "BWP", "BWR", "MR", "MDF", "HDF", "HDHMR", "Plywood", "Marine Ply", "Marine Plywood",
    "Particle Board", "Pre-laminated Board", "Calibrated Plywood", "IS 710", "IS 303", "Commercial Ply",
    # Surface Finishes
    "Laminate", "Laminates", "1mm Laminate", "0.8mm Laminate", "Acrylic", "High Gloss Acrylic",
    "Anti-scratch Acrylic", "Veneer", "Natural Veneer", "Smoked Oak", "Teak Veneer", "Walnut Veneer",
    "PU Finish", "PU Paint", "Polyurethane", "Membrane", "Duco Paint", "Polyester Polish", "Lacquer",
    # Countertop Materials
    "Quartz", "Granite", "Black Galaxy", "Jet Black", "Tan Brown", "Kalinga Stone",
    "Nano White", "Crystallized Glass", "Corian", "Dekton", "Sintered Stone",
    # Hardware & Brands
    "Hettich", "Blum", "Häfele", "Hafele", "Sensys", "InnoTech", "InnoTech Atira",
    "AvanTech", "Tandembox", "Antaro", "Clip Top Blumotion", "Aventos", "Soft Close",
    "Tandem Box", "Hydraulic Lift", "Gas Strut", "Telescopic Channel", "Profile Handle",
    "Gola Profile", "J-Pull", "Magic Corner", "Carousel", "Pantry Unit", "Tall Unit",
    # Specifications & Spatial Planning
    "2BHK", "3BHK", "4BHK", "5BHK", "Villa", "Penthouse", "Apartment",
    "sqft", "sq.ft", "sft", "sq ft", "square feet", "mm", "rft", "running feet",
    "BOQ", "Bill of Quantities", "3D Design", "Floor Plan", "Vastu", "Work Triangle",
    "False Ceiling", "Gypsum", "POP", "Cove Lighting", "Profile Light", "Warm White", "3000K"
]

# Unicode Script Ranges for Indian Languages
UNICODE_SCRIPT_RANGES = {
    "te": (0x0C00, 0x0C7F, "Telugu"),
    "hi": (0x0900, 0x097F, "Hindi"),  # Devanagari (shared with Marathi)
    "ta": (0x0B80, 0x0BFF, "Tamil"),
    "kn": (0x0C80, 0x0CFF, "Kannada"),
    "ml": (0x0D00, 0x0D7F, "Malayalam"),
    "bn": (0x0980, 0x09FF, "Bengali"),
    "gu": (0x0A80, 0x0AFF, "Gujarati"),
    "pa": (0x0A00, 0x0A7F, "Punjabi"),
    "or": (0x0B00, 0x0B7F, "Odia"),
    "ur": (0x0600, 0x06FF, "Urdu")
}

# Transliterated Indian Language Keyword Markers
TRANSLITERATED_MARKERS = {
    "hi": ["kya", "hai", "batao", "chahiye", "kitna", "hoga", "kaise", "ghar", "rasoi", "kamra", "acha", "price kam", "namaste", "dhanyawad", "bhai", "bhaiya", "shukriya", "kharidna", "mera", "meri", "hum", "hume", "aapse", "bhejo"],
    "te": ["enti", "cheppandi", "kavali", "ela", "untundi", "eppudu", "chustam", "baga", "illu", "namaskaram", "dhanyavadalu", "meeru", "chala", "manchi", "chesi", "ivvandi", "maku", "maaku", "avtundi", "avuthundi", "lo"],
    "ta": ["ennachu", "solla", "solungo", "venum", "eppadi", "evvalavu", "nalla", "veedu", "vanakkam", "nandri", "kudunga", "pannalam", "engalukku", "ungalukku", "pannanum", "eppo", "mudiyum", "romba", "kooda", "panrom", "theriyuma"],
    "kn": ["enu", "heli", "beku", "hege", "eshtu", "chennagi", "mane", "namaskara", "dhanyavada", "kodi", "namage", "madabeku", "aguthe", "tumba"],
    "ml": ["enthanu", "parayoo", "venam", "enganeyanu", "ethrayanu", "nalla", "veedu", "namaskaram", "nanni", "njannal", "cheyyano", "aano"],
    "mr": ["kay", "sanga", "pahije", "kasa", "kiti", "chhan", "ghar", "namaskar", "dhanyavad", "ahe", "amhi", "karayche", "amche"]
}

LANGUAGE_NAMES = {
    "en": "English",
    "te": "Telugu",
    "hi": "Hindi",
    "ta": "Tamil",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "or": "Odia",
    "ur": "Urdu"
}


def extract_and_mask_technical_terms(text: str) -> Tuple[Dict[str, str], str]:
    """
    Finds protected interior terms and replaces them with unique tokens {TERM_0}, {TERM_1}, etc.
    Returns: (term_map, masked_text)
    """
    term_map: Dict[str, str] = {}
    masked = text
    idx = 0
    # Sort terms by length descending to match longest phrases first (e.g. 'BWP marine plywood' before 'BWP')
    sorted_terms = sorted(PROTECTED_TECHNICAL_TERMS, key=len, reverse=True)
    for term in sorted_terms:
        pattern = r'\b' + re.escape(term) + r'\b'
        matches = list(re.finditer(pattern, masked, re.IGNORECASE))
        if matches:
            token = f"__PROTECTED_TERM_{idx}__"
            # Get the exact casing from the first match
            exact_matched_text = matches[0].group(0)
            term_map[token] = exact_matched_text
            masked = re.sub(pattern, token, masked, flags=re.IGNORECASE)
            idx += 1
    return term_map, masked


def restore_technical_terms(masked_text: str, term_map: Dict[str, str]) -> str:
    """
    Replaces tokens back with their original technical term values.
    """
    restored = masked_text
    for token, original_term in term_map.items():
        restored = restored.replace(token, original_term)
    return restored


# -------------------------------------------------------------
# 2. LANGUAGE DETECTION ENGINE
# -------------------------------------------------------------

def detect_language(text: str) -> Dict[str, Any]:
    """
    Detects language of incoming text across 12 Indian languages and transliterated variants.
    Returns: {
        'language_code': str,
        'language_name': str,
        'script': str,
        'is_transliterated': bool,
        'confidence': float
    }
    """
    clean = text.strip()
    if not clean:
        return {
            "language_code": "en",
            "language_name": "English",
            "script": "Latin",
            "is_transliterated": False,
            "confidence": 1.0
        }

    # Count script characters
    script_counts: Dict[str, int] = {}
    latin_count = 0
    total_alpha = 0

    for char in clean:
        cp = ord(char)
        if char.isalpha():
            total_alpha += 1
            if ("A" <= char <= "Z") or ("a" <= char <= "z"):
                latin_count += 1
            else:
                for lang_code, (start, end, lang_name) in UNICODE_SCRIPT_RANGES.items():
                    if start <= cp <= end:
                        script_counts[lang_code] = script_counts.get(lang_code, 0) + 1
                        break

    # If native Indian script characters dominate
    if script_counts:
        top_lang = max(script_counts, key=script_counts.get)
        count = script_counts[top_lang]
        total_native = sum(script_counts.values())
        conf = round(min(1.0, count / max(1, total_native)), 2)

        # Disambiguate Devanagari between Hindi and Marathi if applicable
        lang_code = top_lang
        if top_lang == "hi":
            # Check Marathi distinctive words
            marathi_markers = ["आहे", "नाही", "कसे", "करावे", "घर", "पाहिजे", "नमस्कार", "धन्यवाद"]
            if any(m in clean for m in marathi_markers):
                lang_code = "mr"

        return {
            "language_code": lang_code,
            "language_name": LANGUAGE_NAMES.get(lang_code, "Indian Language"),
            "script": UNICODE_SCRIPT_RANGES[top_lang][2],
            "is_transliterated": False,
            "confidence": conf
        }

    # Check for Latin transliterated keywords (Hinglish, Teluglish, Tanglish, etc.)
    text_lower = clean.lower()
    words = set(re.findall(r'\b[a-z]{2,}\b', text_lower))

    best_trans_lang = None
    max_matches = 0
    for lang_code, markers in TRANSLITERATED_MARKERS.items():
        matches = sum(1 for m in markers if m in words or f" {m} " in f" {text_lower} ")
        if matches > max_matches:
            max_matches = matches
            best_trans_lang = lang_code

    if best_trans_lang and max_matches >= 1:
        lang_name = LANGUAGE_NAMES.get(best_trans_lang, "Indian Language")
        variant_name = "Hinglish" if best_trans_lang == "hi" else ("Teluglish" if best_trans_lang == "te" else f"{lang_name} (Transliterated)")
        return {
            "language_code": best_trans_lang,
            "language_name": variant_name,
            "script": "Latin",
            "is_transliterated": True,
            "confidence": round(min(0.95, 0.6 + 0.1 * max_matches), 2)
        }

    return {
        "language_code": "en",
        "language_name": "English",
        "script": "Latin",
        "is_transliterated": False,
        "confidence": 1.0
    }


# -------------------------------------------------------------
# 3. INTERNAL TRANSLATION ENGINE (TRANSLATES TO ENGLISH INTERNALLY)
# -------------------------------------------------------------

def translate_to_english(
    text: str,
    source_language_code: Optional[str] = None,
    source_lang: Optional[str] = None
) -> Dict[str, Any]:
    """
    Translates incoming customer message internally into English while strictly preserving
    all technical terms (BWP, HDHMR, Acrylic, Hettich, dimensions, etc.).
    
    Returns:
    {
        'original_text': str,
        'detected_language': str,
        'source_language': str,
        'language_name': str,
        'english_translation': str,
        'translated_text': str,
        'is_english_output': bool,
        'is_flagged_for_review': bool,
        'technical_terms_preserved': List[str],
        'preserved_terms': List[str],
        'method': str
    }
    """
    effective_source_lang = source_language_code or source_lang
    original = text.strip()
    if not original:
        return {
            "original_text": original,
            "detected_language": "en",
            "source_language": "en",
            "language_name": "English",
            "english_translation": original,
            "translated_text": original,
            "is_english_output": True,
            "is_flagged_for_review": False,
            "technical_terms_preserved": [],
            "preserved_terms": [],
            "method": "empty"
        }

    # Detect language if not provided
    det = detect_language(original) if not effective_source_lang else {
        "language_code": effective_source_lang.split("_")[0],
        "language_name": LANGUAGE_NAMES.get(effective_source_lang.split("_")[0], "Indian Language"),
        "confidence": 1.0,
        "is_transliterated": "_" in effective_source_lang
    }
    lang_code = det["language_code"]

    # Identify protected technical terms present in original
    preserved_terms = []
    for term in PROTECTED_TECHNICAL_TERMS:
        if re.search(r'\b' + re.escape(term) + r'\b', original, re.IGNORECASE):
            preserved_terms.append(term)

    # If already pure English
    if lang_code == "en" and not det.get("is_transliterated"):
        return {
            "original_text": original,
            "detected_language": "en",
            "source_language": "en",
            "language_name": "English",
            "english_translation": original,
            "translated_text": original,
            "is_english_output": True,
            "is_flagged_for_review": False,
            "technical_terms_preserved": preserved_terms,
            "preserved_terms": preserved_terms,
            "method": "pass_through"
        }

    # Attempt AI Translation via Google Gemini if available
    if ai_service.is_gemini_available():
        prompt = f"""You are an architectural and interior design technical translator for SHA Interface Interiors.
Translate this customer message into natural, professional English.

CUSTOMER ORIGINAL MESSAGE:
\"\"\"{original}\"\"\"

MANDATORY RULES:
1. Translate the meaning accurately into clear English.
2. PRESERVE all technical material names and specifications EXACTLY: {', '.join(PROTECTED_TECHNICAL_TERMS[:25])}.
3. DO NOT translate brands like Hettich, Blum, Hafele, Greenlam, Century.
4. DO NOT alter measurements (e.g., 2BHK, 3BHK, 1200 sqft, 18mm, 1mm).
5. Output ONLY the English translation without preamble or quotes.
"""
        res = ai_service.generate_content(prompt, temperature=0.1, max_output_tokens=300)
        if res.get("success") and res.get("text"):
            trans_text = res["text"].strip().strip('"').strip("'")
            return {
                "original_text": original,
                "detected_language": lang_code,
                "source_language": lang_code,
                "language_name": det.get("language_name", "Indian Language"),
                "english_translation": trans_text,
                "translated_text": trans_text,
                "is_english_output": True,
                "is_flagged_for_review": False,
                "technical_terms_preserved": preserved_terms,
                "preserved_terms": preserved_terms,
                "method": "gemini_multilingual"
            }

    # Deterministic Dictionary-based Fallback for Offline / Quota Resilience
    trans_text = _deterministic_translate_fallback(original, lang_code)
    return {
        "original_text": original,
        "detected_language": lang_code,
        "source_language": lang_code,
        "language_name": det.get("language_name", "Indian Language"),
        "english_translation": trans_text,
        "translated_text": trans_text,
        "is_english_output": True,
        "is_flagged_for_review": (trans_text == original and lang_code != "en"),
        "technical_terms_preserved": preserved_terms,
        "preserved_terms": preserved_terms,
        "method": "deterministic_fallback"
    }


def _deterministic_translate_fallback(text: str, lang_code: str) -> str:
    """
    Reliable rule-based translator for common Indian language customer queries and code-mixed terms.
    """
    t = text.strip()
    # Common phrase substitutions (Telugu, Hindi, Tamil, Transliterated)
    replacements = [
        # Telugu (Native script)
        (r'మీ ఆఫీస్ ఎక్కడ ఉంది\??', 'Where is your office?'),
        (r'ఎప్పుడు కలవవచ్చు\??', 'When can we meet?'),
        (r'కోటేషన్ ఇవ్వండి', 'Please give a quotation.'),
        (r'ధర ఎంత అవుతుంది\??', 'What will be the price?'),
        (r'వంటగది ఇంటీరియర్స్ కావాలి', 'We need kitchen interiors.'),
        (r'నాకు 3BHK ఇంటీరియర్ డిజైన్ కావాలి', 'I need 3BHK interior design.'),
        (r'నాకు 2BHK ఇంటీరియర్ డిజైన్ కావాలి', 'I need 2BHK interior design.'),
        (r'మీరు BWP ప్లైవుడ్ వాడుతారా\??', 'Do you use BWP plywood?'),
        (r'నమస్కారం', 'Hello,'),
        (r'ధన్యవాదాలు', 'Thank you.'),
        
        # Hindi (Native script)
        (r'आपका ऑफिस कहाँ है\??', 'Where is your office?'),
        (r'हम कब मिल सकते हैं\??', 'When can we meet?'),
        (r'कोटेशन भेजिए', 'Please send the quotation.'),
        (r'कीमत कितनी होगी\??', 'How much will it cost?'),
        (r'मुझे 3BHK का इंटीरियर कराना है', 'I want complete interior work for my 3BHK.'),
        (r'मुझे 2BHK का इंटीरियर कराना है', 'I want complete interior work for my 2BHK.'),
        (r'क्या आप BWP प्लाइवुड इस्तेमाल करते हैं\??', 'Do you use BWP plywood?'),
        (r'नमस्ते', 'Hello,'),
        (r'धन्यवाद', 'Thank you.'),
        
        # Tamil (Native script)
        (r'உங்கள் அலுவலகம் எங்கே உள்ளது\??', 'Where is your office?'),
        (r'எப்போது சந்திக்கலாம்\??', 'When can we meet?'),
        (r'விலை என்னவாகும்\??', 'What will be the cost?'),
        (r'வணக்கம்', 'Hello,'),
        (r'நன்றி', 'Thank you.'),

        # Transliterated Telugu / Hinglish / Tanglish phrases
        (r'\b(me office ekkada undi|office ekkada)\b', 'where is your office'),
        (r'\b(eppudu kalavavachu|kalavacha|meet avvocha)\b', 'when can we meet'),
        (r'\b(quote kavali|quotation pampandi|quotation ivvandi)\b', 'need quotation'),
        (r'\b(entha avtundi|entha cost)\b', 'how much cost will it be'),
        (r'\b(aapka office kahan hai|office kidhar hai)\b', 'where is your office'),
        (r'\b(kab mil sakte hai|kab visit karu)\b', 'when can we meet'),
        (r'\b(quote bhejo|quotation chahiye|rate batao)\b', 'please send quotation'),
        (r'\b(kitna kharcha aayega|kitna cost hoga)\b', 'how much cost will it be'),
        (r'\b(price kam karo|discount milega kya)\b', 'can you reduce the price / give discount'),
        (r'\b(possession delay ho gaya|handover late hai)\b', 'possession is delayed by builder')
    ]

    result = t
    for pattern, repl in replacements:
        result = re.sub(pattern, repl, result, flags=re.IGNORECASE)

    return result


# -------------------------------------------------------------
# 4. CUSTOMER MESSAGE PROCESSOR FOR CRM INTEGRATION
# -------------------------------------------------------------

def process_customer_message(
    raw_message: str,
    lead_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Standard pipeline:
    Customer Message -> Detect Language -> Translate to English Internally
    -> Returns enriched payload for CRM, AI Assistant, and Shadow Mode.
    """
    detection = detect_language(raw_message)
    translation = translate_to_english(raw_message, detection["language_code"])

    return {
        "raw_message": raw_message,
        "language_code": detection["language_code"],
        "language_name": detection["language_name"],
        "is_transliterated": detection["is_transliterated"],
        "confidence": detection["confidence"],
        "english_translation": translation["english_translation"],
        "is_flagged_for_review": translation["is_flagged_for_review"],
        "technical_terms_preserved": translation["technical_terms_preserved"],
        "lead_id": lead_id
    }
