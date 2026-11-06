"""
sales_intelligence.py - Advanced AI Lead Scoring Explanations & Sales Strategy
SHA Interface Interiors - AI-Powered Lead Management System

Provides factor-by-factor transparency for the 100-point lead scoring engine,
identifies high-probability conversion opportunities, detects upgradable medium-priority
leads (Scores 70–79), and prescribes sales discovery questions.
"""

import sys
import json
from typing import Dict, List, Optional, Any
import database
import lead_scoring
import business_config

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def explain_lead_score(lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deconstructs the lead score into its 4 mathematical dimensions (Budget 30,
    Location 20, Requirements 20, Readiness 30) and generates an executive rationale.
    """
    # Evaluate score using active rule engine
    scored_res = lead_scoring.score_lead(lead)
    score = scored_res["lead_score"]
    priority = scored_res["priority"]
    breakdown = scored_res["score_breakdown"]
    reason = scored_res["scoring_reason"]

    b_pts = breakdown.get("budget_score", 0.0)
    l_pts = breakdown.get("location_score", 0.0)
    r_pts = breakdown.get("requirements_score", 0.0)
    p_pts = breakdown.get("readiness_score", 0.0)

    # Narrative explanation for each pillar
    # 1. Budget
    b_val = lead.get("budget_range", "Not specified")
    p_type = lead.get("project_type", "Residential")
    if b_pts >= 26:
        b_expl = f"Excellent investment capacity ({b_val}) providing strong profit margins for a {p_type} project."
    elif b_pts >= 20:
        b_expl = f"Healthy, realistic budget allocation ({b_val}) fully aligned with SHA Interiors' target turnkey threshold."
    else:
        b_expl = f"Budget is conservative ({b_val}); will require modular value engineering or phased execution."

    # 2. Location
    city = lead.get("city", "Unknown")
    if l_pts == 20:
        l_expl = f"Located in {city} (Tier 1 core studio hub), allowing immediate on-site measurement and rapid project delivery."
    elif l_pts >= 14:
        l_expl = f"Located in {city} (Tier 2 service corridor), manageable via regional design and logistics teams."
    else:
        l_expl = f"Located in {city} (Tier 3 or remote), requiring remote 3D spatial design or special transport allowances."

    # 3. Requirements Clarity
    notes = lead.get("customer_requirements") or ""
    scope = lead.get("scope_of_work", "")
    if r_pts >= 18:
        r_expl = f"Highly defined scope ({scope}) with clear custom specifications ({len(notes.split())} words recorded)."
    elif r_pts >= 12:
        r_expl = f"General scope identified ({scope}), but specific finish preferences and floor plans remain to be clarified."
    else:
        r_expl = "Requirements are vague or placeholder. Immediate discovery call required to establish spatial needs."

    # 4. Purchase Readiness
    readiness = lead.get("purchase_readiness", "Just Exploring")
    timeline = lead.get("project_timeline", "")
    if p_pts == 30:
        r_state = f"High buying velocity: Client is '{readiness}' with desired timeline '{timeline}'."
    elif p_pts == 20:
        r_state = f"Active evaluation: Client is '{readiness}'. Needs competitive 3D lookbook and material comparison."
    elif p_pts == 10:
        r_state = f"Early planning: Client is in '{readiness}' stage. Nurture with space planning guides."
    else:
        r_state = f"Low urgency: Client is '{readiness}'. Keep engaged with low-touch digital catalog broadcasts."

    return {
        "lead_id": lead.get("lead_id"),
        "customer_name": lead.get("customer_name"),
        "total_score": score,
        "priority": priority,
        "breakdown": {
            "budget": {"points": b_pts, "max": 30, "percentage": round((b_pts / 30) * 100), "explanation": b_expl},
            "location": {"points": l_pts, "max": 20, "percentage": round((l_pts / 20) * 100), "explanation": l_expl},
            "requirements": {"points": r_pts, "max": 20, "percentage": round((r_pts / 20) * 100), "explanation": r_expl},
            "readiness": {"points": p_pts, "max": 30, "percentage": round((p_pts / 30) * 100), "explanation": r_state}
        },
        "executive_summary": (
            f"{lead.get('customer_name')} scored {score:.0f}/100 ({priority} Priority). "
            f"Key strengths: {b_val} in {city}. Primary sales lever: {r_state}"
        )
    }


def find_upgradable_leads(
    min_score: float = 70.0,
    max_score: float = 79.9,
    db_path: str = database.DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """
    Identifies high-potential 'Almost High' leads (scores 70-79) that are within 10 points
    of crossing the High-Priority cutoff (80), along with the specific sales action needed.
    """
    sql = f"""
    SELECT lead_id, customer_name, phone, city, budget_range, project_type,
           purchase_readiness, customer_requirements, lead_score, priority, lead_status
    FROM LEADS
    WHERE lead_score >= {min_score} AND lead_score <= {max_score}
      AND lead_status NOT IN ('Converted', 'Lost')
      AND is_opted_out = 0
    ORDER BY lead_score DESC;
    """
    conn = database.get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

    upgradables = []
    for r in rows:
        pts_needed = round(80.0 - r["lead_score"], 1)
        readiness = r.get("purchase_readiness")
        notes = r.get("customer_requirements") or ""

        # Prescribe exact upgrade lever
        levers = []
        if readiness == "Comparing Vendors":
            levers.append("Offer complimentary 3D layout & local site visit to advance readiness from 'Comparing' to 'Ready to Start' (+10 pts).")
        elif readiness == "Budget Planning":
            levers.append("Share itemized value-engineered cost estimate to convert from 'Budget Planning' to 'Ready to Start' (+20 pts).")

        if len(notes.strip()) < 30 or "standard" in notes.lower():
            levers.append("Schedule 10-minute discovery call to clarify floor plan and material preferences (+8 to +12 pts).")

        r["points_to_high_priority"] = pts_needed
        r["upgrade_recommendations"] = levers or [f"Confirm property handover date and invite for meeting at our {business_config.OFFICE_NAME} ({business_config.WORKING_HOURS_START} - {business_config.WORKING_HOURS_END} IST, {business_config.WORKING_DAYS})."]
        upgradables.append(r)

    return upgradables


def generate_sales_consultation_questions(lead: Dict[str, Any]) -> List[str]:
    """
    Generates 5 tailored, consultative sales discovery questions based on gaps in the lead profile.
    """
    name = lead.get("customer_name", "the client")
    city = lead.get("city", "your city")
    p_type = lead.get("project_type", "home")
    budget = lead.get("budget_range", "the stated budget")
    status = lead.get("property_status", "your property")
    scope = lead.get("scope_of_work", "interior design")
    notes = (lead.get("customer_requirements") or "").lower()

    questions = []

    # 1. Timeline & Possession
    if "ready" in status.lower() or "immediate" in lead.get("project_timeline", "").lower():
        questions.append(f"Since your {p_type} in {city} is {status}, what is your firm target move-in date?")
    else:
        questions.append(f"When is the builder expected to hand over possession for site measurements in {city}?")

    # 2. Scope & Technical Deep-Dive
    if "kitchen" in scope.lower() or "kitchen" in notes:
        questions.append(f"For your modular kitchen, what type of cooking workload do you anticipate, and do you prefer seamless Acrylic or anti-fingerprint Matte Laminate?")
    elif "turnkey" in scope.lower():
        questions.append(f"For your complete turnkey {p_type}, are you looking for complete false ceiling and lighting design alongside modular woodwork?")

    # 3. Design Aesthetic
    questions.append(f"Which interior style resonates most with you: clean Contemporary, warm Scandinavian with natural wood, or a high-end Luxury aesthetic with stone and metal accents?")

    # 4. Budget & Scope Alignment
    questions.append(f"Does your {budget} allocation include movable appliances and loose furniture, or is it dedicated specifically to fixed woodwork and civil work?")

    # 5. Next Step Action
    questions.append(f"Would you be open to an initial 20-minute conceptual discovery call this week to review 3D layout options for your {p_type}?")

    return questions
