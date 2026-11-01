import json
import datetime
from typing import Dict, List, Tuple, Any, Optional
import database

# ==============================================================================
# CONFIGURABLE SCORING SETTINGS & DEMO DEFAULTS
# ==============================================================================
# Business Note: These thresholds represent demo defaults for SHA Interface Interiors
# and can be configured to reflect actual studio business rules.

# 1. Budget Suitability Weights (Max 30 Points)
DEFAULT_BUDGET_WEIGHTS = {
    "Above ₹25 lakh": 30,       # Luxury / Large turnkey villa / Premium project
    "₹10 lakh–₹25 lakh": 25,    # Core high-margin target for 3BHK/Villa turnkey
    "₹5 lakh–₹10 lakh": 18,     # Standard 2BHK/3BHK standard package (Studio Sweet Spot)
    "₹3 lakh–₹5 lakh": 10,      # Essential modular woodwork / compact setup
    "Below ₹3 lakh": 2          # Constrained budget; below typical turnkey minimum
}

# Configurable Minimum Target Budget
# Demo Default: "₹5 lakh–₹10 lakh" (Needs confirmation with SHA Interiors management)
CONFIGURABLE_MIN_TARGET_BUDGET = "₹5 lakh–₹10 lakh"

# 2. Location Suitability Weights (Max 20 Points)
# Tiered serviceability configuration:
DEFAULT_LOCATION_TIERS = {
    "Tier 1 - Primary Service Hubs": {
        "cities": ["Bangalore", "Hyderabad"],
        "points": 20,
        "description": "Full design studio & in-house execution teams"
    },
    "Tier 2 - Secondary Service Hubs": {
        "cities": ["Chennai", "Mumbai", "Pune"],
        "points": 14,
        "description": "Active design consultation & verified partner execution"
    },
    "Tier 3 - Expansion / Partner Hubs": {
        "cities": ["Delhi NCR"],
        "points": 8,
        "description": "Remote architectural consultation / partner network"
    }
}

# 3. Requirements Clarity Weights (Max 20 Points)
# 4 points for each of the 5 key project detail fields
REQUIREMENT_FIELD_POINTS = {
    "project_type": 4,
    "property_status": 4,
    "project_timeline": 4,
    "scope_of_work": 4,
    "customer_requirements": 4
}

# 4. Purchase Readiness Weights (Max 30 Points)
DEFAULT_READINESS_WEIGHTS = {
    "Ready to Start": 30,       # High intent; immediate project kickoff
    "Comparing Vendors": 22,    # Active buyer; evaluating quotation & proposals
    "Budget Planning": 12,      # Mid-funnel prospect setting initial allocation
    "Just Exploring": 4         # Top-of-funnel browsing / low immediate urgency
}

# Valid project option lists to avoid awarding points to placeholders
VALID_PROJECT_TYPES = {"1BHK", "2BHK", "3BHK", "Villa", "Modular Kitchen", "Commercial/Office"}
VALID_PROPERTY_STATUSES = {"Ready to Move", "Possession within 30 days", "Possession within 1–3 months", "Under Construction"}
VALID_TIMELINES = {"Immediately", "Within 1 month", "Within 3 months", "Within 6 months", "Just Exploring"}
VALID_SCOPES = {"Full Turnkey Interior", "Modular Kitchen", "Wardrobe", "Renovation", "Furniture and Woodwork", "Commercial Interiors"}

# ==============================================================================
# CORE SCORING LOGIC
# ==============================================================================

def calculate_budget_score(budget_range: Optional[str]) -> Tuple[int, str]:
    """Calculates budget score (0 to 30) and returns human-readable detail."""
    if not budget_range:
        return 0, "No budget range specified"
    cleaned = budget_range.strip()
    score = DEFAULT_BUDGET_WEIGHTS.get(cleaned, 0)
    detail = f"{cleaned} ({score}/30 pts)"
    return score, detail

def calculate_location_score(city: Optional[str]) -> Tuple[int, str]:
    """Calculates location score (0 to 20) based on serviceable city tiers."""
    if not city:
        return 0, "No city provided (0/20 pts)"
    cleaned = city.strip()
    
    for tier_name, tier_info in DEFAULT_LOCATION_TIERS.items():
        if any(cleaned.lower() == c.lower() for c in tier_info["cities"]):
            pts = tier_info["points"]
            return pts, f"{cleaned} [{tier_name}] ({pts}/20 pts)"
            
    return 0, f"{cleaned} [Out of Service Area] (0/20 pts)"

