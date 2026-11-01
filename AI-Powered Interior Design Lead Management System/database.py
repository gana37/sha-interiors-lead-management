import sqlite3
import os
import json
import datetime
from typing import Dict, List, Optional, Tuple, Any

DEFAULT_DB_PATH = "sha_leads.db"

def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Creates and returns an SQLite connection with Row factory enabled."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initializes the SQLite database and creates all tables, columns, and indexes if not present."""
    create_leads_sql = """
    CREATE TABLE IF NOT EXISTS LEADS (
        lead_id TEXT PRIMARY KEY,
        customer_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        city TEXT NOT NULL,
        lead_source TEXT NOT NULL,
        budget_range TEXT NOT NULL,
        project_type TEXT NOT NULL,
        property_status TEXT NOT NULL,
        project_timeline TEXT NOT NULL,
        scope_of_work TEXT NOT NULL,
        customer_requirements TEXT,
        purchase_readiness TEXT NOT NULL,
        preferred_contact_method TEXT NOT NULL,
        lead_status TEXT NOT NULL DEFAULT 'New',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        data_origin TEXT NOT NULL
    );
    """

    create_followup_schedule_sql = """
    CREATE TABLE IF NOT EXISTS FOLLOW_UP_SCHEDULE (
        schedule_id TEXT PRIMARY KEY,
        lead_id TEXT NOT NULL,
        scheduled_for TEXT NOT NULL,
        channel TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Scheduled',
        attempt_number INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        completed_at TEXT,
        stop_reason TEXT,
        FOREIGN KEY (lead_id) REFERENCES LEADS(lead_id)
    );
    """

    create_activity_log_sql = """
    CREATE TABLE IF NOT EXISTS LEAD_ACTIVITY_LOG (
        activity_id TEXT PRIMARY KEY,
        lead_id TEXT NOT NULL,
        activity_type TEXT NOT NULL,
        activity_description TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (lead_id) REFERENCES LEADS(lead_id)
    );
    """
    
    index_sqls = [
        "CREATE INDEX IF NOT EXISTS idx_leads_phone ON LEADS(phone);",
        "CREATE INDEX IF NOT EXISTS idx_leads_email ON LEADS(email);",
        "CREATE INDEX IF NOT EXISTS idx_leads_city ON LEADS(city);",
        "CREATE INDEX IF NOT EXISTS idx_leads_status ON LEADS(lead_status);",
        "CREATE INDEX IF NOT EXISTS idx_leads_origin ON LEADS(data_origin);",
        "CREATE INDEX IF NOT EXISTS idx_followup_lead ON FOLLOW_UP_SCHEDULE(lead_id);",
        "CREATE INDEX IF NOT EXISTS idx_followup_status ON FOLLOW_UP_SCHEDULE(status);",
        "CREATE INDEX IF NOT EXISTS idx_followup_due ON FOLLOW_UP_SCHEDULE(scheduled_for);",
        "CREATE INDEX IF NOT EXISTS idx_activity_lead ON LEAD_ACTIVITY_LOG(lead_id);",
        "CREATE INDEX IF NOT EXISTS idx_activity_time ON LEAD_ACTIVITY_LOG(timestamp);"
    ]
    
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(create_leads_sql)
            cursor.execute(create_followup_schedule_sql)
            cursor.execute(create_activity_log_sql)
            for idx in index_sqls:
                cursor.execute(idx)
                
            # Check for Step 4 & Step 5 columns in LEADS
            cursor.execute("PRAGMA table_info(LEADS);")
            existing_cols = {row[1] for row in cursor.fetchall()}
            
            additional_cols = [
                ("lead_score", "REAL"),
                ("priority", "TEXT"),
                ("score_breakdown", "TEXT"),
                ("scoring_reason", "TEXT"),
                ("scored_at", "TEXT"),
                ("is_opted_out", "INTEGER DEFAULT 0"),
                ("opt_out_reason", "TEXT"),
                ("is_paused", "INTEGER DEFAULT 0"),
                ("last_customer_response", "TEXT"),
                ("last_response_at", "TEXT")
            ]
            
            for col_name, col_type in additional_cols:
                if col_name not in existing_cols:
                    cursor.execute(f"ALTER TABLE LEADS ADD COLUMN {col_name} {col_type};")
                    
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_score ON LEADS(lead_score);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_priority ON LEADS(priority);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_optout ON LEADS(is_opted_out);")
    finally:
        conn.close()

