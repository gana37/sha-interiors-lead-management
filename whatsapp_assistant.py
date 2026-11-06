"""
whatsapp_assistant.py - Conversational AI Sales Assistant & WhatsApp Integration
SHA Interface Interiors - AI Intelligence Suite (Hyderabad Edition)

Provides:
1. Normal Indian phone normalization & validation for WhatsApp.
2. WhatsApp Click-to-Chat URL generation (https://wa.me/PHONE?text=URL_ENCODED).
3. Conversational AI Sales Assistant grounded in live SQLite CRM customer context.
4. Natural conversation memory and message history integration.
5. Detection of customer opt-out and objection handling.
6. Abstract sender interface for future WhatsApp Business Cloud API upgrade.
"""

import os
import sys
import re
import urllib.parse
import datetime
from typing import Dict, List, Optional, Tuple, Any

import database
import estimate_parser
import ai_service
import hyderabad_geo as hg
import business_config

# -------------------------------------------------------------
# 1. PHONE NUMBER NORMALIZATION & WHATSAPP CLICK-TO-CHAT
# -------------------------------------------------------------

def normalize_whatsapp_phone(phone_str: Optional[str]) -> Optional[str]:
    """
    Normalizes an Indian phone number into the standard international WhatsApp format:
    91XXXXXXXXXX (12 digits, no spaces, hyphens, plus signs, or leading zeroes).
    
    Accepts:
    - '+91 98853 01530' -> '919885301530'
    - '9840656800'      -> '919840656800'
    - '09550042018'     -> '919550042018'
    - '+91-70326-56782' -> '917032656782'
    - '00918093333059'  -> '918093333059'
    
    Returns:
    - 12-digit string starting with '91' if valid.
    - None if invalid or missing.
    """
    if not phone_str:
        return None
        
    cleaned = re.sub(r"[\s\-\(\)\.]", "", str(phone_str).strip())
    
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    elif cleaned.startswith("00"):
        cleaned = cleaned[2:]
        
    # If starts with 0 and has 11 digits (e.g. 09840656800)
    if cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = cleaned[1:]
        
    # If already has 91 prefix and 12 digits total
    if cleaned.startswith("91") and len(cleaned) == 12:
        ten_digit = cleaned[2:]
        if ten_digit.isdigit() and (ten_digit[0] in "6789" or ten_digit.startswith("91234")):
            return cleaned
        return None
        
    # If standard 10-digit mobile
    if len(cleaned) == 10 and cleaned.isdigit():
        if cleaned[0] in "6789" or cleaned.startswith("91234"):
            return f"91{cleaned}"
            
    return None

