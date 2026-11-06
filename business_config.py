"""
business_config.py - Central Business Knowledge & Mandatory AI Communication Rules
SHA Interface Interiors - Hyderabad Edition

Single Source of Truth for:
1. Official business & office information (Miyapur office, general office hours, 7-day schedule, Google Maps link).
2. Customer appointment availability window: 2:00 PM to 5:00 PM IST, Monday through Sunday.
3. Confirmation policy: Manual confirmation by salesperson currently; automatic only after successful
   Google Calendar event creation in the future.
4. Mandatory AI communication rules applied consistently across WhatsApp assistant, Gemini prompts,
   outbound enquiry generator, and follow-up templates.
5. Compliant response generators and automated compliance validators (failing if appointments are offered 10 AM-2 PM or 5 PM-6 PM).
"""

from typing import Dict, List, Optional, Tuple, Any

# ==============================================================================
# 1. OFFICIAL BUSINESS INFORMATION
# ==============================================================================

BUSINESS_NAME = "SHA Interface Interiors"
OFFICE_NAME = "Miyapur office"

# Forbidden synonyms that must never be used
FORBIDDEN_OFFICE_TERMS = [
    "Hyderabad Studio",
    "hyderabad studio",
    "Hyderabad studio",
    "Experience Center",
    "experience center",
    "Flagship Center",
    "flagship center"
]

# General Office Operating Hours
OFFICE_HOURS_START = "10:00 AM"
OFFICE_HOURS_END = "6:00 PM"
WORKING_HOURS_START = "10:00 AM"
WORKING_HOURS_END = "6:00 PM"
TIMEZONE = "IST"
OFFICE_HOURS = "10:00 AM to 6:00 PM IST"
WORKING_HOURS = "10:00 AM to 6:00 PM IST"
WORKING_DAYS = "Monday through Sunday"
WORKING_DAYS_SUMMARY = "All seven days of the week, Monday through Sunday"

# ==============================================================================
# 2. CUSTOMER APPOINTMENT AVAILABILITY WINDOW
# ==============================================================================
# General office operates 10 AM to 6 PM, but customer appointment consultations
# are strictly scheduled between 2:00 PM and 5:00 PM IST, all 7 days.
APPOINTMENT_HOURS_START = "2:00 PM"
APPOINTMENT_HOURS_END = "5:00 PM"
APPOINTMENT_HOURS = "2:00 PM to 5:00 PM IST"
APPOINTMENT_DAYS = "Monday through Sunday"
APPOINTMENT_DAYS_SUMMARY = "All seven days of the week, Monday through Sunday"
APPOINTMENT_DURATION = "30 minutes"

# Disallowed appointment booking windows (appointments must NEVER be offered in these slots)
DISALLOWED_APPOINTMENT_SLOTS = [
    "10:00 AM to 2:00 PM",
    "5:00 PM to 6:00 PM",
    "10 AM to 2 PM",
    "5 PM to 6 PM",
    "10:00 AM to 6:00 PM",
    "10 AM to 6 PM"
]

# Official Google Maps Link - Never invent street addresses
OFFICE_MAPS_LINK = "https://maps.app.goo.gl/Ybuctd1ghqFiQ69D6"

# Official Digital Channels
OFFICIAL_WEBSITE = "https://www.sha-interiors-hyderabad.com"
OFFICIAL_INSTAGRAM = "https://www.instagram.com/madhusudhan_gonepelly/"

# Quotation Policy
QUOTATION_POLICY = (
    "Detailed final quotations are provided only after 3D design finalisation and agreed scope of work. "
    "Preliminary budget ranges may be discussed earlier, but final BOQ requires 3D layout finalisation."
)

# Primary Meeting Options
MEETING_OPTIONS = [
    f"Meeting at our {OFFICE_NAME}",
    "Convenient phone call"
]

# ==============================================================================
# 3. APPOINTMENT CONFIRMATION POLICY
# ==============================================================================
# Future Google Calendar confirmation must be automatic ONLY after successful event creation.
# Until Google Calendar is integrated, the existing manual salesperson confirmation workflow is retained.
GOOGLE_CALENDAR_BOOKING_LINK = "https://calendar.app.google/DMb8MRbZBz97gYbc8"
CALENDAR_INTEGRATION_STATUS = "manual_workflow_active"
APPOINTMENT_CONFIRMATION_POLICY = (
    "Until Google Calendar is integrated, all appointments require manual confirmation by the sales consultant. "
    "Future Google Calendar booking confirmation must be automatic only after successful event creation."
)

