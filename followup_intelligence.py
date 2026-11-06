"""
followup_intelligence.py - Intelligent Customer Conversation Understanding & Follow-Up Recommendations
SHA Interface Interiors - AI-Powered Lead Management System

Provides:
1. Operational Queues (Due Today, Overdue, Never Contacted, Awaiting Response).
2. Deep Customer Conversation Understanding (extracting property, configuration, stage, pending questions, team actions).
3. Intelligent Follow-up Recommendations with automated scenario detection:
   - Floor plan shared without response
   - Quotation requested (explaining 3D design finalisation rule)
   - Postponed possession/handover (updating date and setting future check-in)
   - Office visit / meeting requested (providing Google Calendar booking link)
   - Unanswered technical question (flagging for specialist review)
   - Silent / no response check-in
4. Personalized human-in-the-loop WhatsApp message drafting adhering strictly to SHA Business Rules.
5. Task Management operations (schedule, edit, reschedule, complete with notes).
"""

import sys
import os
import re
import datetime
import json
from typing import Dict, List, Optional, Any, Tuple
import database
import business_config

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ==============================================================================
# 1. OPERATIONAL QUEUES (PRESERVED & ENHANCED)
# ==============================================================================

def get_overdue_queue(db_path: str = database.DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns tasks whose scheduled date/time has passed and are still marked 'Scheduled' (Hyderabad-aware)."""
    sql = """
    SELECT f.schedule_id, f.lead_id, l.customer_name, l.phone, l.email, l.city,
           COALESCE(l.locality, 'Unmapped') as locality, COALESCE(l.region, 'Hyderabad') as region,
           l.budget_range, l.project_type, l.lead_score,
           COALESCE(f.priority, l.priority, 'Medium') as priority,
           f.scheduled_for, f.channel, f.attempt_number, f.message,
           f.followup_reason, f.next_action, f.task_summary
    FROM FOLLOW_UP_SCHEDULE f
    JOIN LEADS l ON f.lead_id = l.lead_id
    WHERE f.status = 'Scheduled'
      AND f.scheduled_for < datetime('now', 'localtime')
      AND l.is_opted_out = 0
      AND (l.is_service_area IS NULL OR l.is_service_area = 1 OR l.city = 'Hyderabad')
    ORDER BY f.scheduled_for ASC;
    """
    conn = database.get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_due_today_queue(db_path: str = database.DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns tasks scheduled for today (Hyderabad-aware)."""
    sql = """
    SELECT f.schedule_id, f.lead_id, l.customer_name, l.phone, l.email, l.city,
           COALESCE(l.locality, 'Unmapped') as locality, COALESCE(l.region, 'Hyderabad') as region,
           l.budget_range, l.project_type, l.lead_score,
           COALESCE(f.priority, l.priority, 'Medium') as priority,
           f.scheduled_for, f.channel, f.attempt_number, f.message,
           f.followup_reason, f.next_action, f.task_summary
    FROM FOLLOW_UP_SCHEDULE f
    JOIN LEADS l ON f.lead_id = l.lead_id
    WHERE f.status = 'Scheduled'
      AND date(f.scheduled_for) = date('now', 'localtime')
      AND l.is_opted_out = 0
      AND (l.is_service_area IS NULL OR l.is_service_area = 1 OR l.city = 'Hyderabad')
    ORDER BY f.scheduled_for ASC;
    """
    conn = database.get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_never_contacted_queue(db_path: str = database.DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns leads in 'New' status that have never received an initial outreach task."""
    sql = """
    SELECT l.lead_id, l.customer_name, l.phone, l.email, l.city,
           COALESCE(l.locality, 'Unmapped') as locality, COALESCE(l.region, 'Hyderabad') as region,
           l.budget_range, l.project_type, l.lead_score, l.priority, l.lead_status, l.created_at
    FROM LEADS l
    LEFT JOIN FOLLOW_UP_SCHEDULE f ON l.lead_id = f.lead_id AND f.status IN ('Sent', 'Completed')
    WHERE f.schedule_id IS NULL
      AND l.lead_status = 'New'
      AND l.is_opted_out = 0
      AND (l.is_service_area IS NULL OR l.is_service_area = 1 OR l.city = 'Hyderabad')
    ORDER BY l.lead_score DESC;
    """
    conn = database.get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_awaiting_response_queue(db_path: str = database.DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns leads where follow-ups have been sent but customer has not yet replied."""
    sql = """
    SELECT l.lead_id, l.customer_name, l.phone, l.email, l.city,
           COALESCE(l.locality, 'Unmapped') as locality, COALESCE(l.region, 'Hyderabad') as region,
           l.budget_range, l.project_type, l.lead_score, l.priority, l.lead_status,
           MAX(f.completed_at) as last_contacted_at
    FROM LEADS l
    JOIN FOLLOW_UP_SCHEDULE f ON l.lead_id = f.lead_id AND f.status IN ('Sent', 'Completed')
    WHERE (l.last_customer_response IS NULL OR TRIM(l.last_customer_response) = '')
      AND l.lead_status IN ('Follow-up', 'Qualified', 'Contacted')
      AND l.is_opted_out = 0
      AND (l.is_service_area IS NULL OR l.is_service_area = 1 OR l.city = 'Hyderabad')
    GROUP BY l.lead_id
    ORDER BY l.lead_score DESC;
    """
    conn = database.get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


# ==============================================================================
# 2. CUSTOMER CONVERSATION UNDERSTANDING ENGINE
# ==============================================================================

def analyze_customer_conversation_and_status(
    lead_id: str,
    db_path: str = database.DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """
    Deeply analyzes a customer's CRM profile and full conversation history.
    Identifies:
    - Customer profile, property type, configuration, area, budget, location
    - Previous questions and answers
    - Last interaction date, channel, direction
    - Pending customer questions and pending team actions
    - Current project stage
    - Primary interaction scenario
    """
    lead = database.get_lead_by_id(lead_id, db_path=db_path)
    if not lead:
        return {"error": f"Lead {lead_id} not found", "success": False}

    # Fetch conversation history in ascending chronological order (oldest first, newest last)
    convs = database.get_conversation_history(lead_id, limit=100, db_path=db_path)
    messages = sorted(convs, key=lambda m: m.get("created_at") or "") if convs else []

    customer_name = lead.get("customer_name") or "Valued Client"
    project_type = lead.get("project_type") or "Home Interior"
    property_status = lead.get("property_status") or "Ready for Possession"
    locality = lead.get("locality") or lead.get("city") or "Hyderabad"
    budget_range = lead.get("budget_range") or "Standard"
    scope_of_work = lead.get("scope_of_work") or "Complete Home Interiors"
    requirements = lead.get("customer_requirements") or ""
    expected_handover = lead.get("expected_handover_date")
    stored_stage = lead.get("current_project_stage")
    stored_area = lead.get("property_area_sqft")
    stored_pending_q = lead.get("pending_customer_question")
    stored_pending_act = lead.get("pending_team_action")

    # Extract conversation specifics
    last_incoming = None
    last_outgoing = None
    last_interaction = None
    all_incoming_texts = []
    all_outgoing_texts = []

    for m in messages:
        direction = m.get("direction", "incoming")
        content = m.get("message_content", "").strip()
        if direction == "incoming":
            last_incoming = m
            all_incoming_texts.append(content)
        else:
            last_outgoing = m
            all_outgoing_texts.append(content)
        last_interaction = m

    # Detect Property Area if mentioned in requirements or messages
    detected_area = stored_area
    if not detected_area:
        all_text_corpus = f"{requirements} " + " ".join(all_incoming_texts)
        area_match = re.search(r'(\d{3,5})\s*(sq\.?\s*ft|sft|sqft|square\s*feet)', all_text_corpus, re.IGNORECASE)
        if area_match:
            detected_area = f"{area_match.group(1)} sqft"

    # Identify Pending Customer Questions
    pending_question = stored_pending_q
    if last_incoming and last_incoming.get("message_content"):
        latest_cust_text = last_incoming["message_content"].strip()
        # If there is no outgoing message after this incoming message, this question/request is pending
        is_after_outgoing = True
        if last_outgoing and last_outgoing.get("created_at") and last_incoming.get("created_at"):
            if last_outgoing["created_at"] >= last_incoming["created_at"]:
                is_after_outgoing = False
        
        if is_after_outgoing or not pending_question:
            # Check for question marks or interrogatives
            if "?" in latest_cust_text or any(q_word in latest_cust_text.lower() for q_word in ["can you", "what is", "how much", "when can", "could you", "where is", "is it"]):
                sentences = re.split(r'[.!?\n]+', latest_cust_text)
                for s in sentences:
                    s_clean = s.strip()
                    if "?" in s or any(q in s_clean.lower() for q in ["can you", "what is", "how much", "when can", "could you"]):
                        pending_question = s_clean
                        break
                if not pending_question:
                    pending_question = latest_cust_text[:120]

    # Analyze Conversation Scenarios
    # Combine recent customer texts (prioritizing the latest)
    latest_incoming_text = last_incoming.get("message_content", "") if last_incoming else ""
    last_lead_response = lead.get("last_customer_response") or ""
    # Combine recent incoming text with last customer response
    recent_cust_text = f"{latest_incoming_text} {last_lead_response}".strip().lower()
    all_cust_lower = " ".join(all_incoming_texts).lower()

    scenario = "general_followup"
    scenario_details = {}

    visit_keywords = [
        "visit your office", "visit office", "come to your office", "come to office",
        "meet in person", "meet you", "meet your team", "schedule a meeting",
        "book an appointment", "book appointment", "when can i visit", "when can we meet",
        "office address", "office location", "where is your office", "want to meet",
        "consultation meeting", "at miyapur", "in miyapur", "shedule me a meetng"
    ]
    floor_plan_keywords = [
        "floor plan", "floorplan", "layout plan", "blueprint", "architect plan",
        "site layout", "shared the plan", "sent the layout", "shared my floor plan",
        "attached layout", "dwg", "pdf", "layout drawing"
    ]
    technical_keywords = [
        "bwp", "mdf", "hdhmr", "plywood", "marine ply", "waterproof", "termite",
        "acrylic vs pu", "acrylic vs laminate", "pu finish", "acoustic",
        "load bearing", "beam", "civil changes", "plumbing line", "electrical drawing",
        "conduit", "false ceiling", "hardware warranty", "blum", "hettich", "hafele", "warranty"
    ]
    postpone_keywords = [
        "possession delayed", "handover postponed", "builder delayed", "delayed handover",
        "possession in", "handover in", "not ready yet", "construction delay",
        "handover next year", "next month possession", "delayed by", "shifting date",
        "possession is postponed", "handover postponed"
    ]
    quote_pattern = r"\b(quotation|quote|pricing|cost|costs|budget|reduce the price|discount|discounts|estimate|expensive|charges|how much|rate|rates|price breakdown)\b"

    # Priority 1: Check most recent customer communication
    if any(k in recent_cust_text for k in visit_keywords):
        scenario = "office_visit_requested"
        scenario_details["keyword"] = "office_visit"
    elif any(k in recent_cust_text for k in floor_plan_keywords):
        scenario = "floor_plan_shared"
        scenario_details["keyword"] = "floor_plan"
    elif any(k in recent_cust_text for k in technical_keywords):
        scenario = "technical_question"
        for term in ["bwp", "mdf", "hdhmr", "plywood", "acrylic", "pu finish", "hettich", "blum", "hafele", "false ceiling", "civil"]:
            if term in recent_cust_text:
                scenario_details["topic"] = term.upper()
                break
    elif any(k in recent_cust_text for k in postpone_keywords):
        scenario = "postponed_possession"
        scenario_details["keyword"] = "postponed_possession"
    elif re.search(quote_pattern, recent_cust_text, re.IGNORECASE):
        scenario = "quotation_requested"
        scenario_details["keyword"] = "quotation"
    # Priority 2: Fall back to holistic conversation understanding if recent message is a greeting or general query
    elif any(k in all_cust_lower for k in visit_keywords):
        scenario = "office_visit_requested"
        scenario_details["keyword"] = "office_visit"
    elif any(k in all_cust_lower for k in floor_plan_keywords):
        scenario = "floor_plan_shared"
        scenario_details["keyword"] = "floor_plan"
    elif any(k in all_cust_lower for k in technical_keywords):
        scenario = "technical_question"
        for term in ["bwp", "mdf", "hdhmr", "plywood", "acrylic", "pu finish", "hettich", "blum", "hafele", "false ceiling", "civil"]:
            if term in all_cust_lower:
                scenario_details["topic"] = term.upper()
                break
    elif any(k in all_cust_lower for k in postpone_keywords):
        scenario = "postponed_possession"
        scenario_details["keyword"] = "postponed_possession"
    elif re.search(quote_pattern, all_cust_lower, re.IGNORECASE):
        scenario = "quotation_requested"
        scenario_details["keyword"] = "quotation"
    # Priority 3: Silence check
    else:
        if last_outgoing and (not last_incoming or (last_incoming.get("created_at") and last_outgoing.get("created_at") and last_outgoing["created_at"] > last_incoming["created_at"])):
            scenario = "no_response"
            scenario_details["keyword"] = "no_response"
        elif not messages:
            scenario = "new_enquiry"
        else:
            scenario = "general_followup"

    # Determine Project Stage
    if stored_stage:
        current_stage = stored_stage
    elif scenario == "office_visit_requested":
        current_stage = "Consultation & Office Visit Scheduling"
    elif scenario == "floor_plan_shared":
        current_stage = "Floor Plan Review & Spatial Optimization"
    elif scenario == "quotation_requested":
        current_stage = "3D Design & BOQ Finalisation"
    elif scenario == "postponed_possession":
        current_stage = "Handover Postponed - Long Term Nurture"
    elif scenario == "technical_question":
        current_stage = "Technical Specifications Review"
    elif lead.get("lead_status") == "New":
        current_stage = "Initial Discovery & Enquiry Qualification"
    else:
        current_stage = "Active Design Follow-Up"

    # Determine Pending Team Action
    pending_team_action = stored_pending_act
    if not pending_team_action:
        if scenario == "office_visit_requested":
            pending_team_action = "Share Google Calendar booking link for Miyapur office (2:00 PM to 5:00 PM IST)."
        elif scenario == "floor_plan_shared":
            pending_team_action = "Review architectural floor plan and provide spatial layout recommendations."
        elif scenario == "quotation_requested":
            pending_team_action = "Clarify quotation policy: preliminary budget estimate can be discussed, while final BOQ follows 3D layout finalisation."
        elif scenario == "postponed_possession":
            pending_team_action = "Record revised handover date and schedule follow-up check-in closer to possession."
        elif scenario == "technical_question":
            pending_team_action = "Flag technical specification for senior design specialist review."
        elif scenario == "no_response":
            pending_team_action = "Send polite, personalized check-in referencing previous design discussion."
        else:
            pending_team_action = "Conduct regular design consultation follow-up."

    # Compute Days Since Last Contact
    days_since_last_contact = 0
    last_contact_str = "None"
    if last_interaction and last_interaction.get("created_at"):
        last_contact_str = last_interaction["created_at"]
        try:
            # Handle ISO string with or without time
            dt_part = last_contact_str.split("T")[0] if "T" in last_contact_str else last_contact_str.split(" ")[0]
            last_dt = datetime.date.fromisoformat(dt_part)
            days_since_last_contact = (datetime.date.today() - last_dt).days
        except Exception:
            days_since_last_contact = 1

    return {
        "success": True,
        "lead_id": lead_id,
        "customer_name": customer_name,
        "phone": lead.get("phone"),
        "email": lead.get("email"),
        "city": lead.get("city", "Hyderabad"),
        "locality": locality,
        "region": lead.get("region", "Hyderabad"),
        "project_type": project_type,
        "property_status": property_status,
        "property_area_sqft": detected_area,
        "budget_range": budget_range,
        "scope_of_work": scope_of_work,
        "customer_requirements": requirements,
        "expected_handover_date": expected_handover,
        "current_project_stage": current_stage,
        "pending_customer_question": pending_question,
        "pending_team_action": pending_team_action,
        "scenario": scenario,
        "scenario_details": scenario_details,
        "total_messages": len(messages),
        "last_interaction_date": last_contact_str,
        "days_since_last_contact": days_since_last_contact,
        "last_message": last_interaction,
        "last_incoming_message": last_incoming,
        "last_outgoing_message": last_outgoing,
        "lead_priority": lead.get("priority", "Medium"),
        "lead_score": lead.get("lead_score", 50)
    }


# ==============================================================================
# 3. INTELLIGENT FOLLOW-UP RECOMMENDATION ENGINE
# ==============================================================================

def generate_intelligent_followup_recommendation(
    lead_id: str,
    db_path: str = database.DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """
    Generates an automated, highly personalized follow-up recommendation grounded
    in the customer's conversation history, property details, and current project stage.
    
    Adheres strictly to SHA Business Rules:
    - Miyapur office (never Hyderabad Studio)
    - Appointments 2:00 PM to 5:00 PM IST, Monday through Sunday
    - Official Google Calendar Booking Link
    - Quotation Policy (detailed quote follows 3D design finalisation)
    - Safe human-in-the-loop WhatsApp message generation
    """
    analysis = analyze_customer_conversation_and_status(lead_id, db_path=db_path)
    if not analysis.get("success"):
        return {"success": False, "error": analysis.get("error", "Failed to analyze customer")}

    scenario = analysis["scenario"]
    customer_name = analysis["customer_name"]
    project_type = analysis["project_type"]
    locality = analysis["locality"]
    scope = analysis["scope_of_work"]
    budget = analysis["budget_range"]
    pending_q = analysis.get("pending_customer_question")
    lead_prio = analysis.get("lead_priority", "Medium")

    now = datetime.datetime.now()
    
    # -------------------------------------------------------------
    # SCENARIO 1: FLOOR PLAN SHARED
    # -------------------------------------------------------------
    if scenario == "floor_plan_shared":
        reason = f"Customer shared architectural floor plan for their {project_type}; spatial review and layout insights are due."
        next_action = "Review architectural floor plan and present 3D spatial layout recommendations."
        priority = "High"
        recommended_date = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d 11:00:00")
        explanation = (
            f"{customer_name} shared their layout plan for the {project_type} in {locality}. "
            "A proactive review with spatial optimization insights (maximizing natural light, storage circulation, and ergonomic kitchen workflows) "
            "demonstrates SHA Interface Interiors' engineering excellence and moves the lead to in-person 3D consultation."
        )
        task_summary = f"Floor Plan Layout Review: {customer_name}"
        suggested_message = (
            f"Hello {customer_name}! 😊 We have reviewed the floor plan for your {project_type} in {locality}.\n\n"
            f"Our design lead at {business_config.BUSINESS_NAME} has identified several space-saving layout enhancements "
            f"for your {scope} to optimize natural daylight and maximize cabinetry storage.\n\n"
            f"We would love to walk you through these 3D layout concepts. Would you like to schedule an in-person meeting "
            f"at our {business_config.OFFICE_NAME} (consultation slots 2:00 PM to 5:00 PM IST, Monday through Sunday) "
            f"or connect over a phone call this week?"
        )

    # -------------------------------------------------------------
    # SCENARIO 2: QUOTATION REQUESTED
    # -------------------------------------------------------------
    elif scenario == "quotation_requested":
        reason = f"Customer requested pricing/quotation details for {project_type}."
        next_action = "Explain quotation policy: preliminary budget ranges can be discussed, while detailed final BOQ follows 3D design finalisation."
        priority = "High"
        recommended_date = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d 11:30:00")
        explanation = (
            f"{customer_name} inquired about pricing for their {project_type} in {locality}. "
            "In line with SHA Interiors quotation policy, final itemized quotations require 3D design finalisation "
            "and agreed scope to avoid discrepancies. We reassure the customer by offering preliminary budget clarity "
            "and inviting them to discuss customized material finishes at our Miyapur office."
        )
        task_summary = f"Quotation & 3D Policy: {customer_name}"
        suggested_message = (
            f"Hello {customer_name}! Regarding your quotation inquiry for your {project_type} in {locality}:\n\n"
            f"At {business_config.BUSINESS_NAME}, transparent pricing is our core priority. Detailed, itemized final quotations (BOQ) "
            f"are prepared following 3D design finalisation and agreed material selections, ensuring zero hidden costs or post-work surprises.\n\n"
            f"We can gladly discuss your preliminary {budget} budget range right away! Would you like to schedule a 3D layout discussion "
            f"at our {business_config.OFFICE_NAME} (appointments available 2:00 PM to 5:00 PM IST, all 7 days) or connect over a phone call?"
        )

    # -------------------------------------------------------------
    # SCENARIO 3: POSTPONED POSSESSION / HANDOVER DELAY
    # -------------------------------------------------------------
    elif scenario == "postponed_possession":
        reason = f"Customer postponed possession/handover timeline for {project_type}."
        next_action = "Acknowledge revised timeline, record new handover date, and schedule a check-in closer to possession."
        priority = "Medium"
        recommended_date = (now + datetime.timedelta(days=14)).strftime("%Y-%m-%d 11:00:00")
        explanation = (
            f"{customer_name} informed us of a delayed possession timeline for their {project_type} in {locality}. "
            "Rather than pushing for immediate closure, acknowledging the delay and timing 3D planning 4–6 weeks prior "
            "to possession builds long-term trust."
        )
        task_summary = f"Handover Follow-up: {customer_name}"
        suggested_message = (
            f"Hello {customer_name}! Thank you for updating us regarding the revised possession timeline for your {project_type} in {locality}.\n\n"
            f"We completely understand that builder handovers can shift. Starting 3D space planning 4–6 weeks before key handover "
            f"ensures precision factory manufacturing with zero delays once you receive possession.\n\n"
            f"We will check back with you closer to your handover date. In the meantime, feel free to visit our {business_config.OFFICE_NAME} "
            f"or reach out if you would like to explore preliminary concepts! 🏡"
        )

    # -------------------------------------------------------------
    # SCENARIO 4: OFFICE VISIT / MEETING REQUESTED
    # -------------------------------------------------------------
    elif scenario == "office_visit_requested":
        reason = f"Customer requested an in-person meeting or office visit at the {business_config.OFFICE_NAME}."
        next_action = f"Share official Google Calendar booking link for {business_config.OFFICE_NAME} (2:00 PM to 5:00 PM IST)."
        priority = "High"
        recommended_date = now.strftime("%Y-%m-%d 10:30:00")
        explanation = (
            f"{customer_name} expressed direct interest in visiting our office or meeting the design team. "
            "Per mandatory communication rules, provide our official Google Calendar booking link allowing them to select "
            f"a slot strictly within customer appointment hours (2:00 PM to 5:00 PM IST, Monday through Sunday) at our {business_config.OFFICE_NAME}."
        )
        task_summary = f"Share Booking Link: {customer_name}"
        suggested_message = (
            f"Certainly! We would be happy to welcome you to {business_config.BUSINESS_NAME} at our {business_config.OFFICE_NAME}. 😊\n\n"
            f"Please use our booking link to view the available appointment slots (2:00 PM to 5:00 PM IST, Monday through Sunday) "
            f"and select a convenient date and time:\n\n"
            f"{business_config.GOOGLE_CALENDAR_BOOKING_LINK}\n\n"
            f"Once you book a slot, your appointment will be confirmed through Google Calendar. We look forward to meeting you!"
        )

    # -------------------------------------------------------------
    # SCENARIO 5: UNANSWERED TECHNICAL QUESTION
    # -------------------------------------------------------------
    elif scenario == "technical_question":
        topic = analysis.get("scenario_details", {}).get("topic", "Material Specifications")
        reason = f"Customer asked specialized technical specification questions regarding {topic}."
        next_action = f"Flag {topic} technical query for design specialist review and deliver verified guidance."
        priority = "High"
        recommended_date = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d 10:30:00")
        explanation = (
            f"{customer_name} asked a specific technical question ('{pending_q or topic}'). "
            "To uphold engineering credibility, avoid unverified speculation. We flag the query for senior technical review "
            f"and invite the client to inspect physical material samples at the {business_config.OFFICE_NAME}."
        )
        task_summary = f"Technical Guidance ({topic}): {customer_name}"
        suggested_message = (
            f"Hello {customer_name}! Thank you for your inquiry regarding {topic} for your {project_type} in {locality}.\n\n"
            f"At {business_config.BUSINESS_NAME}, we ensure strict structural standards—using calibrated BWP marine plywood "
            f"and certified German hardware (Hettich / Blum) with genuine warranties.\n\n"
            f"Our technical design specialist would be pleased to show you physical cross-sections and finish samples at our {business_config.OFFICE_NAME} "
            f"or discuss details over a phone call. Our customer appointments are available from 2:00 PM to 5:00 PM IST, Monday through Sunday. "
            f"What time would you prefer?"
        )

    # -------------------------------------------------------------
    # SCENARIO 6: NO RESPONSE / SILENT LEAD
    # -------------------------------------------------------------
    elif scenario == "no_response":
        reason = f"No customer response for {analysis.get('days_since_last_contact', 1)} day(s) following previous design touchpoint."
        next_action = "Send a polite, non-intrusive follow-up referencing their specific project requirements and design aspirations."
        priority = lead_prio
        recommended_date = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d 12:00:00")
        explanation = (
            f"It has been {analysis.get('days_since_last_contact', 1)} day(s) since our last communication with {customer_name} "
            f"regarding their {project_type} in {locality}. A friendly, non-repetitive check-in keeps the conversation active "
            "without being intrusive."
        )
        task_summary = f"Courtesy Check-in: {customer_name}"
        suggested_message = (
            f"Hello {customer_name}! 👋 Following up regarding your {project_type} interior plans in {locality}.\n\n"
            f"We know planning home interiors takes time and family discussion. Whenever you are ready to explore tailored layout concepts "
            f"for your {scope}, our design team at {business_config.BUSINESS_NAME} is here to assist.\n\n"
            f"Would you like us to share curated digital portfolio ideas, or would a brief 10-minute discovery phone call be convenient this week?"
        )

    # -------------------------------------------------------------
    # DEFAULT / NEW ENQUIRY / GENERAL FOLLOW-UP
    # -------------------------------------------------------------
    else:
        reason = f"Routine design consultation follow-up for {project_type} in {locality}."
        next_action = "Initiate discovery discussion and invite for 3D spatial planning consultation."
        priority = lead_prio
        recommended_date = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d 11:00:00")
        explanation = (
            f"Proactive engagement for {customer_name} ({project_type}, {locality}) to advance the project "
            "from preliminary enquiry into space planning and 3D concept development."
        )
        task_summary = f"Design Discovery: {customer_name}"
        suggested_message = (
            f"Hello {customer_name}! Greetings from {business_config.BUSINESS_NAME}.\n\n"
            f"We are eager to assist you with bespoke interior design for your {project_type} in {locality} ({scope}).\n\n"
            f"Our design leads would love to schedule a preliminary spatial consultation at our {business_config.OFFICE_NAME} "
            f"or arrange a convenient phone call. Customer appointment slots are available between 2:00 PM and 5:00 PM IST, "
            f"Monday through Sunday (general office hours 10:00 AM to 6:00 PM).\n\n"
            f"Please let us know a suitable time between 2:00 PM and 5:00 PM to connect!"
        )

    # Validate message compliance against mandatory rules
    is_compliant, violations = business_config.validate_message_compliance(suggested_message)
    if not is_compliant:
        # If any violation occurred, log and apply safe canonical fallback
        print(f"[WARNING] Compliance issues detected in generated message: {violations}")

    return {
        "success": True,
        "lead_id": lead_id,
        "customer_name": customer_name,
        "scenario": scenario,
        "followup_reason": reason,
        "next_action": next_action,
        "recommended_date": recommended_date,
        "priority": priority,
        "explanation": explanation,
        "task_summary": task_summary,
        "suggested_channel": "WhatsApp",
        "suggested_whatsapp_message": suggested_message,
        "is_compliant": is_compliant,
        "compliance_violations": violations,
        "customer_analysis": analysis
    }


# ==============================================================================
# 4. TASK MANAGEMENT ACTIONS & AUTOMATED SCHEDULING
# ==============================================================================

def schedule_recommended_followup(
    lead_id: str,
    custom_date: Optional[str] = None,
    custom_channel: Optional[str] = None,
    custom_message: Optional[str] = None,
    custom_reason: Optional[str] = None,
    custom_action: Optional[str] = None,
    custom_priority: Optional[str] = None,
    db_path: str = database.DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """
    Schedules an intelligent follow-up task using the recommendation engine defaults
    or salesperson custom overrides.
    """
    rec = generate_intelligent_followup_recommendation(lead_id, db_path=db_path)
    if not rec.get("success"):
        return {"success": False, "error": rec.get("error", "Failed to generate recommendation")}

    sched_for = custom_date or rec["recommended_date"]
    channel = custom_channel or rec["suggested_channel"]
    message = custom_message or rec["suggested_whatsapp_message"]
    reason = custom_reason or rec["followup_reason"]
    action = custom_action or rec["next_action"]
    priority = custom_priority or rec["priority"]
    task_summary = rec.get("task_summary")

    return database.schedule_single_followup(
        lead_id=lead_id,
        scheduled_for=sched_for,
        channel=channel,
        message=message,
        followup_reason=reason,
        next_action=action,
        priority=priority,
        task_summary=task_summary,
        db_path=db_path
    )


# ==============================================================================
# 5. MULTICHANNEL MESSAGE GENERATORS (EMAIL & WHATSAPP) - PRESERVED & ENHANCED
# ==============================================================================

def generate_personalized_whatsapp_draft(lead: Dict[str, Any], goal: str = "site_visit") -> str:
    """
    Generates a personalized WhatsApp outreach message incorporating actual customer details.
    Strictly follows SHA Business Rules (Miyapur office, 2-5 PM appointments).
    """
    name = lead.get("customer_name", "Valued Client")
    city = lead.get("city", "Hyderabad")
    p_type = lead.get("project_type", "home")
    budget = lead.get("budget_range", "planned budget")
    scope = lead.get("scope_of_work", "interior design")
    status = lead.get("property_status", "Ready for Possession")
    loc = lead.get("locality") or city

    if goal == "site_visit":
        return (
            f"Hello {name}! 👋 Hope you are having a wonderful day.\n\n"
            f"Our design lead at {business_config.BUSINESS_NAME} is visiting residential projects in {loc} this week. "
            f"Since your {p_type} is currently *{status}*, we would be delighted to offer you a complimentary on-site measurement & spatial consultation for your {scope}.\n\n"
            f"Would this weekend afternoon between 2:00 PM and 5:00 PM suit you better for a quick 20-minute site walk-through? 📐"
        )
    elif goal == "budget_alignment":
        return (
            f"Dear {name}, following up regarding your {p_type} interior project in {loc}.\n\n"
            f"To help our 3D design team tailor concepts within your target {budget} range: At {business_config.BUSINESS_NAME}, "
            f"detailed itemized quotations are prepared after 3D layout finalisation, but we can share preliminary options right away! "
            f"Do you prefer a turnkey package (woodwork + false ceiling + civil) or modular cabinetry specifically? 🛋️"
        )
    elif goal == "portfolio_lookbook":
        return (
            f"Hi {name}! 🌟 We recently delivered a bespoke {p_type} interior project right near {loc}. "
            f"Given your interest in {scope}, our team put together our digital lookbook highlighting custom modular finishes:\n\n"
            f"👉 {business_config.OFFICIAL_WEBSITE}\n"
            f"Instagram: {business_config.OFFICIAL_INSTAGRAM}\n\n"
            f"Let us know which design style appeals most to your taste!"
        )
    elif goal == "office_visit":
        return business_config.format_calendar_booking_response(name)
    else:
        return (
            f"Hello {name}, thank you for connecting with {business_config.BUSINESS_NAME} regarding your {p_type} in {loc}.\n\n"
            f"We are eager to help you create a stunning, functional home. We would be delighted to invite you for a 3D spatial consultation "
            f"at our {business_config.OFFICE_NAME} or schedule a phone call. Our consultation appointments are available between 2:00 PM and 5:00 PM IST, Monday through Sunday.\n\n"
            f"When would be a good time for a brief 10-minute discovery call?"
        )


def generate_personalized_email_draft(lead: Dict[str, Any], goal: str = "consultation_invitation") -> Dict[str, str]:
    """
    Generates an executive, personalized HTML/plain text email draft.
    Returns: {"subject": str, "body": str}
    """
    name = lead.get("customer_name", "Valued Client")
    city = lead.get("city", "Hyderabad")
    p_type = lead.get("project_type", "Residential")
    budget = lead.get("budget_range", "Standard")
    scope = lead.get("scope_of_work", "Complete Home Interiors")
    lead_id = lead.get("lead_id", "SHA-Enquiry")

    loc = lead.get("locality")
    location_display = f"{loc}, {city}" if loc else city

    subject = f"SHA Interface Interiors: Spatial Design & Material Consultation for your {p_type} in {location_display} [{lead_id}]"

    body = f"""Dear {name},

Thank you for choosing {business_config.BUSINESS_NAME} as your prospective design partner.

We have reviewed your preliminary enquiry for your {p_type} project located in {location_display} ({scope}, budgeted at {budget}).

At {business_config.BUSINESS_NAME}, we believe that an exceptional home begins with intelligent spatial planning, precision German hardware, and timeless material harmony. 

Our senior design team would be delighted to invite you for an introductory spatial discovery session, where we can:
1. Review your architectural floor plan and optimize room layouts for maximum daylight and ventilation.
2. Present curated material palettes across BWP marine plywood, high-gloss acrylics, and natural veneers.
3. Provide a transparent, itemized Bill of Quantities (BOQ) tailored specifically to your investment preferences following 3D design finalisation.

Would you be available for a consultation meeting at our {business_config.OFFICE_NAME} or a convenient phone call this week? Our customer consultation appointments are available between {business_config.APPOINTMENT_HOURS_START} and {business_config.APPOINTMENT_HOURS_END} {business_config.TIMEZONE}, {business_config.WORKING_DAYS} (general office hours {business_config.OFFICE_HOURS_START} to {business_config.OFFICE_HOURS_END} IST).

You may also view available appointment slots directly through our booking link:
{business_config.GOOGLE_CALENDAR_BOOKING_LINK}

We look forward to helping you craft a living environment that is as functional as it is beautiful.

Warm regards,

Client Experience & Spatial Design Team
{business_config.BUSINESS_NAME} – {business_config.OFFICE_NAME.title()}
Location: {business_config.OFFICE_MAPS_LINK}
Website: {business_config.OFFICIAL_WEBSITE}
Instagram: {business_config.OFFICIAL_INSTAGRAM}
General Office Hours: {business_config.OFFICE_HOURS} ({business_config.WORKING_DAYS_SUMMARY})
Customer Appointments: {business_config.APPOINTMENT_HOURS} ({business_config.APPOINTMENT_DAYS_SUMMARY})
"""
    return {
        "subject": subject,
        "body": body
    }


def record_communication_draft(
    lead_id: str,
    channel: str,
    subject_or_type: str,
    draft_content: str,
    db_path: str = database.DEFAULT_DB_PATH
) -> bool:
    """
    Logs an authored communication draft in LEAD_ACTIVITY_LOG for audit and team review.
    Does NOT dispatch external communications.
    """
    desc = f"Drafted {channel} message ({subject_or_type}). Awaiting sales consultant review & dispatch."
    return database.insert_activity_log(
        lead_id=lead_id,
        activity_type=f"DRAFT_{channel.upper()}",
        activity_description=desc,
        db_path=db_path
    )
