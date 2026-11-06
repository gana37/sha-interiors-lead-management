"""
shadow_mode.py - AI Shadow Mode Intelligence & Background Analysis Engine
SHA Interface Interiors - AI-Powered Interior Design Lead Management System

Key Capabilities:
1. Non-Intrusive Background Execution: Analyzes customer conversations silently without dispatching messages.
2. 10 Strategic Scenarios Detection:
   - Scenario 1: Office Visit / Consultation Interest
   - Scenario 2: Floor Plan / Layout Shared
   - Scenario 3: Quotation / Cost Inquiry
   - Scenario 4: Technical Specs / Material Inquiries
   - Scenario 5: Possession Delay / Builder Handover Delay
   - Scenario 6: Site Visit / Physical Measurement Request
   - Scenario 7: 3D Visualization / Design Request
   - Scenario 8: Follow-up Re-engagement (Silent Customer)
   - Scenario 9: Price Comparison / Competitor Quotation
   - Scenario 10: Ready to Proceed / Booking Finalization
3. Idempotent Recommendation Generation: Avoids duplicate alerts for the same scenario.
4. Human-in-the-Loop Review Lifecycle: Pending Review -> Approved / Modified / Rejected.
5. Promotion: Approved recommendations seamlessly convert into CRM scheduled follow-up tasks.
6. MANDATORY RULE: All WhatsApp drafts and recommendations are generated in ENGLISH ONLY.
"""

import os
import sys
import datetime
import uuid
import re
from typing import List, Dict, Any, Optional, Tuple

import database
import business_config
import ai_service
import multilingual_engine


SCENARIO_CONFIGS = {
    "OFFICE_VISIT_INTEREST": {
        "title": "Office Visit & Consultation Interest",
        "keywords": ["visit", "meet", "office", "appointment", "schedule", "miyapur", "location", "timing", "when can i come", "when can we meet"],
        "priority": "High",
        "delay_days": 0
    },
    "FLOOR_PLAN_SHARED": {
        "title": "Floor Plan / Layout Shared",
        "keywords": ["floor plan", "layout", "drawing", "blue print", "pdf", "cad", "attached", "dimensions", "measurements", "sft", "sqft"],
        "priority": "High",
        "delay_days": 1
    },
    "QUOTATION_REQUEST": {
        "title": "Quotation / Cost Estimate Request",
        "keywords": ["quote", "quotation", "cost", "price", "rate", "budget", "package", "how much", "charges", "estimate"],
        "priority": "High",
        "delay_days": 1
    },
    "TECHNICAL_SPECS": {
        "title": "Technical Material & Hardware Specifications",
        "keywords": ["plywood", "bwp", "marine", "hdhmr", "acrylic", "veneer", "hettich", "blum", "hafele", "thickness", "is 710", "is 303"],
        "priority": "Medium",
        "delay_days": 1
    },
    "POSSESSION_DELAY": {
        "title": "Builder Handover / Possession Delay",
        "keywords": ["possession delay", "delay", "builder delayed", "next year", "not ready", "late", "next month", "construction pending"],
        "priority": "Low",
        "delay_days": 21
    },
    "SITE_VISIT_REQUEST": {
        "title": "Site Visit / In-Person Measurement Request",
        "keywords": ["site visit", "come to flat", "visit property", "measure flat", "site measurement", "inspection", "on-site"],
        "priority": "High",
        "delay_days": 1
    },
    "THREE_D_DESIGN_REQUEST": {
        "title": "3D Design & Elevation Visualization",
        "keywords": ["3d", "3d design", "render", "elevation", "view", "3d model", "visualize", "walkthrough"],
        "priority": "Medium",
        "delay_days": 1
    },
    "SILENT_CUSTOMER_ENGAGEMENT": {
        "title": "Silent Customer Re-Engagement",
        "keywords": ["thinking", "discuss with family", "later", "check and let you know", "will update"],
        "priority": "Medium",
        "delay_days": 3
    },
    "COMPETITOR_COMPARISON": {
        "title": "Competitor Price & Quality Comparison",
        "keywords": ["competitor", "other quotation", "another interior", "cheaper", "expensive", "market price", "discount", "reduce price"],
        "priority": "High",
        "delay_days": 1
    },
    "READY_TO_PROCEED": {
        "title": "Ready to Finalize & Proceed",
        "keywords": ["finalize", "start work", "proceed", "advance", "token", "contract", "agreement", "ready to pay", "confirm project"],
        "priority": "Urgent",
        "delay_days": 0
    }
}