def calculate_requirements_score(lead: Dict[str, Any]) -> Tuple[int, Dict[str, int], str]:
    """
    Calculates requirements clarity score (0 to 20).
    Awards up to 4 points per valid field. Does NOT award points for placeholders or trivial text.
    """
    breakdown = {}
    details = []
    
    # 1. Project Type
    pt = str(lead.get("project_type", "")).strip()
    if pt in VALID_PROJECT_TYPES:
        breakdown["project_type"] = 4
        details.append(f"Project Type: {pt} (4/4)")
    else:
        breakdown["project_type"] = 0
        details.append("Project Type: Unspecified/Invalid (0/4)")

    # 2. Property Status
    ps = str(lead.get("property_status", "")).strip()
    if ps in VALID_PROPERTY_STATUSES:
        breakdown["property_status"] = 4
        details.append(f"Property Status: {ps} (4/4)")
    else:
        breakdown["property_status"] = 0
        details.append("Property Status: Unspecified (0/4)")

    # 3. Project Timeline
    tl = str(lead.get("project_timeline", "")).strip()
    if tl in VALID_TIMELINES:
        breakdown["project_timeline"] = 4
        details.append(f"Timeline: {tl} (4/4)")
    else:
        breakdown["project_timeline"] = 0
        details.append("Timeline: Unspecified (0/4)")

    # 4. Scope of Work
    sw = str(lead.get("scope_of_work", "")).strip()
    if sw in VALID_SCOPES:
        breakdown["scope_of_work"] = 4
        details.append(f"Scope: {sw} (4/4)")
    else:
        breakdown["scope_of_work"] = 0
        details.append("Scope: Unspecified (0/4)")

    # 5. Customer Requirements text
    cr = str(lead.get("customer_requirements") or "").strip()
    # Check that text is not a placeholder like 'Select', 'None', 'N/A'
    if len(cr) >= 30 and cr.lower() not in ["none", "select", "n/a", "not specified"]:
        breakdown["customer_requirements"] = 4
        details.append("Custom Notes: Detailed (4/4)")
    elif len(cr) >= 10 and cr.lower() not in ["none", "select", "n/a", "not specified"]:
        breakdown["customer_requirements"] = 2
        details.append("Custom Notes: Brief (2/4)")
    else:
        breakdown["customer_requirements"] = 0
        details.append("Custom Notes: Minimal/None (0/4)")

    total_req_score = sum(breakdown.values())
    summary_text = f"{total_req_score}/20 pts ({'; '.join(details)})"
    return total_req_score, breakdown, summary_text

def calculate_readiness_score(purchase_readiness: Optional[str]) -> Tuple[int, str]:
    """Calculates purchase readiness score (0 to 30)."""
    if not purchase_readiness:
        return 0, "No purchase readiness indicated (0/30 pts)"
    cleaned = purchase_readiness.strip()
    score = DEFAULT_READINESS_WEIGHTS.get(cleaned, 0)
    detail = f"{cleaned} ({score}/30 pts)"
    return score, detail

def classify_priority(total_score: float) -> str:
    """Classifies priority according to total lead score."""
    if total_score >= 80:
        return "High"
    elif total_score >= 50:
        return "Medium"
    else:
        return "Low"

def generate_scoring_reason(
    total_score: float,
    priority: str,
    budget_score: int,
    location_score: int,
    requirements_score: int,
    readiness_score: int,
    lead: Dict[str, Any]
) -> str:
    """
    Generates a clear, explainable, human-readable scoring reason dynamically
    from the mathematical scoring factors without using language models.
    """
    readiness = lead.get("purchase_readiness", "Unspecified")
    city = lead.get("city", "Unknown")
    budget = lead.get("budget_range", "Unspecified")
    p_type = lead.get("project_type", "Project")
    
    reasons = []
    
    # Readiness driver
    if readiness_score >= 25:
        reasons.append(f"Customer is ready for immediate engagement ({readiness})")
    elif readiness_score >= 15:
        reasons.append(f"Customer is actively comparing quotes ({readiness})")
    elif readiness_score >= 10:
        reasons.append(f"Customer is in the planning phase ({readiness})")
    else:
        reasons.append(f"Customer is exploring options ({readiness})")
        
    # Budget driver
    if budget_score >= 25:
        reasons.append(f"prime budget tier ({budget})")
    elif budget_score >= 18:
        reasons.append(f"viable budget tier ({budget})")
    elif budget_score >= 10:
        reasons.append(f"entry-level budget ({budget})")
    else:
        reasons.append(f"low budget tier ({budget})")
        
    # Location driver
    if location_score == 20:
        reasons.append(f"located in primary service hub ({city})")
    elif location_score >= 14:
        reasons.append(f"located in secondary service hub ({city})")
    elif location_score > 0:
        reasons.append(f"located in expansion hub ({city})")
    else:
        reasons.append(f"located outside standard service hubs ({city})")
        
    # Requirements driver
    if requirements_score >= 18:
        reasons.append(f"comprehensive {p_type} specifications provided")
    elif requirements_score >= 12:
        reasons.append(f"adequate {p_type} requirements provided")
    else:
        reasons.append("sparse project details provided")
        
    explanation = f"{priority} Priority ({total_score:.0f}/100): " + ", ".join(reasons) + "."
    return explanation

