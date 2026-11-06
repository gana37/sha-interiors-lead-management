"""
ai_service.py - Google Gemini AI Service Module
SHA Interface Interiors - AI-Powered Lead Management System

Provides official Google Gemini Python SDK integration with secure API key
handling, model fallback cascade, rate-limit resilience, and zero-hallucination
CRM context grounding.
"""

import os
import sys
import warnings
from typing import Dict, List, Optional, Any
import business_config

# Suppress deprecated generativeai FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="google.generativeai")

# Ensure stdout handles UTF-8 on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Attempt to load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    pass

# Supported Gemini models in priority order
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
FALLBACK_MODELS = [
    DEFAULT_MODEL,
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-pro-latest"
]
# Remove duplicates while preserving order
FALLBACK_MODELS = list(dict.fromkeys(FALLBACK_MODELS))

PLACEHOLDER_KEYS = {
    "",
    "your_gemini_api_key_here",
    "your_api_key_here",
    "none",
    "null"
}


def get_gemini_api_key() -> Optional[str]:
    """
    Retrieves the Gemini API key from environment variables or Streamlit secrets.
    Never logs, prints, or exposes the key.
    """
    # 1. Check OS / .env environment variables
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key and key.strip().lower() not in PLACEHOLDER_KEYS and len(key.strip()) > 10:
        return key.strip()

    # 2. Check Streamlit Cloud Secrets if streamlit is active in runtime
    if "streamlit" in sys.modules:
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                if "GEMINI_API_KEY" in st.secrets:
                    s_key = st.secrets["GEMINI_API_KEY"]
                    if s_key and s_key.strip().lower() not in PLACEHOLDER_KEYS and len(s_key.strip()) > 10:
                        return s_key.strip()
                if "GOOGLE_API_KEY" in st.secrets:
                    s_key = st.secrets["GOOGLE_API_KEY"]
                    if s_key and s_key.strip().lower() not in PLACEHOLDER_KEYS and len(s_key.strip()) > 10:
                        return s_key.strip()
        except Exception:
            pass

    return None


def is_gemini_available() -> bool:
    """Returns True if a valid Gemini API key is configured."""
    return get_gemini_api_key() is not None


def get_active_model_name() -> str:
    """Returns the primary configured model name."""
    return DEFAULT_MODEL


def verify_connection() -> Dict[str, Any]:
    """
    Tests connection to Google Gemini API using a lightweight ping.
    Returns status dictionary without exposing the API key.
    """
    key = get_gemini_api_key()
    if not key:
        return {
            "connected": False,
            "model": DEFAULT_MODEL,
            "error": "No Gemini API key found. Configure GEMINI_API_KEY in .env or Streamlit Secrets."
        }

    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        
        # Test default model
        model = genai.GenerativeModel(DEFAULT_MODEL)
        response = model.generate_content("Ping. Respond with 'PONG'.")
        if response and response.text:
            return {
                "connected": True,
                "model": DEFAULT_MODEL,
                "message": "Connection verified successfully."
            }
        else:
            return {
                "connected": False,
                "model": DEFAULT_MODEL,
                "error": "API returned an empty response."
            }
    except Exception as e:
        err_msg = str(e)
        # Classify common Gemini errors for user-friendly guidance
        clean_err = _classify_gemini_error(err_msg)
        return {
            "connected": False,
            "model": DEFAULT_MODEL,
            "error": clean_err
        }


def _classify_gemini_error(err_msg: str) -> str:
    """Converts raw API exception text into a clean, actionable error summary."""
    lowered = err_msg.lower()
    if "api_key_invalid" in lowered or "invalid api key" in lowered or "api key not valid" in lowered or "400" in lowered and "key" in lowered:
        return "Invalid Gemini API Key. Please verify your key at https://aistudio.google.com/app/apikey"
    if "quota" in lowered or "resourceexhausted" in lowered or "429" in lowered:
        return "Google Gemini API rate limit or quota exceeded. The CRM is seamlessly using the built-in local engine."
    if "permissiondenied" in lowered or "403" in lowered:
        return "Permission denied for this Gemini model. Check your API project permissions in Google AI Studio."
    if "not found" in lowered or "404" in lowered:
        return f"Model '{DEFAULT_MODEL}' not found. Verify model availability for your account."
    if "timeout" in lowered or "timed out" in lowered or "connection" in lowered:
        return "Network connection to Google Gemini timed out. Local CRM engine activated."
    # Truncate any long message to avoid leaking internals
    return f"Gemini API Error: {err_msg[:120]}"


