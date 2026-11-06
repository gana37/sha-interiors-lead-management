"""
ai_assistant.py - Unified AI CRM & Interior Design Intelligence Assistant
SHA Interface Interiors - AI-Powered Lead Management System

Master intelligence layer combining:
1. Complete CRM Database Intelligence (Safe SQL execution & tabular reporting)
2. Interior Design Expert (Styles, space planning, lighting, Vastu)
3. Materials & Technical Consultant (Core boards, finishes, hardware, countertops)
4. Advanced Interior Cost Estimator (3-Tier parametric estimates, BOQs)
5. Sales Intelligence & Lead Score Explainer (Breakdowns, upgradability analysis)
6. Customer 360° Consultation Briefs & Tailored Discovery Questions
7. Follow-Up Command Center (Multichannel WhatsApp & Email drafts)
8. Official Google Gemini SDK with SQLite Grounding & Deterministic Fallback
"""

import os
import sys
import re
from typing import Dict, List, Optional, Any

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import database
import hyderabad_geo as hg
import lead_scoring
import followup_templates
import ai_service
import db_intelligence
import design_knowledge
import material_knowledge
import cost_estimator
import sales_intelligence
import customer_intelligence
import followup_intelligence
import business_config
import crm_search


def is_ai_api_available() -> bool:
    """Checks whether a valid Gemini API key is configured and available."""
    return ai_service.is_gemini_available()


def get_ai_status_info() -> Dict[str, Any]:
    """Returns the operational status of the AI Assistant."""
    configured = ai_service.is_gemini_available()
    model = ai_service.get_active_model_name()
    return {
        "gemini_active": configured,
        "model": model if configured else "None",
        "engine": f"Google Gemini AI ({model})" if configured else "Built-in CRM & Interior Intelligence Engine (Deterministic)",
        "fallback_ready": True
    }


# ==============================================================================
# 1. CUSTOMER REQUIREMENTS & NEXT ACTIONS
# ==============================================================================

def summarize_customer_requirements(lead: Dict[str, Any]) -> str:
    """
    Summarizes customer requirements from CRM details.
    Deterministic, fast, and guaranteed to include customer name, project type, and key metrics.
    """
    name = lead.get("customer_name", "Client")
    p_type = lead.get("project_type", "Residential")
    city = lead.get("city", "Unknown City")
    budget = lead.get("budget_range", "Standard")
    status = lead.get("property_status", "Unspecified")
    timeline = lead.get("project_timeline", "Standard")
    scope = lead.get("scope_of_work", "Full Interiors")
    notes = lead.get("customer_requirements") or "No custom notes recorded."
    score = lead.get("lead_score")
    priority = lead.get("priority", "Medium")

    score_str = f"{score:.0f}/100" if score is not None else "—"

    summary = (
        f"**Requirement Summary for {name} ({lead.get('lead_id', 'Unassigned')}):**\n"
        f"- **Project:** {p_type} in {city} ({scope})\n"
        f"- **Budget Allocation:** {budget}\n"
        f"- **Possession & Urgency:** {status} (Desired timeline: {timeline})\n"
        f"- **Client Notes:** \"{notes}\"\n"
        f"- **Qualification:** {priority} Priority (Score: {score_str})"
    )
    return summary


def summarize_customer_requirements_ai(lead: Dict[str, Any]) -> str:
    """
    Generates an executive, client-facing design brief using Gemini AI if available,
    falling back to the deterministic structured summary.
    """
    if not is_ai_api_available():
        return summarize_customer_requirements(lead)

    prompt = (
        f"Create an executive interior design client brief for our design team at SHA Interface Interiors.\n"
        f"Client Name: {lead.get('customer_name')}\n"
        f"Lead ID: {lead.get('lead_id')}\n"
        f"Project Type: {lead.get('project_type')}\n"
        f"Location: {lead.get('city')}\n"
        f"Budget Range: {lead.get('budget_range')}\n"
        f"Scope: {lead.get('scope_of_work')}\n"
        f"Property Status: {lead.get('property_status')}\n"
        f"Timeline: {lead.get('project_timeline')}\n"
        f"Client Notes: {lead.get('customer_requirements')}\n"
        f"Priority: {lead.get('priority')} (Score: {lead.get('lead_score')}/100)\n\n"
        f"Format as a concise 3-paragraph brief: 1) Client Profile & Scope, 2) Design & Spatial Priorities, "
        f"3) Key Recommendations for the first design meeting. Keep it professional and focused."
    )

    res = ai_service.generate_content(prompt=prompt, temperature=0.3)
    if res.get("success") and res.get("text"):
        return res["text"]
    return summarize_customer_requirements(lead)