def score_lead(lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates a single lead record and produces:
    - total_score (0 to 100)
    - priority ('High', 'Medium', 'Low')
    - score_breakdown (dict of sub-scores)
    - scoring_reason (human-readable string)
    - scored_at (ISO timestamp)
    """
    b_score, b_detail = calculate_budget_score(lead.get("budget_range"))
    l_score, l_detail = calculate_location_score(lead.get("city"))
    r_score, r_subdict, r_detail = calculate_requirements_score(lead)
    p_score, p_detail = calculate_readiness_score(lead.get("purchase_readiness"))
    
    total = float(b_score + l_score + r_score + p_score)
    # Strict clamping between 0 and 100
    total = max(0.0, min(100.0, total))
    priority = classify_priority(total)
    
    now_str = datetime.datetime.now().isoformat()
    reason = generate_scoring_reason(total, priority, b_score, l_score, r_score, p_score, lead)
    
    breakdown = {
        "budget_score": b_score,
        "budget_max": 30,
        "budget_detail": b_detail,
        "location_score": l_score,
        "location_max": 20,
        "location_detail": l_detail,
        "requirements_score": r_score,
        "requirements_max": 20,
        "requirements_detail": r_detail,
        "requirements_subfields": r_subdict,
        "readiness_score": p_score,
        "readiness_max": 30,
        "readiness_detail": p_detail,
        "total_score": total,
        "max_score": 100
    }
    
    return {
        "lead_id": lead.get("lead_id"),
        "lead_score": total,
        "priority": priority,
        "score_breakdown": breakdown,
        "scoring_reason": reason,
        "scored_at": now_str
    }

def score_and_save_lead(lead_id: str, db_path: str = database.DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Calculates and updates score for an individual lead in SQLite."""
    lead = database.get_lead_by_id(lead_id, db_path=db_path)
    if not lead:
        return None
        
    res = score_lead(lead)
    database.update_lead_score(
        lead_id=lead_id,
        lead_score=res["lead_score"],
        priority=res["priority"],
        score_breakdown=json.dumps(res["score_breakdown"]),
        scoring_reason=res["scoring_reason"],
        db_path=db_path
    )
    return res

def score_all_leads(db_path: str = database.DEFAULT_DB_PATH, force_rescore: bool = False) -> Dict[str, Any]:
    """
    Scores all eligible leads in the SQLite database.
    If force_rescore is False, only leads with NULL lead_score are scored.
    """
    database.init_db(db_path)
    all_leads = database.get_all_leads(db_path=db_path)
    
    if not force_rescore:
        leads_to_score = [l for l in all_leads if l.get("lead_score") is None]
    else:
        leads_to_score = all_leads
        
    if not leads_to_score:
        return {
            "total_evaluated": len(all_leads),
            "scored_count": 0,
            "message": "All eligible leads are already scored."
        }
        
    scored_items = []
    priority_counts = {"High": 0, "Medium": 0, "Low": 0}
    
    for lead in leads_to_score:
        scoring_res = score_lead(lead)
        scored_items.append(scoring_res)
        priority_counts[scoring_res["priority"]] += 1
        
    # Transactional batch update in SQLite
    updated_count = database.batch_update_lead_scores(scored_items, db_path=db_path)
    
    return {
        "total_evaluated": len(all_leads),
        "scored_count": updated_count,
        "priority_counts": priority_counts,
        "message": f"Successfully scored {updated_count} leads in SQLite."
    }
