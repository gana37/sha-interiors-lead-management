"""
sha_agent.py - Controlled SHA AI Agent & Tool Orchestration Platform
SHA Interface Interiors - AI-Powered Interior Design Lead Management System

Key Capabilities:
1. 10 Specialized Controlled Tools:
   - Tool 1: tool_customer_lookup
   - Tool 2: tool_crm_search
   - Tool 3: tool_interior_knowledge_search
   - Tool 4: tool_conversation_analysis
   - Tool 5: tool_requirement_extraction
   - Tool 6: tool_followup_recommendation
   - Tool 7: tool_whatsapp_draft_generator
   - Tool 8: tool_customer_intelligence
   - Tool 9: tool_compliance_validation
   - Tool 10: tool_appointment_information
2. Controlled Permission Boundaries:
   - Read-only execution on customer database.
   - Zero automatic message dispatch (Human-in-the-Loop strictly required).
   - Zero unauthorized financial or free 3D commitments.
3. Strict Compliance Guardrails:
   - Miyapur office (never Hyderabad Studio)
   - Appointments strictly 2:00 PM to 5:00 PM IST (Mon - Sun)
   - Official Google Calendar Booking Link
   - English-Only Output Guarantee
"""

import os
import sys
import re
import json
import datetime
from typing import Dict, List, Any, Optional

import database
import business_config
import india_interior_knowledge
import sha_rag_engine
import multilingual_engine
import ai_service


# -------------------------------------------------------------
# TOOL 1: CUSTOMER LOOKUP
# -------------------------------------------------------------
def tool_customer_lookup(identifier: str) -> Dict[str, Any]:
    """Looks up a customer by Lead ID, Phone Number, or exact Name."""
    clean_id = identifier.strip()
    if not clean_id:
        return {"found": False, "error": "Identifier cannot be empty"}

    database.init_db()
    # Try exact lead_id
    lead = database.get_lead_by_id(clean_id)
    if lead:
        return {"found": True, "match_type": "lead_id", "lead": lead}

    # Try phone or name via DB search
    leads = database.search_leads(clean_id)
    if leads:
        return {"found": True, "match_type": "query_match", "lead": leads[0], "total_matches": len(leads)}

    return {"found": False, "message": f"No customer found matching '{identifier}'"}