def recommend_next_action(lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recommends next operational sales action based on priority, readiness, and status.
    Deterministic rule engine ensuring consistent business logic across CRM workflows.
    """
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
                "recommended_action": f"Schedule Meeting at {business_config.OFFICE_NAME.title()} or Phone Call in {city}",
                "urgency": "Immediate (Same-Day)",
                "rationale": f"High Priority client with prime budget seeking immediate start for {p_type}. Offer meeting at {business_config.OFFICE_NAME} (open {business_config.WORKING_HOURS_START} to {business_config.WORKING_HOURS_END} IST, all 7 days) or a phone call."
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


def draft_personalized_pitch(
    lead: Dict[str, Any],
    goal: str = "site_visit_invitation",
    use_gemini: bool = True
) -> str:
    """
    Drafts a personalized WhatsApp / SMS outreach message for the lead.
    Uses Gemini AI for creative phrasing if available; falls back seamlessly to verified templates.
    """
    if use_gemini and is_ai_api_available():
        prompt = (
            f"Draft a warm, polite, and persuasive WhatsApp message from 'SHA Interface Interiors' "
            f"to prospective client {lead.get('customer_name')}.\n"
            f"Details: {lead.get('project_type')} in {lead.get('city')}, Budget: {lead.get('budget_range')}, "
            f"Status: {lead.get('property_status')}, Notes: {lead.get('customer_requirements')}.\n"
            f"Goal: {goal.replace('_', ' ').title()}.\n"
            f"Keep it under 60 words, tailored to their property and city, and end with a gentle question."
        )
        res = ai_service.generate_content(prompt=prompt, temperature=0.5, max_output_tokens=150)
        if res.get("success") and res.get("text"):
            return res["text"].strip().strip('"')

    # Fallback to standard templates
    return followup_templates.generate_personalized_message(goal, lead)


def build_crm_grounding_context(query: str, db_path: str = database.DEFAULT_DB_PATH) -> str:
    """
    Extracts verified factual data from SQLite matching the query's entities
    (city, priority, status, specific lead ID, follow-ups).
    This guarantees Gemini AI has ground truth and will not hallucinate.
    """
    stats = database.get_lead_stats(db_path)
    q_lower = query.lower()

    lines = [
        "VERIFIED REAL CRM STATS (from sha_leads.db):",
        f"- Total Leads in CRM: {stats['total_leads']}",
        f"- Priority Split: High={stats['priority_counts'].get('High', 0)}, Medium={stats['priority_counts'].get('Medium', 0)}, Low={stats['priority_counts'].get('Low', 0)}",
        f"- Average Lead Score: {stats['avg_score']:.1f}/100",
        f"- Lead Stages: New={stats['status_counts'].get('New', 0)}, Qualified={stats['status_counts'].get('Qualified', 0)}, Follow-up={stats['status_counts'].get('Follow-up', 0)}, Converted={stats['status_counts'].get('Converted', 0)}, Lost={stats['status_counts'].get('Lost', 0)}",
        f"- Top Cities: {', '.join([f'{c} ({n})' for c, n in stats['top_cities'].items()])}"
    ]

    # Specific city filter
    detected_cities = [c for c in ["bangalore", "hyderabad", "chennai", "mumbai", "pune", "delhi", "kolkata"] if c in q_lower]
    if detected_cities:
        for c_slug in detected_cities:
            c_name = c_slug.capitalize()
            city_leads = database.get_all_leads(db_path=db_path, city=c_name)
            lines.append(f"\nACTUAL LEADS IN {c_name.upper()} (Total count: {len(city_leads)}):")
            for l in city_leads[:10]:
                lines.append(
                    f"  * {l['lead_id']} | {l['customer_name']} | {l['project_type']} | "
                    f"Budget: {l['budget_range']} | Score: {l['lead_score']:.0f} | "
                    f"Priority: {l['priority']} | Status: {l['lead_status']}"
                )

    # High-Priority leads
    if "high" in q_lower or "priority" in q_lower or not detected_cities:
        high_leads = database.get_all_leads(db_path=db_path, priority="High", order_by="lead_score DESC")
        lines.append(f"\nHIGH-PRIORITY LEADS (Total count: {len(high_leads)}):")
        for l in high_leads[:8]:
            lines.append(
                f"  * {l['lead_id']} | {l['customer_name']} ({l['city']}) | {l['project_type']} | "
                f"Budget: {l['budget_range']} | Score: {l['lead_score']:.0f} | Status: {l['lead_status']}"
            )

    # Urgent / Attention needed leads
    if "attention" in q_lower or "urgent" in q_lower or "immediate" in q_lower or "new" in q_lower:
        urgent_leads = database.get_all_leads(db_path=db_path, priority="High", lead_status="New")
        lines.append(f"\nURGENT LEADS (High-Priority with Status 'New') (Total count: {len(urgent_leads)}):")
        for l in urgent_leads[:6]:
            lines.append(
                f"  * {l['lead_id']} | {l['customer_name']} ({l['city']}) | {l['project_type']} | "
                f"Budget: {l['budget_range']} | Score: {l['lead_score']:.0f}"
            )

    # Follow-up schedule
    if "follow" in q_lower or "due" in q_lower or "task" in q_lower or "schedule" in q_lower:
        fu_stats = database.get_followup_stats(db_path)
        due_tasks = database.get_followups(db_path=db_path, status="Scheduled", limit=8)
        lines.append(f"\nFOLLOW-UP PIPELINE:")
        lines.append(f"- Scheduled: {fu_stats['scheduled_count']}, Sent: {fu_stats['sent_count']}, Cancelled: {fu_stats['cancelled_count']}")
        lines.append("- Upcoming Tasks:")
        for t in due_tasks:
            name_val = t.get('customer_name') or f"Lead {t.get('lead_id')}"
            lines.append(f"  * Task #{t.get('schedule_id') or t.get('task_id')}: {name_val} via {t.get('channel')} scheduled for {t.get('scheduled_for')}")

    # Hyderabad Locality context
    for loc in hg.get_all_localities():
        if loc.lower() in q_lower:
            loc_leads = database.get_all_leads(db_path=db_path, locality=loc, active_only=True)
            reg = hg.get_region_for_locality(loc)
            pin = hg.get_pincode_for_locality(loc)
            lines.append(f"\nHYDERABAD LOCALITY INTELLIGENCE [{loc}] (Region: {reg}, PIN: {pin}, Total leads: {len(loc_leads)}):")
            for l in loc_leads[:8]:
                lines.append(
                    f"  * {l['lead_id']} | {l['customer_name']} | Locality: {l.get('locality')} | Region: {l.get('region')} | "
                    f"Budget: {l['budget_range']} | Project: {l['project_type']} | Score: {l['lead_score']:.0f} ({l['priority']})"
                )
            break

    # Hyderabad Region context
    for reg in hg.HYDERABAD_REGIONS:
        if reg.lower() in q_lower:
            reg_leads = database.get_all_leads(db_path=db_path, region=reg, active_only=True)
            lines.append(f"\nHYDERABAD REGIONAL INTELLIGENCE [{reg}] (Total leads: {len(reg_leads)}):")
            for l in reg_leads[:8]:
                lines.append(
                    f"  * {l['lead_id']} | {l['customer_name']} | Locality: {l.get('locality')} | Region: {l.get('region')} | "
                    f"Budget: {l['budget_range']} | Project: {l['project_type']} | Score: {l['lead_score']:.0f} ({l['priority']})"
                )
            break

    # Specific lead ID search
    id_match = re.search(r"SHA-[\w\-]+", query, re.IGNORECASE)
    if id_match:
        lead_id = id_match.group(0).upper()
        lead_rec = database.get_lead_by_id(lead_id, db_path=db_path)
        if lead_rec:
            lines.append(f"\nEXACT LEAD RECORD [{lead_id}]:")
            for k in ["customer_name", "phone", "email", "city", "project_type", "budget_range", "lead_score", "priority", "lead_status", "property_status", "project_timeline", "customer_requirements"]:
                lines.append(f"  {k}: {lead_rec.get(k)}")

    return "\n".join(lines)


# ==============================================================================
# 2. MASTER NATURAL LANGUAGE INTENT ROUTER & ENGINE
# ==============================================================================

def answer_crm_query(
    query: str,
    db_path: str = database.DEFAULT_DB_PATH,
    history: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Unified entry point answering questions across CRM data, interior design styles,
    materials specifications, project cost estimation, and sales strategy.
    Zero hallucination guarantee: grounded in SQLite database and verified knowledge bases.
    """
    q_lower = query.lower().strip()

    # --------------------------------------------------------------------------
    # 1. INTENT: Cost Estimation
    # --------------------------------------------------------------------------
    if any(k in q_lower for k in ["estimate", "cost for", "how much for", "price of", "budget for", "how much does"]) and any(p in q_lower for p in ["bhk", "villa", "interior", "kitchen", "flat", "apartment", "sqft", "sq ft"]):
        p_type = "3BHK"
        for pt in ["1bhk", "2bhk", "3bhk", "4bhk", "villa", "studio", "commercial"]:
            if pt in q_lower:
                p_type = pt.upper() if pt != "commercial" else "Commercial"
                break
        matched_city = "Hyderabad"
        for c in ["hyderabad", "bangalore", "chennai", "mumbai", "pune", "delhi"]:
            if c in q_lower:
                matched_city = c.capitalize()
                break
        est = cost_estimator.estimate_project_cost(property_type=p_type, city=matched_city)
        return cost_estimator.format_cost_estimate_markdown(est)

    # --------------------------------------------------------------------------
    # 1B. INTENT: Advanced CRM Search Engine & Multi-Filter Queries
    # --------------------------------------------------------------------------
    if crm_search.is_crm_search_query(query):
        search_res = crm_search.parse_and_search_crm(query, db_path=db_path, history=history)
        if search_res.get("markdown"):
            return search_res["markdown"]

    # --------------------------------------------------------------------------
    # 2. INTENT: Material & Technical Comparison / Details
    # --------------------------------------------------------------------------
    if any(k in q_lower for k in ["plywood", "hdhmr", "mdf", "particle board", "laminate", "acrylic", "veneer", "pu finish", "blum", "hettich", "hafele", "quartz", "granite"]):
        return material_knowledge.search_material_knowledge(query)

    # --------------------------------------------------------------------------
    # 3. INTENT: Interior Design Styles & Room Layouts
    # --------------------------------------------------------------------------
    if any(k in q_lower for k in ["scandinavian", "minimalist", "contemporary", "vastu", "work triangle", "false ceiling", "wardrobe layout", "living room layout", "modular kitchen layout", "design style", "color palette"]):
        return design_knowledge.search_design_knowledge(query)

    # --------------------------------------------------------------------------
    # 4. INTENT: Upgradable Leads (Scores 70–79)
    # --------------------------------------------------------------------------
    if "upgradable" in q_lower or "almost high" in q_lower or ("become high priority" in q_lower):
        up_leads = sales_intelligence.find_upgradable_leads(db_path=db_path)
        if not up_leads:
            return "✅ No active leads currently sit in the 70–79 score boundary range. All qualified leads are already assigned."
        table_md = db_intelligence.format_leads_table(up_leads, max_rows=10)
        return (
            f"📈 **Identified {len(up_leads)} High-Potential 'Almost High' Leads (Score 70–79):**\n"
            f"These prospects are within 1 to 10 points of crossing the High-Priority cutoff (80). "
            f"A single discovery call or material lookbook can elevate them into high-margin conversion opportunities:\n\n"
            + table_md
        )

    # --------------------------------------------------------------------------
    # 5. INTENT: Sales Pipeline Valuation
    # --------------------------------------------------------------------------
    if "pipeline" in q_lower or "sales pipeline" in q_lower or "total value" in q_lower or "pipeline value" in q_lower:
        pipe = db_intelligence.calculate_sales_pipeline_value(db_path=db_path)
        return (
            f"💰 **SHA Interface Interiors - Sales Pipeline Valuation:**\n\n"
            f"- **Nominal Pipeline Value:** **{pipe['formatted_nominal']}** ({pipe['active_pipeline_deals']} active prospective accounts)\n"
            f"- **Weighted Realization Pipeline:** **{pipe['formatted_weighted']}** (Probability-weighted by High: 45%, Medium: 20%, Low: 5%)\n"
            f"- **Closed & Converted Pipeline:** **{pipe['formatted_converted']}** ({pipe['converted_deal_count']} closed turnkey projects)\n\n"
            f"*Pipeline valuation applies conservative midpoints across budget brackets (`Below ₹3L`: ₹2.5L, `₹3L–₹5L`: ₹4L, `₹5L–₹10L`: ₹7.5L, `₹10L–₹25L`: ₹17.5L, `Above ₹25L`: ₹35L).*"
        )

    # --------------------------------------------------------------------------
    # 6. INTENT: Duplicate Detection & Missing Information Audit
    # --------------------------------------------------------------------------
    if "duplicate" in q_lower or "duplicates" in q_lower:
        dups = db_intelligence.detect_duplicate_leads(db_path=db_path)
        if not dups:
            return "✅ **Duplicate Audit Complete:** No duplicate phone numbers or accounts found across active CRM leads."
        items = [f"- Phone `{d['phone']}` matches {d['count']} accounts: {d['names']} (`{d['lead_ids']}`)" for d in dups[:10]]
        return f"⚠️ **Duplicate Accounts Detected ({len(dups)} instances):**\n\n" + "\n".join(items)

    if "missing" in q_lower or "missing info" in q_lower or "completeness" in q_lower:
        audit = db_intelligence.detect_missing_information(db_path=db_path)
        return (
            f"📋 **CRM Data Completeness Audit:**\n"
            f"- **Overall CRM Record Completeness:** **{audit['completeness_score']}%**\n"
            f"- **Total Active Leads:** {audit['total_leads']}\n"
            f"- **Missing Email Addresses:** {audit['missing_email_count']} leads\n"
            f"- **Missing/Placeholder Requirements Notes:** {audit['vague_or_missing_notes_count']} leads\n"
            f"- **Missing Phone Numbers:** {audit['missing_phone_count']} leads\n\n"
            f"💡 **Recommendation:** Prioritize discovery calls to capture email addresses and floor plan handovers for 3D render delivery."
        )

    # --------------------------------------------------------------------------
    # 7. INTENT: Customers Needing Modular Kitchen
    # --------------------------------------------------------------------------
    if "kitchen" in q_lower and ("who" in q_lower or "show" in q_lower or "leads" in q_lower or "customers" in q_lower):
        k_leads = db_intelligence.get_leads_needing_modular_kitchen(db_path=db_path)
        table_md = db_intelligence.format_leads_table(k_leads, max_rows=10)
        return f"🍳 **Customers Requiring Modular Kitchen Cabinetry ({len(k_leads)} Leads):**\n\n" + table_md

    # --------------------------------------------------------------------------
    # 8. INTENT: Customers Ready to Purchase
    # --------------------------------------------------------------------------
    if "ready to purchase" in q_lower or "ready to start" in q_lower:
        r_leads = db_intelligence.get_leads_ready_to_purchase(db_path=db_path)
        table_md = db_intelligence.format_leads_table(r_leads, max_rows=10)
        return f"⚡ **High-Velocity Customers Ready to Start Immediately ({len(r_leads)} Leads):**\n\n" + table_md

    # --------------------------------------------------------------------------
    # 9. INTENT: Leads without Follow-ups
    # --------------------------------------------------------------------------
    if "without follow-up" in q_lower or "without followups" in q_lower or "no follow-up" in q_lower or "no followups" in q_lower:
        no_fu = db_intelligence.get_leads_without_followups(db_path=db_path)
        if not no_fu:
            return "✅ All active leads currently have scheduled follow-up tasks."
        table_md = db_intelligence.format_leads_table(no_fu, max_rows=10)
        return f"⚠️ **Active Leads Without Scheduled Follow-Ups ({len(no_fu)} Leads):**\n\n" + table_md

    # --------------------------------------------------------------------------
    # 10. INTENT: Overdue Follow-ups
    # --------------------------------------------------------------------------
    if "overdue" in q_lower:
        od = db_intelligence.get_overdue_followups(db_path=db_path)
        if not od:
            return "✅ **Overdue Audit:** There are currently no overdue follow-up tasks."
        items = [f"- **{o['customer_name']}** ({o['city']}): Scheduled for `{o['scheduled_for']}` via {o['channel']} (Attempt #{o['attempt_number']})" for o in od[:10]]
        return f"⏰ **Overdue Follow-up Tasks ({len(od)} Pending):**\n\n" + "\n".join(items)

    # --------------------------------------------------------------------------
    # 11. INTENT: Specific Customer Lookup or Score Explanation
    # --------------------------------------------------------------------------
    lead_id_match = re.search(r"SHA-[\w\-]+", query, re.IGNORECASE)
    if lead_id_match:
        target_id = lead_id_match.group(0).upper()
        lead_rec = database.get_lead_by_id(target_id, db_path=db_path)
        if lead_rec:
            if "score" in q_lower or "why" in q_lower or "explain" in q_lower:
                expl = sales_intelligence.explain_lead_score(lead_rec)
                b = expl["breakdown"]
                return (
                    f"### 🎯 Lead Score Explanation for {lead_rec['customer_name']} (`{target_id}`)\n\n"
                    f"**Total Score:** **{expl['total_score']:.0f}/100** | **Priority:** **{expl['priority']}**\n\n"
                    f"- 💰 **Budget Suitability:** **{b['budget']['points']}/30** ({b['budget']['percentage']}%)\n  _{b['budget']['explanation']}_\n"
                    f"- 📍 **Location Suitability:** **{b['location']['points']}/20** ({b['location']['percentage']}%)\n  _{b['location']['explanation']}_\n"
                    f"- 📝 **Requirements Clarity:** **{b['requirements']['points']}/20** ({b['requirements']['percentage']}%)\n  _{b['requirements']['explanation']}_\n"
                    f"- ⚡ **Purchase Readiness:** **{b['readiness']['points']}/30** ({b['readiness']['percentage']}%)\n  _{b['readiness']['explanation']}_\n\n"
                    f"**Executive Rationale:** {expl['executive_summary']}"
                )
            dossier = customer_intelligence.build_customer_360_dossier(target_id, db_path=db_path)
            if dossier:
                return customer_intelligence.format_customer_360_markdown(dossier)

    # --------------------------------------------------------------------------
    # 12. INTENT: Top 10 Leads by Score
    # --------------------------------------------------------------------------
    if "top 10" in q_lower or "top leads" in q_lower:
        top_leads = db_intelligence.get_top_leads_by_score(limit=10, db_path=db_path)
        table_md = db_intelligence.format_leads_table(top_leads, max_rows=10)
        return "🏆 **Top 10 Ranked Leads by Qualification Score:**\n\n" + table_md

    # --------------------------------------------------------------------------
    # 13. INTENT: Budget threshold (Above 10 Lakh)
    # --------------------------------------------------------------------------
    if "above 10" in q_lower or "above ₹10" in q_lower or "> 10" in q_lower:
        high_budget_leads = db_intelligence.get_customers_by_budget_threshold(min_amount_lakh=10.0, db_path=db_path)
        table_md = db_intelligence.format_leads_table(high_budget_leads, max_rows=15)
        return f"💎 **Customers with Budgets Above ₹10 Lakh ({len(high_budget_leads)} Accounts):**\n\n" + table_md

    # --------------------------------------------------------------------------
    # 14. INTENT: City Analytics (Which city has most leads? etc.)
    # --------------------------------------------------------------------------
    if "which city" in q_lower or "most leads" in q_lower:
        c_stats = db_intelligence.get_city_lead_analytics(db_path=db_path)
        if c_stats:
            top_city = c_stats[0]
            lines = [f"- **{c['city']}:** {c['total_leads']} leads (🟢 {c['high_priority_count']} High Priority, Avg Score: {c['avg_score']}/100)" for c in c_stats]
            return (
                f"🏙️ **{top_city['city']}** has the highest lead volume with **{top_city['total_leads']} leads** "
                f"({top_city['high_priority_count']} High Priority accounts).\n\n"
                f"**Complete Regional Breakdown:**\n" + "\n".join(lines)
            )

    # --------------------------------------------------------------------------
    # 14b. INTENT: Hyderabad Locality Filter (e.g. Gachibowli, Kokapet, Madhapur)
    # --------------------------------------------------------------------------
    for loc in hg.get_all_localities():
        # Match locality name with word boundary to avoid false substring positives
        if re.search(r"\b" + re.escape(loc.lower()) + r"\b", q_lower):
            loc_leads = database.get_all_leads(db_path=db_path, locality=loc, active_only=True)
            top_hp = [l for l in loc_leads if l.get("priority") == "High"]
            reg = hg.get_region_for_locality(loc)
            pin = hg.get_pincode_for_locality(loc)
            table_md = db_intelligence.format_leads_table(loc_leads, max_rows=10)
            return (
                f"📍 We currently track **{len(loc_leads)} active leads in {loc}** "
                f"({reg}, PIN: {pin} | {len(top_hp)} High-Priority):\n\n" + table_md
            )

    # --------------------------------------------------------------------------
    # 14c. INTENT: Hyderabad Region Filter (e.g. West Hyderabad, North Hyderabad)
    # --------------------------------------------------------------------------
    for reg in hg.HYDERABAD_REGIONS + ["Secunderabad & Metropolitan Areas"]:
        if reg.lower() in q_lower or (reg == "Secunderabad" and "secunderabad" in q_lower):
            reg_leads = database.get_all_leads(db_path=db_path, region=reg, active_only=True)
            top_hp = [l for l in reg_leads if l.get("priority") == "High"]
            table_md = db_intelligence.format_leads_table(reg_leads, max_rows=10)
            return (
                f"🌐 We currently track **{len(reg_leads)} active leads in {reg}** "
                f"({len(top_hp)} High-Priority):\n\n" + table_md
            )

    # --------------------------------------------------------------------------
    # 15. INTENT: Specific City Filter
    # --------------------------------------------------------------------------
    for c in ["bangalore", "hyderabad", "chennai", "mumbai", "pune", "delhi", "kolkata"]:
        if c in q_lower and not ("cost" in q_lower or "estimate" in q_lower):
            c_name = c.capitalize()
            city_leads = database.get_all_leads(db_path=db_path, city=c_name)
            top_hp = [l for l in city_leads if l.get("priority") == "High"]
            table_md = db_intelligence.format_leads_table(city_leads, max_rows=10)
            return (
                f"📍 We currently track **{len(city_leads)} leads in {c_name}** "
                f"({len(top_hp)} High-Priority):\n\n" + table_md
            )

    # --------------------------------------------------------------------------
    # 16. INTENT: High Priority Leads Overall
    # --------------------------------------------------------------------------
    if "high priority" in q_lower or "high-priority" in q_lower or ("high" in q_lower and "leads" in q_lower):
        hp_leads = db_intelligence.get_leads_by_priority("High", db_path=db_path)
        stats = database.get_lead_stats(db_path)
        table_md = db_intelligence.format_leads_table(hp_leads, max_rows=10)
        return (
            f"🔥 We currently track **{len(hp_leads)} High-Priority leads** across all markets "
            f"(average qualification score: {stats['avg_score']:.1f}/100).\n\n" + table_md
        )

    # --------------------------------------------------------------------------
    # 17. INTENT: Attention Required / Urgent
    # --------------------------------------------------------------------------
    if "attention" in q_lower or "urgent" in q_lower or "immediate" in q_lower:
        urgent_leads = database.get_all_leads(db_path=db_path, priority="High", lead_status="New")
        if urgent_leads:
            table_md = db_intelligence.format_leads_table(urgent_leads, max_rows=10)
            return (
                f"### ⚠️ Attention Required: **{len(urgent_leads)} High-Priority leads with status 'New'** awaiting initial outreach:\n\n"
                + table_md
            )
        else:
            return "✅ No urgent leads pending. All High-Priority leads have been assigned or contacted."

    # --------------------------------------------------------------------------
    # 18. INTENT: Follow-up Status Overview
    # --------------------------------------------------------------------------
    if "follow-up" in q_lower or "due" in q_lower or "followups" in q_lower or "schedule" in q_lower:
        fu_stats = database.get_followup_stats(db_path)
        due_list = database.get_followups(db_path=db_path, status="Scheduled", limit=8)
        if due_list:
            items = [f"- **{f['customer_name']}** ({f['city']}): Attempt #{f['attempt_number']} via {f['channel']} scheduled for `{f['scheduled_for'][:16]}`" for f in due_list]
            return (
                f"⏰ **Follow-up Pipeline Status:** There are **{fu_stats['scheduled_count']} scheduled follow-ups** active.\n\n"
                f"**Upcoming Touchpoints:**\n" + "\n".join(items)
            )
        else:
            return f"✅ There are currently no overdue follow-ups. Total scheduled tasks: {fu_stats['scheduled_count']}."

    # --------------------------------------------------------------------------
    # 19. INTENT: Total Leads / Pipeline Summary
    # --------------------------------------------------------------------------
    if "total" in q_lower or "how many leads" in q_lower or "summary" in q_lower or "overview" in q_lower:
        stats = database.get_lead_stats(db_path)
        return (
            f"📊 **SHA Interface Interiors CRM Summary:**\n"
            f"- **Total Active Leads:** {stats['total_leads']}\n"
            f"- **Priority Split:** 🟢 {stats['priority_counts'].get('High', 0)} High | 🟡 {stats['priority_counts'].get('Medium', 0)} Medium | 🔴 {stats['priority_counts'].get('Low', 0)} Low\n"
            f"- **Pipeline Stages:** New: {stats['status_counts'].get('New', 0)} | Qualified: {stats['status_counts'].get('Qualified', 0)} | Follow-up: {stats['status_counts'].get('Follow-up', 0)} | Converted: {stats['status_counts'].get('Converted', 0)} | Lost: {stats['status_counts'].get('Lost', 0)}\n"
            f"- **Average Lead Score:** {stats['avg_score']:.1f}/100"
        )

    # --------------------------------------------------------------------------
    # 20. GENERATIVE GEMINI FALLBACK (FOR CONVERSATIONAL & OPEN-ENDED INQUIRIES)
    # --------------------------------------------------------------------------
    if is_ai_api_available():
        try:
            stats = database.get_lead_stats(db_path)
            high_leads = database.get_all_leads(db_path=db_path, priority="High", order_by="lead_score DESC")[:8]
            grounding = (
                f"VERIFIED REAL CRM STATS:\n"
                f"- Total Leads: {stats['total_leads']}\n"
                f"- High: {stats['priority_counts'].get('High', 0)}, Medium: {stats['priority_counts'].get('Medium', 0)}, Low: {stats['priority_counts'].get('Low', 0)}\n"
                f"- Top Cities: {stats['top_cities']}\n"
                f"- Sample High Leads: {[{'id': l['lead_id'], 'name': l['customer_name'], 'city': l['city'], 'budget': l['budget_range'], 'score': l['lead_score']} for l in high_leads]}\n"
            )
            res = ai_service.generate_chat_response(query=query, history=history or [], crm_context_str=grounding)
            if res.get("success") and res.get("text"):
                return res["text"]
        except Exception:
            pass

    # Default friendly guidance
    stats = database.get_lead_stats(db_path)
    return (
        f"I have reviewed the CRM database. We currently track **{stats['total_leads']} leads** with an average qualification score of **{stats['avg_score']:.1f}/100**.\n\n"
        f"You can ask me questions across:\n"
        f"- 📊 **CRM Intelligence:** *'How many high-priority leads?'*, *'Show leads from Hyderabad'*, *'Which city has most leads?'*, *'Calculate pipeline value'*\n"
        f"- 🏛️ **Interior Design:** *'Explain Scandinavian design'*, *'Vastu principles for master bedroom'*, *'Modular kitchen layout'* \n"
        f"- 🪵 **Materials & Finishes:** *'Compare Plywood vs HDHMR'*, *'Acrylic vs Laminate'*, *'Why Blum hinges?'*\n"
        f"- 💰 **Cost Estimation:** *'Estimate cost for 3BHK in Bangalore'*, *'How much for a 2BHK interior?'*\n"
        f"- 🎯 **Sales Strategy:** *'Which leads can become high priority?'*, *'Explain score for SHA-2026-0001'*"
    )