# Benchmark Canonical Customer Response (Automatic Google Calendar Booking Link Sharing)
EXAMPLE_CUSTOMER_RESPONSE = (
    "Certainly! We would be happy to welcome you to SHA Interface Interiors at our Miyapur office.\n\n"
    "Please use our booking link to view the available appointment slots and select a convenient date and time:\n\n"
    "https://calendar.app.google/DMb8MRbZBz97gYbc8\n\n"
    "Once you book a slot, your appointment will be confirmed through Google Calendar. We look forward to meeting you!"
)

EXAMPLE_MANUAL_CONSULTATION_RESPONSE = (
    "Thank you for your interest in SHA Interface Interiors! We would be happy to arrange a meeting at our Miyapur office or schedule a phone call to discuss your requirements.\n\n"
    "Our general office hours are 10:00 AM to 6:00 PM, Monday through Sunday, and customer consultation appointments are available from 2:00 PM to 5:00 PM IST.\n\n"
    "Please let us know your preferred date and time between 2:00 PM and 5:00 PM, and our team will assist you with confirming the appointment."
)

# Mandatory rules as a structured list
MANDATORY_RULES_LIST = [
    'Always refer to the office as "Miyapur office".',
    'Never call it "Hyderabad Studio".',
    "When discussing appointments, offer meeting options at the Miyapur office or a phone call.",
    "General office hours are 10:00 AM to 6:00 PM IST, all seven days of the week, Monday through Sunday.",
    "Customer appointment consultations are available ONLY from 2:00 PM to 5:00 PM IST, Monday through Sunday.",
    "When asking for an appointment time, request a preferred time strictly within 2:00 PM to 5:00 PM IST.",
    "NEVER offer or solicit appointments between 10:00 AM and 2:00 PM or between 5:00 PM and 6:00 PM.",
    "Use Indian Standard Time (IST).",
    "Never claim the office is closed on Sundays or other weekdays.",
    f"Do not invent the physical street address. Use the official Google Maps link when sharing directions: {OFFICE_MAPS_LINK}",
    "Do not promise an appointment is confirmed until the salesperson confirms it (or until future automatic Google Calendar event creation succeeds).",
    "Do NOT automatically include the Google Calendar booking link in every customer response. Include it ONLY when the customer explicitly asks to book an appointment, wants to visit the Miyapur office, asks for available meeting slots, or clearly requests a scheduled consultation or meeting.",
    "Do NOT include the booking link when customers ask ordinary questions about starting dates, completion timelines, handover duration, pricing, budget, materials, designs, progress, requirements, or general business information."
]


# ==============================================================================
# 4. REUSABLE AI SYSTEM INSTRUCTION PROMPT BLOCK
# ==============================================================================