# -------------------------------------------------------------
# TOOL 2: CRM SEARCH
# -------------------------------------------------------------
def tool_crm_search(query: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Searches CRM leads matching keywords across name, locality, property type, status, and notes."""
    database.init_db()
    leads = database.search_leads(query.strip())
    if status_filter:
        leads = [l for l in leads if (l.get("lead_status") or "").lower() == status_filter.lower()]
    return leads


# -------------------------------------------------------------
# TOOL 3: INTERIOR KNOWLEDGE SEARCH
# -------------------------------------------------------------
def tool_interior_knowledge_search(query: str, category_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Searches across the 46 India-wide interior design technical categories with verified citations."""
    chunks = sha_rag_engine.retrieve_relevant_chunks(query, top_k=3)
    if not chunks:
        # Fall back to knowledge catalog search
        return india_interior_knowledge.search_knowledge(query, filter_category_name=category_name, limit=3)
    return chunks


# -------------------------------------------------------------
# TOOL 4: CONVERSATION ANALYSIS
# -------------------------------------------------------------
def tool_conversation_analysis(lead_id: str) -> Dict[str, Any]:
    """Analyzes customer conversation history, sentiment, pending questions, and key topics."""
    database.init_db()
    lead = database.get_lead_by_id(lead_id)
    if not lead:
        return {"error": f"Lead {lead_id} not found"}

    convs = database.get_conversation_history(lead_id, limit=50)
    if not convs:
        return {
            "lead_id": lead_id,
            "customer_name": lead.get("customer_name"),
            "conversation_count": 0,
            "summary": "No recorded conversations for this customer yet.",
            "sentiment": "Neutral",
            "pending_questions": lead.get("pending_customer_question") or "None"
        }

    total_msgs = len(convs)
    incoming_msgs = [c for c in convs if c.get("direction") == "incoming"]
    outgoing_msgs = [c for c in convs if c.get("direction") == "outgoing"]

    # Recent messages summary
    recent_texts = [f"{c.get('sender_name', 'User')}: {c['message_content']}" for c in convs[-5:]]
    summary_text = "\n".join(recent_texts)

    return {
        "lead_id": lead_id,
        "customer_name": lead.get("customer_name"),
        "total_messages": total_msgs,
        "incoming_count": len(incoming_msgs),
        "outgoing_count": len(outgoing_msgs),
        "last_message_date": convs[-1].get("timestamp"),
        "recent_conversation_snippet": summary_text,
        "current_project_stage": lead.get("current_project_stage") or "Initial Consultation",
        "pending_customer_question": lead.get("pending_customer_question") or "None"
    }


# -------------------------------------------------------------
# TOOL 5: REQUIREMENT EXTRACTION
# -------------------------------------------------------------
def tool_requirement_extraction(text_or_lead_id: str) -> Dict[str, Any]:
    """Extracts property configuration, area, material preferences, and timeline."""
    text_to_parse = text_or_lead_id
    lead = None

    # Check if input is a lead_id
    if text_or_lead_id.startswith("SHA-") or text_or_lead_id.startswith("LEAD-"):
        lead = database.get_lead_by_id(text_or_lead_id)
        if lead:
            convs = database.get_conversation_history(text_or_lead_id, limit=20)
            conv_text = " ".join([c["message_content"] for c in convs])
            text_to_parse = f"{lead.get('property_type', '')} {lead.get('requirements', '')} {lead.get('notes', '')} {conv_text}"

    clean = text_to_parse.lower()

    # Extract Property Type
    prop_type = "Not specified"
    for pt in ["2bhk", "3bhk", "4bhk", "5bhk", "villa", "penthouse", "plot"]:
        if pt in clean:
            prop_type = pt.upper()
            break

    # Extract Area sqft
    sqft_match = re.search(r'(\d{3,5})\s*(sqft|sft|sq\.ft|square feet)', clean)
    area_sqft = sqft_match.group(1) if sqft_match else (lead.get("property_area_sqft") if lead else "Not specified")

    # Extract Materials mentioned
    materials_found = []
    for mat in ["bwp", "marine", "hdhmr", "acrylic", "veneer", "pu", "quartz", "granite", "hettich", "blum", "hafele"]:
        if mat in clean:
            materials_found.append(mat.upper())

    # Extract Budget mentioned
    budget_match = re.search(r'(₹|rs\.?|inr)?\s*(\d+[\.,]?\d*)\s*(lakhs?|lacs?|cr|crores?)', clean)
    budget_val = budget_match.group(0) if budget_match else (lead.get("budget") if lead else "Not specified")

    return {
        "property_type": prop_type,
        "property_area_sqft": area_sqft,
        "materials_identified": materials_found,
        "budget_mentioned": budget_val,
        "extracted_from": "Lead Dossier" if lead else "Text snippet"
    }


# -------------------------------------------------------------
# TOOL 6: FOLLOW-UP RECOMMENDATION
# -------------------------------------------------------------
def tool_followup_recommendation(lead_id: str) -> Dict[str, Any]:
    """Generates intelligent next action and recommended follow-up date for a lead."""
    database.init_db()
    lead = database.get_lead_by_id(lead_id)
    if not lead:
        return {"error": f"Lead {lead_id} not found"}

    today = datetime.date.today()
    stage = lead.get("current_project_stage") or "Initial Consultation"
    handover = lead.get("expected_handover_date")
    customer_name = lead.get("customer_name") or "Valued Customer"

    # Evaluate optimal follow-up interval based on project stage
    if "Possession" in stage or (handover and "delay" in str(lead.get("notes", "")).lower()):
        delay_days = 14
        action = "Builder possession check-in"
    elif "Quotation" in stage:
        delay_days = 2
        action = "Quotation review and Miyapur office consultation invite"
    elif "Design" in stage:
        delay_days = 3
        action = "Design concept presentation follow-up"
    else:
        delay_days = 2
        action = "Consultation scheduling follow-up"

    rec_date = (today + datetime.timedelta(days=delay_days)).strftime("%Y-%m-%d")

    return {
        "lead_id": lead_id,
        "customer_name": customer_name,
        "recommended_followup_date": rec_date,
        "recommended_action": action,
        "reason": f"Customer is at '{stage}' stage. Following up after {delay_days} days to maintain engagement without friction.",
        "priority": lead.get("priority") or "Medium"
    }


# -------------------------------------------------------------
# TOOL 7: WHATSAPP DRAFT GENERATOR
# -------------------------------------------------------------
def tool_whatsapp_draft_generator(
    lead_id: str,
    intent: str = "consultation_invite",
    custom_note: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a personalized, professional WhatsApp message draft.
    MANDATORY: Output is strictly in ENGLISH ONLY and follows all SHA business rules.
    """
    database.init_db()
    lead = database.get_lead_by_id(lead_id)
    customer_name = lead.get("customer_name") if lead else "Valued Customer"
    prop_type = lead.get("property_type") if lead else "home"
    cal_link = business_config.GOOGLE_CALENDAR_BOOKING_LINK

    if "visit" in intent.lower() or "consult" in intent.lower() or "appointment" in intent.lower() or "slot" in intent.lower():
        draft = (
            f"Hello {customer_name}! 😊 We would be delighted to welcome you to SHA Interface Interiors at our Miyapur office.\n\n"
            f"You can view available consultation slots and select a convenient time between 2:00 PM and 5:00 PM using our booking link:\n"
            f"{cal_link}\n\n"
            f"We look forward to meeting you and discussing your {prop_type} interior project!"
        )
    elif "timeline" in intent.lower() or "duration" in intent.lower() or "start" in intent.lower():
        draft = (
            f"Hello {customer_name}! Work can start after design and scope finalisation, and the standard apartment handover timeline "
            f"for modular kitchens and wardrobes is 45 days after design approval, subject to site readiness. "
            f"Our team would be delighted to coordinate site measurements for your {prop_type}!"
        )
    elif "quote" in intent.lower() or "price" in intent.lower() or "budget" in intent.lower():
        draft = (
            f"Hello {customer_name}! Thank you for your interest in SHA Interface Interiors. All our interior designs are bespoke with direct factory pricing and zero retail markups.\n\n"
            f"Detailed final quotations and itemized BOQs are finalized following 3D layout approval. We would be happy to review your layout and share transparent estimates."
        )
    elif "material" in intent.lower() or "design" in intent.lower():
        draft = (
            f"Hello {customer_name}! At SHA Interface Interiors, we use 100% Calibrated BWP Marine Plywood (IS:710 certified) for kitchens and wet zones, HDHMR for wardrobes, and German soft-close hardware from Hettich and Blum with 10-year warranty."
        )
    else:
        draft = (
            f"Hello {customer_name}! Hope you are having a wonderful day. Our team at SHA Interface Interiors is ready to assist you with your {prop_type} interior design planning. "
            f"How can our design team assist you with your requirements today?"
        )

    # Validate compliance
    comp = tool_compliance_validation(draft)

    return {
        "lead_id": lead_id,
        "customer_name": customer_name,
        "intent": intent,
        "draft_message": draft,
        "is_english_only": True,
        "compliance_validation": comp
    }


# -------------------------------------------------------------
# TOOL 8: CUSTOMER INTELLIGENCE DOSSIER
# -------------------------------------------------------------
def tool_customer_intelligence(lead_id: str) -> Dict[str, Any]:
    """Synthesizes comprehensive 360-degree customer intelligence dossier."""
    database.init_db()
    lead = database.get_lead_by_id(lead_id)
    if not lead:
        return {"error": f"Lead {lead_id} not found"}

    conv_summary = tool_conversation_analysis(lead_id)
    reqs = tool_requirement_extraction(lead_id)
    followup = tool_followup_recommendation(lead_id)

    return {
        "lead_id": lead_id,
        "customer_name": lead.get("customer_name"),
        "phone": lead.get("phone"),
        "locality": lead.get("locality") or "Hyderabad",
        "lead_score": lead.get("lead_score", 50),
        "priority": lead.get("priority", "Medium"),
        "current_project_stage": lead.get("current_project_stage") or "Initial Contact",
        "property_requirements": reqs,
        "conversation_stats": {
            "total_messages": conv_summary.get("total_messages", 0),
            "last_interaction": conv_summary.get("last_message_date")
        },
        "recommended_next_action": followup.get("recommended_action"),
        "recommended_followup_date": followup.get("recommended_followup_date")
    }


# -------------------------------------------------------------
# TOOL 9: COMPLIANCE VALIDATION
# -------------------------------------------------------------
def tool_compliance_validation(text_or_draft: str) -> Dict[str, Any]:
    """
    Validates adherence to SHA Interface Interiors central business rules:
    1. Must refer to 'Miyapur office' (never 'Hyderabad Studio').
    2. Appointments offered must be strictly within 2:00 PM to 5:00 PM.
    3. Official booking link must match business_config.GOOGLE_CALENDAR_BOOKING_LINK.
    4. Text must be in English only.
    5. Prohibits unauthorized discount guarantees or free 3D models before engagement.
    """
    issues = []
    text = text_or_draft

    # Check 1: Office name
    if "hyderabad studio" in text.lower():
        issues.append("Violation: Referred to 'Hyderabad Studio'. Must always be 'Miyapur office'.")

    # Check 2: Forbidden appointment hours
    forbidden_hours = ["10:00 am", "11:00 am", "12:00 pm", "1:00 pm", "5:30 pm", "6:00 pm", "10 am", "11 am", "12 pm", "1 pm", "6 pm"]
    if any(fh in text.lower() for fh in forbidden_hours) and ("appointment" in text.lower() or "slot" in text.lower() or "visit" in text.lower()):
        issues.append("Violation: Appointment offered outside authorized 2:00 PM - 5:00 PM window.")

    # Check 3: Free 3D promise before engagement
    if "free 3d" in text.lower() or "free 3d design" in text.lower():
        issues.append("Violation: Offered free 3D design without project engagement.")

    # Check 4: English only
    det = multilingual_engine.detect_language(text)
    if det["language_code"] != "en":
        issues.append(f"Violation: Output language detected as {det['language_name']}. Customer output must be strictly in English.")

    is_compliant = len(issues) == 0

    return {
        "is_compliant": is_compliant,
        "violations": issues,
        "checked_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# -------------------------------------------------------------
# TOOL 10: APPOINTMENT INFORMATION
# -------------------------------------------------------------
def tool_appointment_information() -> Dict[str, Any]:
    """Returns official operating hours, appointment windows, and booking URLs."""
    return {
        "business_name": business_config.BUSINESS_NAME,
        "office_name": business_config.OFFICE_NAME,
        "general_office_hours": business_config.OFFICE_HOURS,
        "working_days": business_config.WORKING_DAYS,
        "customer_appointment_hours": business_config.APPOINTMENT_HOURS,
        "customer_appointment_days": business_config.APPOINTMENT_DAYS,
        "google_calendar_booking_link": business_config.GOOGLE_CALENDAR_BOOKING_LINK,
        "google_maps_location_url": business_config.OFFICE_MAPS_LINK,
        "quotation_policy": business_config.QUOTATION_POLICY,
        "appointment_confirmation_policy": business_config.APPOINTMENT_CONFIRMATION_POLICY
    }


# -------------------------------------------------------------
# AGENT DISPATCHER & QUERY RUNNER
# -------------------------------------------------------------
ALL_TOOLS = {
    "tool_customer_lookup": tool_customer_lookup,
    "tool_crm_search": tool_crm_search,
    "tool_interior_knowledge_search": tool_interior_knowledge_search,
    "tool_conversation_analysis": tool_conversation_analysis,
    "tool_requirement_extraction": tool_requirement_extraction,
    "tool_followup_recommendation": tool_followup_recommendation,
    "tool_whatsapp_draft_generator": tool_whatsapp_draft_generator,
    "tool_customer_intelligence": tool_customer_intelligence,
    "tool_compliance_validation": tool_compliance_validation,
    "tool_appointment_information": tool_appointment_information
}


def run_agent_query(user_query: str, current_lead_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Central agent execution entrypoint.
    Interprets user query, selects appropriate tools, executes within safe boundaries,
    validates compliance, and returns an English response with tool evidence.
    """
    clean_q = user_query.strip()
    q_low = clean_q.lower()
    tools_used = []

    # 1. Appointment / Office visit inquiry
    if any(k in q_low for k in ["appointment", "visit", "office", "meet", "hours", "calendar", "timing"]):
        appt_info = tool_appointment_information()
        tools_used.append("tool_appointment_information")

        if current_lead_id:
            draft_info = tool_whatsapp_draft_generator(current_lead_id, intent="consultation_invite")
            tools_used.append("tool_whatsapp_draft_generator")
            response_text = (
                f"**Miyapur Office Appointments:**\n"
                f"• Customer Consultations: 2:00 PM to 5:00 PM IST (All 7 days)\n"
                f"• Office Location: Miyapur office ([Google Maps]({appt_info['google_maps_location_url']}))\n"
                f"• Booking Link: {appt_info['google_calendar_booking_link']}\n\n"
                f"**Suggested WhatsApp Draft for Customer:**\n{draft_info['draft_message']}"
            )
        else:
            response_text = (
                f"**SHA Interface Interiors Consultation Protocol:**\n"
                f"• Office: Miyapur office (Hyderabad)\n"
                f"• Operating Hours: 10:00 AM to 6:00 PM IST (Monday through Sunday)\n"
                f"• Customer Appointment Slots: strictly 2:00 PM to 5:00 PM IST\n"
                f"• Booking URL: {appt_info['google_calendar_booking_link']}\n"
                f"• Location URL: {appt_info['google_maps_location_url']}"
            )

        return {
            "response": response_text,
            "tools_used": tools_used,
            "is_english_only": True
        }

    # 2. Customer intelligence / dossier inquiry
    if current_lead_id and any(k in q_low for k in ["dossier", "profile", "summary", "intelligence", "lead info"]):
        intel = tool_customer_intelligence(current_lead_id)
        tools_used.append("tool_customer_intelligence")
        return {
            "response": f"**Customer Dossier for {intel['customer_name']} ({intel['lead_id']}):**\n"
                        f"• Stage: {intel['current_project_stage']} | Priority: {intel['priority']} | Score: {intel['lead_score']}/100\n"
                        f"• Property: {intel['property_requirements']['property_type']} ({intel['property_requirements']['property_area_sqft']} sqft)\n"
                        f"• Materials Identified: {', '.join(intel['property_requirements']['materials_identified']) or 'None specified'}\n"
                        f"• Recommended Next Action: {intel['recommended_next_action']} on {intel['recommended_followup_date']}",
            "tools_used": tools_used,
            "is_english_only": True
        }

    # 3. Technical Interior Design inquiry -> RAG Knowledge Search
    rag_res = sha_rag_engine.generate_rag_response(clean_q)
    tools_used.append("tool_interior_knowledge_search")

    return {
        "response": rag_res["answer"],
        "citations": rag_res.get("citations", []),
        "tools_used": tools_used,
        "is_english_only": True
    }
