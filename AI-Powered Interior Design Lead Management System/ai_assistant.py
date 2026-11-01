import os
import json
import re
from typing import Dict, List, Optional, Any
import database
import lead_scoring
import followup_templates

# Retrieve optional API key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

def is_ai_api_available() -> bool:
    """Checks whether a valid Gemini API key is configured."""
    return bool(GEMINI_API_KEY and len(GEMINI_API_KEY.strip()) > 10)

def summarize_customer_requirements(lead: Dict[str, Any]) -> str:
    """Summarizes customer requirements from CRM details."""
    name = lead.get("customer_name", "Client")
    p_type = lead.get("project_type", "Residential")
    city = lead.get("city", "Unknown City")
    budget = lead.get("budget_range", "Standard")
    status = lead.get("property_status", "Unspecified")
    timeline = lead.get("project_timeline", "Standard")
    scope = lead.get("scope_of_work", "Full Interiors")
    notes = lead.get("customer_requirements") or "No custom notes recorded."
    
    summary = (
        f"**Requirement Summary for {name} ({lead.get('lead_id')}):**\n"
        f"- **Project:** {p_type} in {city} ({scope})\n"
        f"- **Budget Allocation:** {budget}\n"
        f"- **Possession & Urgency:** {status} (Desired timeline: {timeline})\n"
        f"- **Client Notes:** \"{notes}\"\n"
        f"- **Qualification:** {lead.get('priority', 'Medium')} Priority (Score: {lead.get('lead_score', '—')}/100)"
    )
    return summary

def recommend_next_action(lead: Dict[str, Any]) -> Dict[str, Any]:
    """Recommends next operational sales action based on priority, readiness, and status."""
    priority = lead.get("priority", "Medium")
    readiness = lead.get("purchase_readiness", "Budget Planning")
    status = lead.get("lead_status", "New")
    city = lead.get("city", "Bangalore")
    p_type = lead.get("project_type", "2BHK")
    
    if status == "Converted":
        return {
            "recommended_action": "Onboard Project to 3D Design Team",
            "urgency": "Low (Deal Closed)",
            "rationale": "Client is converted. Transition customer to Project Execution Manager and assign senior 3D CAD designer."
        }
    if status == "Lost":
        return {
            "recommended_action": "Archive Lead / Semi-Annual Re-engagement",
            "urgency": "None",
            "rationale": "Deal closed as Lost. Schedule future catalog broadcast in 6 months."
        }
    if lead.get("is_opted_out") == 1:
        return {
            "recommended_action": "Do Not Contact (Opt-out Active)",
            "urgency": "None",
            "rationale": "Client opted out. Strictly respect contact preferences."
        }
    if lead.get("last_customer_response"):
        return {
            "recommended_action": "Direct Phone Call by Senior Consultant",
            "urgency": "Immediate (Within 2 Hours)",
            "rationale": f"Customer actively responded: \"{lead['last_customer_response']}\". Take over from automated cadence and confirm client query."
        }
    if priority == "High":
        if readiness == "Ready to Start":
            return {
                "recommended_action": f"Schedule On-Site Measurement & Studio Visit in {city}",
                "urgency": "Immediate (Same-Day)",
                "rationale": f"High Priority client with prime budget seeking immediate start for {p_type}. Offer free spatial consultation."
            }
        else:
            return {
                "recommended_action": "Share Curated 3D Portfolio & Budget Comparison",
                "urgency": "High (Within 24 Hours)",
                "rationale": "Client actively comparing vendors. Showcase completed projects in their local city to demonstrate superior craftsmanship."
            }
    elif priority == "Medium":
        return {
            "recommended_action": "Send Introductory Space Planning Lookbook",
            "urgency": "Standard (Within 48 Hours)",
            "rationale": "Nurture client with modular kitchen & wardrobe finish samples to refine project scope."
        }
    else:
        return {
            "recommended_action": "Automated Digital Catalog Delivery",
            "urgency": "Low (Follow standard schedule)",
            "rationale": "Client is just exploring. Keep engaged with low-touch digital lookbooks."
        }