AI_SYSTEM_INSTRUCTION_BLOCK = f"""
OFFICIAL BUSINESS KNOWLEDGE & MANDATORY COMMUNICATION RULES:
1. Business Name: {BUSINESS_NAME}
2. Office Name: {OFFICE_NAME} (MANDATORY: Always refer to the office as "{OFFICE_NAME}". NEVER call it "Hyderabad Studio", "Experience Center", or any other title).
3. General Office Hours: {OFFICE_HOURS} (10:00 AM to 6:00 PM Indian Standard Time, Monday through Sunday).
4. Customer Appointment Availability: {APPOINTMENT_HOURS} ({APPOINTMENT_HOURS_START} to {APPOINTMENT_HOURS_END} IST, Monday through Sunday). Appointment duration: {APPOINTMENT_DURATION}.
5. Working Days: {WORKING_DAYS_SUMMARY} (Open all 7 days of the week! Never claim the office is closed on Sundays or other weekdays).
6. Selective Google Calendar Booking Link Sharing Rule:
   CRITICAL RULE: Do NOT automatically include the Google Calendar booking link in every customer response.
   Include the official Google Calendar booking link ({GOOGLE_CALENDAR_BOOKING_LINK}) ONLY when:
   1. The customer explicitly asks to book an appointment.
   2. The customer wants to visit the Miyapur office.
   3. The customer asks for available meeting slots.
   4. The customer clearly requests a scheduled consultation or meeting.

   Do NOT include the booking link when customers ask ordinary questions about:
   - Project starting dates.
   - Project completion timelines.
   - Handover duration.
   - Pricing or budget.
   - Materials and designs.
   - Project progress or requirements.
   - General business information.

   For these conversations, answer the customer's actual question directly using verified SHA business information.
   Standard timeline response example: If a customer asks, "When can you start the project and how long will it take?", explain that work can start after design and scope finalisation, and that the standard apartment handover timeline for modular kitchens and wardrobes is 45 days after design approval, subject to site readiness. (DO NOT append the booking link or appointment invitation).

   When explicit appointment or visit criteria are met (points 1-4 above), provide the official Google Calendar booking link:
   {GOOGLE_CALENDAR_BOOKING_LINK}
   Standard response structure:
   "Certainly! We would be happy to welcome you to {BUSINESS_NAME} at our {OFFICE_NAME}.

   Please use our booking link to view the available appointment slots and select a convenient date and time:

   {GOOGLE_CALENDAR_BOOKING_LINK}

   Once you book a slot, your appointment will be confirmed through Google Calendar. We look forward to meeting you!"
   Customers must select from the slots actually available on Google Calendar. NEVER invent or promise an available appointment time.
7. Appointment Options: When discussing appointments or meetings, offer two options: an in-person meeting at our {OFFICE_NAME} or a convenient phone call.
8. Preferred Time Request: When asking for appointment preferences manually, ALWAYS request a preferred date and time strictly within {APPOINTMENT_HOURS} ({APPOINTMENT_HOURS_START} to {APPOINTMENT_HOURS_END}).
   CRITICAL RESTRICTION: NEVER offer, solicit, or suggest appointments between 10:00 AM and 2:00 PM or between 5:00 PM and 6:00 PM.
9. Confirmation Boundary: Do not promise an appointment is confirmed until the salesperson confirms it. (Future Google Calendar booking confirmation will be automatic ONLY after successful event creation; until Google Calendar is integrated, retain the existing manual confirmation workflow).
10. Location & Directions: Do NOT invent a physical street address. Always share the official Google Maps link: {OFFICE_MAPS_LINK}
11. Official Digital Channels: Website: {OFFICIAL_WEBSITE} | Instagram: {OFFICIAL_INSTAGRAM}
12. Quotation Policy: Detailed final quotations are provided only after 3D design finalisation and agreed scope of work. Preliminary budget ranges may be discussed earlier, but final BOQ requires 3D layout finalisation.
13. Customer Data Isolation: Every customer's requirements, property specifications, and budget must remain strictly isolated. Never confuse or cross-pollinate details between different clients.
"""


# ==============================================================================
# 5. HELPER FUNCTIONS & CANONICAL PHRASINGS
# ==============================================================================

def get_business_info() -> Dict[str, Any]:
    """Returns official business info dictionary."""
    return {
        "business_name": BUSINESS_NAME,
        "office_name": OFFICE_NAME,
        "office_hours": OFFICE_HOURS,
        "office_hours_start": OFFICE_HOURS_START,
        "office_hours_end": OFFICE_HOURS_END,
        "working_hours": WORKING_HOURS,
        "working_hours_start": WORKING_HOURS_START,
        "working_hours_end": WORKING_HOURS_END,
        "appointment_hours": APPOINTMENT_HOURS,
        "appointment_hours_start": APPOINTMENT_HOURS_START,
        "appointment_hours_end": APPOINTMENT_HOURS_END,
        "timezone": TIMEZONE,
        "working_days": WORKING_DAYS,
        "working_days_summary": WORKING_DAYS_SUMMARY,
        "appointment_days": APPOINTMENT_DAYS,
        "appointment_days_summary": APPOINTMENT_DAYS_SUMMARY,
        "calendar_integration_status": CALENDAR_INTEGRATION_STATUS,
        "appointment_confirmation_policy": APPOINTMENT_CONFIRMATION_POLICY,
        "office_maps_link": OFFICE_MAPS_LINK,
        "meeting_options": MEETING_OPTIONS,
        "example_customer_response": EXAMPLE_CUSTOMER_RESPONSE,
        "official_website": OFFICIAL_WEBSITE,
        "official_instagram": OFFICIAL_INSTAGRAM,
        "quotation_policy": QUOTATION_POLICY
    }