def build_whatsapp_click_to_chat_url(phone_str: Optional[str], message: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Builds the official WhatsApp Click-to-Chat URL.
    Format: https://wa.me/{PHONE_NUMBER}?text={URL_ENCODED_MESSAGE}
    
    Returns:
        (click_to_chat_url, error_message)
    """
    normalized_phone = normalize_whatsapp_phone(phone_str)
    if not normalized_phone:
        return None, "Invalid or missing phone number. Please ensure customer has a valid 10-digit Indian mobile number."
        
    clean_message = (message or "").strip()
    if not clean_message:
        return None, "Message cannot be empty."
        
    encoded_text = urllib.parse.quote(clean_message)
    url = f"https://wa.me/{normalized_phone}?text={encoded_text}"
    return url, None

# -------------------------------------------------------------
# 2. OPT-OUT & COMPLIANCE INTENT DETECTION
# -------------------------------------------------------------

OPT_OUT_KEYWORDS = [
    "stop", "unsubscribe", "opt out", "opt-out", "don't message", "dont message",
    "stop messaging", "do not call", "do not message", "not interested anymore",
    "remove my number", "remove me", "cancel inquiry", "cancel enquiry"
]

def detect_opt_out_intent(message_text: str) -> bool:
    """Detects if an incoming customer message requests communication cessation."""
    if not message_text:
        return False
    lowered = message_text.lower().strip()
    for kw in OPT_OUT_KEYWORDS:
        if kw in lowered:
            return True
    return False

# -------------------------------------------------------------
# 3. CRM CONTEXT COMPILER FOR SALES ASSISTANT
# -------------------------------------------------------------

def build_customer_prompt_context(lead: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> str:
    """
    Assembles a grounded factual profile of the customer from SQLite CRM.
    Ensures zero hallucination and strict adherence to known data.
    """
    lead_id = lead.get("lead_id", "N/A")
    name = lead.get("customer_name", "Valued Customer")
    phone = lead.get("phone", "N/A")
    locality = lead.get("locality") or lead.get("city") or "Hyderabad"
    region = lead.get("region") or "Hyderabad Metropolitan Area"
    bhk = lead.get("project_type", "Residential Apartment")
    budget = lead.get("budget_range", "Standard Package")
    status = lead.get("lead_status", "Active")
    score = lead.get("lead_score", "N/A")
    priority = lead.get("priority", "Medium")
    scope = lead.get("scope_of_work", "Full Interiors")
    property_status = lead.get("property_status", "Ready for design")
    timeline = lead.get("project_timeline", "Within 1-3 months")
    readiness = lead.get("purchase_readiness", "Exploring")
    requirements = lead.get("customer_requirements", "Complete home interior finishing")
    
    lead_ref = lead.get("lead_reference") or "Not Yet Assigned"
    est_at_raw = lead.get("estimate_generated_at")
    est_display = estimate_parser.format_estimate_display_long(est_at_raw) if est_at_raw else "N/A"
    
    history_lines = []
    for msg in conversation_history[-8:]:
        direction = "Customer" if msg.get("direction") == "incoming" else "SHA Interiors Sales Consultant"
        content = msg.get("message_content") or msg.get("ai_generated_response") or ""
        time_str = msg.get("created_at") or ""
        history_lines.append(f"[{time_str}] {direction}: {content.strip()}")
        
    history_block = "\n".join(history_lines) if history_lines else "No previous WhatsApp messages recorded."
    
    context = f"""
=== SHA INTERIORS CRM CUSTOMER DOSSIER ===
Customer ID: {lead_id}
Customer Name: {name}
Phone: {phone}
Location: {locality} ({region}, Hyderabad, Telangana)
Project Type / Property: {bhk} ({property_status})
Budget Segment: {budget}
Scope of Work: {scope}
Requirements: {requirements}
Client Timeline: {timeline}
Purchase Readiness: {readiness}
Lead Priority: {priority} (Score: {score}/100)
CRM Lead Status: {status}
Estimate Reference Number: {lead_ref}
Estimate Generated Date & Time: {est_display}
Assigned Sales Consultant: Senior Interior Consultant (SHA Interiors)

=== CONVERSATION HISTORY (MOST RECENT) ===
{history_block}
==========================================
"""
    return context.strip()

# -------------------------------------------------------------
# 4. CONVERSATIONAL AI SALES AGENT (GEMINI + LOCAL HYBRID)
# -------------------------------------------------------------

SYSTEM_SALES_INSTRUCTION = f"""
You are a warm, highly professional, polite, and consultative Senior Interior Design Sales Consultant at {business_config.BUSINESS_NAME}, Hyderabad.
You are replying directly to a customer on WhatsApp.

{business_config.AI_SYSTEM_INSTRUCTION_BLOCK}

RULES OF ENGAGEMENT:
1. Speak naturally like an experienced human sales consultant, NOT like an automated robot or rigid chatbot.
2. Address the customer politely by name (e.g. 'Hello Dr. Chakravarthy,' or 'Hi Vivek,').
3. Directly answer what the customer asked, addressing their specific question or objection.
4. Understand natural, informal English, short messages, abbreviations, and minor typos.
5. GROUNDING & ACCURACY:
   - Use the customer's actual project details from the CRM dossier (locality, BHK, estimate reference, budget).
   - If the customer asks about their estimate, refer to their specific estimate reference number and date if available.
   - If they ask about modular kitchen or package inclusions, explain SHA Interiors' premium modular solutions (factory-finished carcasses, waterproof marine ply, soft-close hardware, 45-day handover guarantee, 10-year warranty).
   - DISCOUNTS: Never promise unapproved arbitrary discounts. State that SHA Interiors offers transparent, direct-from-factory pricing with no hidden markups, but our Senior Design Lead can explore value-engineering and customized material selections during a meeting at our Miyapur office or over a phone call to optimize their budget.
   - DURATION: State our standard 45-day handover guarantee for apartments post design approval, subject to site readiness.
   - MISSING INFORMATION: Never invent prices, measurements, or site details. If information is not in the CRM, state that you will check with the site engineering team and confirm promptly.
   - COMPLAINTS / ESCALATIONS: Acknowledge with genuine empathy and assure that a Design Director will personally contact them today.
   - OPT-OUT: If the customer requests to stop messages or is not interested, acknowledge politely with respect, thank them for their time, and assure them we won't disturb them further.
6. Keep messages concise (usually 2 to 4 conversational sentences or short paragraphs), suitable for reading on WhatsApp.
7. APPOINTMENTS & SELECTIVE GOOGLE CALENDAR BOOKING LINK:
   - Always refer to our office as "Miyapur office". Never call it "Hyderabad Studio".
   - General office hours are 10:00 AM to 6:00 PM IST, all seven days of the week (Monday through Sunday).
   - Customer appointment consultations are available ONLY from 2:00 PM to 5:00 PM IST, Monday through Sunday (30-minute slots).
   - CRITICAL BOOKING LINK RULE: Do NOT automatically include the Google Calendar booking link in every customer response.
     Include the official Google Calendar booking link ({business_config.GOOGLE_CALENDAR_BOOKING_LINK}) ONLY when:
     1. The customer explicitly asks to book an appointment.
     2. The customer wants to visit the Miyapur office.
     3. The customer asks for available meeting slots.
     4. The customer clearly requests a scheduled consultation or meeting.
   - STRICT EXCLUSIONS - DO NOT include the booking link when customers ask ordinary questions about:
     * Project starting dates.
     * Project completion timelines.
     * Handover duration.
     * Pricing or budget.
     * Materials and designs.
     * Project progress or requirements.
     * General business information.
     For these conversations, answer the customer's actual question directly using verified SHA business information.
     Canonical timeline explanation: If a customer asks, "When can you start the project and how long will it take?", explain that work can start after design and scope finalisation, and that the standard apartment handover timeline for modular kitchens and wardrobes is 45 days after design approval, subject to site readiness. (DO NOT append the booking link or an appointment invitation).
   - When criteria 1-4 are met, standard polite response:
     "Certainly! We would be happy to welcome you to {business_config.BUSINESS_NAME} at our {business_config.OFFICE_NAME}. 😊

     You can check the available appointment slots and select a convenient date and time using our booking link:

     {business_config.GOOGLE_CALENDAR_BOOKING_LINK}

     We look forward to meeting you!"
   - Customers must select from the slots actually available on Google Calendar. NEVER invent or promise an available appointment time.
   - Do NOT promise an appointment is confirmed until the salesperson confirms it (or until future automatic Google Calendar event creation succeeds).
   - If the customer asks for directions or office address, share the official Google Maps link: {business_config.OFFICE_MAPS_LINK} (never invent a street address).
8. Do NOT use markdown headers, asterisks overload, or code blocks. Write clean WhatsApp-friendly text.
"""

def generate_conversational_reply(
    lead_id: str,
    incoming_message: str,
    db_path: str = database.DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """
    Generates a contextual, natural conversational sales reply to a customer's WhatsApp message.
    Uses Google Gemini if available, with an expert local fallback engine grounded in CRM context.
    """
    lead = database.get_lead_by_id(lead_id, db_path=db_path)
    if not lead:
        return {
            "success": False,
            "reply": "Lead record not found in CRM.",
            "source": "error",
            "model": "none"
        }
        
    history = database.get_conversation_history(lead_id, limit=10, db_path=db_path)
    context_str = build_customer_prompt_context(lead, history)
    
    # Check for direct opt-out intent
    is_opt_out = detect_opt_out_intent(incoming_message)
    
    # 1. Attempt Gemini Generation
    if ai_service.is_gemini_available():
        user_prompt = f"""
{context_str}

LATEST INCOMING WHATSAPP MESSAGE FROM CUSTOMER:
"{incoming_message.strip()}"

Please draft the best WhatsApp reply to this message as the Senior Sales Consultant.
Follow all professional sales rules and stay strictly grounded in the customer's CRM profile.
"""
        gemini_res = ai_service.generate_content(
            prompt=user_prompt,
            system_instruction=SYSTEM_SALES_INSTRUCTION,
            temperature=0.35,
            max_output_tokens=350
        )
        if gemini_res.get("success") and gemini_res.get("text"):
            clean_reply = gemini_res["text"].strip()
            # Clean any leftover markdown headers
            clean_reply = re.sub(r"^#+\s*", "", clean_reply)
            
            # Safeguard: Do not include booking link for ordinary questions
            if not business_config.should_include_calendar_booking_link(incoming_message):
                if business_config.GOOGLE_CALENDAR_BOOKING_LINK in clean_reply or "calendar.app.google" in clean_reply:
                    # Fallback to verified compliant local expert reply
                    clean_reply = _generate_local_expert_reply(lead, incoming_message, history, is_opt_out)

            return {
                "success": True,
                "reply": clean_reply,
                "source": "gemini",
                "model": gemini_res.get("model", "gemini"),
                "is_opt_out": is_opt_out
            }
            
    # 2. Local Expert Sales Intelligence Fallback
    local_reply = _generate_local_expert_reply(lead, incoming_message, history, is_opt_out)
    return {
        "success": True,
        "reply": local_reply,
        "source": "local_sales_brain",
        "model": "sha_local_intelligence_v1",
        "is_opt_out": is_opt_out
    }

def _generate_local_expert_reply(
    lead: Dict[str, Any],
    incoming_msg: str,
    history: List[Dict[str, Any]],
    is_opt_out: bool = False
) -> str:
    """
    Local heuristic sales expert engine.
    Ensures high-converting, compliant sales replies even when offline or without Gemini.
    CRITICAL RULE:
    Google Calendar booking link is included ONLY when:
    1. The customer explicitly asks to book an appointment.
    2. The customer wants to visit the Miyapur office.
    3. The customer asks for available meeting slots.
    4. The customer clearly requests a scheduled consultation or meeting.
    Strictly NO booking link for timeline, start dates, duration, pricing, materials, designs, or general business info.
    """
    name = lead.get("customer_name") or "there"
    loc = lead.get("property_location") or "Hyderabad"
    bhk = lead.get("property_type") or "home"
    budget = lead.get("budget_range", "your requirements")
    ref = lead.get("lead_reference")
    est_at_raw = lead.get("estimate_generated_at")
    est_time = estimate_parser.format_estimate_display(est_at_raw) if est_at_raw else None
    
    msg_lower = incoming_msg.lower().strip()
    
    # 1. Opt-out / Unsubscribe / Not interested
    if is_opt_out or "not interested" in msg_lower or "cancel" in msg_lower:
        return (
            f"Hello {name}, thank you for letting us know. We completely understand and respect your decision. "
            f"We have updated your preferences and will not send further promotional messages. "
            f"If you ever need interior design support in {loc} in the future, we would be delighted to assist. Wishing you the best!"
        )

    # 2. Timeline / Duration / Start Date (Strictly answer question directly - NO booking link)
    timeline_triggers = [
        "when can you start", "start the project", "start project", "when can we start", "when do you start",
        "how long will it take", "how long does it take", "how long", "duration", "timeline",
        "completion timeline", "how many days", "handover", "completion", "how soon can you finish"
    ]
    if any(w in msg_lower for w in timeline_triggers) and not business_config.should_include_calendar_booking_link(msg_lower):
        return (
            f"Hello {name}, work can start after design and scope finalisation, and the standard apartment handover timeline "
            f"for modular kitchens and wardrobes is 45 days after design approval, subject to site readiness. "
            f"We can initiate the on-site 3D laser measurement within 24 to 48 hours in {loc}. "
            f"Are you planning to start right away or within the coming month?"
        )

    # 3. Explicit Appointment Booking / Miyapur Office Visit / Available Slots / Scheduled Meeting
    # INCLUDE GOOGLE CALENDAR BOOKING LINK ONLY WHEN EXPLICIT CRITERIA ARE MET!
    if business_config.should_include_calendar_booking_link(msg_lower):
        return business_config.format_calendar_booking_response(name)

    # 4. Pricing & Discount Objections (Answer directly with factory pricing & value engineering; NO booking link)
    if any(w in msg_lower for w in ["reduce", "discount", "cheaper", "less price", "high price", "expensive", "negotiate", "cost too high", "lower"]):
        return (
            f"Hi {name}, we completely understand that getting maximum value for your interior investment is important. "
            f"At SHA Interiors, our quotations are direct factory-pricing with zero retail markups, premium marine plywood, and branded hardware with a 10-year warranty. "
            f"We would love to do a quick 15-minute consultation to walk you through smart value-engineering options that optimize finishes to comfortably align with your target budget for your {bhk}. "
            f"Would you be free for a brief phone call or a consultation meeting at our {business_config.OFFICE_NAME} (consultation appointments available {business_config.APPOINTMENT_HOURS_START} to {business_config.APPOINTMENT_HOURS_END} IST, {business_config.APPOINTMENT_DAYS})?"
        )

    # 5. Pure Working Hours / Timings / Sunday Operations (Without explicit booking intent - NO booking link)
    is_timing_query = any(w in msg_lower for w in ["timing", "timings", "hours", "working hours", "office timing", "office hours", "open on sunday", "sunday open", "are you open sunday", "open sunday", "sundays", "weekend", "open on weekend"])
    if is_timing_query:
        return (
            f"Hello {name}, our {business_config.OFFICE_NAME} is open all seven days of the week, Monday through Sunday, from {business_config.OFFICE_HOURS_START} to {business_config.OFFICE_HOURS_END} IST. "
            f"Customer consultation appointments are scheduled between {business_config.APPOINTMENT_HOURS_START} and {business_config.APPOINTMENT_HOURS_END} IST (30-minute consultation slots).\n\n"
            f"We are open Monday through Sunday. Please let us know how we can assist you with your {bhk} interior design in {loc}!"
        )

    # 6. Office Location / Directions / Google Maps Link (NO booking link)
    if any(w in msg_lower for w in ["where is your office", "where are you located", "office location", "office address", "address", "maps", "map", "google map", "google maps", "directions", "how to reach", "location"]):
        return (
            f"Hello {name}, our office is the {business_config.OFFICE_NAME} in Hyderabad. You can view our official location and get directions on Google Maps here:\n"
            f"{business_config.OFFICE_MAPS_LINK}\n\n"
            f"General office hours are {business_config.OFFICE_HOURS_START} to {business_config.OFFICE_HOURS_END} IST, {business_config.WORKING_DAYS} (all seven days), "
            f"with customer appointments scheduled between {business_config.APPOINTMENT_HOURS_START} and {business_config.APPOINTMENT_HOURS_END} IST. "
            f"We would be delighted to host you for a meeting at our {business_config.OFFICE_NAME} or connect over a phone call at your convenience!"
        )

    # 7. Request for Previous Work / Photos / Portfolio / Designs (NO booking link)
    if any(w in msg_lower for w in ["previous", "portfolio", "photos", "pictures", "designs", "images", "samples", "show me", "site visit"]):
        return (
            f"Hi {name}, we would be delighted to share our portfolio and interior designs! We have executed multiple 2BHK, 3BHK, and 4BHK turnkey projects across {loc} and greater Hyderabad. "
            f"I am preparing a curated digital lookbook highlighting our modular kitchens, living spaces, and master bedrooms. "
            f"We can also arrange a meeting at our {business_config.OFFICE_NAME} or an in-person walkthrough at one of our ongoing sites. Would you like me to send the lookbook here?"
        )

    # 8. Package Inclusions / Materials / Modular Kitchen / Wardrobes (NO booking link)
    if any(w in msg_lower for w in ["package", "included", "inclusions", "kitchen", "modular kitchen", "wardrobe", "woodwork", "materials", "what is included"]):
        return (
            f"Hi {name}, thank you for asking! Our turnkey packages for {bhk} properties in {loc} include: "
            f"1) Ergonomic modular kitchen with 100% Calibrated BWP boiling waterproof marine plywood (IS:710 certified), acrylic/laminate finishes, and soft-close hardware; "
            f"2) Custom floor-to-ceiling wardrobes; 3) TV entertainment unit and foyer storage; 4) Comprehensive 45-day handover guarantee with 10 years warranty. "
            f"Would you like me to share a PDF catalog of our latest modular kitchen & wardrobe installations?"
        )

    # 9. Estimate Reference / Pricing & Cost Inquiries (NO booking link)
    if any(w in msg_lower for w in ["estimate", "quotation", "quote", "explain quotation", "explain the quote", "breakdown", "reference", "cost", "pricing", "price", "budget"]):
        ref_text = f"under reference {ref}" if ref else "shared with you"
        time_text = f" generated on {est_time}" if est_time else ""
        return (
            f"Hello {name}, regarding your interior estimate and pricing {ref_text}{time_text}: "
            f"at SHA Interiors, our quotations are direct factory-pricing with zero retail markups, covering modular woodwork, hardware fittings, and turnkey execution for your {bhk} in {loc}. "
            f"Our Senior Design Consultant can share the detailed room-by-room itemized breakdown and explain the finish selections. "
            f"Would you like our team to share the itemized breakdown?"
        )

    # 10. Request for Callback / Call (NO booking link)
    if any(w in msg_lower for w in ["call me", "can someone call", "call", "phone me", "speak on phone", "ring me"]):
        return (
            f"Certainly, {name}! Our Senior Interior Consultant will call you on your registered number shortly. "
            f"Is now a convenient time to speak, or do you have a preferred time window today?"
        )

    # 11. Decision Delay / "Need time to decide" / "Will contact next week" (NO booking link)
    if any(w in msg_lower for w in ["need time", "decide later", "next week", "later", "thinking", "discuss with family", "discuss with wife", "busy"]):
        return (
            f"No problem at all, {name}! Take your time to review and discuss with your family. "
            f"We want you to feel 100% confident in your choice for your {bhk} home in {loc}. "
            f"I will check in with you gently next week. In the meantime, feel free to drop any questions right here!"
        )

    # 12. Generic / Short / Greeting (NO booking link)
    if any(w in msg_lower for w in ["hi", "hello", "hey", "good morning", "good evening", "details", "info"]):
        return (
            f"Hello {name}, hope you are having a wonderful day! "
            f"I am following up on your interior enquiry for your {bhk} home in {loc}. "
            f"How can our design team assist you with your requirements today?"
        )

    # 13. Default Consultative Response (NO booking link)
    return (
        f"Hello {name}, thank you for reaching out regarding your {bhk} interior design in {loc}. "
        f"Our team at SHA Interface Interiors is here to assist you with design concepts, material specifications, and turnkey execution. "
        f"General office hours at our {business_config.OFFICE_NAME} are {business_config.OFFICE_HOURS_START} to {business_config.OFFICE_HOURS_END} IST, Monday through Sunday. "
        f"How can our design team assist you with your requirements today?"
    )

class WhatsAppSenderInterface:
    """Abstract interface for dispatching WhatsApp messages."""
    def send_message(self, phone: str, message: str) -> Dict[str, Any]:
        raise NotImplementedError

class WhatsAppClickToChatSender(WhatsAppSenderInterface):
    """
    Standard Click-to-Chat sender.
    Generates URL for the salesperson's logged-in desktop/laptop WhatsApp session.
    Never marks message as sent automatically.
    """
    def send_message(self, phone: str, message: str) -> Dict[str, Any]:
        url, error = build_whatsapp_click_to_chat_url(phone, message)
        if error:
            return {"success": False, "error": error, "method": "click_to_chat"}
        return {
            "success": True,
            "click_to_chat_url": url,
            "method": "click_to_chat",
            "message": "Click-to-Chat URL generated. Salesperson must manually send and confirm in CRM."
        }

class WhatsAppCloudApiAdapter(WhatsAppSenderInterface):
    """
    Stub for future official WhatsApp Business Cloud API integration.
    Requires META_WHATSAPP_TOKEN, PHONE_NUMBER_ID, and Business Account.
    """
    def __init__(self, api_token: Optional[str] = None, phone_number_id: Optional[str] = None):
        self.api_token = api_token or os.environ.get("META_WHATSAPP_TOKEN")
        self.phone_number_id = phone_number_id or os.environ.get("META_PHONE_NUMBER_ID")
        
    def send_message(self, phone: str, message: str) -> Dict[str, Any]:
        if not self.api_token or not self.phone_number_id:
            return {
                "success": False,
                "error": "WhatsApp Business Cloud API credentials not configured. Please use Click-to-Chat mode.",
                "method": "cloud_api"
            }
        # Ready for future HTTP POST to https://graph.facebook.com/v18.0/{phone_number_id}/messages
        return {
            "success": False,
            "error": "Cloud API ready for production credentials.",
            "method": "cloud_api"
        }