def generate_next_lead_id(prefix: str = "SHA", db_path: str = DEFAULT_DB_PATH) -> str:
    """Generates the next sequential Lead ID, e.g. SHA-2026-0001."""
    year = datetime.datetime.now().year
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT lead_id FROM LEADS WHERE lead_id LIKE ? ORDER BY lead_id DESC LIMIT 1;",
            (f"{prefix}-{year}-%",)
        )
        row = cursor.fetchone()
        if row:
            last_id = row["lead_id"]
            try:
                seq = int(last_id.split("-")[-1]) + 1
            except ValueError:
                seq = 1
        else:
            cursor.execute("SELECT COUNT(*) as count FROM LEADS;")
            seq = cursor.fetchone()["count"] + 1
            
        return f"{prefix}-{year}-{seq:04d}"
    finally:
        conn.close()

def insert_lead(lead_data: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> bool:
    """Inserts a single lead record into the database."""
    init_db(db_path)
    now = datetime.datetime.now().isoformat()
    
    record = {
        "lead_id": lead_data["lead_id"],
        "customer_name": lead_data["customer_name"].strip(),
        "phone": lead_data["phone"].strip(),
        "email": (lead_data.get("email") or "").strip() or None,
        "city": lead_data["city"].strip(),
        "lead_source": lead_data.get("lead_source", "Website Inquiry").strip(),
        "budget_range": lead_data["budget_range"].strip(),
        "project_type": lead_data["project_type"].strip(),
        "property_status": lead_data["property_status"].strip(),
        "project_timeline": lead_data["project_timeline"].strip(),
        "scope_of_work": lead_data["scope_of_work"].strip(),
        "customer_requirements": (lead_data.get("customer_requirements") or "").strip() or None,
        "purchase_readiness": lead_data["purchase_readiness"].strip(),
        "preferred_contact_method": lead_data.get("preferred_contact_method", "Phone Call").strip(),
        "lead_status": lead_data.get("lead_status", "New").strip(),
        "created_at": lead_data.get("created_at", now),
        "updated_at": lead_data.get("updated_at", now),
        "data_origin": lead_data.get("data_origin", "manual_entry"),
        "lead_score": lead_data.get("lead_score"),
        "priority": lead_data.get("priority"),
        "score_breakdown": lead_data.get("score_breakdown"),
        "scoring_reason": lead_data.get("scoring_reason"),
        "scored_at": lead_data.get("scored_at"),
        "is_opted_out": lead_data.get("is_opted_out", 0),
        "opt_out_reason": lead_data.get("opt_out_reason"),
        "is_paused": lead_data.get("is_paused", 0),
        "last_customer_response": lead_data.get("last_customer_response"),
        "last_response_at": lead_data.get("last_response_at")
    }
    
    sql = """
    INSERT INTO LEADS (
        lead_id, customer_name, phone, email, city, lead_source,
        budget_range, project_type, property_status, project_timeline,
        scope_of_work, customer_requirements, purchase_readiness,
        preferred_contact_method, lead_status, created_at, updated_at, data_origin,
        lead_score, priority, score_breakdown, scoring_reason, scored_at,
        is_opted_out, opt_out_reason, is_paused, last_customer_response, last_response_at
    ) VALUES (
        :lead_id, :customer_name, :phone, :email, :city, :lead_source,
        :budget_range, :project_type, :property_status, :project_timeline,
        :scope_of_work, :customer_requirements, :purchase_readiness,
        :preferred_contact_method, :lead_status, :created_at, :updated_at, :data_origin,
        :lead_score, :priority, :score_breakdown, :scoring_reason, :scored_at,
        :is_opted_out, :opt_out_reason, :is_paused, :last_customer_response, :last_response_at
    );
    """
    
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql, record)
        return True
    finally:
        conn.close()