def should_include_calendar_booking_link(incoming_msg: str) -> bool:
    """
    Determines whether a customer's message meets the strict criteria for sharing the Google Calendar booking link.
    Include the booking link ONLY when:
    1. The customer explicitly asks to book an appointment.
    2. The customer wants to visit the Miyapur office.
    3. The customer asks for available meeting slots.
    4. The customer clearly requests a scheduled consultation or meeting.

    Strictly EXCLUDE ordinary questions about:
    - Project starting dates.
    - Project completion timelines.
    - Handover duration.
    - Pricing or budget.
    - Materials and designs.
    - Project progress or requirements.
    - General business information.
    """
    if not incoming_msg or not incoming_msg.strip():
        return False

    msg_lower = incoming_msg.lower().strip()

    # Explicit phrases for criteria 1 - 4
    explicit_triggers = [
        # 1. Explicitly asks to book an appointment
        "book an appointment", "book appointment", "booking an appointment",
        "want an appointment", "need an appointment", "make an appointment",
        "appointment booking", "can i book an appointment", "how do i book an appointment",
        "schedule an appointment", "schedule appointment", "scheduling an appointment",
        "can i schedule an appointment", "want to schedule an appointment",
        # 2. Wants to visit the Miyapur office
        "visit your office", "visit the office", "visit office", "visiting your office",
        "visiting the office", "want to visit", "like to visit", "can i visit", "can we visit",
        "come to office", "come to your office", "coming to office", "coming to your office",
        "coming to the office", "come to the office", "coming to miyapur office",
        "come to miyapur office", "visit miyapur office", "office visit", "visit in person",
        "walk into your office", "when can i visit", "when can we visit", "when can i come", "when can we come",
        # 3. Asks for available meeting slots
        "available meeting slots", "available slots", "meeting slots", "available appointment slots",
        "slots available", "slots are available", "what slots", "which slots",
        "available timings for meeting", "available times for meeting", "open slots",
        "book a slot", "book slot", "booking slot", "reserve a slot",
        # 4. Clearly requests a scheduled consultation or meeting
        "schedule a meeting", "schedule meeting", "scheduling a meeting",
        "arrange a meeting", "book a meeting", "meet your team", "meet the team",
        "meet sha interiors team", "meet with your team", "meet with the team",
        "meet you in person", "meet in person", "when can we meet", "when can i meet",
        "can i meet your team", "can we meet", "want to meet", "like to meet",
        "schedule a consultation", "schedule consultation", "scheduling a consultation",
        "book a consultation", "book consultation", "booking a consultation",
        "consultation appointment"
    ]

    has_explicit = any(phrase in msg_lower for phrase in explicit_triggers)
    if not has_explicit:
        return False

    # Check for ordinary duration/timeline questions about the appointment itself
    duration_of_appointment_queries = [
        "how long does the meeting take", "how long is the consultation",
        "how long will the appointment take", "duration of appointment", "duration of meeting"
    ]
    if any(q in msg_lower for q in duration_of_appointment_queries):
        return False

    return True


def format_calendar_booking_response(customer_name: Optional[str] = None) -> str:
    """
    Generates standard, friendly response sharing the official Google Calendar booking link
    when a customer expresses interest in visiting the office, meeting the team, or scheduling an appointment.
    """
    return (
        f"Certainly! We would be happy to welcome you to {BUSINESS_NAME} at our {OFFICE_NAME}.\n\n"
        f"Please use our booking link to view the available appointment slots and select a convenient date and time:\n\n"
        f"{GOOGLE_CALENDAR_BOOKING_LINK}\n\n"
        f"Once you book a slot, your appointment will be confirmed through Google Calendar. We look forward to meeting you!"
    )


