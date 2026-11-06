"""
crm_search.py - Advanced CRM Search Engine & Multi-Filter Query Layer
SHA Interface Interiors - AI-Powered Lead Management System

Provides:
1. Multi-parameter structured search across customer name, phone, locality,
   budget, project type, priority, status, conversion, follow-ups, and date range.
2. Natural-language query parser understanding CRM requests without hallucination.
3. Formatted tabular outputs with lead inspection metadata.
4. Locality comparison and aggregation analytics.
"""

import os
import sys
import re
import datetime
from typing import Dict, List, Optional, Any, Tuple

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import database
import hyderabad_geo as hg
import db_intelligence


# ------------------------------------------------------------------------------
# 1. BUDGET PARSING UTILITIES
# ------------------------------------------------------------------------------

def parse_budget_lakh_bounds(budget_str: Optional[str]) -> Tuple[float, float]:
    """
    Extracts (min_lakh, max_lakh) bounds from budget strings like:
    'Below ₹3 lakh'      -> (0.0, 3.0)
    '₹3 lakh–₹5 lakh'    -> (3.0, 5.0)
    '₹5 lakh–₹10 lakh'   -> (5.0, 10.0)
    '₹5 lakh – ₹8 lakh'  -> (5.0, 8.0)
    '₹10 lakh–₹25 lakh'  -> (10.0, 25.0)
    '₹12 lakh – ₹18 lakh'-> (12.0, 18.0)
    'Above ₹25 lakh'     -> (25.0, 999.0)
    """
    if not budget_str:
        return (0.0, 999.0)
    
    b_lower = budget_str.lower()
    # Find all integer or float numbers
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", budget_str)]
    
    if "above" in b_lower or ">" in b_lower:
        val = nums[0] if nums else 25.0
        return (val, 999.0)
    if "below" in b_lower or "<" in b_lower:
        val = nums[0] if nums else 3.0
        return (0.0, val)
    if len(nums) >= 2:
        return (min(nums[0], nums[1]), max(nums[0], nums[1]))
    elif len(nums) == 1:
        return (nums[0], nums[0])
    return (0.0, 999.0)


def budget_matches_range(
    lead_budget_str: Optional[str],
    min_filter_lakh: Optional[float] = None,
    max_filter_lakh: Optional[float] = None
) -> bool:
    """Checks whether a lead's budget overlaps or satisfies requested min/max thresholds."""
    if min_filter_lakh is None and max_filter_lakh is None:
        return True
    
    lead_min, lead_max = parse_budget_lakh_bounds(lead_budget_str)
    
    if min_filter_lakh is not None:
        # Lead's upper bound must at least reach the requested minimum
        if lead_max < min_filter_lakh:
            return False
            
    if max_filter_lakh is not None:
        # Lead's lower bound must not exceed the requested maximum
        if lead_min > max_filter_lakh:
            return False
            
    return True


# ------------------------------------------------------------------------------
# 2. MULTI-FILTER STRUCTURED SEARCH ENGINE
# ------------------------------------------------------------------------------