def batch_insert_leads(leads_list: List[Dict[str, Any]], db_path: str = DEFAULT_DB_PATH) -> int:
    """Transactionally inserts a batch of leads."""
    if not leads_list:
        return 0
    init_db(db_path)
    now = datetime.datetime.now().isoformat()
    
    sql = """
    INSERT INTO LEADS (
        lead_id, customer_name, phone, email, city, lead_source,
        budget_range, project_type, property_status, project_timeline,
        scope_of_work, customer_requirements, purchase_readiness,
        preferred_contact_method, lead_status, created_at, updated_at, data_origin,
        lead_score, priority, score_breakdown, scoring_reason, scored_at,
        is_opted_out, opt_out_reason, is_paused, last_customer_response, last_response_at
    ) VALUES (
        :lead_id, :customer_name, :phone, :email, :city, :lead_source,
        :budget_range, :project_type, :property_status, :project_timeline,
        :scope_of_work, :customer_requirements, :purchase_readiness,
        :preferred_contact_method, :lead_status, :created_at, :updated_at, :data_origin,
        :lead_score, :priority, :score_breakdown, :scoring_reason, :scored_at,
        :is_opted_out, :opt_out_reason, :is_paused, :last_customer_response, :last_response_at
    );
    """
    
    formatted_leads = []
    for l in leads_list:
        formatted_leads.append({
            "lead_id": l["lead_id"],
            "customer_name": l["customer_name"].strip(),
            "phone": l["phone"].strip(),
            "email": (l.get("email") or "").strip() or None,
            "city": l["city"].strip(),
            "lead_source": l.get("lead_source", "Website Inquiry").strip(),
            "budget_range": l["budget_range"].strip(),
            "project_type": l["project_type"].strip(),
            "property_status": l["property_status"].strip(),
            "project_timeline": l["project_timeline"].strip(),
            "scope_of_work": l["scope_of_work"].strip(),
            "customer_requirements": (l.get("customer_requirements") or "").strip() or None,
            "purchase_readiness": l["purchase_readiness"].strip(),
            "preferred_contact_method": l.get("preferred_contact_method", "Phone Call").strip(),
            "lead_status": l.get("lead_status", "New").strip(),
            "created_at": l.get("created_at", now),
            "updated_at": l.get("updated_at", now),
            "data_origin": l.get("data_origin", "synthetic_import"),
            "lead_score": l.get("lead_score"),
            "priority": l.get("priority"),
            "score_breakdown": l.get("score_breakdown"),
            "scoring_reason": l.get("scoring_reason"),
            "scored_at": l.get("scored_at"),
            "is_opted_out": l.get("is_opted_out", 0),
            "opt_out_reason": l.get("opt_out_reason"),
            "is_paused": l.get("is_paused", 0),
            "last_customer_response": l.get("last_customer_response"),
            "last_response_at": l.get("last_response_at")
        })
        
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.executemany(sql, formatted_leads)
        return len(formatted_leads)
    finally:
        conn.close()

def update_lead_score(
    lead_id: str,
    lead_score: float,
    priority: str,
    score_breakdown: str,
    scoring_reason: str,
    db_path: str = DEFAULT_DB_PATH
) -> bool:
    """Updates the lead score, priority, breakdown, and reasoning without altering lead_status."""
    init_db(db_path)
    now = datetime.datetime.now().isoformat()
    sql = """
    UPDATE LEADS SET
        lead_score = ?,
        priority = ?,
        score_breakdown = ?,
        scoring_reason = ?,
        scored_at = ?,
        updated_at = ?
    WHERE lead_id = ?;
    """
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql, (lead_score, priority, score_breakdown, scoring_reason, now, now, lead_id))
        return cursor.rowcount > 0
    finally:
        conn.close()