def generate_content(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.3,
    max_output_tokens: int = 1000
) -> Dict[str, Any]:
    """
    Invokes the Google Gemini SDK with fallback model cascading.
    Returns:
        {
            "success": bool,
            "text": str,
            "model": str,
            "error": Optional[str],
            "fallback_used": bool
        }
    """
    key = get_gemini_api_key()
    if not key:
        return {
            "success": False,
            "text": "",
            "model": DEFAULT_MODEL,
            "error": "GEMINI_API_KEY is not configured.",
            "fallback_used": True
        }

    try:
        import google.generativeai as genai
    except ImportError:
        return {
            "success": False,
            "text": "",
            "model": DEFAULT_MODEL,
            "error": "google-generativeai SDK is not installed.",
            "fallback_used": True
        }

    genai.configure(api_key=key)

    last_error = None
    for model_name in FALLBACK_MODELS:
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
            
            kwargs: Dict[str, Any] = {
                "model_name": model_name,
                "generation_config": generation_config
            }
            if system_instruction:
                kwargs["system_instruction"] = system_instruction
                
            model = genai.GenerativeModel(**kwargs)
            response = model.generate_content(prompt)
            
            if response and response.text:
                return {
                    "success": True,
                    "text": response.text.strip(),
                    "model": model_name,
                    "error": None,
                    "fallback_used": (model_name != DEFAULT_MODEL)
                }
        except Exception as e:
            last_error = _classify_gemini_error(str(e))
            # Continue to next model in cascade
            continue

    return {
        "success": False,
        "text": "",
        "model": DEFAULT_MODEL,
        "error": last_error or "All Gemini models in fallback cascade failed.",
        "fallback_used": True
    }


def generate_chat_response(
    query: str,
    history: List[Dict[str, str]],
    crm_context_str: str,
    system_instruction: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes a multi-turn chat turn with grounding in real SQLite CRM data.
    """
    key = get_gemini_api_key()
    if not key:
        return {
            "success": False,
            "text": "",
            "model": DEFAULT_MODEL,
            "error": "GEMINI_API_KEY not configured.",
            "fallback_used": True
        }

    try:
        import google.generativeai as genai
    except ImportError:
        return {
            "success": False,
            "text": "",
            "model": DEFAULT_MODEL,
            "error": "google-generativeai SDK not installed.",
            "fallback_used": True
        }

    genai.configure(api_key=key)

    # Build comprehensive prompt incorporating multi-turn history and ground-truth CRM data
    formatted_prompt = (
        f"=== VERIFIED REAL CRM DATA FROM SQLITE DATABASE ===\n"
        f"{crm_context_str}\n"
        f"===================================================\n\n"
    )

    if history:
        formatted_prompt += "=== CONVERSATION HISTORY ===\n"
        # Only take the last 6 turns to keep context tight
        for turn in history[-6:]:
            role = "Consultant" if turn.get("role") == "user" else "Assistant"
            formatted_prompt += f"{role}: {turn.get('content', '')}\n"
        formatted_prompt += "============================\n\n"

    formatted_prompt += (
        f"Consultant Question: {query}\n\n"
        f"Instructions:\n"
        f"1. You are the senior AI Sales & Design Consultant Assistant for {business_config.BUSINESS_NAME}.\n"
        f"2. Base all counts, names, budgets, and cities STRICTLY on the verified CRM data above.\n"
        f"3. Never hallucinate lead names, phone numbers, or numbers that are not in the provided data.\n"
        f"4. If asked about leads in a city, list the actual leads provided in the data.\n"
        f"5. Maintain a professional, consultative, and encouraging tone suitable for a high-end interior design firm.\n"
        f"6. Format with clean markdown bullet points and bold highlights.\n"
        f"7. When answering queries about leads needing review or action, clearly use the heading '### ⚠️ Attention Required:' (or 'No urgent leads pending.') to highlight actionable leads.\n"
        f"8. MANDATORY OFFICE RULES: Always refer to our office as '{business_config.OFFICE_NAME}' (NEVER 'Hyderabad Studio'). "
        f"General office hours: {business_config.OFFICE_HOURS}, {business_config.WORKING_DAYS_SUMMARY} (open all 7 days of the week). "
        f"Customer consultation appointments: strictly {business_config.APPOINTMENT_HOURS}, {business_config.APPOINTMENT_DAYS_SUMMARY}. "
        f"NEVER offer or solicit appointments between 10:00 AM and 2:00 PM or between 5:00 PM and 6:00 PM. "
        f"Official Google Maps link: {business_config.OFFICE_MAPS_LINK} .\n"
    )

    default_system = (
        f"You are the expert CRM & Interior Design Assistant for {business_config.BUSINESS_NAME} – Hyderabad Edition, "
        f"specializing in Hyderabad, Secunderabad, and surrounding Telangana metropolitan regions "
        f"(including Gachibowli, Madhapur, Jubilee Hills, Banjara Hills, Kondapur, Kokapet, Financial District, Kukatpally, Tellapur, Miyapur).\n\n"
        f"{business_config.AI_SYSTEM_INSTRUCTION_BLOCK}\n"
        f"Always provide precise factual data grounded strictly in verified CRM records."
    )

    return generate_content(
        prompt=formatted_prompt,
        system_instruction=system_instruction or default_system,
        temperature=0.3,
        max_output_tokens=1200
    )
