"""
db_intelligence.py - Safe Database Intelligence & SQL Analysis Layer
SHA Interface Interiors - AI-Powered Lead Management System

Provides safe, read-only SQL query execution, validation, pre-defined analytical
queries, duplicate detection, missing information auditing, and pipeline valuation.
Strictly blocks any database-modifying queries (INSERT, UPDATE, DELETE, DROP, etc.).
"""

import sqlite3
import os
import sys
import re
from typing import Dict, List, Optional, Tuple, Any
import database

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DB_SCHEMA_INFO = """
Database Schema:
Table: LEADS
  - lead_id (TEXT, PRIMARY KEY, e.g. 'SHA-2026-0001')
  - customer_name (TEXT, NOT NULL)
  - phone (TEXT, NOT NULL)
  - email (TEXT)
  - city (TEXT, NOT NULL, e.g. 'Bangalore', 'Hyderabad', 'Chennai', 'Mumbai', 'Pune', 'Delhi')
  - lead_source (TEXT, e.g. 'Website Inquiry', 'Meta Ads', 'Architect Referral')
  - budget_range (TEXT, e.g. 'Below ₹3 lakh', '₹3 lakh–₹5 lakh', '₹5 lakh–₹10 lakh', '₹10 lakh–₹25 lakh', 'Above ₹25 lakh')
  - project_type (TEXT, e.g. '1BHK', '2BHK', '3BHK', '4BHK', 'Villa', 'Commercial')
  - property_status (TEXT, e.g. 'Ready for Possession', 'Under Construction', 'Renovation', 'New Handover')
  - project_timeline (TEXT, e.g. 'Immediate (Within 15 days)', '1–3 months', '3–6 months', 'Exploring / Flexible')
  - scope_of_work (TEXT, e.g. 'Complete Turnkey Interiors', 'Full Home Interiors', 'Modular Kitchen & Wardrobes', 'Living & Dining Decor')
  - customer_requirements (TEXT, detailed client notes)
  - purchase_readiness (TEXT, e.g. 'Ready to Start', 'Comparing Vendors', 'Budget Planning', 'Just Exploring')
  - preferred_contact_method (TEXT, e.g. 'Phone Call', 'WhatsApp', 'Email')
  - lead_status (TEXT, e.g. 'New', 'Qualified', 'Follow-up', 'Converted', 'Lost')
  - lead_score (REAL, 0.0 to 100.0)
  - priority (TEXT, 'High', 'Medium', 'Low')
  - score_breakdown (TEXT, JSON string)
  - scoring_reason (TEXT)
  - scored_at (TEXT)
  - is_opted_out (INTEGER, 0 or 1)
  - opt_out_reason (TEXT)
  - is_paused (INTEGER, 0 or 1)
  - last_customer_response (TEXT)
  - last_response_at (TEXT)
  - created_at (TEXT, ISO timestamp)
  - updated_at (TEXT, ISO timestamp)
  - data_origin (TEXT, 'synthetic_import' or 'manual_entry')

Table: FOLLOW_UP_SCHEDULE
  - schedule_id (TEXT, PRIMARY KEY, e.g. 'FU-...')
  - lead_id (TEXT, FOREIGN KEY references LEADS.lead_id)
  - scheduled_for (TEXT, e.g. '2026-11-05 10:00:00')
  - channel (TEXT, e.g. 'WhatsApp', 'Phone Call', 'Email')
  - message (TEXT)
  - status (TEXT, 'Scheduled', 'Sent', 'Cancelled')
  - attempt_number (INTEGER)
  - created_at (TEXT)
  - completed_at (TEXT)
  - stop_reason (TEXT)

Table: LEAD_ACTIVITY_LOG
  - activity_id (TEXT, PRIMARY KEY)
  - lead_id (TEXT, FOREIGN KEY references LEADS.lead_id)
  - activity_type (TEXT, e.g. 'CREATED', 'SCORED', 'FOLLOWUP_SCHEDULED', 'STATUS_CHANGE')
  - activity_description (TEXT)
  - timestamp (TEXT)
"""

FORBIDDEN_SQL_PATTERNS = [
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bCREATE\b",
    r"\bTRUNCATE\b",
    r"\bREPLACE\s+INTO\b",
    r"\bATTACH\b",
    r"\bDETACH\b",
    r"\bPRAGMA\b",
    r"\bVACUUM\b",
    r"\bREINDEX\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"--",        # SQL single-line comments
    r"/\*",       # SQL multi-line comments
]


