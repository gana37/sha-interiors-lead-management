"""
whatsapp_importer.py - Multimodal WhatsApp Conversation Import Engine
SHA Interface Interiors - AI-Powered Interior Design Lead Management System

Supports 3 Import Methods:
1. Manual Message Entry (Incoming & Outgoing with sender & timestamp).
2. Screenshot Vision Import (Gemini Multimodal Vision + Pillow for PNG, JPG, JPEG).
3. TXT Export Import (Regex parser for Indian & International date/time formats, multiline, duplicate prevention).
"""

import os
import sys
import io
import re
import hashlib
import json
import datetime
from typing import Dict, List, Optional, Tuple, Any

import database
import multilingual_engine
import whatsapp_assistant
import ai_service

# -------------------------------------------------------------
# 1. MANUAL MESSAGE IMPORT
# -------------------------------------------------------------

def import_manual_message(
    lead_id: str,
    message_content: str,
    direction: str = "incoming",
    sender_name: Optional[str] = None,
    timestamp: Optional[str] = None,
    db_path: str = database.DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """
    Imports a manually entered WhatsApp message or reply into the CRM.
    Passes text through multilingual engine for language detection and English translation.
    """
    clean_text = message_content.strip()
    if not clean_text:
        return {"success": False, "error": "Message content cannot be empty."}

    # Verify lead exists
    lead = database.get_lead_by_id(lead_id, db_path=db_path)
    if not lead:
        return {"success": False, "error": f"Lead ID '{lead_id}' not found in CRM."}

    # Process multilingual understanding
    proc = multilingual_engine.process_customer_message(clean_text, lead_id=lead_id)

    # Prevent duplicate
    if database.check_duplicate_conversation_message(lead_id, clean_text, created_at=timestamp, db_path=db_path):
        return {
            "success": False,
            "error": "Duplicate detected: This exact message is already recorded for this customer.",
            "is_duplicate": True
        }

    res = database.add_imported_conversation_message(
        lead_id=lead_id,
        message_content=clean_text,
        direction=direction,
        channel="WhatsApp",
        original_language=proc["language_code"],
        english_translation=proc["english_translation"],
        source_type="Manual",
        timestamp=timestamp,
        db_path=db_path
    )
    res["language_name"] = proc["language_name"]
    res["english_translation"] = proc["english_translation"]
    return res


# -------------------------------------------------------------
# 2. WHATSAPP SCREENSHOT VISION IMPORT
# -------------------------------------------------------------

def extract_from_screenshot(
    image_bytes: bytes,
    file_name: str = "screenshot.jpg",
    lead_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extracts structured conversation messages from a WhatsApp screenshot using Gemini Multimodal Vision.
    Preserves message order, identifies direction (incoming/outgoing), timestamps, and confidence.
    """
    if not image_bytes:
        return {"success": False, "error": "No image data provided.", "messages": []}

    # Compute file hash
    file_hash = hashlib.sha256(image_bytes).hexdigest()

    # Load PIL image
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return {"success": False, "error": f"Failed to parse image file: {str(e)}", "messages": []}

    extracted_messages: List[Dict[str, Any]] = []

    # Check Gemini API availability for multimodal extraction
    if ai_service.is_gemini_available():
        try:
            import google.generativeai as genai
            key = ai_service.get_gemini_api_key()
            genai.configure(api_key=key)

            prompt = """You are an accurate WhatsApp screenshot transcription and OCR engine for an interior design CRM.
Inspect this WhatsApp chat screenshot and extract every visible message bubble in exact chronological order.

For each message bubble, extract:
1. "sender": name or phone of sender if visible (e.g. customer name, "Consultant", "You", or "Unknown").
2. "direction": "incoming" (if message is from customer on the left) or "outgoing" (if sent from our device on the right/green).
3. "message_text": exact verbatim text of the message.
4. "timestamp": visible time/date (e.g. "10:30 AM", "Yesterday", "2026-11-05 10:30"), or null if not visible.
5. "confidence": float between 0.0 and 1.0 indicating OCR certainty.
6. "language": language code (e.g. "te", "hi", "en", "ta", etc.).

CRITICAL CONSTRAINTS:
- DO NOT invent missing messages.
- DO NOT hallucinate phone numbers.
- If text is blurry or partially obscured, set confidence < 0.70.
- Return ONLY a valid JSON array of objects.

JSON FORMAT:
[
  {"sender": "Customer", "direction": "incoming", "message_text": "...", "timestamp": "10:30 AM", "confidence": 0.95, "language": "en"}
]
"""
            model = genai.GenerativeModel("gemini-flash-latest")
            response = model.generate_content([prompt, img])

            if response and response.text:
                raw_json = response.text.strip()
                # Remove markdown fences if present
                raw_json = re.sub(r"^```(?:json)?\s*", "", raw_json)
                raw_json = re.sub(r"\s*```$", "", raw_json)
                parsed = json.loads(raw_json)
                if isinstance(parsed, list):
                    for idx, item in enumerate(parsed):
                        text = item.get("message_text", "").strip()
                        if text:
                            proc = multilingual_engine.process_customer_message(text)
                            extracted_messages.append({
                                "index": idx + 1,
                                "sender": item.get("sender", "Customer"),
                                "direction": item.get("direction", "incoming"),
                                "message_text": text,
                                "timestamp": item.get("timestamp") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "confidence": float(item.get("confidence", 0.9)),
                                "is_flagged_for_review": float(item.get("confidence", 0.9)) < 0.75,
                                "original_language": proc["language_code"],
                                "english_translation": proc["english_translation"]
                            })
        except Exception as e:
            # Fall back gracefully to manual preview if API fails
            pass

    # If no messages extracted via API (or offline), provide empty preview with notice
    return {
        "success": True,
        "file_name": file_name,
        "file_hash": file_hash,
        "lead_id": lead_id,
        "extracted_count": len(extracted_messages),
        "messages": extracted_messages,
        "needs_manual_review": any(m.get("is_flagged_for_review") for m in extracted_messages)
    }


# -------------------------------------------------------------
# 3. WHATSAPP TXT EXPORT IMPORT
# -------------------------------------------------------------

# Supported WhatsApp exported header regex patterns
TXT_HEADER_PATTERNS = [
    # 1. 15/01/26, 10:30 am - Sender: Message (Indian 12-hour format)
    re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?\s*(?:[apAP]\.?[mM]\.?))\s*-\s*([^:]+):\s*(.*)$'),
    # 2. 15/01/2026, 10:30 - Sender: Message (24-hour format)
    re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*([^:]+):\s*(.*)$'),
    # 3. [15/01/26, 10:30:15 AM] Sender: Message (iOS bracketed 12h)
    re.compile(r'^\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?\s*(?:[apAP]\.?[mM]\.?))\]\s*([^:]+):\s*(.*)$'),
    # 4. [15/01/2026, 10:30:15] Sender: Message (iOS bracketed 24h)
    re.compile(r'^\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?)\]\s*([^:]+):\s*(.*)$'),
    # 5. 15.01.26, 10:30 - Sender: Message (Dot separator)
    re.compile(r'^(\d{1,2}\.\d{1,2}\.\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?\s*(?:[apAP]\.?[mM]\.?)?)\s*-\s*([^:]+):\s*(.*)$'),
    # 6. 15-01-2026, 10:30 - Sender: Message (Hyphen separator)
    re.compile(r'^(\d{1,2}-\d{1,2}-\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?\s*(?:[apAP]\.?[mM]\.?)?)\s*-\s*([^:]+):\s*(.*)$')
]

SYSTEM_MESSAGE_MARKERS = [
    "messages and calls are end-to-end encrypted",
    "this chat is with a business account",
    "joined using this group's invite link",
    "created group",
    "security code changed",
    "<media omitted>",
    "you deleted this message",
    "this message was deleted"
]

def parse_whatsapp_txt_export(
    raw_text: str,
    default_sender_self: str = "SHA Consultant"
) -> List[Dict[str, Any]]:
    """
    Parses WhatsApp exported TXT files supporting multiple date/time formats,
    multiline message continuation, and system message filtering.
    """
    lines = raw_text.splitlines()
    parsed_records: List[Dict[str, Any]] = []
    current_msg: Optional[Dict[str, Any]] = None

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        # Check if line matches any WhatsApp header format
        matched = False
        for pattern in TXT_HEADER_PATTERNS:
            m = pattern.match(line_str)
            if m:
                matched = True
                date_str, time_str, sender_raw, content_raw = m.groups()
                sender = sender_raw.strip()
                content = content_raw.strip()

                # Filter system messages
                if any(sm in content.lower() or sm in sender.lower() for sm in SYSTEM_MESSAGE_MARKERS):
                    continue

                # Save previous multiline message
                if current_msg:
                    parsed_records.append(current_msg)

                # Standardize ISO timestamp
                iso_ts = _parse_date_time_to_iso(date_str, time_str)

                # Determine direction: if sender contains "you" or our team
                direction = "outgoing" if any(w in sender.lower() for w in ["you", "sha", "consultant", "sales"]) else "incoming"

                # Process multilingual understanding
                proc = multilingual_engine.process_customer_message(content)

                current_msg = {
                    "raw_sender": sender,
                    "direction": direction,
                    "date_str": date_str,
                    "time_str": time_str,
                    "timestamp": iso_ts,
                    "message_content": content,
                    "original_language": proc["language_code"],
                    "language_name": proc["language_name"],
                    "english_translation": proc["english_translation"]
                }
                break

        if not matched and current_msg:
            # Multiline continuation belonging to previous message
            current_msg["message_content"] += "\n" + line_str
            # Update translation for extended multiline
            proc_ext = multilingual_engine.process_customer_message(current_msg["message_content"])
            current_msg["english_translation"] = proc_ext["english_translation"]

    if current_msg:
        parsed_records.append(current_msg)

    return parsed_records


def _parse_date_time_to_iso(date_str: str, time_str: str) -> str:
    """Standardizes date and time strings into 'YYYY-MM-DD HH:MM:SS'."""
    clean_date = date_str.replace(".", "/").replace("-", "/")
    parts = clean_date.split("/")
    if len(parts) == 3:
        p1, p2, p3 = parts
        # If year is 2 digits
        if len(p3) == 2:
            p3 = f"20{p3}"
        # Determine day vs month (Indian format is DD/MM/YYYY)
        try:
            day, month, year = int(p1), int(p2), int(p3)
            # Normalize 12-hour AM/PM
            clean_time = time_str.strip().lower()
            is_pm = "pm" in clean_time
            is_am = "am" in clean_time
            t_only = re.sub(r'[apAP]\.?[mM]\.?', '', clean_time).strip()
            t_parts = t_only.split(":")
            hour = int(t_parts[0])
            minute = int(t_parts[1]) if len(t_parts) > 1 else 0
            second = int(t_parts[2]) if len(t_parts) > 2 else 0

            if is_pm and hour < 12:
                hour += 12
            elif is_am and hour == 12:
                hour = 0

            dt = datetime.datetime(year, month, day, hour, minute, second)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

    return f"{date_str} {time_str}"


# -------------------------------------------------------------
# 4. CUSTOMER MATCHING & BATCH COMMIT
# -------------------------------------------------------------

def match_lead_from_conversation(
    parsed_messages: List[Dict[str, Any]],
    db_path: str = database.DEFAULT_DB_PATH
) -> Tuple[Optional[str], float, str]:
    """
    Attempts to match parsed conversation messages with an existing CRM lead
    using phone numbers and sender names.
    Returns: (matched_lead_id, confidence, rationale)
    """
    leads = database.get_all_leads(db_path=db_path)
    if not leads or not parsed_messages:
        return None, 0.0, "No leads or messages to match."

    # 1. Check for Phone Number in senders or messages
    for msg in parsed_messages:
        sender = msg.get("raw_sender", "")
        norm_phone = whatsapp_assistant.normalize_whatsapp_phone(sender)
        if norm_phone:
            for l in leads:
                l_norm = whatsapp_assistant.normalize_whatsapp_phone(l.get("phone"))
                if l_norm == norm_phone:
                    return l["lead_id"], 1.0, f"Exact Phone Match: {norm_phone} matches {l['customer_name']}"

    # 2. Check for Name Match in senders
    senders = {m.get("raw_sender", "").strip().lower() for m in parsed_messages if m.get("direction") == "incoming"}
    for s in senders:
        if s and len(s) > 2:
            for l in leads:
                c_name = l["customer_name"].strip().lower()
                if s == c_name or s in c_name or c_name in s:
                    return l["lead_id"], 0.85, f"Sender Name Match: '{msg.get('raw_sender')}' matches '{l['customer_name']}'"

    return None, 0.0, "No definitive customer match found. Manual selection required."


def commit_imported_messages(
    lead_id: str,
    messages_to_import: List[Dict[str, Any]],
    file_name: str = "manual_import",
    file_type: str = "TXT_Export",
    db_path: str = database.DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """
    Validates, deduplicates, and commits a list of parsed messages to CUSTOMER_CONVERSATIONS.
    Never merges conversations belonging to different customers.
    """
    lead = database.get_lead_by_id(lead_id, db_path=db_path)
    if not lead:
        return {"success": False, "error": f"Lead {lead_id} does not exist."}

    batch_id = f"BATCH-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    imported_count = 0
    duplicate_count = 0

    for msg in messages_to_import:
        content = msg.get("message_text") or msg.get("message_content") or ""
        content = content.strip()
        if not content:
            continue

        ts = msg.get("timestamp")
        # Check duplicate
        if database.check_duplicate_conversation_message(lead_id, content, created_at=ts, db_path=db_path):
            duplicate_count += 1
            continue

        direction = msg.get("direction", "incoming")
        lang = msg.get("original_language", "en")
        trans = msg.get("english_translation")
        conf = msg.get("confidence")

        database.add_imported_conversation_message(
            lead_id=lead_id,
            message_content=content,
            direction=direction,
            channel="WhatsApp",
            original_language=lang,
            english_translation=trans,
            source_type=file_type,
            ocr_confidence=conf,
            import_batch_id=batch_id,
            timestamp=ts,
            db_path=db_path
        )
        imported_count += 1

    # Record imported file
    database.record_imported_file(
        file_name=file_name,
        file_type=file_type,
        lead_id=lead_id,
        extracted_count=imported_count,
        db_path=db_path
    )

    return {
        "success": True,
        "lead_id": lead_id,
        "customer_name": lead["customer_name"],
        "batch_id": batch_id,
        "imported_count": imported_count,
        "duplicate_count": duplicate_count,
        "total_processed": len(messages_to_import)
    }