def format_appointment_invitation(customer_name: Optional[str] = None, project_type: Optional[str] = None) -> str:
    """Generates standard appointment invitation requesting appointments strictly within 2:00 PM to 5:00 PM IST."""
    salutation = f"Hello {customer_name}," if customer_name else "Hello,"
    prop_clause = f" for your {project_type}" if project_type else ""
    return (
        f"{salutation}\n\n"
        f"Thank you for your interest in {BUSINESS_NAME}! We would be delighted to arrange a meeting at our {OFFICE_NAME} "
        f"or schedule a convenient phone call to understand your requirements{prop_clause} in more detail.\n\n"
        f"Our general office hours are {OFFICE_HOURS_START} to {OFFICE_HOURS_END} IST, {WORKING_DAYS} (all seven days), "
        f"with customer consultation appointments available between {APPOINTMENT_HOURS_START} and {APPOINTMENT_HOURS_END} IST.\n\n"
        f"Please let us know your preferred date and time between {APPOINTMENT_HOURS_START} and {APPOINTMENT_HOURS_END}, "
        f"and our team will assist you with confirming the appointment."
    )


def format_directions_response(customer_name: Optional[str] = None) -> str:
    """Generates standard directions response with the official Google Maps link."""
    salutation = f"Hello {customer_name}," if customer_name else "Hello,"
    return (
        f"{salutation}\n\n"
        f"Our office is the {OFFICE_NAME} in Hyderabad. You can view our official location and get directions on Google Maps here:\n"
        f"{OFFICE_MAPS_LINK}\n\n"
        f"General office hours are {OFFICE_HOURS_START} to {OFFICE_HOURS_END} IST, {WORKING_DAYS} (all seven days), "
        f"with customer appointments scheduled between {APPOINTMENT_HOURS_START} and {APPOINTMENT_HOURS_END} IST. "
        f"We look forward to meeting you at our {OFFICE_NAME} or speaking over a phone call at your convenience!"
    )


def format_sunday_hours_response(customer_name: Optional[str] = None) -> str:
    """Generates explicit clarification confirming 7-day operations including Sunday with 2 PM - 5 PM appointments."""
    salutation = f"Hello {customer_name}," if customer_name else "Hello,"
    return (
        f"{salutation}\n\n"
        f"Yes! Our {OFFICE_NAME} is open all seven days of the week, Monday through Sunday, from {OFFICE_HOURS_START} to {OFFICE_HOURS_END} IST. "
        f"Customer consultation appointments are scheduled between {APPOINTMENT_HOURS_START} and {APPOINTMENT_HOURS_END} IST.\n\n"
        f"We would be happy to arrange a meeting at our {OFFICE_NAME} on Sunday or schedule a convenient phone call. "
        f"Please let us know your preferred time between {APPOINTMENT_HOURS_START} and {APPOINTMENT_HOURS_END}, and our team will assist you with the appointment."
    )


# ==============================================================================
# 6. COMPLIANCE VALIDATOR (EXPLICITLY FAILS IF APPOINTMENTS OFFER 10 AM-2 PM OR 5 PM-6 PM)
# ==============================================================================