def is_shadow_mode_enabled() -> bool:
    """Checks whether Shadow Mode is enabled in CRM config."""
    return database.get_shadow_mode_status()


def set_shadow_mode_enabled(enabled: bool) -> bool:
    """Toggles Shadow Mode ON (True) or OFF (False)."""
    return database.set_shadow_mode_status(enabled)


def get_pending_recommendations(lead_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all pending shadow recommendations for staff review."""
    return database.get_shadow_recommendations(lead_id=lead_id, status="Pending Review")


def analyze_conversation_for_shadow_recommendations(
    lead_id: str,
    latest_message_override: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Analyzes customer conversations for the given lead.
    Detects applicable scenarios, formulates recommendations with English WhatsApp drafts,
    enforces idempotency, and records new recommendations in SHADOW_RECOMMENDATIONS.
    """
    if not is_shadow_mode_enabled():
        return []

    database.init_db()
    lead = database.get_lead_by_id(lead_id)
    if not lead:
        return []

    # Get conversation history
    convs = database.get_conversation_history(lead_id)
    if not convs and not latest_message_override:
        return []

    # Determine text to analyze
    if latest_message_override:
        recent_texts = [latest_message_override]
    else:
        # Check last 3 messages
        recent_texts = [c["message_content"] for c in convs[-3:]]

    combined_text = " \n ".join(recent_texts)
    # Translate internally to English if needed
    trans_res = multilingual_engine.translate_to_english(combined_text)
    analyzed_text = trans_res["english_translation"].lower()

    detected_recommendations = []
    today = datetime.date.today()

    for scenario_key, cfg in SCENARIO_CONFIGS.items():
        # Check if keywords match
        matched_kws = [kw for kw in cfg["keywords"] if kw in analyzed_text]
        if not matched_kws:
            continue

        # Check idempotency: does an active recommendation for this scenario already exist?
        existing_recs = database.get_shadow_recommendations(lead_id=lead_id)
        is_duplicate = False
        for er in existing_recs:
            if er["scenario"] == scenario_key and er["status"] in ["Pending Review", "Approved"]:
                is_duplicate = True
                break

        if is_duplicate:
            continue

        # Formulate scenario-specific action and English WhatsApp draft
        rec_date = (today + datetime.timedelta(days=cfg["delay_days"])).strftime("%Y-%m-%d")
        customer_name = lead.get("customer_name") or "Valued Customer"
        property_type = lead.get("property_type") or "home"

        reason, next_action, whatsapp_draft = _generate_scenario_content(
            scenario_key=scenario_key,
            customer_name=customer_name,
            property_type=property_type,
            matched_evidence=", ".join(matched_kws)
        )

        rec_id = f"REC-{uuid.uuid4().hex[:8].upper()}"
        recommendation_payload = {
            "recommendation_id": rec_id,
            "lead_id": lead_id,
            "scenario": scenario_key,
            "reason": reason,
            "next_action": next_action,
            "priority": cfg["priority"],
            "recommended_date": rec_date,
            "english_whatsapp_draft": whatsapp_draft,
            "conversation_evidence": f"Detected keywords: {', '.join(matched_kws)} in recent conversation.",
            "confidence_score": 0.95
        }

        # Insert into database
        db_rec_id = database.insert_shadow_recommendation(recommendation_payload)
        if db_rec_id:
            recommendation_payload["recommendation_id"] = db_rec_id
            detected_recommendations.append(recommendation_payload)

    return detected_recommendations


def _generate_scenario_content(
    scenario_key: str,
    customer_name: str,
    property_type: str,
    matched_evidence: str
) -> Tuple[str, str, str]:
    """Generates scenario-specific English content and drafts adhering to SHA business rules."""

    cal_link = business_config.GOOGLE_CALENDAR_BOOKING_LINK

    if scenario_key == "OFFICE_VISIT_INTEREST":
        reason = f"Customer expressed direct interest in meeting or visiting SHA office ({matched_evidence})."
        next_action = "Share Google Calendar booking link for consultation at Miyapur office (2:00 PM - 5:00 PM)."
        draft = (
            f"Hello {customer_name}! 😊 We would be delighted to welcome you to SHA Interface Interiors at our Miyapur office.\n\n"
            f"You can view available appointment slots and select a convenient time between 2:00 PM and 5:00 PM using our booking link:\n"
            f"{cal_link}\n\n"
            f"We look forward to meeting you and discussing your {property_type} interior project!"
        )

    elif scenario_key == "FLOOR_PLAN_SHARED":
        reason = f"Customer provided floor plan or layout details ({matched_evidence})."
        next_action = "Review architectural dimensions, prepare 2D layout zoning, and schedule consultation."
        draft = (
            f"Hello {customer_name}, thank you for sharing your floor plan! Our design team is currently reviewing the spatial layout for your {property_type}.\n\n"
            f"To walk you through our recommended space planning and initial concept, we would love to invite you to our Miyapur office.\n\n"
            f"Please reserve your preferred consultation slot between 2:00 PM and 5:00 PM here:\n"
            f"{cal_link}"
        )

    elif scenario_key == "QUOTATION_REQUEST":
        reason = f"Customer asked for price estimate or quotation ({matched_evidence})."
        next_action = "Explain SHA customized quotation workflow; avoid ballpark figures without exact specs."
        draft = (
            f"Hello {customer_name}! Thank you for your inquiry. At SHA Interface Interiors, all our interior solutions are custom-engineered to your exact floor plan and material preferences.\n\n"
            f"We provide transparent direct factory-pricing with zero retail markups. Detailed final quotations and itemized BOQ are finalized following 3D design approval.\n\n"
            f"Would you like our design team to review your floor plan dimensions for your {property_type}?"
        )

    elif scenario_key == "TECHNICAL_SPECS":
        reason = f"Customer inquired about materials, boards, or hardware brands ({matched_evidence})."
        next_action = "Share SHA verified material standard sheet (BWP IS:710, HDHMR, Hettich/Blum hardware)."
        draft = (
            f"Hello {customer_name}! At SHA Interface Interiors, we maintain strict quality standards:\n"
            f"• Wet Zones & Kitchen: 100% Calibrated BWP Marine Plywood (IS:710 certified)\n"
            f"• Wardrobes & Dry Areas: High-density HDHMR boards with 1.0mm premium laminates\n"
            f"• Hardware: German soft-close hinges and tandem runners from Hettich and Blum with 10-year warranty\n\n"
            f"All panels are precision-edged in factory conditions. Would you like our technical specifications sheet for your {property_type}?"
        )

    elif scenario_key == "POSSESSION_DELAY":
        reason = f"Customer informed of possession/handover delay by builder ({matched_evidence})."
        next_action = "Schedule follow-up reminder 3 weeks prior to revised handover date without aggressive sales push."
        draft = (
            f"Hello {customer_name}, thank you for updating us regarding your possession timeline. Builder delays are very common, so please take your time!\n\n"
            f"We have noted your updated schedule and will check back with you closer to handover. If you wish to plan design concepts early, you are always welcome at our Miyapur office."
        )

    elif scenario_key == "SITE_VISIT_REQUEST":
        reason = f"Customer requested on-site inspection or measurements ({matched_evidence})."
        next_action = "Coordinate dedicated on-site measurement slot with senior site engineer."
        draft = (
            f"Hello {customer_name}! We would be happy to schedule an on-site visit to inspect your {property_type} and take precise laser measurements.\n\n"
            f"Our site team can coordinate with you. Please let us know if a weekday or weekend afternoon suits you best."
        )

    elif scenario_key == "THREE_D_DESIGN_REQUEST":
        reason = f"Customer requested 3D renders or views ({matched_evidence})."
        next_action = "Clarify 3D visualization workflow following initial architectural consultation."
        draft = (
            f"Hello {customer_name}! We specialize in photorealistic 3D visualizations tailored to your specific space.\n\n"
            f"Our bespoke 3D design process begins right after initial layout planning and site measurements, ensuring every render matches actual site dimensions. Would you like to share your floor plan so we can explore design concepts for your {property_type}?"
        )

    elif scenario_key == "SILENT_CUSTOMER_ENGAGEMENT":
        reason = f"Customer has been inactive following initial quotation/information ({matched_evidence})."
        next_action = "Gentle check-in sharing recent project portfolio."
        draft = (
            f"Hello {customer_name}, hope you are having a wonderful week! Just following up to see if you had a chance to review our interior design portfolio.\n\n"
            f"Whenever you are ready to explore material selections or design ideas, we would love to host you at our Miyapur office:\n"
            f"{cal_link}"
        )

    elif scenario_key == "COMPETITOR_COMPARISON":
        reason = f"Customer is comparing price or specifications against other interior firms ({matched_evidence})."
        next_action = "Highlight SHA differentiators: 100% factory calibration, genuine BWP IS:710, warranty transparency."
        draft = (
            f"Hello {customer_name}! We appreciate you comparing options. When comparing interior estimates, please ensure other providers offer genuine BWP Marine Ply (IS:710) and factory-calibrated edge-banding rather than commercial board or on-site manual pressing.\n\n"
            f"We would be glad to show you live side-by-side material comparisons at our Miyapur office:\n"
            f"{cal_link}"
        )

    elif scenario_key == "READY_TO_PROCEED":
        reason = f"Customer expressed readiness to finalize and proceed with project ({matched_evidence})."
        next_action = "Draft formal project milestone agreement, payment schedule, and kick-off meeting."
        draft = (
            f"Hello {customer_name}! We are thrilled to welcome you to the SHA Interface Interiors family! 🎉\n\n"
            f"Let us schedule our formal kick-off session at the Miyapur office to finalize the design agreement and project milestones:\n"
            f"{cal_link}"
        )

    else:
        reason = "Conversation requires strategic follow-up."
        next_action = "Review customer requirements and send personalized follow-up."
        draft = (
            f"Hello {customer_name}! Thank you for connecting with SHA Interface Interiors. Please let us know how we can best assist with your {property_type} interiors."
        )

    return reason, next_action, draft


def review_shadow_recommendation(
    recommendation_id: str,
    action: str,
    reviewer_notes: Optional[str] = None,
    modified_draft: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handles staff action on a shadow recommendation:
    - 'Approve': Promotes into scheduled follow-up and sets status='Approved'.
    - 'Modify': Saves edited draft/action and sets status='Modified'.
    - 'Reject': Dismisses recommendation and sets status='Rejected'.
    """
    clean_action = action.strip().capitalize()
    if clean_action not in ["Approved", "Modified", "Rejected"]:
        return {"success": False, "error": f"Invalid action: {action}. Must be Approved, Modified, or Rejected."}

    # Fetch recommendation
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM SHADOW_RECOMMENDATIONS WHERE recommendation_id = ?;", (recommendation_id,))
        row = cursor.fetchone()
        if not row:
            return {"success": False, "error": f"Recommendation {recommendation_id} not found."}

        lead_id = row["lead_id"]
        scenario = row["scenario"]
        next_action = row["next_action"]
        rec_date = row["recommended_date"]
        final_draft = modified_draft if (clean_action == "Modified" and modified_draft) else row["english_whatsapp_draft"]

        promoted_schedule_id = None

        if clean_action in ["Approved", "Modified"]:
            # Promote to scheduled follow-up in database
            target_time = f"{rec_date} 14:30:00"
            sched_res = database.schedule_single_followup(
                lead_id=lead_id,
                scheduled_for=target_time,
                channel="WhatsApp",
                message=final_draft,
                followup_reason=f"Shadow Mode Recommendation: {scenario}",
                next_action=next_action,
                priority=row["priority"],
                task_summary=f"[{scenario}] {next_action}"
            )
            promoted_schedule_id = sched_res.get("schedule_id")

        # Update recommendation status in DB
        database.update_shadow_recommendation_status(
            recommendation_id=recommendation_id,
            status=clean_action,
            reviewer_notes=reviewer_notes,
            modified_draft=modified_draft,
            promoted_schedule_id=promoted_schedule_id
        )

        return {
            "success": True,
            "status": clean_action,
            "recommendation_id": recommendation_id,
            "promoted_schedule_id": promoted_schedule_id
        }
    finally:
        conn.close()