def batch_update_lead_scores(
    scored_leads: List[Dict[str, Any]],
    db_path: str = DEFAULT_DB_PATH
) -> int:
    """Batch updates lead scores and priorities in a single atomic transaction."""
    if not scored_leads:
        return 0
    init_db(db_path)
    now = datetime.datetime.now().isoformat()
    sql = """
    UPDATE LEADS SET
        lead_score = :lead_score,
        priority = :priority,
        score_breakdown = :score_breakdown,
        scoring_reason = :scoring_reason,
        scored_at = :scored_at,
        updated_at = :updated_at
    WHERE lead_id = :lead_id;
    """
    params = []
    for item in scored_leads:
        params.append({
            "lead_id": item["lead_id"],
            "lead_score": item["lead_score"],
            "priority": item["priority"],
            "score_breakdown": item["score_breakdown"] if isinstance(item["score_breakdown"], str) else json.dumps(item["score_breakdown"]),
            "scoring_reason": item["scoring_reason"],
            "scored_at": item.get("scored_at", now),
            "updated_at": now
        })
        
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.executemany(sql, params)
        return len(params)
    finally:
        conn.close()

def update_lead_crm_status(lead_id: str, new_status: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Updates the CRM lead status (e.g. New, Qualified, Follow-up, Converted, Lost)."""
    init_db(db_path)
    now = datetime.datetime.now().isoformat()
    sql = "UPDATE LEADS SET lead_status = ?, updated_at = ? WHERE lead_id = ?;"
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql, (new_status, now, lead_id))
        return cursor.rowcount > 0
    finally:
        conn.close()

def update_lead_opt_out(lead_id: str, is_opted_out: int, reason: Optional[str] = None, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Updates the opt-out state of a lead."""
    init_db(db_path)
    now = datetime.datetime.now().isoformat()
    sql = "UPDATE LEADS SET is_opted_out = ?, opt_out_reason = ?, updated_at = ? WHERE lead_id = ?;"
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql, (is_opted_out, reason, now, lead_id))
        return cursor.rowcount > 0
    finally:
        conn.close()

def update_lead_pause_state(lead_id: str, is_paused: int, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Pauses or resumes follow-ups for a lead."""
    init_db(db_path)
    now = datetime.datetime.now().isoformat()
    sql = "UPDATE LEADS SET is_paused = ?, updated_at = ? WHERE lead_id = ?;"
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql, (is_paused, now, lead_id))
        return cursor.rowcount > 0
    finally:
        conn.close()

def record_customer_response(lead_id: str, response_text: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Records a customer response and updates response timestamp."""
    init_db(db_path)
    now = datetime.datetime.now().isoformat()
    sql = "UPDATE LEADS SET last_customer_response = ?, last_response_at = ?, updated_at = ? WHERE lead_id = ?;"
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql, (response_text, now, now, lead_id))
        return cursor.rowcount > 0
    finally:
        conn.close()

# -------------------------------------------------------------
# ACTIVITY LOG OPERATIONS
# -------------------------------------------------------------

def insert_activity_log(
    lead_id: str,
    activity_type: str,
    activity_description: str,
    timestamp: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> str:
    """Logs an action, status change, or customer interaction in LEAD_ACTIVITY_LOG."""
    init_db(db_path)
    now = timestamp or datetime.datetime.now().isoformat()
    activity_id = f"ACT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(2).hex()}"
    
    sql = """
    INSERT INTO LEAD_ACTIVITY_LOG (activity_id, lead_id, activity_type, activity_description, timestamp)
    VALUES (?, ?, ?, ?, ?);
    """
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql, (activity_id, lead_id, activity_type, activity_description, now))
        return activity_id
    finally:
        conn.close()