def validate_sql_query(sql: str) -> Tuple[bool, str]:
    """
    Validates that the SQL query is strictly read-only (SELECT / WITH)
    and contains no mutating or injection patterns.
    """
    cleaned = sql.strip()
    if not cleaned:
        return False, "Query is empty."

    # Remove trailing semicolon if present
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()

    # Block multiple statements (semicolon in the middle)
    if ";" in cleaned:
        return False, "Multiple SQL statements are not permitted."

    # Check for forbidden keywords using regex word boundary
    for pat in FORBIDDEN_SQL_PATTERNS:
        if re.search(pat, cleaned, re.IGNORECASE):
            match = re.search(pat, cleaned, re.IGNORECASE).group(0)
            return False, f"Forbidden SQL operation detected: '{match}'. AI queries are strictly read-only."

    # Must start with SELECT or WITH
    upper_start = cleaned.upper().lstrip()
    if not (upper_start.startswith("SELECT") or upper_start.startswith("WITH")):
        return False, "Only SELECT or WITH queries are permitted."

    return True, ""


def execute_safe_query(
    sql: str,
    params: tuple = (),
    db_path: str = database.DEFAULT_DB_PATH,
    max_rows: int = 300
) -> Dict[str, Any]:
    """
    Executes a validated read-only SQL query against the SQLite database.
    Returns:
        {
            "success": bool,
            "columns": List[str],
            "rows": List[Dict[str, Any]],
            "row_count": int,
            "truncated": bool,
            "error": Optional[str],
            "sql": str
        }
    """
    is_valid, err_msg = validate_sql_query(sql)
    if not is_valid:
        return {
            "success": False,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "truncated": False,
            "error": err_msg,
            "sql": sql
        }

    # Ensure URI read-only connection
    clean_sql = sql.strip().rstrip(";")
    # Wrap in limit if not present and not an aggregation query
    has_limit = bool(re.search(r"\bLIMIT\b", clean_sql, re.IGNORECASE))
    is_aggregate_only = bool(re.search(r"^\s*SELECT\s+(COUNT|AVG|SUM|MIN|MAX)\b", clean_sql, re.IGNORECASE))
    
    executable_sql = clean_sql
    if not has_limit and not is_aggregate_only:
        executable_sql = f"{clean_sql} LIMIT {max_rows + 1}"

    conn = database.get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(executable_sql, params)
        raw_rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        truncated = len(raw_rows) > max_rows
        final_rows = raw_rows[:max_rows]
        dict_rows = [dict(row) for row in final_rows]

        return {
            "success": True,
            "columns": columns,
            "rows": dict_rows,
            "row_count": len(dict_rows),
            "truncated": truncated,
            "error": None,
            "sql": executable_sql
        }
    except Exception as e:
        return {
            "success": False,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "truncated": False,
            "error": f"Database execution error: {str(e)}",
            "sql": sql
        }
    finally:
        conn.close()


# ==============================================================================
# HIGH-LEVEL DETERMINISTIC ANALYTICAL QUERIES
# ==============================================================================