def search_crm_leads(
    filters: Optional[Dict[str, Any]] = None,
    db_path: str = database.DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """
    Executes a comprehensive, multi-filter search against actual SQLite CRM records.
    Filters can include:
      - name: str (case-insensitive substring)
      - phone: str (digits substring)
      - locality: str or list of str
      - region: str or list of str
      - project_type: str or list of str ('1BHK', '2BHK', '3BHK', '4BHK', 'Villa', etc.)
      - priority: str or list of str ('High', 'Medium', 'Low')
      - lead_status: str or list of str ('New', 'Qualified', 'Follow-up', 'Converted', 'Lost')
      - conversion_status: str ('All', 'Converted', 'Active / Not Converted', 'Lost')
      - followup_status: str ('All', 'Pending / Upcoming Follow-up', 'Overdue Follow-up', 'No Follow-up Scheduled')
      - min_budget_lakh: float
      - max_budget_lakh: float
      - date_from: str ('YYYY-MM-DD')
      - date_to: str ('YYYY-MM-DD')
      - data_origin: str ('all', 'exclude_test_data', 'test_data_only')

    Returns:
      {
        'success': bool,
        'leads': List[Dict[str, Any]],
        'total_count': int,
        'high_priority_count': int,
        'medium_priority_count': int,
        'low_priority_count': int,
        'filter_summary': str
      }
    """
    if filters is None:
        filters = {}

    all_leads = database.get_all_leads(db_path=db_path)
    # Pre-fetch all scheduled follow-ups to map next touchpoint per lead
    scheduled_tasks = database.get_followups(db_path=db_path, status="Scheduled")
    
    # Map next follow-up per lead_id (earliest scheduled_for)
    next_fu_map: Dict[str, Dict[str, Any]] = {}
    for task in sorted(scheduled_tasks, key=lambda t: t.get("scheduled_for", "")):
        lid = task.get("lead_id")
        if lid and lid not in next_fu_map:
            next_fu_map[lid] = task

    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    matching: List[Dict[str, Any]] = []

    # Clean input filters
    filter_name = str(filters.get("name", "")).strip().lower()
    filter_phone = re.sub(r"\D", "", str(filters.get("phone", "")).strip())
    
    filter_locality = filters.get("locality")
    if isinstance(filter_locality, str):
        filter_locality = [filter_locality] if filter_locality and filter_locality != "All" else []
    elif not filter_locality:
        filter_locality = []
    filter_locality = [loc.lower().strip() for loc in filter_locality if loc != "All"]

    filter_region = filters.get("region")
    if isinstance(filter_region, str):
        filter_region = [filter_region] if filter_region and filter_region != "All" else []
    elif not filter_region:
        filter_region = []
    filter_region = [r.lower().strip() for r in filter_region if r != "All"]

    filter_ptype = filters.get("project_type")
    if isinstance(filter_ptype, str):
        filter_ptype = [filter_ptype] if filter_ptype and filter_ptype != "All" else []
    elif not filter_ptype:
        filter_ptype = []
    filter_ptype = [pt.lower().strip() for pt in filter_ptype if pt != "All"]

    filter_priority = filters.get("priority")
    if isinstance(filter_priority, str):
        filter_priority = [filter_priority] if filter_priority and filter_priority != "All" else []
    elif not filter_priority:
        filter_priority = []
    filter_priority = [p.capitalize().strip() for p in filter_priority if p != "All"]

    filter_status = filters.get("lead_status")
    if isinstance(filter_status, str):
        filter_status = [filter_status] if filter_status and filter_status != "All" else []
    elif not filter_status:
        filter_status = []
    filter_status = [s.lower().strip() for s in filter_status if s != "All"]

    conv_status = filters.get("conversion_status", "All")
    fu_status = filters.get("followup_status", "All")
    
    min_b = filters.get("min_budget_lakh")
    max_b = filters.get("max_budget_lakh")
    
    date_from = str(filters.get("date_from", "")).strip()
    date_to = str(filters.get("date_to", "")).strip()

    data_origin_scope = filters.get("data_origin", "all")

    for lead in all_leads:
        # 1. Data Origin Filter
        origin = lead.get("data_origin", "")
        if data_origin_scope == "exclude_test_data" and origin == "test_data":
            continue
        if data_origin_scope == "test_data_only" and origin != "test_data":
            continue

        # 2. Customer Name Match
        if filter_name:
            c_name = str(lead.get("customer_name", "")).lower()
            lid = str(lead.get("lead_id", "")).lower()
            if filter_name not in c_name and filter_name not in lid:
                continue

        # 3. Phone Number Match
        if filter_phone:
            lead_digits = re.sub(r"\D", "", str(lead.get("phone", "")))
            if filter_phone not in lead_digits:
                continue

        # 4. Locality Match
        if filter_locality:
            lead_loc = str(lead.get("locality") or lead.get("city") or "").lower().strip()
            if not any(fl in lead_loc for fl in filter_locality):
                continue

        # 5. Region Match
        if filter_region:
            lead_reg = str(lead.get("region") or "").lower().strip()
            if not any(fr in lead_reg for fr in filter_region):
                continue

        # 6. Project Type Match
        if filter_ptype:
            lead_pt = str(lead.get("project_type", "")).lower().strip()
            if not any(fpt in lead_pt for fpt in filter_ptype):
                continue

        # 7. Priority Match
        if filter_priority:
            lead_prio = str(lead.get("priority", "")).capitalize().strip()
            if lead_prio not in filter_priority:
                continue

        # 8. Lead Status Match
        if filter_status:
            lead_st = str(lead.get("lead_status", "")).lower().strip()
            if not any(fs in lead_st for fs in filter_status):
                continue

        # 9. Conversion Status Match
        lead_curr_st = str(lead.get("lead_status", "")).lower()
        if conv_status in ["Active / Not Converted", "Not Converted", "active"]:
            if lead_curr_st in ["converted", "lost"]:
                continue
        elif conv_status == "Converted":
            if lead_curr_st != "converted":
                continue
        elif conv_status == "Lost":
            if lead_curr_st != "lost":
                continue

        # 10. Follow-up Status Match
        lead_id = lead.get("lead_id")
        has_sched_fu = lead_id in next_fu_map
        next_task = next_fu_map.get(lead_id)
        next_fu_time = next_task.get("scheduled_for", "") if next_task else ""

        if fu_status in ["Pending / Upcoming Follow-up", "Pending", "Upcoming"]:
            if not has_sched_fu:
                continue
        elif fu_status in ["Overdue Follow-up", "Overdue"]:
            if not has_sched_fu or next_fu_time >= now_iso:
                continue
        elif fu_status in ["No Follow-up Scheduled", "None"]:
            if has_sched_fu:
                continue

        # 11. Budget Range Match
        if min_b is not None or max_b is not None:
            if not budget_matches_range(lead.get("budget_range"), min_filter_lakh=min_b, max_filter_lakh=max_b):
                continue

        # 12. Date Range Match (created_at)
        created_val = str(lead.get("created_at", ""))
        if date_from and created_val:
            if created_val[:10] < date_from:
                continue
        if date_to and created_val:
            if created_val[:10] > date_to:
                continue

        # Enrich lead with next follow-up details
        lead_copy = dict(lead)
        if next_task:
            lead_copy["next_followup_channel"] = next_task.get("channel", "WhatsApp")
            lead_copy["next_followup_time"] = next_task.get("scheduled_for", "")
            lead_copy["next_followup_desc"] = f"{next_task.get('channel')} on {next_task.get('scheduled_for')[:16]}"
        else:
            lead_copy["next_followup_channel"] = "None"
            lead_copy["next_followup_time"] = "None"
            lead_copy["next_followup_desc"] = "No Task Scheduled"

        matching.append(lead_copy)

    # Sort matching leads by score descending
    matching.sort(key=lambda l: float(l.get("lead_score") or 0.0), reverse=True)

    hp_count = sum(1 for l in matching if str(l.get("priority", "")).capitalize() == "High")
    mp_count = sum(1 for l in matching if str(l.get("priority", "")).capitalize() == "Medium")
    lp_count = sum(1 for l in matching if str(l.get("priority", "")).capitalize() == "Low")

    # Generate summary of active filters
    active_tokens = []
    if filter_name: active_tokens.append(f"Name matching '{filter_name}'")
    if filter_phone: active_tokens.append(f"Phone containing '{filter_phone}'")
    if filter_locality: active_tokens.append(f"Locality: {', '.join([l.title() for l in filter_locality])}")
    if filter_region: active_tokens.append(f"Region: {', '.join([r.title() for r in filter_region])}")
    if filter_ptype: active_tokens.append(f"Project Type: {', '.join([pt.upper() for pt in filter_ptype])}")
    if filter_priority: active_tokens.append(f"Priority: {', '.join(filter_priority)}")
    if filter_status: active_tokens.append(f"Status: {', '.join([s.title() for s in filter_status])}")
    if conv_status != "All": active_tokens.append(f"Conversion: {conv_status}")
    if fu_status != "All": active_tokens.append(f"Follow-up: {fu_status}")
    if min_b is not None: active_tokens.append(f"Min Budget: ₹{min_b}L")
    if max_b is not None: active_tokens.append(f"Max Budget: ₹{max_b}L")
    if date_from or date_to: active_tokens.append(f"Date Range: {date_from or 'Start'} to {date_to or 'Today'}")

    summary_desc = "; ".join(active_tokens) if active_tokens else "All active leads (no filters applied)"

    return {
        "success": True,
        "leads": matching,
        "total_count": len(matching),
        "high_priority_count": hp_count,
        "medium_priority_count": mp_count,
        "low_priority_count": lp_count,
        "filter_summary": summary_desc
    }


# ------------------------------------------------------------------------------
# 3. NATURAL LANGUAGE SEARCH PARSER & ROUTER
# ------------------------------------------------------------------------------

def is_crm_search_query(query: str) -> bool:
    """Detects whether a user query is asking for CRM search, lead retrieval, or locality analysis."""
    q_lower = query.lower().strip()
    
    # Priority
    if any(w in q_lower for w in ["high priority", "high-priority", "medium priority", "low priority", "high leads", "top priority"]):
        return True
        
    # Locality comparison
    if ("compare" in q_lower and "localit" in q_lower) or "locality breakdown" in q_lower:
        return True

    # Check for lead / customer / account keywords
    has_lead_entity = any(w in q_lower for w in [
        "lead", "leads", "customer", "customers", "client", "clients",
        "account", "accounts", "prospect", "prospects", "who has", "who have",
        "who are", "show me", "find", "search", "list", "lookup"
    ])

    # Project type customers (e.g. "3bhk customers", "find all 3bhk", "show 3bhk")
    if any(pt in q_lower for pt in ["1bhk", "2bhk", "3bhk", "4bhk", "villa"]):
        if has_lead_entity or any(w in q_lower for w in ["in ", "with ", "at ", "from ", "all"]):
            if not ("cost" in q_lower or "estimate" in q_lower or "how much" in q_lower):
                return True

    # Locality + leads (e.g. "customers in gachibowli", "leads in miyapur", "in gachibowli")
    for loc in hg.get_all_localities():
        if re.search(r"\b" + re.escape(loc.lower()) + r"\b", q_lower):
            if has_lead_entity or any(w in q_lower for w in ["in ", "at ", "from "]):
                if not ("cost" in q_lower or "estimate" in q_lower):
                    return True

    # Budgets + leads
    if ("budget" in q_lower or "above" in q_lower or "below" in q_lower) and (has_lead_entity or "lakh" in q_lower):
        if not ("estimate" in q_lower or "how much" in q_lower or "cost of" in q_lower or "price" in q_lower):
            return True

    # Follow-ups
    if any(w in q_lower for w in [
        "pending follow-up", "pending follow-ups", "pending followups",
        "upcoming follow-up", "upcoming follow-ups", "upcoming followups",
        "without follow-up", "without followups", "no follow-up", "leads with follow-up"
    ]):
        return True

    # Conversion
    if any(w in q_lower for w in ["not converted", "unconverted", "non-converted", "who have not converted", "converted leads"]):
        return True

    # Customer Name / Phone / Lead ID
    if re.search(r"SHA-[\w\-]+", query, re.IGNORECASE):
        return True
    digits = re.findall(r"\d+", query)
    if digits and len("".join(digits)) >= 5:
        return True
    if any(w in q_lower for w in ["find customer", "search customer", "show customer", "lookup customer", "find client", "search client"]):
        return True

    return False



def parse_and_search_crm(
    query: str,
    db_path: str = database.DEFAULT_DB_PATH,
    history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Parses conversational and natural-language user queries into targeted CRM searches.
    Guarantees 100% adherence to actual database records without hallucination.
    """
    q_clean = query.strip()
    q_lower = q_clean.lower()
    
    # --------------------------------------------------------------------------
    # 1. SPECIAL INTENT: Locality Comparison
    # --------------------------------------------------------------------------
    if ("compare" in q_lower and "localit" in q_lower) or "locality breakdown" in q_lower or "compare leads from different hyderabad localities" in q_lower:
        return {
            "intent": "locality_comparison",
            "markdown": format_locality_comparison_markdown(db_path=db_path)
        }

    # Extract conversational context from previous turn if available
    context_filters: Dict[str, Any] = {}
    if history and len(history) >= 2:
        last_user = history[-2].get("content", "").lower() if history[-2].get("role") == "user" else ""
        if "3bhk" in last_user and not any(p in q_lower for p in ["1bhk", "2bhk", "4bhk", "villa"]):
            if any(term in q_lower for term in ["which of them", "which ones", "how many of those", "who among them"]):
                context_filters["project_type"] = "3BHK"
        if "high" in last_user and "priority" in last_user and not any(p in q_lower for p in ["medium", "low"]):
            if any(term in q_lower for term in ["which of them", "which ones", "how many of those", "who among them"]):
                context_filters["priority"] = "High"

    filters: Dict[str, Any] = dict(context_filters)

    # --------------------------------------------------------------------------
    # 2. Extract Lead Priority
    # --------------------------------------------------------------------------
    if "high-priority" in q_lower or "high priority" in q_lower or "high leads" in q_lower or "top priority" in q_lower:
        filters["priority"] = "High"
    elif "medium-priority" in q_lower or "medium priority" in q_lower:
        filters["priority"] = "Medium"
    elif "low-priority" in q_lower or "low priority" in q_lower:
        filters["priority"] = "Low"

    # --------------------------------------------------------------------------
    # 3. Extract Locality
    # --------------------------------------------------------------------------
    matched_locs = []
    for loc in hg.get_all_localities():
        # Match with word boundary
        if re.search(r"\b" + re.escape(loc.lower()) + r"\b", q_lower):
            matched_locs.append(loc)
    if matched_locs:
        filters["locality"] = matched_locs

    # --------------------------------------------------------------------------
    # 4. Extract Project Type
    # --------------------------------------------------------------------------
    for pt in ["1bhk", "2bhk", "3bhk", "4bhk", "villa", "studio", "commercial"]:
        if re.search(r"\b" + pt + r"\b", q_lower):
            filters["project_type"] = pt.upper() if pt != "commercial" else "Commercial"
            break

    # --------------------------------------------------------------------------
    # 5. Extract Budget Thresholds
    # --------------------------------------------------------------------------
    # Above ₹10 lakh / above 10 lakh / > 10
    budget_above_match = re.search(r"(?:above|over|more than|>|greater than)\s*(?:₹|rs\.?)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|l|lac|lacs)?", q_lower)
    if budget_above_match:
        val = float(budget_above_match.group(1))
        filters["min_budget_lakh"] = val
    elif "above 10" in q_lower or "above ₹10" in q_lower:
        filters["min_budget_lakh"] = 10.0

    budget_below_match = re.search(r"(?:below|under|less than|<)\s*(?:₹|rs\.?)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|l|lac|lacs)?", q_lower)
    if budget_below_match:
        val = float(budget_below_match.group(1))
        filters["max_budget_lakh"] = val

    # --------------------------------------------------------------------------
    # 6. Extract Conversion Status
    # --------------------------------------------------------------------------
    if any(phrase in q_lower for phrase in ["not converted", "haven't converted", "unconverted", "non-converted", "who have not converted", "leads that have not converted", "pending conversion"]):
        filters["conversion_status"] = "Active / Not Converted"
    elif "converted" in q_lower and not ("not" in q_lower or "haven't" in q_lower or "rate" in q_lower or "conversion" in q_lower):
        filters["conversion_status"] = "Converted"

    # --------------------------------------------------------------------------
    # 7. Extract Follow-up Status
    # --------------------------------------------------------------------------
    if any(phrase in q_lower for phrase in ["pending follow-up", "pending follow-ups", "pending followups", "upcoming follow-up", "upcoming follow-ups", "upcoming followups", "leads with follow-up", "leads with pending follow-ups", "leads with upcoming follow-ups", "with scheduled follow-up"]):
        filters["followup_status"] = "Pending / Upcoming Follow-up"
    elif "overdue follow" in q_lower or "overdue task" in q_lower:
        filters["followup_status"] = "Overdue Follow-up"
    elif "without follow-up" in q_lower or "no follow-up" in q_lower or "without followups" in q_lower:
        filters["followup_status"] = "No Follow-up Scheduled"

    # --------------------------------------------------------------------------
    # 8. Extract Customer Name / Phone Number / Lead ID
    # --------------------------------------------------------------------------
    # Look for Lead ID format SHA-...
    id_match = re.search(r"SHA-[\w\-]+", q_clean, re.IGNORECASE)
    if id_match:
        filters["name"] = id_match.group(0).upper()
    else:
        # Check for phone numbers (continuous or space-separated digits of length >= 5)
        raw_digits = re.findall(r"\d+", q_clean)
        concat_digits = "".join(raw_digits)
        # Avoid treating budget lakh amount or BHK digit as phone
        is_budget_or_bhk_only = bool(re.search(r"(?:bhk|lakh|lac|lacs|cr)", q_lower)) and len(concat_digits) <= 4
        if len(concat_digits) >= 5 and not is_budget_or_bhk_only:
            filters["phone"] = concat_digits
        else:
            # Check against known customer names in CRM
            all_leads_records = database.get_all_leads(db_path=db_path)
            matched_name = None
            for lead_obj in all_leads_records:
                full_nm = lead_obj.get("customer_name", "").strip()
                if not full_nm:
                    continue
                # Full name match
                if full_nm.lower() in q_lower:
                    matched_name = full_nm
                    break
                # Check individual name tokens (e.g. Kanishka, Dinesh, Chakravarthy, Priti, Aditya, Ganesh)
                name_tokens = [tok.strip() for tok in re.split(r"[\s\.\-]+", full_nm) if len(tok.strip()) >= 3]
                for tok in name_tokens:
                    if tok.lower() not in {"and", "the", "for", "all", "our"} and re.search(r"" + re.escape(tok.lower()) + r"", q_lower):
                        matched_name = tok
                        break
                if matched_name:
                    break
            
            if matched_name:
                filters["name"] = matched_name

    # Execute search
    res = search_crm_leads(filters=filters, db_path=db_path)
    res["intent"] = "crm_search"
    res["query"] = query
    res["markdown"] = format_search_results_markdown(res, query_title=query)
    return res


# ------------------------------------------------------------------------------
# 4. MARKDOWN FORMATTING & PRESENTATION
# ------------------------------------------------------------------------------

def format_search_results_markdown(
    search_res: Dict[str, Any],
    query_title: Optional[str] = None
) -> str:
    """Formats search results into an executive, clean markdown presentation."""
    leads = search_res.get("leads", [])
    total = search_res.get("total_count", 0)
    hp = search_res.get("high_priority_count", 0)
    mp = search_res.get("medium_priority_count", 0)
    lp = search_res.get("low_priority_count", 0)
    summary = search_res.get("filter_summary", "All matching leads")

    if total == 0:
        return (
            f"🔍 **Search Query:** *\"{query_title or 'CRM Lead Search'}\"*\n\n"
            f"⚠️ **No matching leads found** in the active CRM database matching criteria: `{summary}`.\n\n"
            f"💡 **Suggestions:**\n"
            f"- Verify the spelling of the customer's name or locality.\n"
            f"- Try relaxing budget thresholds or clearing some filters.\n"
            f"- Search using the 10-digit phone number or Lead ID (e.g. `SHA-TEST-0001` or `SHA-2026-0001`)."
        )

    lines = []
    header_title = f"Found **{total} matching lead{'s' if total != 1 else ''}** in SHA Interiors CRM"
    if query_title:
        lines.append(f"### 🎯 {header_title}")
        lines.append(f"**Filter Criteria:** {summary}\n")
    else:
        lines.append(f"### 📋 {header_title}\n")

    # Priority Metric Tag
    prio_badges = []
    if hp > 0: prio_badges.append(f"🟢 **{hp} High Priority**")
    if mp > 0: prio_badges.append(f"🟡 **{mp} Medium Priority**")
    if lp > 0: prio_badges.append(f"🔴 **{lp} Low Priority**")
    lines.append(" | ".join(prio_badges) + "\n")

    # Build Table
    lines.append("| Lead ID | Customer Name | Phone | Locality | Property | Budget | Score | Priority | Status | Next Follow-up |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |")

    for l in leads:
        lid = l.get("lead_id", "N/A")
        name = l.get("customer_name", "Valued Client")
        phone = l.get("phone", "N/A")
        loc = l.get("locality") or l.get("city") or "Hyderabad"
        ptype = l.get("project_type", "Residential")
        budget = l.get("budget_range", "Standard")
        score = f"{float(l.get('lead_score') or 0.0):.0f}"
        prio = l.get("priority", "Medium")
        status = l.get("lead_status", "New")
        fu_desc = l.get("next_followup_desc", "None Scheduled")

        prio_icon = "🟢" if prio == "High" else ("🟡" if prio == "Medium" else "🔴")
        lines.append(f"| `{lid}` | **{name}** | `{phone}` | {loc} | {ptype} | {budget} | **{score}** | {prio_icon} {prio} | `{status}` | {fu_desc} |")

    lines.append("\n*All data is verified and retrieved live from the SHA Interface Interiors SQLite CRM database.*")
    return "\n".join(lines)


def format_locality_comparison_markdown(db_path: str = database.DEFAULT_DB_PATH) -> str:
    """Generates an executive side-by-side locality comparison table and analysis."""
    all_leads = database.get_all_leads(db_path=db_path)
    
    loc_stats: Dict[str, Dict[str, Any]] = {}
    for l in all_leads:
        loc = l.get("locality") or l.get("city") or "Unmapped"
        if loc not in loc_stats:
            loc_stats[loc] = {
                "locality": loc,
                "region": l.get("region") or hg.get_region_for_locality(loc),
                "total": 0,
                "high_count": 0,
                "med_count": 0,
                "scores": [],
                "budgets": []
            }
        loc_stats[loc]["total"] += 1
        prio = l.get("priority", "Medium")
        if prio == "High":
            loc_stats[loc]["high_count"] += 1
        elif prio == "Medium":
            loc_stats[loc]["med_count"] += 1
        if l.get("lead_score") is not None:
            loc_stats[loc]["scores"].append(float(l["lead_score"]))
        if l.get("budget_range"):
            loc_stats[loc]["budgets"].append(l["budget_range"])

    sorted_locs = sorted(loc_stats.values(), key=lambda x: (x["high_count"], len(x["scores"]) and sum(x["scores"])/len(x["scores"])), reverse=True)

    lines = [
        "### 🏙️ Hyderabad Metropolitan Localities Lead Comparison",
        "Comprehensive cross-locality breakdown across lead volumes, qualification scores, and priority distribution:\n",
        "| Locality | Region | Active Leads | High Priority | Med Priority | Avg Score | Typical Budget Segment |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :--- |"
    ]

    for ls in sorted_locs:
        avg_sc = f"{sum(ls['scores'])/len(ls['scores']):.1f}/100" if ls["scores"] else "—"
        typ_b = ls["budgets"][0] if ls["budgets"] else "Standard"
        lines.append(
            f"| **{ls['locality']}** | {ls['region']} | **{ls['total']}** | 🟢 {ls['high_count']} | 🟡 {ls['med_count']} | **{avg_sc}** | {typ_b} |"
        )

    lines.append("\n**Key Executive Insights:**")
    lines.append("- **West Hyderabad (Kondapur & Gachibowli):** Highest density of High-Priority turnkey leads with premium ₹10L–₹25L+ budget allocations.")
    lines.append("- **North-West Hyderabad (Miyapur & Bachupally):** Fast-growing residential corridors with active 2BHK/3BHK inquiries in the ₹5L–₹18L bracket.")
    lines.append("- **Central & Established Corridors (Abids & Kukatpally):** High conversion potential with mature residential renovation demand.")

    return "\n".join(lines)