def get_lead_activities(lead_id: str, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieves all activity history for a specific lead."""
    init_db(db_path)
    sql = "SELECT * FROM LEAD_ACTIVITY_LOG WHERE lead_id = ? ORDER BY timestamp DESC;"
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (lead_id,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

# -------------------------------------------------------------
# FOLLOW-UP SCHEDULE OPERATIONS
# -------------------------------------------------------------

def insert_followup_schedule(record: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> bool:
    """Inserts a single follow-up task into FOLLOW_UP_SCHEDULE."""
    init_db(db_path)
    now = datetime.datetime.now().isoformat()
    sql = """
    INSERT INTO FOLLOW_UP_SCHEDULE (
        schedule_id, lead_id, scheduled_for, channel, message,
        status, attempt_number, created_at, completed_at, stop_reason
    ) VALUES (
        :schedule_id, :lead_id, :scheduled_for, :channel, :message,
        :status, :attempt_number, :created_at, :completed_at, :stop_reason
    );
    """
    data = {
        "schedule_id": record["schedule_id"],
        "lead_id": record["lead_id"],
        "scheduled_for": record["scheduled_for"],
        "channel": record.get("channel", "WhatsApp"),
        "message": record["message"],
        "status": record.get("status", "Scheduled"),
        "attempt_number": record.get("attempt_number", 1),
        "created_at": record.get("created_at", now),
        "completed_at": record.get("completed_at"),
        "stop_reason": record.get("stop_reason")
    }
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql, data)
        return True
    finally:
        conn.close()

def batch_insert_followup_schedules(records: List[Dict[str, Any]], db_path: str = DEFAULT_DB_PATH) -> int:
    """Transactionally inserts multiple follow-up schedule records."""
    if not records:
        return 0
    init_db(db_path)
    now = datetime.datetime.now().isoformat()
    sql = """
    INSERT INTO FOLLOW_UP_SCHEDULE (
        schedule_id, lead_id, scheduled_for, channel, message,
        status, attempt_number, created_at, completed_at, stop_reason
    ) VALUES (
        :schedule_id, :lead_id, :scheduled_for, :channel, :message,
        :status, :attempt_number, :created_at, :completed_at, :stop_reason
    );
    """
    params = []
    for r in records:
        params.append({
            "schedule_id": r["schedule_id"],
            "lead_id": r["lead_id"],
            "scheduled_for": r["scheduled_for"],
            "channel": r.get("channel", "WhatsApp"),
            "message": r["message"],
            "status": r.get("status", "Scheduled"),
            "attempt_number": r.get("attempt_number", 1),
            "created_at": r.get("created_at", now),
            "completed_at": r.get("completed_at"),
            "stop_reason": r.get("stop_reason")
        })
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.executemany(sql, params)
        return len(params)
    finally:
        conn.close()

def update_followup_status(
    schedule_id: str,
    status: str,
    completed_at: Optional[str] = None,
    stop_reason: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> bool:
    """Updates the status and resolution details of a scheduled follow-up."""
    init_db(db_path)
    sql = """
    UPDATE FOLLOW_UP_SCHEDULE SET
        status = ?,
        completed_at = ?,
        stop_reason = ?
    WHERE schedule_id = ?;
    """
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql, (status, completed_at, stop_reason, schedule_id))
        return cursor.rowcount > 0
    finally:
        conn.close()

def cancel_scheduled_followups_for_lead(
    lead_id: str,
    stop_reason: str,
    db_path: str = DEFAULT_DB_PATH
) -> int:
    """Cancels all future Scheduled or Due follow-ups for a specific lead."""
    init_db(db_path)
    now = datetime.datetime.now().isoformat()
    sql = """
    UPDATE FOLLOW_UP_SCHEDULE SET
        status = 'Cancelled',
        completed_at = ?,
        stop_reason = ?
    WHERE lead_id = ? AND status IN ('Scheduled', 'Due');
    """
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql, (now, stop_reason, lead_id))
        return cursor.rowcount
    finally:
        conn.close()

def get_followups(
    db_path: str = DEFAULT_DB_PATH,
    lead_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Retrieves follow-up tasks with optional filters."""
    init_db(db_path)
    sql = """
    SELECT f.*, l.customer_name, l.phone, l.city, l.priority, l.lead_status, l.budget_range, l.project_type
    FROM FOLLOW_UP_SCHEDULE f
    LEFT JOIN LEADS l ON f.lead_id = l.lead_id
    WHERE 1=1
    """
    params: List[Any] = []
    if lead_id:
        sql += " AND f.lead_id = ?"
        params.append(lead_id)
    if status and status != "All":
        sql += " AND f.status = ?"
        params.append(status)
        
    sql += " ORDER BY f.scheduled_for ASC"
    if limit:
        sql += f" LIMIT {int(limit)}"
        
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

def get_followup_by_id(schedule_id: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves a single follow-up task by ID."""
    init_db(db_path)
    sql = """
    SELECT f.*, l.customer_name, l.phone, l.city, l.priority, l.lead_status, l.is_opted_out, l.is_paused, l.last_customer_response
    FROM FOLLOW_UP_SCHEDULE f
    LEFT JOIN LEADS l ON f.lead_id = l.lead_id
    WHERE f.schedule_id = ?;
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (schedule_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_followup_stats(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Returns aggregated summary metrics for follow-ups."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM FOLLOW_UP_SCHEDULE;")
        total = cursor.fetchone()["total"]
        
        cursor.execute("SELECT status, COUNT(*) as count FROM FOLLOW_UP_SCHEDULE GROUP BY status;")
        status_counts = {r["status"]: r["count"] for r in cursor.fetchall()}
        
        # Check due tasks (scheduled_for <= now and status == 'Scheduled')
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "SELECT COUNT(*) as due_count FROM FOLLOW_UP_SCHEDULE WHERE status IN ('Scheduled', 'Due') AND scheduled_for <= ?;",
            (now_str,)
        )
        due_now = cursor.fetchone()["due_count"]
        
        return {
            "total_followups": total,
            "status_counts": status_counts,
            "due_count": due_now,
            "completed_count": status_counts.get("Completed", 0) + status_counts.get("Sent", 0),
            "cancelled_count": status_counts.get("Cancelled", 0),
            "scheduled_count": status_counts.get("Scheduled", 0)
        }
    finally:
        conn.close()

# -------------------------------------------------------------
# QUERY LEADS WITH ENHANCED FILTERING
# -------------------------------------------------------------

def get_all_leads(
    db_path: str = DEFAULT_DB_PATH,
    city: Optional[str] = None,
    project_type: Optional[str] = None,
    budget_range: Optional[str] = None,
    lead_status: Optional[str] = None,
    priority: Optional[str] = None,
    data_origin: Optional[str] = None,
    search_query: Optional[str] = None,
    order_by: str = "created_at DESC"
) -> List[Dict[str, Any]]:
    """Retrieves leads with optional filtering and search."""
    init_db(db_path)
    sql = "SELECT * FROM LEADS WHERE 1=1"
    params: List[Any] = []
    
    if city and city != "All":
        sql += " AND city = ?"
        params.append(city)
    if project_type and project_type != "All":
        sql += " AND project_type = ?"
        params.append(project_type)
    if budget_range and budget_range != "All":
        sql += " AND budget_range = ?"
        params.append(budget_range)
    if lead_status and lead_status != "All":
        sql += " AND lead_status = ?"
        params.append(lead_status)
    if priority and priority != "All":
        sql += " AND priority = ?"
        params.append(priority)
    if data_origin and data_origin != "All":
        sql += " AND data_origin = ?"
        params.append(data_origin)
    if search_query:
        query_pattern = f"%{search_query.strip()}%"
        sql += " AND (customer_name LIKE ? OR lead_id LIKE ? OR phone LIKE ? OR email LIKE ?)"
        params.extend([query_pattern, query_pattern, query_pattern, query_pattern])
        
    valid_orders = {
        "created_at DESC": "created_at DESC",
        "lead_score DESC": "lead_score DESC NULLS LAST",
        "lead_score ASC": "lead_score ASC NULLS LAST",
        "customer_name ASC": "customer_name ASC"
    }
    sql += f" ORDER BY {valid_orders.get(order_by, 'created_at DESC')};"
    
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def get_lead_by_id(lead_id: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves a single lead by its lead_id."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM LEADS WHERE lead_id = ?;", (lead_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def check_duplicate_contact(
    phone: str, 
    email: Optional[str] = None, 
    exclude_lead_id: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Checks whether the phone or email is already registered to another lead."""
    init_db(db_path)
    clean_phone = phone.strip()
    clean_email = (email or "").strip().lower()
    
    sql = "SELECT lead_id, customer_name, phone, email, lead_status, data_origin FROM LEADS WHERE phone = ?"
    params = [clean_phone]
    
    if clean_email:
        sql += " OR (email IS NOT NULL AND LOWER(email) = ?)"
        params.append(clean_email)
        
    if exclude_lead_id:
        sql = f"SELECT * FROM ({sql}) WHERE lead_id != ?"
        params.append(exclude_lead_id)
        
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def get_existing_lead_ids(db_path: str = DEFAULT_DB_PATH) -> set:
    """Returns a set of all lead_ids currently in the database."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT lead_id FROM LEADS;")
        return {row["lead_id"] for row in cursor.fetchall()}
    finally:
        conn.close()

def get_lead_stats(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Returns aggregated summary metrics for the CRM dashboard, including AI scoring metrics."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM LEADS;")
        total = cursor.fetchone()["total"]
        
        cursor.execute("SELECT lead_status, COUNT(*) as count FROM LEADS GROUP BY lead_status;")
        status_counts = {r["lead_status"]: r["count"] for r in cursor.fetchall()}
        
        cursor.execute("SELECT data_origin, COUNT(*) as count FROM LEADS GROUP BY data_origin;")
        origin_counts = {r["data_origin"]: r["count"] for r in cursor.fetchall()}
        
        cursor.execute("SELECT city, COUNT(*) as count FROM LEADS GROUP BY city ORDER BY count DESC LIMIT 5;")
        top_cities = {r["city"]: r["count"] for r in cursor.fetchall()}
        
        cursor.execute("SELECT project_type, COUNT(*) as count FROM LEADS GROUP BY project_type;")
        project_types = {r["project_type"]: r["count"] for r in cursor.fetchall()}
        
        cursor.execute("SELECT COUNT(*) as scored_count FROM LEADS WHERE lead_score IS NOT NULL;")
        scored_count = cursor.fetchone()["scored_count"]
        
        cursor.execute("SELECT AVG(lead_score) as avg_score FROM LEADS WHERE lead_score IS NOT NULL;")
        avg_score_row = cursor.fetchone()["avg_score"]
        avg_score = round(avg_score_row, 1) if avg_score_row is not None else 0.0
        
        cursor.execute("SELECT priority, COUNT(*) as count FROM LEADS WHERE priority IS NOT NULL GROUP BY priority;")
        priority_counts = {r["priority"]: r["count"] for r in cursor.fetchall()}
        
        # Follow-up stats integration
        cursor.execute("SELECT COUNT(*) as total_fu FROM FOLLOW_UP_SCHEDULE;")
        total_fu = cursor.fetchone()["total_fu"]
        
        cursor.execute("SELECT COUNT(*) as completed_fu FROM FOLLOW_UP_SCHEDULE WHERE status IN ('Completed', 'Sent');")
        completed_fu = cursor.fetchone()["completed_fu"]
        
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("SELECT COUNT(*) as pending_fu FROM FOLLOW_UP_SCHEDULE WHERE status IN ('Scheduled', 'Due') AND scheduled_for <= ?;", (now_str,))
        pending_fu = cursor.fetchone()["pending_fu"]
        
        return {
            "total_leads": total,
            "status_counts": status_counts,
            "origin_counts": origin_counts,
            "top_cities": top_cities,
            "project_types": project_types,
            "scored_count": scored_count,
            "avg_score": avg_score,
            "priority_counts": priority_counts,
            "total_followups": total_fu,
            "pending_followups": pending_fu,
            "completed_followups": completed_fu
        }
    finally:
        conn.close()