def get_leads_overview(db_path: str = database.DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Retrieves full pipeline overview stats."""
    return database.get_lead_stats(db_path)


def get_leads_by_priority(priority: str = "High", db_path: str = database.DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieves leads for a specific priority tier."""
    sql = """
    SELECT l.lead_id, l.customer_name, l.phone, l.city, l.budget_range, l.project_type,
           l.lead_score, l.priority, l.lead_status, l.purchase_readiness,
           (SELECT scheduled_for FROM FOLLOW_UP_SCHEDULE WHERE lead_id = l.lead_id AND status = 'Scheduled' ORDER BY scheduled_for ASC LIMIT 1) as next_followup
    FROM LEADS l
    WHERE l.priority = ?
    ORDER BY l.lead_score DESC;
    """
    res = execute_safe_query(sql, (priority.capitalize(),), db_path=db_path)
    return res["rows"] if res["success"] else []


def find_customer(query_term: str, db_path: str = database.DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Searches customers by name, phone number, email, or lead ID."""
    term = f"%{query_term.strip()}%"
    sql = """
    SELECT l.lead_id, l.customer_name, l.phone, l.email, l.city, l.budget_range, l.project_type,
           l.lead_score, l.priority, l.lead_status, l.purchase_readiness, l.property_status,
           l.project_timeline, l.scope_of_work, l.customer_requirements,
           (SELECT scheduled_for FROM FOLLOW_UP_SCHEDULE WHERE lead_id = l.lead_id AND status = 'Scheduled' ORDER BY scheduled_for ASC LIMIT 1) as next_followup
    FROM LEADS l
    WHERE l.lead_id LIKE ? OR l.customer_name LIKE ? OR l.phone LIKE ? OR l.email LIKE ?
    ORDER BY l.lead_score DESC;
    """
    res = execute_safe_query(sql, (term, term, term, term), db_path=db_path)
    return res["rows"] if res["success"] else []


def get_top_leads_by_score(limit: int = 10, db_path: str = database.DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns top N leads ranked by lead score."""
    sql = f"""
    SELECT l.lead_id, l.customer_name, l.phone, l.city, l.budget_range, l.project_type,
           l.lead_score, l.priority, l.lead_status, l.purchase_readiness,
           (SELECT scheduled_for FROM FOLLOW_UP_SCHEDULE WHERE lead_id = l.lead_id AND status = 'Scheduled' ORDER BY scheduled_for ASC LIMIT 1) as next_followup
    FROM LEADS l
    ORDER BY l.lead_score DESC
    LIMIT {int(limit)};
    """
    res = execute_safe_query(sql, db_path=db_path)
    return res["rows"] if res["success"] else []


def get_city_lead_analytics(db_path: str = database.DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns lead volume, avg score, and high-priority count grouped by city."""
    sql = """
    SELECT city,
           COUNT(*) as total_leads,
           SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END) as high_priority_count,
           SUM(CASE WHEN priority = 'Medium' THEN 1 ELSE 0 END) as medium_priority_count,
           SUM(CASE WHEN priority = 'Low' THEN 1 ELSE 0 END) as low_priority_count,
           ROUND(AVG(lead_score), 1) as avg_score
    FROM LEADS
    GROUP BY city
    ORDER BY total_leads DESC;
    """
    res = execute_safe_query(sql, db_path=db_path)
    return res["rows"] if res["success"] else []


def get_customers_by_budget_threshold(min_amount_lakh: float = 10.0, db_path: str = database.DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns customers with budget at or above the specified lakh threshold."""
    # Matches ranges that represent 10 lakh or higher
    high_ranges = ["₹10 lakh–₹25 lakh", "Above ₹25 lakh"]
    if min_amount_lakh <= 5.0:
        high_ranges.append("₹5 lakh–₹10 lakh")
    if min_amount_lakh <= 3.0:
        high_ranges.append("₹3 lakh–₹5 lakh")

    placeholders = ",".join(["?"] * len(high_ranges))
    sql = f"""
    SELECT l.lead_id, l.customer_name, l.phone, l.city, l.budget_range, l.project_type,
           l.lead_score, l.priority, l.lead_status, l.purchase_readiness,
           (SELECT scheduled_for FROM FOLLOW_UP_SCHEDULE WHERE lead_id = l.lead_id AND status = 'Scheduled' ORDER BY scheduled_for ASC LIMIT 1) as next_followup
    FROM LEADS l
    WHERE l.budget_range IN ({placeholders})
    ORDER BY l.lead_score DESC;
    """
    res = execute_safe_query(sql, tuple(high_ranges), db_path=db_path)
    return res["rows"] if res["success"] else []


def get_leads_ready_to_purchase(db_path: str = database.DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns leads actively looking to start immediately (Ready to Start)."""
    sql = """
    SELECT l.lead_id, l.customer_name, l.phone, l.city, l.budget_range, l.project_type,
           l.lead_score, l.priority, l.lead_status, l.project_timeline,
           (SELECT scheduled_for FROM FOLLOW_UP_SCHEDULE WHERE lead_id = l.lead_id AND status = 'Scheduled' ORDER BY scheduled_for ASC LIMIT 1) as next_followup
    FROM LEADS l
    WHERE l.purchase_readiness = 'Ready to Start'
    ORDER BY l.lead_score DESC;
    """
    res = execute_safe_query(sql, db_path=db_path)
    return res["rows"] if res["success"] else []


def get_leads_needing_modular_kitchen(db_path: str = database.DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns leads requiring modular kitchen cabinetry."""
    sql = """
    SELECT l.lead_id, l.customer_name, l.phone, l.city, l.budget_range, l.project_type,
           l.scope_of_work, l.lead_score, l.priority, l.lead_status,
           (SELECT scheduled_for FROM FOLLOW_UP_SCHEDULE WHERE lead_id = l.lead_id AND status = 'Scheduled' ORDER BY scheduled_for ASC LIMIT 1) as next_followup
    FROM LEADS l
    WHERE l.scope_of_work LIKE '%Kitchen%'
       OR l.customer_requirements LIKE '%kitchen%'
       OR l.scope_of_work = 'Complete Turnkey Interiors'
    ORDER BY l.lead_score DESC;
    """
    res = execute_safe_query(sql, db_path=db_path)
    return res["rows"] if res["success"] else []


def get_leads_without_followups(db_path: str = database.DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns active leads that currently have NO follow-up task scheduled."""
    sql = """
    SELECT l.lead_id, l.customer_name, l.phone, l.city, l.budget_range, l.project_type,
           l.lead_score, l.priority, l.lead_status, 'None Scheduled' as next_followup
    FROM LEADS l
    LEFT JOIN FOLLOW_UP_SCHEDULE f ON l.lead_id = f.lead_id AND f.status = 'Scheduled'
    WHERE f.schedule_id IS NULL
      AND l.lead_status NOT IN ('Converted', 'Lost')
      AND l.is_opted_out = 0
    ORDER BY l.lead_score DESC;
    """
    res = execute_safe_query(sql, db_path=db_path)
    return res["rows"] if res["success"] else []


def get_overdue_followups(db_path: str = database.DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns follow-up tasks whose scheduled time has passed and status is still 'Scheduled'."""
    now_str = database.get_current_time_kolkata() if hasattr(database, "get_current_time_kolkata") else ""
    # Use SQLite datetime('now', 'localtime')
    sql = """
    SELECT f.schedule_id, f.lead_id, l.customer_name, l.phone, l.city, l.budget_range,
           l.lead_score, l.priority, f.scheduled_for, f.channel, f.attempt_number,
           f.message
    FROM FOLLOW_UP_SCHEDULE f
    JOIN LEADS l ON f.lead_id = l.lead_id
    WHERE f.status = 'Scheduled'
      AND f.scheduled_for < datetime('now', 'localtime')
    ORDER BY f.scheduled_for ASC;
    """
    res = execute_safe_query(sql, db_path=db_path)
    return res["rows"] if res["success"] else []


def get_recently_added_leads(limit: int = 10, db_path: str = database.DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns the most recently created customer inquiries."""
    sql = f"""
    SELECT l.lead_id, l.customer_name, l.phone, l.city, l.budget_range, l.project_type,
           l.lead_score, l.priority, l.lead_status, l.created_at,
           (SELECT scheduled_for FROM FOLLOW_UP_SCHEDULE WHERE lead_id = l.lead_id AND status = 'Scheduled' ORDER BY scheduled_for ASC LIMIT 1) as next_followup
    FROM LEADS l
    ORDER BY l.created_at DESC
    LIMIT {int(limit)};
    """
    res = execute_safe_query(sql, db_path=db_path)
    return res["rows"] if res["success"] else []


def detect_duplicate_leads(db_path: str = database.DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Identifies duplicate customer leads based on matching phone number or email."""
    sql = """
    SELECT phone, COUNT(*) as count, GROUP_CONCAT(lead_id) as lead_ids, GROUP_CONCAT(customer_name) as names
    FROM LEADS
    WHERE phone IS NOT NULL AND phone != ''
    GROUP BY phone
    HAVING COUNT(*) > 1;
    """
    res = execute_safe_query(sql, db_path=db_path)
    return res["rows"] if res["success"] else []


def detect_missing_information(db_path: str = database.DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Audits CRM records for missing critical information (email, custom requirements, contact preferences)."""
    sql_missing_email = "SELECT COUNT(*) as c FROM LEADS WHERE email IS NULL OR TRIM(email) = '';"
    sql_missing_notes = "SELECT COUNT(*) as c FROM LEADS WHERE customer_requirements IS NULL OR TRIM(customer_requirements) = '' OR customer_requirements LIKE '%standard%' OR customer_requirements LIKE '%minimal%';"
    sql_missing_phone = "SELECT COUNT(*) as c FROM LEADS WHERE phone IS NULL OR TRIM(phone) = '';"

    c_email = execute_safe_query(sql_missing_email, db_path=db_path)["rows"][0]["c"]
    c_notes = execute_safe_query(sql_missing_notes, db_path=db_path)["rows"][0]["c"]
    c_phone = execute_safe_query(sql_missing_phone, db_path=db_path)["rows"][0]["c"]

    total = execute_safe_query("SELECT COUNT(*) as c FROM LEADS;", db_path=db_path)["rows"][0]["c"]

    return {
        "total_leads": total,
        "missing_email_count": c_email,
        "vague_or_missing_notes_count": c_notes,
        "missing_phone_count": c_phone,
        "completeness_score": round(((total * 3 - (c_email + c_notes + c_phone)) / max(total * 3, 1)) * 100, 1)
    }


def calculate_sales_pipeline_value(db_path: str = database.DEFAULT_DB_PATH) -> Dict[str, Any]:
    """
    Calculates estimated sales pipeline value by mapping budget ranges to conservative midpoint rupees,
    and computing both nominal pipeline and probability-weighted pipeline.
    """
    # Midpoint rupee value mapping
    BUDGET_MIDPOINTS = {
        "Below ₹3 lakh": 250000,
        "₹3 lakh–₹5 lakh": 400000,
        "₹5 lakh–₹10 lakh": 750000,
        "₹10 lakh–₹25 lakh": 1750000,
        "Above ₹25 lakh": 3500000
    }

    # Conversion probability weights by priority
    PRIORITY_WEIGHTS = {
        "High": 0.45,    # 45% conversion expectation
        "Medium": 0.20,  # 20% conversion expectation
        "Low": 0.05      # 5% conversion expectation
    }

    sql = """
    SELECT budget_range, priority, lead_status, COUNT(*) as count
    FROM LEADS
    WHERE lead_status NOT IN ('Lost')
    GROUP BY budget_range, priority, lead_status;
    """
    res = execute_safe_query(sql, db_path=db_path)
    if not res["success"]:
        return {"nominal_value": 0, "weighted_value": 0, "active_deal_count": 0}

    total_nominal = 0.0
    total_weighted = 0.0
    active_count = 0
    converted_value = 0.0
    converted_count = 0

    for r in res["rows"]:
        b_val = BUDGET_MIDPOINTS.get(r["budget_range"], 750000)
        cnt = r["count"]
        status = r["lead_status"]
        priority = r["priority"] or "Medium"

        if status == "Converted":
            converted_value += b_val * cnt
            converted_count += cnt
        else:
            total_nominal += b_val * cnt
            total_weighted += b_val * cnt * PRIORITY_WEIGHTS.get(priority, 0.15)
            active_count += cnt

    return {
        "nominal_pipeline_inr": total_nominal,
        "weighted_pipeline_inr": total_weighted,
        "active_pipeline_deals": active_count,
        "converted_pipeline_inr": converted_value,
        "converted_deal_count": converted_count,
        "formatted_nominal": f"₹{total_nominal / 10000000:.2f} Cr",
        "formatted_weighted": f"₹{total_weighted / 10000000:.2f} Cr",
        "formatted_converted": f"₹{converted_value / 10000000:.2f} Cr"
    }


def format_leads_table(leads: List[Dict[str, Any]], max_rows: int = 15) -> str:
    """
    Formats a list of lead dictionaries into the standard, clean Markdown table:
    Lead ID | Customer Name | Phone | Locality | Region | Budget | Project Type | Lead Score | Priority | Status | Next Follow-up
    """
    if not leads:
        return "*No matching leads found.*"

    header = (
        "| Lead ID | Customer Name | Phone | Locality | Region | Budget | Project Type | Lead Score | Priority | Status | Next Follow-up |\n"
        "|:---|:---|:---|:---|:---|:---|:---|:---:|:---:|:---:|:---:|\n"
    )

    rows = []
    for l in leads[:max_rows]:
        score_val = f"{l.get('lead_score'):.0f}" if l.get('lead_score') is not None else "—"
        p_val = l.get('priority', '—')
        p_pill = f"🟢 {p_val}" if p_val == "High" else (f"🟡 {p_val}" if p_val == "Medium" else f"🔴 {p_val}")
        next_fu = l.get('next_followup') or "None Scheduled"
        if len(str(next_fu)) > 16:
            next_fu = str(next_fu)[:16]

        loc = l.get('locality') or 'Unmapped'
        reg = l.get('region') or 'Unspecified'

        row = (
            f"| `{l.get('lead_id', '—')}` "
            f"| **{l.get('customer_name', '—')}** "
            f"| {l.get('phone', '—')} "
            f"| {loc} "
            f"| {reg} "
            f"| {l.get('budget_range', '—')} "
            f"| {l.get('project_type', '—')} "
            f"| **{score_val}** "
            f"| {p_pill} "
            f"| {l.get('lead_status', '—')} "
            f"| {next_fu} |"
        )
        rows.append(row)

    table_md = header + "\n".join(rows)
    if len(leads) > max_rows:
        table_md += f"\n\n*... showing {max_rows} of {len(leads)} matching leads.*"

    return table_md
