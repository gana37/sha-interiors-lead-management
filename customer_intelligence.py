"""
customer_intelligence.py - Customer 360° Dossier & Consultation Assistant
SHA Interface Interiors - AI-Powered Lead Management System

Compiles comprehensive client dossiers from SQLite, retrieves full interaction and
follow-up histories, identifies missing profile data, prescribes consultation questions,
and generates bespoke preliminary design recommendations.
"""

import sys
from typing import Dict, List, Optional, Any
import database
import sales_intelligence
import design_knowledge

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def build_customer_360_dossier(lead_id: str, db_path: str = database.DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """
    Assembles a complete 360-degree client brief using verified SQLite records.
    """
    lead = database.get_lead_by_id(lead_id.strip(), db_path=db_path)
    if not lead:
        return None

    # Retrieve interaction history
    activity_logs = database.get_activity_logs_for_lead(lead_id, db_path=db_path) if hasattr(database, "get_activity_logs_for_lead") else []

    # Retrieve follow-up history
    conn = database.get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT schedule_id, scheduled_for, channel, message, status, attempt_number, completed_at, stop_reason "
            "FROM FOLLOW_UP_SCHEDULE WHERE lead_id = ? ORDER BY scheduled_for ASC;",
            (lead_id,)
        )
        followups = [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

    # Score explanation
    score_details = sales_intelligence.explain_lead_score(lead)

    # Missing information audit
    missing_fields = []
    if not lead.get("email") or "@" not in str(lead.get("email")):
        missing_fields.append("Email Address (Required for 3D render sharing & official quotations)")
    if not lead.get("customer_requirements") or len(str(lead.get("customer_requirements")).strip()) < 15:
        missing_fields.append("Specific Room-by-room Requirements & Layout Preferences")
    if lead.get("property_status") == "Unspecified" or not lead.get("property_status"):
        missing_fields.append("Property Handover / Site Readiness Status")
    if lead.get("project_timeline") == "Flexible / Exploring":
        missing_fields.append("Firm Move-in / Handover Target Date")

    # Generate bespoke consultation questions targeting missing information
    consultation_questions = sales_intelligence.generate_sales_consultation_questions(lead)

    # Tailored style recommendations
    p_type = lead.get("project_type", "2BHK")
    budget = lead.get("budget_range", "₹5 lakh–₹10 lakh")

    recommended_styles = []
    if "Above ₹25" in budget or "Villa" in p_type:
        recommended_styles.append("luxury")
        recommended_styles.append("contemporary")
    elif "₹10 lakh–₹25" in budget:
        recommended_styles.append("contemporary")
        recommended_styles.append("modern")
    else:
        recommended_styles.append("scandinavian")
        recommended_styles.append("space_saving")

    design_tips = []
    for s_key in recommended_styles:
        s_info = design_knowledge.get_style_info(s_key)
        if s_info:
            design_tips.append({
                "style": s_info["title"],
                "reason": f"Matches {p_type} in {lead.get('city')} with {budget} allocation.",
                "palette": ", ".join(s_info["color_palette"][:3]),
                "materials": ", ".join(s_info["materials"][:3])
            })

    return {
        "lead_id": lead.get("lead_id"),
        "customer_name": lead.get("customer_name"),
        "phone": lead.get("phone"),
        "email": lead.get("email") or "Not provided",
        "city": lead.get("city"),
        "lead_source": lead.get("lead_source"),
        "budget_range": lead.get("budget_range"),
        "project_type": lead.get("project_type"),
        "property_status": lead.get("property_status"),
        "project_timeline": lead.get("project_timeline"),
        "scope_of_work": lead.get("scope_of_work"),
        "customer_requirements": lead.get("customer_requirements") or "No custom notes recorded.",
        "purchase_readiness": lead.get("purchase_readiness"),
        "lead_status": lead.get("lead_status"),
        "is_opted_out": bool(lead.get("is_opted_out", 0)),
        "score_details": score_details,
        "activity_logs": activity_logs,
        "followup_history": followups,
        "missing_fields": missing_fields,
        "consultation_questions": consultation_questions,
        "design_recommendations": design_tips,
        "created_at": lead.get("created_at")
    }


def format_customer_360_markdown(dossier: Dict[str, Any]) -> str:
    """Formats the customer 360 dossier into an executive briefing document."""
    s = dossier["score_details"]
    p_badge = "🟢 High Priority" if s["priority"] == "High" else ("🟡 Medium Priority" if s["priority"] == "Medium" else "🔴 Low Priority")

    md = (
        f"## 👤 Customer 360° Consultation Brief: {dossier['customer_name']} (`{dossier['lead_id']}`)\n\n"
        f"**Status:** `{dossier['lead_status']}` | **Priority:** **{p_badge}** | **Score:** **{s['total_score']:.0f}/100**\n\n"
        f"### 📍 Project Profile\n"
        f"- **Location:** {dossier['city']} ({dossier['lead_source']})\n"
        f"- **Project Type:** {dossier['project_type']} ({dossier['scope_of_work']})\n"
        f"- **Budget Allocation:** **{dossier['budget_range']}**\n"
        f"- **Property Readiness:** {dossier['property_status']} (Timeline: {dossier['project_timeline']})\n"
        f"- **Buying Urgency:** {dossier['purchase_readiness']}\n"
        f"- **Client Notes:** *\"{dossier['customer_requirements']}\"*\n\n"
        f"### 📊 Lead Score Breakdown\n"
        f"- **Budget Suitability:** {s['breakdown']['budget']['points']}/30 — {s['breakdown']['budget']['explanation']}\n"
        f"- **Location Suitability:** {s['breakdown']['location']['points']}/20 — {s['breakdown']['location']['explanation']}\n"
        f"- **Requirements Clarity:** {s['breakdown']['requirements']['points']}/20 — {s['breakdown']['requirements']['explanation']}\n"
        f"- **Purchase Readiness:** {s['breakdown']['readiness']['points']}/30 — {s['breakdown']['readiness']['explanation']}\n\n"
    )

    if dossier["missing_fields"]:
        md += "### ⚠️ Missing Information to Clarify:\n"
        for mf in dossier["missing_fields"]:
            md += f"- ❓ **{mf}**\n"
        md += "\n"

    md += "### 🎯 Suggested Sales Discovery Questions:\n"
    for idx, q in enumerate(dossier["consultation_questions"], 1):
        md += f"{idx}. {q}\n"
    md += "\n"

    if dossier["design_recommendations"]:
        md += "### 🎨 Recommended Design Concepts:\n"
        for dr in dossier["design_recommendations"]:
            md += f"- **{dr['style']}:** {dr['reason']} *Palette: {dr['palette']} | Materials: {dr['materials']}*\n"
        md += "\n"

    # Follow-up schedule table
    fu_list = dossier["followup_history"]
    if fu_list:
        md += "### 📅 Follow-Up History & Scheduled Touchpoints:\n"
        md += "| Attempt | Channel | Scheduled For | Status | Action |\n|:---:|:---:|:---:|:---:|:---|\n"
        for fu in fu_list:
            md += f"| #{fu['attempt_number']} | {fu['channel']} | {fu['scheduled_for'][:16]} | `{fu['status']}` | {fu['message'][:40]}... |\n"
    else:
        md += "### 📅 Follow-Up Status: *No follow-up tasks currently scheduled.*\n"

    return md