def answer_crm_query(query: str, db_path: str = database.DEFAULT_DB_PATH) -> str:
    """
    Answers natural language questions about CRM records using factual SQLite data.
    Works reliably both with Gemini API (if key present) and local SQL-based intent engine (fallback).
    """
    q_lower = query.lower().strip()
    
    # Check if Gemini API is available and can be called
    if is_ai_api_available():
        try:
            # Prepare compact CRM context
            stats = database.get_lead_stats(db_path)
            high_leads = database.get_all_leads(db_path=db_path, priority="High", order_by="lead_score DESC")[:10]
            summary_context = {
                "total_leads": stats["total_leads"],
                "high_priority_count": stats["priority_counts"].get("High", 0),
                "medium_priority_count": stats["priority_counts"].get("Medium", 0),
                "low_priority_count": stats["priority_counts"].get("Low", 0),
                "average_score": stats["avg_score"],
                "top_cities": stats["top_cities"],
                "sample_high_leads": [
                    {"name": l["customer_name"], "city": l["city"], "budget": l["budget_range"], "score": l["lead_score"]}
                    for l in high_leads
                ]
            }
            prompt = (
                f"You are the SHA Interface Interiors CRM AI Assistant. "
                f"Answer the user's question accurately using ONLY this real CRM data: {json.dumps(summary_context)}.\n"
                f"User Question: {query}\n"
                f"Keep answers professional, concise, and focused on interior design sales."
            )
            # Invoke Gemini REST API
            import urllib.request
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            # Fall back to local engine seamlessly
            pass

    # =========================================================================
    # BUILT-IN CRM INTELLIGENCE ENGINE (Factual Local Fallback)
    # =========================================================================
    stats = database.get_lead_stats(db_path)
    
    # 1. High priority counts
    if "high priority" in q_lower or "high-priority" in q_lower:
        hp_count = stats["priority_counts"].get("High", 0)
        
        # Check city filter in query
        matched_city = None
        for c in ["bangalore", "hyderabad", "chennai", "mumbai", "pune", "delhi"]:
            if c in q_lower:
                matched_city = c.capitalize()
                break
                
        if matched_city:
            city_hp = database.get_all_leads(db_path=db_path, city=matched_city, priority="High")
            lines = [f"- **{l['customer_name']}** ({l['lead_id']}): {l['project_type']}, Budget: {l['budget_range']} (Score: {l['lead_score']:.0f})" for l in city_hp[:5]]
            return (
                f"📍 We currently have **{len(city_hp)} High-Priority leads** in **{matched_city}**.\n\n"
                f"Top inquiries:\n" + "\n".join(lines)
            )
        else:
            return (
                f"🔥 We have **{hp_count} High-Priority leads** across all markets "
                f"(average score: {stats['avg_score']}/100). "
                f"These clients represent high-margin turnkey projects ready for immediate engagement."
            )

    # 2. Follow-ups due today
    if "follow-up" in q_lower or "due" in q_lower or "followups" in q_lower:
        fu_stats = database.get_followup_stats(db_path)
        due_list = database.get_followups(db_path=db_path, status="Scheduled", limit=5)
        if due_list:
            items = [f"- **{f['customer_name']}** ({f['city']}): Attempt #{f['attempt_number']} via {f['channel']} scheduled for {f['scheduled_for']}" for f in due_list]
            return (
                f"⏰ **Follow-up Status:** There are **{fu_stats['scheduled_count']} scheduled follow-ups** in the pipeline.\n\n"
                f"Upcoming touches:\n" + "\n".join(items)
            )
        else:
            return f"✅ There are currently no overdue follow-ups. Total scheduled tasks: {fu_stats['scheduled_count']}."

    # 3. Attention needed / urgent leads
    if "attention" in q_lower or "urgent" in q_lower or "immediate" in q_lower:
        urgent_leads = database.get_all_leads(db_path=db_path, priority="High", lead_status="New")
        if urgent_leads:
            items = [f"- **{l['customer_name']}** ({l['city']}): {l['project_type']} - {l['budget_range']} (Score: {l['lead_score']:.0f})" for l in urgent_leads[:5]]
            return (
                f"⚠️ **Attention Required:** There are **{len(urgent_leads)} High-Priority leads with status 'New'** awaiting initial qualification:\n\n"
                + "\n".join(items) + "\n\nAssign these leads to design consultants for immediate outreach."
            )
        else:
            return "✅ All High-Priority leads have been assigned or contacted. No urgent unassigned leads pending."

    # 4. Total leads / overview
    if "total" in q_lower or "how many leads" in q_lower or "summary" in q_lower:
        return (
            f"📊 **SHA Interface Interiors CRM Summary:**\n"
            f"- **Total Active Leads:** {stats['total_leads']}\n"
            f"- **Priority Split:** 🟢 {stats['priority_counts'].get('High', 0)} High | 🟡 {stats['priority_counts'].get('Medium', 0)} Medium | 🔴 {stats['priority_counts'].get('Low', 0)} Low\n"
            f"- **Pipeline Stages:** New: {stats['status_counts'].get('New', 0)} | Qualified: {stats['status_counts'].get('Qualified', 0)} | Follow-up: {stats['status_counts'].get('Follow-up', 0)} | Converted: {stats['status_counts'].get('Converted', 0)} | Lost: {stats['status_counts'].get('Lost', 0)}\n"
            f"- **Average Lead Score:** {stats['avg_score']}/100"
        )

    # 5. Default intelligent response
    return (
        f"I have reviewed the CRM database. We currently track **{stats['total_leads']} leads** with an average qualification score of **{stats['avg_score']}/100**.\n"
        f"You can ask me questions like:\n"
        f"- *'How many high-priority leads do we have?'*\n"
        f"- *'Show high-priority leads in Bangalore or Hyderabad'*\n"
        f"- *'Which leads need immediate attention?'*\n"
        f"- *'What are the follow-up tasks scheduled?'*"
    )
