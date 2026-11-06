import sqlite3
import os
import json
import datetime
from typing import Dict, List, Optional, Tuple, Any
import hyderabad_geo as hg
import estimate_parser

DEFAULT_DB_PATH = "sha_leads.db"

def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Creates and returns an SQLite connection with Row factory enabled."""
    conn = sqlite3.connect(db_path, timeout=30.0)
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

    create_conversation_history_sql = """
    CREATE TABLE IF NOT EXISTS CUSTOMER_CONVERSATIONS (
        conversation_id TEXT PRIMARY KEY,
        lead_id TEXT NOT NULL,
        message_id TEXT NOT NULL,
        direction TEXT NOT NULL,
        channel TEXT NOT NULL DEFAULT 'WhatsApp',
        message_content TEXT NOT NULL,
        ai_generated_response TEXT,
        approval_status TEXT NOT NULL DEFAULT 'Draft',
        sending_status TEXT NOT NULL DEFAULT 'Draft',
        sent_at TEXT,
        created_at TEXT NOT NULL,
        metadata TEXT,
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
        "CREATE INDEX IF NOT EXISTS idx_activity_time ON LEAD_ACTIVITY_LOG(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_conv_lead ON CUSTOMER_CONVERSATIONS(lead_id);",
        "CREATE INDEX IF NOT EXISTS idx_conv_time ON CUSTOMER_CONVERSATIONS(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_conv_status ON CUSTOMER_CONVERSATIONS(sending_status);"
    ]
    
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(create_leads_sql)
            cursor.execute(create_followup_schedule_sql)
            cursor.execute(create_activity_log_sql)
            cursor.execute(create_conversation_history_sql)
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
                ("last_response_at", "TEXT"),
                ("state", "TEXT DEFAULT 'Telangana'"),
                ("locality", "TEXT"),
                ("region", "TEXT"),
                ("pincode", "TEXT"),
                ("is_service_area", "INTEGER DEFAULT 1"),
                ("lead_reference", "TEXT"),
                ("estimate_generated_at", "TEXT"),
                ("opt_out_date", "TEXT"),
                ("assigned_salesperson", "TEXT DEFAULT 'Senior Interior Consultant'"),
                ("expected_handover_date", "TEXT"),
                ("current_project_stage", "TEXT"),
                ("property_area_sqft", "TEXT"),
                ("pending_customer_question", "TEXT"),
                ("pending_team_action", "TEXT"),
                ("last_interaction_date", "TEXT"),
                ("last_interaction_summary", "TEXT")
            ]
            
            for col_name, col_type in additional_cols:
                if col_name not in existing_cols:
                    cursor.execute(f"ALTER TABLE LEADS ADD COLUMN {col_name} {col_type};")
                    
            
            # Check for new columns in FOLLOW_UP_SCHEDULE
            cursor.execute("PRAGMA table_info(FOLLOW_UP_SCHEDULE);")
            existing_sched_cols = {row[1] for row in cursor.fetchall()}
            sched_additional_cols = [
                ("followup_reason", "TEXT"),
                ("next_action", "TEXT"),
                ("completion_notes", "TEXT"),
                ("priority", "TEXT"),
                ("rescheduled_from", "TEXT"),
                ("rescheduled_reason", "TEXT"),
                ("task_summary", "TEXT")
            ]
            for col_name, col_type in sched_additional_cols:
                if col_name not in existing_sched_cols:
                    cursor.execute(f"ALTER TABLE FOLLOW_UP_SCHEDULE ADD COLUMN {col_name} {col_type};")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_followup_prio ON FOLLOW_UP_SCHEDULE(priority);")

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_score ON LEADS(lead_score);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_priority ON LEADS(priority);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_optout ON LEADS(is_opted_out);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_locality ON LEADS(locality);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_region ON LEADS(region);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_service_area ON LEADS(is_service_area);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_ref ON LEADS(lead_reference);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_estimate_time ON LEADS(estimate_generated_at);")
            
            # Additional columns in CUSTOMER_CONVERSATIONS
            cursor.execute("PRAGMA table_info(CUSTOMER_CONVERSATIONS);")
            existing_conv_cols = {row[1] for row in cursor.fetchall()}
            conv_additional_cols = [
                ("original_language", "TEXT DEFAULT 'en'"),
                ("english_translation", "TEXT"),
                ("source_type", "TEXT DEFAULT 'Manual'"),
                ("ocr_confidence", "REAL"),
                ("is_flagged_for_review", "INTEGER DEFAULT 0"),
                ("import_batch_id", "TEXT"),
                ("audio_transcription", "TEXT")
            ]
            for col_name, col_type in conv_additional_cols:
                if col_name not in existing_conv_cols:
                    cursor.execute(f"ALTER TABLE CUSTOMER_CONVERSATIONS ADD COLUMN {col_name} {col_type};")

            # Create IMPORTED_CONVERSATION_FILES table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS IMPORTED_CONVERSATION_FILES (
                file_id TEXT PRIMARY KEY,
                lead_id TEXT,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_hash TEXT,
                raw_content TEXT,
                extracted_message_count INTEGER DEFAULT 0,
                imported_at TEXT NOT NULL,
                FOREIGN KEY (lead_id) REFERENCES LEADS(lead_id)
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_import_lead ON IMPORTED_CONVERSATION_FILES(lead_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_import_hash ON IMPORTED_CONVERSATION_FILES(file_hash);")

            # Create SHADOW_RECOMMENDATIONS table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS SHADOW_RECOMMENDATIONS (
                recommendation_id TEXT PRIMARY KEY,
                lead_id TEXT NOT NULL,
                scenario TEXT NOT NULL,
                reason TEXT NOT NULL,
                next_action TEXT NOT NULL,
                priority TEXT NOT NULL,
                recommended_date TEXT NOT NULL,
                english_whatsapp_draft TEXT NOT NULL,
                conversation_evidence TEXT,
                confidence_score REAL DEFAULT 1.0,
                status TEXT NOT NULL DEFAULT 'Pending Review',
                reviewer_notes TEXT,
                modified_draft TEXT,
                promoted_schedule_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (lead_id) REFERENCES LEADS(lead_id)
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_shadow_lead ON SHADOW_RECOMMENDATIONS(lead_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_shadow_status ON SHADOW_RECOMMENDATIONS(status);")

            # Create SHADOW_MODE_CONFIG table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS SHADOW_MODE_CONFIG (
                config_key TEXT PRIMARY KEY,
                config_value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)
            cursor.execute("""
            INSERT OR IGNORE INTO SHADOW_MODE_CONFIG (config_key, config_value, updated_at)
            VALUES ('shadow_mode_enabled', '1', datetime('now', 'localtime'));
            """)

            # Create KNOWLEDGE_VECTORS table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS KNOWLEDGE_VECTORS (
                chunk_id TEXT PRIMARY KEY,
                category_number INTEGER,
                category_name TEXT,
                topic TEXT,
                title TEXT,
                source_type TEXT,
                verified_source TEXT,
                region TEXT,
                content TEXT,
                embedding_json TEXT,
                created_at TEXT
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vec_cat ON KNOWLEDGE_VECTORS(category_number);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vec_topic ON KNOWLEDGE_VECTORS(topic);")
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
    ref = (lead_data.get("lead_reference") or "").strip() or None
    est_at = (lead_data.get("estimate_generated_at") or "").strip() or None
    if ref and not est_at:
        _, iso_decoded, _ = estimate_parser.parse_estimate_reference(ref)
        if iso_decoded:
            est_at = iso_decoded
    
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
        "last_response_at": lead_data.get("last_response_at"),
        "lead_reference": ref,
        "estimate_generated_at": est_at
    }
    
    sql = """
    INSERT INTO LEADS (
        lead_id, customer_name, phone, email, city, lead_source,
        budget_range, project_type, property_status, project_timeline,
        scope_of_work, customer_requirements, purchase_readiness,
        preferred_contact_method, lead_status, created_at, updated_at, data_origin,
        lead_score, priority, score_breakdown, scoring_reason, scored_at,
        is_opted_out, opt_out_reason, is_paused, last_customer_response, last_response_at,
        lead_reference, estimate_generated_at
    ) VALUES (
        :lead_id, :customer_name, :phone, :email, :city, :lead_source,
        :budget_range, :project_type, :property_status, :project_timeline,
        :scope_of_work, :customer_requirements, :purchase_readiness,
        :preferred_contact_method, :lead_status, :created_at, :updated_at, :data_origin,
        :lead_score, :priority, :score_breakdown, :scoring_reason, :scored_at,
        :is_opted_out, :opt_out_reason, :is_paused, :last_customer_response, :last_response_at,
        :lead_reference, :estimate_generated_at
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
        is_opted_out, opt_out_reason, is_paused, last_customer_response, last_response_at,
        lead_reference, estimate_generated_at
    ) VALUES (
        :lead_id, :customer_name, :phone, :email, :city, :lead_source,
        :budget_range, :project_type, :property_status, :project_timeline,
        :scope_of_work, :customer_requirements, :purchase_readiness,
        :preferred_contact_method, :lead_status, :created_at, :updated_at, :data_origin,
        :lead_score, :priority, :score_breakdown, :scoring_reason, :scored_at,
        :is_opted_out, :opt_out_reason, :is_paused, :last_customer_response, :last_response_at,
        :lead_reference, :estimate_generated_at
    );
    """
    
    formatted_leads = []
    for l in leads_list:
        ref = (l.get("lead_reference") or "").strip() or None
        est_at = (l.get("estimate_generated_at") or "").strip() or None
        if ref and not est_at:
            _, iso_decoded, _ = estimate_parser.parse_estimate_reference(ref)
            if iso_decoded:
                est_at = iso_decoded

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
            "last_response_at": l.get("last_response_at"),
            "lead_reference": ref,
            "estimate_generated_at": est_at
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
    sql = "UPDATE LEADS SET is_opted_out = ?, opt_out_reason = ?, opt_out_date = ?, updated_at = ? WHERE lead_id = ?;"
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql, (is_opted_out, reason, now if is_opted_out else None, now, lead_id))
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
    INSERT OR REPLACE INTO FOLLOW_UP_SCHEDULE (
        schedule_id, lead_id, scheduled_for, channel, message,
        status, attempt_number, created_at, completed_at, stop_reason,
        followup_reason, next_action, completion_notes, priority,
        rescheduled_from, rescheduled_reason, task_summary
    ) VALUES (
        :schedule_id, :lead_id, :scheduled_for, :channel, :message,
        :status, :attempt_number, :created_at, :completed_at, :stop_reason,
        :followup_reason, :next_action, :completion_notes, :priority,
        :rescheduled_from, :rescheduled_reason, :task_summary
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
        "stop_reason": record.get("stop_reason"),
        "followup_reason": record.get("followup_reason"),
        "next_action": record.get("next_action"),
        "completion_notes": record.get("completion_notes"),
        "priority": record.get("priority"),
        "rescheduled_from": record.get("rescheduled_from"),
        "rescheduled_reason": record.get("rescheduled_reason"),
        "task_summary": record.get("task_summary")
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
    INSERT OR REPLACE INTO FOLLOW_UP_SCHEDULE (
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
    limit: Optional[int] = None,
    active_only: bool = False,
    locality: Optional[str] = None,
    region: Optional[str] = None,
    priority: Optional[str] = None,
    channel: Optional[str] = None,
    due_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    due_filter: Optional[str] = None,
    order_by: str = "f.scheduled_for ASC"
) -> List[Dict[str, Any]]:
    """Retrieves follow-up tasks with optional filters (locality, region, priority, dates, channel)."""
    init_db(db_path)
    sql = """
    SELECT 
        f.schedule_id,
        f.lead_id,
        f.scheduled_for,
        f.channel,
        f.message,
        f.status,
        f.attempt_number,
        f.created_at,
        f.completed_at,
        f.stop_reason,
        f.followup_reason,
        f.next_action,
        f.completion_notes,
        f.rescheduled_from,
        f.rescheduled_reason,
        f.task_summary,
        COALESCE(f.priority, l.priority, 'Medium') as priority,
        f.priority as task_priority,
        l.customer_name,
        l.phone,
        l.email,
        l.city,
        COALESCE(l.locality, 'Unmapped') as locality,
        COALESCE(l.region, 'Hyderabad') as region,
        COALESCE(l.pincode, '') as pincode,
        l.priority as lead_priority,
        l.lead_status,
        l.budget_range,
        l.project_type,
        l.lead_score,
        l.lead_reference,
        l.estimate_generated_at,
        l.is_opted_out,
        l.opt_out_reason,
        l.is_paused,
        l.last_customer_response,
        l.last_response_at,
        l.expected_handover_date,
        l.current_project_stage,
        l.property_area_sqft,
        l.pending_customer_question,
        l.pending_team_action,
        l.last_interaction_date,
        l.last_interaction_summary,
        COALESCE(l.assigned_salesperson, 'Senior Interior Consultant') as assigned_salesperson
    FROM FOLLOW_UP_SCHEDULE f
    LEFT JOIN LEADS l ON f.lead_id = l.lead_id
    WHERE 1=1
    """
    params: List[Any] = []
    
    if active_only:
        sql += " AND (l.city = 'Hyderabad' OR l.is_service_area = 1)"
    if lead_id:
        sql += " AND f.lead_id = ?"
        params.append(lead_id)
    if status and status not in ("All", "All Statuses", "All Tasks"):
        sql += " AND f.status = ?"
        params.append(status)
    if locality and locality not in ("All", "All Localities"):
        sql += " AND l.locality = ?"
        params.append(locality)
    if region and region not in ("All", "All Regions"):
        if region in ("Secunderabad & Metropolitan Areas", "Secunderabad"):
            sql += " AND (l.region = 'Secunderabad' OR l.region = 'Secunderabad & Metropolitan Areas')"
        else:
            sql += " AND l.region = ?"
            params.append(region)
    if priority and priority not in ("All", "All Priorities"):
        sql += " AND (f.priority = ? OR (f.priority IS NULL AND l.priority = ?))"
        params.extend([priority, priority])
    if channel and channel not in ("All", "All Channels"):
        sql += " AND f.channel = ?"
        params.append(channel)
    if due_date:
        sql += " AND date(f.scheduled_for) = date(?)"
        params.append(due_date)
    if start_date:
        sql += " AND date(f.scheduled_for) >= date(?)"
        params.append(start_date)
    if end_date:
        sql += " AND date(f.scheduled_for) <= date(?)"
        params.append(end_date)
        
    if due_filter:
        df_lower = due_filter.strip().lower()
        today_date = datetime.date.today().isoformat()
        if df_lower == "today":
            sql += " AND date(f.scheduled_for) = ? AND f.status IN ('Scheduled', 'Due')"
            params.append(today_date)
        elif df_lower == "overdue":
            sql += " AND date(f.scheduled_for) < ? AND f.status IN ('Scheduled', 'Due')"
            params.append(today_date)
        elif df_lower == "upcoming":
            sql += " AND date(f.scheduled_for) > ? AND f.status IN ('Scheduled', 'Due')"
            params.append(today_date)
        elif df_lower == "completed":
            sql += " AND f.status IN ('Completed', 'Sent')"
        elif df_lower == "pending":
            sql += " AND f.status IN ('Scheduled', 'Due')"
            
    # Validate order_by to prevent SQL injection
    safe_orders = {
        "scheduled_for ASC": "f.scheduled_for ASC",
        "scheduled_for DESC": "f.scheduled_for DESC",
        "customer_name ASC": "l.customer_name ASC",
        "priority DESC": "l.lead_score DESC",
        "priority ASC": "l.lead_score ASC",
        "f.scheduled_for ASC": "f.scheduled_for ASC",
        "f.scheduled_for DESC": "f.scheduled_for DESC"
    }
    sql += f" ORDER BY {safe_orders.get(order_by.strip(), 'f.scheduled_for ASC')}"
    
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
    """Retrieves a single follow-up task by ID with full customer context."""
    init_db(db_path)
    sql = """
    SELECT 
        f.*,
        COALESCE(f.priority, l.priority, 'Medium') as priority,
        f.priority as task_priority,
        l.priority as lead_priority,
        l.customer_name,
        l.phone,
        l.email,
        l.city,
        COALESCE(l.locality, 'Unmapped') as locality,
        COALESCE(l.region, 'Hyderabad') as region,
        COALESCE(l.pincode, '') as pincode,
        l.lead_status,
        l.budget_range,
        l.project_type,
        l.lead_score,
        l.lead_reference,
        l.estimate_generated_at,
        l.is_opted_out,
        l.opt_out_reason,
        l.is_paused,
        l.last_customer_response,
        l.last_response_at,
        l.expected_handover_date,
        l.current_project_stage,
        l.property_area_sqft,
        l.pending_customer_question,
        l.pending_team_action,
        l.last_interaction_date,
        l.last_interaction_summary,
        COALESCE(l.assigned_salesperson, 'Senior Interior Consultant') as assigned_salesperson
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

def get_followup_stats(db_path: str = DEFAULT_DB_PATH, active_only: bool = False) -> Dict[str, Any]:
    """Returns aggregated summary metrics for follow-ups with Hyderabad and channel awareness."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today_date = datetime.date.today().isoformat()
        
        where_active = " WHERE (l.city = 'Hyderabad' OR l.is_service_area = 1)" if active_only else " WHERE 1=1"
        
        # 1. Total follow-ups
        cursor.execute(f"""
            SELECT COUNT(*) as total 
            FROM FOLLOW_UP_SCHEDULE f 
            LEFT JOIN LEADS l ON f.lead_id = l.lead_id 
            {where_active};
        """)
        total = cursor.fetchone()["total"]
        
        # 2. Status counts
        cursor.execute(f"""
            SELECT f.status, COUNT(*) as count 
            FROM FOLLOW_UP_SCHEDULE f 
            LEFT JOIN LEADS l ON f.lead_id = l.lead_id 
            {where_active}
            GROUP BY f.status;
        """)
        status_counts = {r["status"]: r["count"] for r in cursor.fetchall()}
        
        # 3. Due today (scheduled_for on today's date and status in Scheduled/Due)
        cursor.execute(f"""
            SELECT COUNT(*) as c 
            FROM FOLLOW_UP_SCHEDULE f 
            LEFT JOIN LEADS l ON f.lead_id = l.lead_id 
            {where_active}
              AND f.status IN ('Scheduled', 'Due')
              AND date(f.scheduled_for) = ?;
        """, (today_date,))
        due_today = cursor.fetchone()["c"]
        
        # 4. Overdue (scheduled_for before today and status in Scheduled/Due)
        cursor.execute(f"""
            SELECT COUNT(*) as c 
            FROM FOLLOW_UP_SCHEDULE f 
            LEFT JOIN LEADS l ON f.lead_id = l.lead_id 
            {where_active}
              AND f.status IN ('Scheduled', 'Due')
              AND date(f.scheduled_for) < ?;
        """, (today_date,))
        overdue = cursor.fetchone()["c"]
        
        # 5. Upcoming (scheduled_for after today and status in Scheduled/Due)
        cursor.execute(f"""
            SELECT COUNT(*) as c 
            FROM FOLLOW_UP_SCHEDULE f 
            LEFT JOIN LEADS l ON f.lead_id = l.lead_id 
            {where_active}
              AND f.status IN ('Scheduled', 'Due')
              AND date(f.scheduled_for) > ?;
        """, (today_date,))
        upcoming = cursor.fetchone()["c"]
        
        # 6. Due now (scheduled_for <= now and status in Scheduled/Due)
        cursor.execute(f"""
            SELECT COUNT(*) as c 
            FROM FOLLOW_UP_SCHEDULE f 
            LEFT JOIN LEADS l ON f.lead_id = l.lead_id 
            {where_active}
              AND f.status IN ('Scheduled', 'Due')
              AND f.scheduled_for <= ?;
        """, (now_str,))
        due_now = cursor.fetchone()["c"]
        
        # 7. Channel breakdowns for pending tasks
        cursor.execute(f"""
            SELECT COUNT(*) as c 
            FROM FOLLOW_UP_SCHEDULE f 
            LEFT JOIN LEADS l ON f.lead_id = l.lead_id 
            {where_active}
              AND f.status IN ('Scheduled', 'Due')
              AND f.channel = 'WhatsApp';
        """)
        pending_whatsapp = cursor.fetchone()["c"]
        
        cursor.execute(f"""
            SELECT COUNT(*) as c 
            FROM FOLLOW_UP_SCHEDULE f 
            LEFT JOIN LEADS l ON f.lead_id = l.lead_id 
            {where_active}
              AND f.status IN ('Scheduled', 'Due')
              AND f.channel IN ('Phone Call', 'Call', 'Phone');
        """)
        pending_calls = cursor.fetchone()["c"]
        
        cursor.execute(f"""
            SELECT COUNT(*) as c 
            FROM FOLLOW_UP_SCHEDULE f 
            LEFT JOIN LEADS l ON f.lead_id = l.lead_id 
            {where_active}
              AND f.status IN ('Scheduled', 'Due')
              AND f.channel = 'Email';
        """)
        pending_emails = cursor.fetchone()["c"]
        
        completed = status_counts.get("Completed", 0) + status_counts.get("Sent", 0)
        cancelled = status_counts.get("Cancelled", 0)
        scheduled = status_counts.get("Scheduled", 0)
        
        return {
            "total_followups": total,
            "status_counts": status_counts,
            "due_count": due_now,
            "due_today": due_today,
            "overdue": overdue,
            "upcoming": upcoming,
            "completed": completed,
            "completed_count": completed,
            "cancelled": cancelled,
            "cancelled_count": cancelled,
            "scheduled_count": scheduled,
            "pending_whatsapp": pending_whatsapp,
            "pending_calls": pending_calls,
            "pending_emails": pending_emails
        }
    finally:
        conn.close()

# -------------------------------------------------------------
# CONVERSATION MEMORY & MESSAGING DATABASE OPERATIONS
# -------------------------------------------------------------

def add_conversation_message(
    lead_id: str,
    direction: str,
    message_content: str,
    channel: str = "WhatsApp",
    ai_generated_response: Optional[str] = None,
    approval_status: str = "Draft",
    sending_status: str = "Draft",
    sent_at: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    db_path: str = DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """Adds a customer message or AI response draft to CUSTOMER_CONVERSATIONS."""
    init_db(db_path)
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conv_id = f"CONV-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(3).hex().upper()}"
    msg_id = f"MSG-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(2).hex().upper()}"
    meta_json = json.dumps(metadata) if metadata else None
    
    sql = """
    INSERT INTO CUSTOMER_CONVERSATIONS (
        conversation_id, lead_id, message_id, direction, channel,
        message_content, ai_generated_response, approval_status,
        sending_status, sent_at, created_at, metadata
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                conv_id, lead_id, msg_id, direction, channel,
                message_content.strip(),
                ai_generated_response.strip() if ai_generated_response else None,
                approval_status, sending_status, sent_at, now_iso, meta_json
            ))
            
            # If incoming message, update last_customer_response on lead
            if direction.lower() == "incoming":
                cursor.execute("""
                    UPDATE LEADS SET
                        last_customer_response = ?,
                        last_response_at = ?,
                        updated_at = ?
                    WHERE lead_id = ?;
                """, (message_content.strip()[:200], now_iso, now_iso, lead_id))
                
        return {
            "conversation_id": conv_id,
            "lead_id": lead_id,
            "message_id": msg_id,
            "direction": direction,
            "channel": channel,
            "message_content": message_content,
            "ai_generated_response": ai_generated_response,
            "approval_status": approval_status,
            "sending_status": sending_status,
            "sent_at": sent_at,
            "created_at": now_iso
        }
    finally:
        conn.close()

def get_conversation_history(
    lead_id: str,
    limit: int = 50,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Retrieves chronological conversation messages for a customer."""
    init_db(db_path)
    sql = """
    SELECT * FROM CUSTOMER_CONVERSATIONS
    WHERE lead_id = ?
    ORDER BY created_at ASC
    LIMIT ?;
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (lead_id, limit))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

def update_conversation_status(
    conversation_id: str,
    sending_status: str,
    sent_at: Optional[str] = None,
    approval_status: Optional[str] = None,
    edited_reply: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> bool:
    """Updates the status of a conversation message (e.g., 'User-Confirmed Sent')."""
    init_db(db_path)
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fields = ["sending_status = ?"]
    params: List[Any] = [sending_status]
    
    if sent_at or sending_status == "User-Confirmed Sent":
        fields.append("sent_at = ?")
        params.append(sent_at or now_iso)
    if approval_status:
        fields.append("approval_status = ?")
        params.append(approval_status)
    if edited_reply is not None:
        fields.append("ai_generated_response = ?")
        params.append(edited_reply)
        
    params.append(conversation_id)
    sql = f"UPDATE CUSTOMER_CONVERSATIONS SET {', '.join(fields)} WHERE conversation_id = ?;"
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
        return cursor.rowcount > 0
    finally:
        conn.close()

def schedule_single_followup(
    lead_id: str,
    scheduled_for: str,
    channel: str,
    message: str,
    followup_reason: Optional[str] = None,
    next_action: Optional[str] = None,
    priority: Optional[str] = None,
    task_summary: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """Creates a new scheduled follow-up task for a customer with intelligent task context."""
    init_db(db_path)
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sched_id = f"SCHED-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(2).hex().upper()}"
    
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            # Determine attempt number
            cursor.execute("SELECT COUNT(*) FROM FOLLOW_UP_SCHEDULE WHERE lead_id = ?;", (lead_id,))
            attempt_count = cursor.fetchone()[0] + 1
            
            cursor.execute("""
                INSERT INTO FOLLOW_UP_SCHEDULE (
                    schedule_id, lead_id, scheduled_for, channel, message,
                    status, attempt_number, created_at,
                    followup_reason, next_action, priority, task_summary
                ) VALUES (?, ?, ?, ?, ?, 'Scheduled', ?, ?, ?, ?, ?, ?);
            """, (
                sched_id, lead_id, scheduled_for, channel, message.strip(), attempt_count, now_iso,
                followup_reason.strip() if followup_reason else None,
                next_action.strip() if next_action else None,
                priority.strip() if priority else None,
                task_summary.strip() if task_summary else None
            ))
            
            # Log activity
            act_id = f"ACT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(2).hex()}"
            reason_clause = f" | Reason: {followup_reason.strip()}" if followup_reason else ""
            cursor.execute("""
                INSERT INTO LEAD_ACTIVITY_LOG (activity_id, lead_id, activity_type, activity_description, timestamp)
                VALUES (?, ?, 'SCHEDULE_FOLLOWUP', ?, ?);
            """, (act_id, lead_id, f"Follow-up scheduled for {scheduled_for} via {channel}{reason_clause}", now_iso))
            
        return {
            "success": True,
            "schedule_id": sched_id,
            "scheduled_for": scheduled_for,
            "channel": channel,
            "attempt_number": attempt_count,
            "followup_reason": followup_reason,
            "next_action": next_action,
            "priority": priority,
            "task_summary": task_summary
        }
    finally:
        conn.close()

# -------------------------------------------------------------
# QUERY LEADS WITH ENHANCED FILTERING
# -------------------------------------------------------------

def get_all_leads(
    db_path: str = DEFAULT_DB_PATH,
    city: Optional[str] = None,
    locality: Optional[str] = None,
    region: Optional[str] = None,
    project_type: Optional[str] = None,
    budget_range: Optional[str] = None,
    lead_status: Optional[str] = None,
    priority: Optional[str] = None,
    data_origin: Optional[str] = None,
    search_query: Optional[str] = None,
    order_by: str = "created_at DESC",
    active_only: bool = False,
    estimate_date_from: Optional[str] = None,
    estimate_date_to: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves leads with optional filtering and search. Supports locality, region, and estimate dates."""
    init_db(db_path)
    sql = "SELECT * FROM LEADS WHERE 1=1"
    params: List[Any] = []
    
    if active_only:
        sql += " AND (city = 'Hyderabad' OR is_service_area = 1)"
    if city and city != "All":
        sql += " AND city = ?"
        params.append(city)
    if locality and locality not in ("All", "All Localities"):
        sql += " AND locality = ?"
        params.append(locality)
    if region and region not in ("All", "All Regions"):
        if region in ("Secunderabad & Metropolitan Areas", "Secunderabad"):
            sql += " AND (region = 'Secunderabad' OR region = 'Secunderabad & Metropolitan Areas')"
        else:
            sql += " AND region = ?"
            params.append(region)
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
        if data_origin in ("Exclude Test Data", "genuine_only"):
            sql += " AND data_origin != 'test_data'"
        elif data_origin in ("Test Data Only", "test_only", "test_data"):
            sql += " AND data_origin = 'test_data'"
        else:
            sql += " AND data_origin = ?"
            params.append(data_origin)
    if search_query:
        query_pattern = f"%{search_query.strip()}%"
        sql += " AND (customer_name LIKE ? OR lead_id LIKE ? OR phone LIKE ? OR email LIKE ? OR locality LIKE ? OR region LIKE ? OR pincode LIKE ? OR lead_reference LIKE ?)"
        params.extend([query_pattern] * 8)
        
    if estimate_date_from:
        sql += " AND substr(estimate_generated_at, 1, 10) >= ?"
        params.append(str(estimate_date_from))
    if estimate_date_to:
        sql += " AND substr(estimate_generated_at, 1, 10) <= ?"
        params.append(str(estimate_date_to))

    valid_orders = {
        "created_at DESC": "created_at DESC",
        "lead_score DESC": "lead_score DESC NULLS LAST",
        "lead_score ASC": "lead_score ASC NULLS LAST",
        "customer_name ASC": "customer_name ASC",
        "estimate_generated_at DESC": "estimate_generated_at DESC NULLS LAST",
        "estimate_generated_at ASC": "estimate_generated_at ASC NULLS LAST",
        "estimate_date DESC": "estimate_generated_at DESC NULLS LAST",
        "estimate_date ASC": "estimate_generated_at ASC NULLS LAST"
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

def search_leads(query: str, db_path: str = DEFAULT_DB_PATH):
    """Searches leads by query across customer_name, phone, locality, city, notes, requirements."""
    return get_all_leads(db_path=db_path, search_query=query)

def get_hyderabad_leads(db_path: str = DEFAULT_DB_PATH, **kwargs) -> List[Dict[str, Any]]:
    """Convenience accessor strictly returning active Hyderabad service-area leads."""
    return get_all_leads(db_path=db_path, active_only=True, **kwargs)

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

def get_lead_stats(
    db_path: str = DEFAULT_DB_PATH,
    active_only: bool = False,
    data_origin: Optional[str] = None,
    dataset_scope: str = "all"
) -> Dict[str, Any]:
    """Returns aggregated summary metrics for the CRM dashboard, including AI scoring metrics."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        
        where = []
        params = []
        if active_only:
            where.append("(city = 'Hyderabad' OR is_service_area = 1)")
        if data_origin in ("Exclude Test Data", "genuine_only") or dataset_scope == "genuine_only":
            where.append("data_origin != 'test_data'")
        elif data_origin in ("Test Data Only", "test_only", "test_data") or dataset_scope == "test_only":
            where.append("data_origin = 'test_data'")
        elif data_origin and data_origin != "All":
            where.append("data_origin = ?")
            params.append(data_origin)
            
        where_sql = f" WHERE {' AND '.join(where)}" if where else ""
        
        cursor.execute(f"SELECT COUNT(*) as total FROM LEADS{where_sql};", params)
        total = cursor.fetchone()["total"]
        
        cursor.execute(f"SELECT lead_status, COUNT(*) as count FROM LEADS{where_sql} GROUP BY lead_status;", params)
        status_counts = {r["lead_status"]: r["count"] for r in cursor.fetchall()}
        
        cursor.execute(f"SELECT data_origin, COUNT(*) as count FROM LEADS{where_sql} GROUP BY data_origin;", params)
        origin_counts = {r["data_origin"]: r["count"] for r in cursor.fetchall()}
        
        cursor.execute(f"SELECT city, COUNT(*) as count FROM LEADS{where_sql} GROUP BY city ORDER BY count DESC LIMIT 5;", params)
        top_cities = {r["city"]: r["count"] for r in cursor.fetchall()}
        
        cursor.execute(f"SELECT project_type, COUNT(*) as count FROM LEADS{where_sql} GROUP BY project_type;", params)
        project_types = {r["project_type"]: r["count"] for r in cursor.fetchall()}
        
        scored_where = list(where)
        scored_where.append("lead_score IS NOT NULL")
        scored_sql = f" WHERE {' AND '.join(scored_where)}"
        
        cursor.execute(f"SELECT COUNT(*) as scored_count FROM LEADS{scored_sql};", params)
        scored_count = cursor.fetchone()["scored_count"]
        
        cursor.execute(f"SELECT AVG(lead_score) as avg_score FROM LEADS{scored_sql};", params)
        avg_score_row = cursor.fetchone()["avg_score"]
        avg_score = round(avg_score_row, 1) if avg_score_row is not None else 0.0
        
        prio_where = list(where)
        prio_where.append("priority IS NOT NULL")
        prio_sql = f" WHERE {' AND '.join(prio_where)}"
        cursor.execute(f"SELECT priority, COUNT(*) as count FROM LEADS{prio_sql} GROUP BY priority;", params)
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


def update_lead_estimate_info(
    lead_id: str,
    lead_reference: Optional[str],
    estimate_generated_at: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> bool:
    """Updates the lead reference and decoded estimate datetime."""
    init_db(db_path)
    now = datetime.datetime.now().isoformat()
    if lead_reference and not estimate_generated_at:
        _, iso_decoded, _ = estimate_parser.parse_estimate_reference(lead_reference)
        if iso_decoded:
            estimate_generated_at = iso_decoded

    sql = "UPDATE LEADS SET lead_reference = ?, estimate_generated_at = ?, updated_at = ? WHERE lead_id = ?;"
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql, (lead_reference, estimate_generated_at, now, lead_id))
        return cursor.rowcount > 0
    finally:
        conn.close()


def backfill_estimate_datetimes_from_reference(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """
    Backfills lead_reference and estimate_generated_at for existing database leads.
    Safely joins with genuine CSV reference records if available.
    """
    import re
    init_db(db_path)
    conn = get_connection(db_path)
    decoded_count = 0
    missing_count = 0
    processed_count = 0
    
    # Load reference mappings from genuine CSV
    ref_map = {}
    csv_file = "SHA_Real_Customer_Leads.csv"
    if os.path.exists(csv_file):
        try:
            import pandas as pd
            df = pd.read_csv(csv_file)
            for _, r in df.iterrows():
                phone_raw = str(r.get("Phone", "")).strip()
                ref_val = str(r.get("Lead_Reference", "")).strip()
                if ref_val and ref_val.lower() not in ("nan", "none", ""):
                    digits_phone = re.sub(r"\D", "", phone_raw)
                    if len(digits_phone) >= 10:
                        ref_map[digits_phone[-10:]] = ref_val
                    name = str(r.get("Customer_Name", "")).strip().lower()
                    if name:
                        ref_map[name] = ref_val
        except Exception:
            pass

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT lead_id, customer_name, phone, lead_reference, estimate_generated_at FROM LEADS;")
        leads = cursor.fetchall()
        for l in leads:
            processed_count += 1
            l_id = l["lead_id"]
            ref = l["lead_reference"]
            est_at = l["estimate_generated_at"]
            
            # If reference missing in DB, check if matched in CSV
            if not ref:
                phone_digits = re.sub(r"\D", "", l["phone"] or "")
                last10 = phone_digits[-10:] if len(phone_digits) >= 10 else None
                name_clean = (l["customer_name"] or "").strip().lower()
                matched_ref = ref_map.get(last10) or ref_map.get(name_clean)
                if matched_ref:
                    ref = matched_ref
            
            if ref:
                _, iso_decoded, warning = estimate_parser.parse_estimate_reference(ref)
                if iso_decoded:
                    with conn:
                        conn.cursor().execute(
                            "UPDATE LEADS SET lead_reference = ?, estimate_generated_at = ? WHERE lead_id = ?;",
                            (ref, iso_decoded, l_id)
                        )
                    decoded_count += 1
                else:
                    with conn:
                        conn.cursor().execute(
                            "UPDATE LEADS SET lead_reference = ? WHERE lead_id = ?;",
                            (ref, l_id)
                        )
                    missing_count += 1
            else:
                missing_count += 1

        return {
            "processed": processed_count,
            "decoded": decoded_count,
            "missing_or_invalid": missing_count
        }
    finally:
        conn.close()


def edit_followup_task(
    schedule_id: str,
    scheduled_for: Optional[str] = None,
    channel: Optional[str] = None,
    message: Optional[str] = None,
    followup_reason: Optional[str] = None,
    next_action: Optional[str] = None,
    priority: Optional[str] = None,
    task_summary: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> bool:
    """Edits an existing scheduled follow-up task and logs the update."""
    init_db(db_path)
    updates = []
    params = []
    if scheduled_for is not None:
        updates.append("scheduled_for = ?")
        params.append(scheduled_for)
    if channel is not None:
        updates.append("channel = ?")
        params.append(channel)
    if message is not None:
        updates.append("message = ?")
        params.append(message.strip())
    if followup_reason is not None:
        updates.append("followup_reason = ?")
        params.append(followup_reason.strip())
    if next_action is not None:
        updates.append("next_action = ?")
        params.append(next_action.strip())
    if priority is not None:
        updates.append("priority = ?")
        params.append(priority.strip())
    if task_summary is not None:
        updates.append("task_summary = ?")
        params.append(task_summary.strip())
        
    if not updates:
        return True
        
    sql = f"UPDATE FOLLOW_UP_SCHEDULE SET {', '.join(updates)} WHERE schedule_id = ?;"
    params.append(schedule_id)
    
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT lead_id FROM FOLLOW_UP_SCHEDULE WHERE schedule_id = ?;", (schedule_id,))
            row = cursor.fetchone()
            lead_id = row["lead_id"] if row else None
            
            cursor.execute(sql, params)
            
            if lead_id:
                now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                act_id = f"ACT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(2).hex()}"
                cursor.execute("""
                    INSERT INTO LEAD_ACTIVITY_LOG (activity_id, lead_id, activity_type, activity_description, timestamp)
                    VALUES (?, ?, 'TASK_EDITED', ?, ?);
                """, (act_id, lead_id, f"Follow-up task {schedule_id} was updated by salesperson.", now_iso))
        return True
    finally:
        conn.close()


def reschedule_followup_task(
    schedule_id: str,
    new_scheduled_for: str,
    reschedule_reason: str,
    new_channel: Optional[str] = None,
    new_message: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """Reschedules an existing task with a recorded reason, preserving the prior schedule time."""
    init_db(db_path)
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT lead_id, scheduled_for, channel, message FROM FOLLOW_UP_SCHEDULE WHERE schedule_id = ?;", (schedule_id,))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": f"Task {schedule_id} not found"}
                
            lead_id = row["lead_id"]
            old_scheduled_for = row["scheduled_for"]
            final_channel = new_channel or row["channel"]
            final_message = new_message if new_message is not None else row["message"]
            
            cursor.execute("""
                UPDATE FOLLOW_UP_SCHEDULE SET
                    scheduled_for = ?,
                    channel = ?,
                    message = ?,
                    status = 'Scheduled',
                    rescheduled_from = ?,
                    rescheduled_reason = ?
                WHERE schedule_id = ?;
            """, (new_scheduled_for, final_channel, final_message, old_scheduled_for, reschedule_reason.strip(), schedule_id))
            
            act_id = f"ACT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(2).hex()}"
            cursor.execute("""
                INSERT INTO LEAD_ACTIVITY_LOG (activity_id, lead_id, activity_type, activity_description, timestamp)
                VALUES (?, ?, 'TASK_RESCHEDULED', ?, ?);
            """, (act_id, lead_id, f"Task {schedule_id} rescheduled from {old_scheduled_for} to {new_scheduled_for}. Reason: {reschedule_reason.strip()}", now_iso))
            
        return {
            "success": True,
            "schedule_id": schedule_id,
            "old_scheduled_for": old_scheduled_for,
            "new_scheduled_for": new_scheduled_for,
            "rescheduled_reason": reschedule_reason.strip()
        }
    finally:
        conn.close()


def complete_followup_task(
    schedule_id: str,
    completion_notes: str,
    db_path: str = DEFAULT_DB_PATH
) -> bool:
    """Marks a follow-up task as Completed with required completion notes."""
    init_db(db_path)
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT lead_id, channel FROM FOLLOW_UP_SCHEDULE WHERE schedule_id = ?;", (schedule_id,))
            row = cursor.fetchone()
            if not row:
                return False
            lead_id = row["lead_id"]
            channel = row["channel"]
            
            cursor.execute("""
                UPDATE FOLLOW_UP_SCHEDULE SET
                    status = 'Completed',
                    completed_at = ?,
                    completion_notes = ?
                WHERE schedule_id = ?;
            """, (now_iso, completion_notes.strip(), schedule_id))
            
            act_id = f"ACT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(2).hex()}"
            cursor.execute("""
                INSERT INTO LEAD_ACTIVITY_LOG (activity_id, lead_id, activity_type, activity_description, timestamp)
                VALUES (?, ?, 'TASK_COMPLETED', ?, ?);
            """, (act_id, lead_id, f"Follow-up task {schedule_id} completed via {channel}. Notes: {completion_notes.strip()}", now_iso))
        return True
    finally:
        conn.close()


def update_lead_project_context(
    lead_id: str,
    expected_handover_date: Optional[str] = None,
    current_project_stage: Optional[str] = None,
    property_area_sqft: Optional[str] = None,
    pending_customer_question: Optional[str] = None,
    pending_team_action: Optional[str] = None,
    last_interaction_summary: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> bool:
    """Updates customer project tracking context (handover date, project stage, area, pending questions)."""
    init_db(db_path)
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updates = ["updated_at = ?"]
    params = [now_iso]
    if expected_handover_date is not None:
        updates.append("expected_handover_date = ?")
        params.append(expected_handover_date)
    if current_project_stage is not None:
        updates.append("current_project_stage = ?")
        params.append(current_project_stage)
    if property_area_sqft is not None:
        updates.append("property_area_sqft = ?")
        params.append(property_area_sqft)
    if pending_customer_question is not None:
        updates.append("pending_customer_question = ?")
        params.append(pending_customer_question)
    if pending_team_action is not None:
        updates.append("pending_team_action = ?")
        params.append(pending_team_action)
    if last_interaction_summary is not None:
        updates.append("last_interaction_summary = ?")
        params.append(last_interaction_summary)
        
    sql = f"UPDATE LEADS SET {', '.join(updates)} WHERE lead_id = ?;"
    params.append(lead_id)
    
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
        return True
    finally:
        conn.close()


# -------------------------------------------------------------
# IMPORTED CONVERSATIONS & SHADOW MODE DATABASE METHODS
# -------------------------------------------------------------

def add_imported_conversation_message(
    lead_id: str,
    message_content: str,
    direction: str = "incoming",
    channel: str = "WhatsApp",
    original_language: str = "en",
    english_translation: Optional[str] = None,
    source_type: str = "Manual",
    ocr_confidence: Optional[float] = None,
    is_flagged_for_review: int = 0,
    import_batch_id: Optional[str] = None,
    timestamp: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """Saves an imported conversation message with language, translation, and source provenance."""
    init_db(db_path)
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    created_val = timestamp or now_iso
    conv_id = f"CONV-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(3).hex().upper()}"
    msg_id = f"MSG-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(2).hex().upper()}"

    sql = """
    INSERT INTO CUSTOMER_CONVERSATIONS (
        conversation_id, lead_id, message_id, direction, channel,
        message_content, original_language, english_translation,
        source_type, ocr_confidence, is_flagged_for_review,
        import_batch_id, approval_status, sending_status, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Draft', 'Imported', ?);
    """
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                conv_id, lead_id, msg_id, direction, channel,
                message_content.strip(), original_language,
                english_translation.strip() if english_translation else None,
                source_type, ocr_confidence, is_flagged_for_review,
                import_batch_id, created_val
            ))

            # If incoming message, update last_customer_response on lead
            if direction.lower() == "incoming":
                cursor.execute("""
                    UPDATE LEADS SET
                        last_customer_response = ?,
                        last_response_at = ?,
                        updated_at = ?
                    WHERE lead_id = ?;
                """, (message_content.strip()[:200], created_val, now_iso, lead_id))

        return {
            "success": True,
            "conversation_id": conv_id,
            "message_id": msg_id,
            "lead_id": lead_id,
            "message_content": message_content,
            "created_at": created_val
        }
    finally:
        conn.close()


def check_duplicate_conversation_message(
    lead_id: str,
    message_content: str,
    created_at: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> bool:
    """Checks whether an identical message already exists for this lead to prevent duplicate import."""
    init_db(db_path)
    conn = get_connection(db_path)
    clean_msg = message_content.strip()
    try:
        cursor = conn.cursor()
        if created_at:
            cursor.execute("""
                SELECT COUNT(*) FROM CUSTOMER_CONVERSATIONS
                WHERE lead_id = ? AND TRIM(message_content) = ? AND created_at = ?;
            """, (lead_id, clean_msg, created_at))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM CUSTOMER_CONVERSATIONS
                WHERE lead_id = ? AND TRIM(message_content) = ?;
            """, (lead_id, clean_msg))
        count = cursor.fetchone()[0]
        return count > 0
    finally:
        conn.close()


def record_imported_file(
    file_name: str,
    file_type: str,
    file_hash: Optional[str] = None,
    lead_id: Optional[str] = None,
    raw_content: Optional[str] = None,
    extracted_count: int = 0,
    db_path: str = DEFAULT_DB_PATH
) -> str:
    """Logs an imported file record for audit and duplicate prevention."""
    init_db(db_path)
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_id = f"FILE-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(2).hex().upper()}"
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO IMPORTED_CONVERSATION_FILES (
                    file_id, lead_id, file_name, file_type, file_hash,
                    raw_content, extracted_message_count, imported_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (file_id, lead_id, file_name, file_type, file_hash, raw_content, extracted_count, now_iso))
        return file_id
    finally:
        conn.close()


def get_shadow_mode_status(db_path: str = DEFAULT_DB_PATH) -> bool:
    """Returns True if Shadow Mode is enabled in configuration."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT config_value FROM SHADOW_MODE_CONFIG WHERE config_key = 'shadow_mode_enabled';")
        row = cursor.fetchone()
        if row and row["config_value"] in ("1", "true", "True", "ON", "on"):
            return True
        return False
    finally:
        conn.close()


def set_shadow_mode_status(enabled: bool, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Enables or disables Shadow Mode in configuration."""
    init_db(db_path)
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    val_str = "1" if enabled else "0"
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO SHADOW_MODE_CONFIG (config_key, config_value, updated_at)
                VALUES ('shadow_mode_enabled', ?, ?)
                ON CONFLICT(config_key) DO UPDATE SET config_value = ?, updated_at = ?;
            """, (val_str, now_iso, val_str, now_iso))
        return True
    finally:
        conn.close()


def insert_shadow_recommendation(rec: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> str:
    """Stores an AI Shadow Mode recommendation separately from real follow-up tasks."""
    init_db(db_path)
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rec_id = f"SHAD-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(2).hex().upper()}"
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO SHADOW_RECOMMENDATIONS (
                    recommendation_id, lead_id, scenario, reason, next_action,
                    priority, recommended_date, english_whatsapp_draft,
                    conversation_evidence, confidence_score, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending Review', ?, ?);
            """, (
                rec_id, rec["lead_id"], rec.get("scenario", "General"),
                rec["reason"], rec["next_action"], rec.get("priority", "Medium"),
                rec["recommended_date"], rec["english_whatsapp_draft"],
                rec.get("conversation_evidence"), rec.get("confidence_score", 1.0),
                now_iso, now_iso
            ))
        return rec_id
    finally:
        conn.close()


def get_shadow_recommendations(
    lead_id: Optional[str] = None,
    status: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Retrieves shadow recommendations with joined customer lead context."""
    init_db(db_path)
    sql = """
    SELECT sr.*, l.customer_name, l.phone, l.locality, l.project_type, l.budget_range, l.priority as lead_priority
    FROM SHADOW_RECOMMENDATIONS sr
    JOIN LEADS l ON sr.lead_id = l.lead_id
    WHERE 1=1
    """
    params = []
    if lead_id:
        sql += " AND sr.lead_id = ?"
        params.append(lead_id)
    if status and status != "All":
        sql += " AND sr.status = ?"
        params.append(status)
    sql += " ORDER BY sr.created_at DESC;"

    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def update_shadow_recommendation_status(
    recommendation_id: str,
    status: str,
    reviewer_notes: Optional[str] = None,
    modified_draft: Optional[str] = None,
    promoted_schedule_id: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> bool:
    """Updates recommendation status (Approved, Modified, Rejected) and links promoted tasks."""
    init_db(db_path)
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE SHADOW_RECOMMENDATIONS SET
                    status = ?,
                    reviewer_notes = COALESCE(?, reviewer_notes),
                    modified_draft = COALESCE(?, modified_draft),
                    promoted_schedule_id = COALESCE(?, promoted_schedule_id),
                    updated_at = ?
                WHERE recommendation_id = ?;
            """, (status, reviewer_notes, modified_draft, promoted_schedule_id, now_iso, recommendation_id))
        return True
    finally:
        conn.close()