def validate_message_compliance(message_text: str) -> Tuple[bool, List[str]]:
    """
    Validates whether an AI or template-generated response satisfies mandatory business rules.
    Explicitly fails if customer appointment messages offer 10 AM–2 PM or 5 PM–6 PM.
    Returns (is_compliant, list_of_violations).
    """
    violations = []
    text_lower = message_text.lower()

    # Rule 2: Never call it "Hyderabad Studio"
    if "hyderabad studio" in text_lower:
        violations.append('Violated Rule 2: Refers to office as "Hyderabad Studio" instead of "Miyapur office".')

    # If studio is used as an office name
    if "our studio" in text_lower or "visit our studio" in text_lower or "the studio" in text_lower:
        violations.append('Violated Rule 1: Uses generic "studio" instead of "Miyapur office".')

    # Rule 7: Never claim office is closed on Sundays or weekends
    closed_triggers = [
        "closed on sunday", "closed on sundays", "closed sunday", "closed sundays",
        "closed on weekend", "closed on weekends", "we are closed on sunday",
        "office is closed on sunday", "not open on sunday"
    ]
    for ct in closed_triggers:
        if ct in text_lower:
            violations.append(f"Violated Rule 7: Claims office is closed on Sunday ('{ct}'). Office is open all 7 days.")

    # Rule: Check customer appointment availability restriction (2 PM to 5 PM ONLY)
    is_appointment_context = any(term in text_lower for term in [
        "appointment", "schedule a meeting", "schedule meeting", "book appointment",
        "meeting at our miyapur office", "arrange a meeting", "consultation", "preferred date and time",
        "suitable time", "preferred time", "meet you", "meet at", "meeting", "meet"
    ])

    if is_appointment_context:
        # Forbidden appointment offering phrases (10 AM to 2 PM or 5 PM to 6 PM)
        disallowed_offerings = [
            "between 10:00 am and 6:00 pm", "between 10 am and 6 pm",
            "10:00 am to 6:00 pm for appointment", "10 am to 6 pm for appointment",
            "appointments from 10:00 am to 6:00 pm", "appointments from 10 am to 6 pm",
            "appointments available 10:00 am to 6:00 pm", "appointments available 10 am to 6 pm",
            "appointments are available from 10:00 am to 6:00 pm", "appointments are available 10 am to 6 pm",
            "between 10:00 am and 2:00 pm", "between 10 am and 2 pm",
            "10:00 am to 2:00 pm", "10 am to 2 pm",
            "10:00am to 2:00pm", "10am to 2pm",
            "10:00 am - 2:00 pm", "10 am - 2 pm",
            "10:00 am to 1:00 pm", "10 am to 1 pm",
            "10:00 am to 12:00 pm", "10 am to 12 pm",
            "between 5:00 pm and 6:00 pm", "between 5 pm and 6 pm",
            "5:00 pm to 6:00 pm", "5 pm to 6 pm",
            "5:00pm to 6:00pm", "5pm to 6pm",
            "5:00 pm - 6:00 pm", "5 pm - 6 pm",
            "appointment at 10", "appointment at 11", "appointment at 12", "appointment at 1 pm",
            "appointment at 5:30", "appointment at 6",
            "meeting at 10 am", "meeting at 11 am", "meeting at 12 pm", "meeting at 1 pm",
            "meeting at 5:30 pm", "meeting at 6 pm"
        ]
        
        # Check if text specifically solicits or offers appointment times outside 2 PM to 5 PM
        for slot in disallowed_offerings:
            if slot in text_lower:
                violations.append(f"Violated Rule 2 & 3: Customer appointment offered outside permitted window ('{slot}'). Appointments must strictly be within 2 PM to 5 PM IST.")

        # If it requests appointment time manually without booking link, it MUST mention 2 PM to 5 PM
        if GOOGLE_CALENDAR_BOOKING_LINK not in message_text:
            if ("preferred date and time" in text_lower or "preferred time" in text_lower or "suitable time" in text_lower) and any(w in text_lower for w in ["appointment", "meeting", "consultation", "schedule", "connect"]):
                if "2:00 pm" not in text_lower and "2 pm" not in text_lower and "2:00 pm to 5:00 pm" not in text_lower:
                    violations.append("Violated Rule 3: Appointment request does not specify the mandatory 2 PM to 5 PM window.")

    # Rule: If booking link is shared, verify exact official URL
    if "booking link" in text_lower or "calendar.app.google" in text_lower:
        if GOOGLE_CALENDAR_BOOKING_LINK not in message_text:
            violations.append(f"Violated Booking Rule: Calendar booking link mentioned without using official URL: {GOOGLE_CALENDAR_BOOKING_LINK}")

    # Rule: Do not include booking link in ordinary timeline, pricing, or material responses
    is_ordinary_topic = any(t in text_lower for t in [
        "handover timeline for modular kitchens", "standard apartment handover timeline",
        "45 days after design approval", "calibrated bwp marine plywood"
    ])
    if is_ordinary_topic and GOOGLE_CALENDAR_BOOKING_LINK in message_text:
        violations.append("Violated Booking Link Rule: Booking link was included in an ordinary question response (timeline/materials/pricing).")

    # Rule 8: If maps link is shared, verify exact official URL
    if "maps" in text_lower or "google.com/maps" in text_lower or "maps.app.goo.gl" in text_lower:
        if OFFICE_MAPS_LINK not in message_text:
            violations.append(f"Violated Rule 8: Maps mentioned without using official link: {OFFICE_MAPS_LINK}")

    # Check for hallucinated street addresses
    street_hallucinations = ["road no", "road number", "plot no", "jubilee hills check post", "hitech city main road"]
    for sh in street_hallucinations:
        if sh in text_lower:
            violations.append(f"Violated Rule 8: Invented physical street address ('{sh}') instead of official Maps link.")

    return len(violations) == 0, violations
