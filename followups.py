import datetime
import zoneinfo
from typing import Dict, List, Optional, Tuple, Any
import database
import followup_templates

# Target timezone
KOLKATA_TZ = zoneinfo.ZoneInfo("Asia/Kolkata")

# Configurable scheduling intervals (in days from reference/qualification time)
DEFAULT_FOLLOWUP_SCHEDULE_RULES = {
    "High": [
        {"attempt": 1, "days_offset": 1, "channel": "WhatsApp", "template": "acknowledgement"},
        {"attempt": 2, "days_offset": 3, "channel": "Phone Call", "template": "site_visit_invitation"},
        {"attempt": 3, "days_offset": 7, "channel": "Email", "template": "portfolio_sharing"}
    ],
    "Medium": [
        {"attempt": 1, "days_offset": 2, "channel": "WhatsApp", "template": "acknowledgement"},
        {"attempt": 2, "days_offset": 5, "channel": "Email", "template": "requirements_clarification"},
        {"attempt": 3, "days_offset": 10, "channel": "WhatsApp", "template": "portfolio_sharing"}
    ],
    "Low": [
        {"attempt": 1, "days_offset": 7, "channel": "Email", "template": "portfolio_sharing"},
        {"attempt": 2, "days_offset": 14, "channel": "WhatsApp", "template": "no_response"}
    ]
}

def get_current_time_kolkata() -> datetime.datetime:
    """Returns the current wall-clock datetime in Asia/Kolkata timezone."""
    return datetime.datetime.now(KOLKATA_TZ)

def check_stop_conditions(lead_id: str, db_path: str = database.DEFAULT_DB_PATH) -> Tuple[bool, Optional[str]]:
    """
    Evaluates whether follow-ups must be stopped or prevented for a lead.
    Returns (should_stop, stop_reason).
    """
    lead = database.get_lead_by_id(lead_id, db_path=db_path)
    if not lead:
        return True, "Lead record not found in CRM"
        
    # 1. Terminal CRM Status check
    status = lead.get("lead_status", "").strip().lower()
    if status == "converted":
        return True, "Lead is Converted: Customer finalized; automated follow-ups ceased"
    if status == "lost":
        return True, "Lead is Lost: Customer deal closed/lost; follow-ups cancelled"
        
    # 2. Opt-out check
    if lead.get("is_opted_out") == 1:
        reason = lead.get("opt_out_reason") or "Customer requested communication opt-out"
        return True, f"Customer Opted Out: {reason}"
        
    # 3. Manual Pause check
    if lead.get("is_paused") == 1:
        return True, "Follow-ups Manually Paused by Sales Representative"
        
    # 4. Active Customer Response check
    if lead.get("last_customer_response"):
        resp_time = lead.get("last_response_at", "recently")
        return True, f"Customer Responded: Awaiting manual representative action (Last response: '{lead['last_customer_response']}' at {resp_time})"
        
    # 5. Invalid Contact check
    phone = lead.get("phone", "").strip()
    if not phone or len(phone) < 10:
        return True, "Invalid Contact: Missing or unserviceable phone number"
        
    return False, None

def schedule_followups_for_lead(
    lead_id: str,
    base_time: Optional[datetime.datetime] = None,
    db_path: str = database.DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """
    Generates and persists the scheduled follow-up sequence for a lead according to priority.
    Checks stop conditions before scheduling.
    """
    lead = database.get_lead_by_id(lead_id, db_path=db_path)
    if not lead:
        return {"success": False, "error": f"Lead {lead_id} not found", "scheduled_count": 0}
        
    # Check stop conditions
    should_stop, stop_reason = check_stop_conditions(lead_id, db_path=db_path)
    if should_stop:
        return {
            "success": False,
            "error": f"Cannot schedule follow-ups: {stop_reason}",
            "scheduled_count": 0
        }
        
    # Priority determination
    priority = lead.get("priority") or "Medium"
    rules = DEFAULT_FOLLOWUP_SCHEDULE_RULES.get(priority, DEFAULT_FOLLOWUP_SCHEDULE_RULES["Medium"])
    
    start_time = base_time or get_current_time_kolkata()
    now_iso = get_current_time_kolkata().isoformat()
    
    new_schedules = []
    for rule in rules:
        attempt = rule["attempt"]
        days = rule["days_offset"]
        channel = rule["channel"]
        tmpl = rule["template"]
        
        scheduled_dt = start_time + datetime.timedelta(days=days)
        scheduled_for_str = scheduled_dt.strftime("%Y-%m-%d %H:%M:%S")
        schedule_id = f"SCH-{lead_id}-{attempt}"
        
        # Generate personalized message draft
        msg_draft = followup_templates.generate_personalized_message(tmpl, lead)
        
        new_schedules.append({
            "schedule_id": schedule_id,
            "lead_id": lead_id,
            "scheduled_for": scheduled_for_str,
            "channel": channel,
            "message": msg_draft,
            "status": "Scheduled",
            "attempt_number": attempt,
            "created_at": now_iso
        })
        
    # First cancel any stale scheduled tasks to avoid duplicate attempts
    database.cancel_scheduled_followups_for_lead(lead_id, "Rescheduled new follow-up cadence", db_path=db_path)
    
    # Batch insert
    inserted = database.batch_insert_followup_schedules(new_schedules, db_path=db_path)
    
    # Log activity
    database.insert_activity_log(
        lead_id=lead_id,
        activity_type="Follow-up Sequence Scheduled",
        activity_description=f"Automated {priority} Priority cadence ({inserted} tasks) scheduled starting {start_time.strftime('%Y-%m-%d')}.",
        db_path=db_path
    )
    
    return {
        "success": True,
        "lead_id": lead_id,
        "priority": priority,
        "scheduled_count": inserted,
        "tasks": new_schedules
    }

def schedule_followups_for_all_eligible_leads(db_path: str = database.DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Schedules follow-ups for all eligible non-converted, non-lost, non-opted-out leads."""
    database.init_db(db_path)
    leads = database.get_all_leads(db_path=db_path)
    
    total_eligible = 0
    total_scheduled = 0
    skipped_count = 0
    
    for l in leads:
        lead_id = l["lead_id"]
        should_stop, _ = check_stop_conditions(lead_id, db_path=db_path)
        if should_stop:
            skipped_count += 1
            continue
            
        # Check if already has active scheduled tasks
        existing = database.get_followups(db_path=db_path, lead_id=lead_id, status="Scheduled")
        if existing:
            continue
            
        res = schedule_followups_for_lead(lead_id, db_path=db_path)
        if res["success"]:
            total_eligible += 1
            total_scheduled += res["scheduled_count"]
            
    return {
        "eligible_leads": total_eligible,
        "total_tasks_scheduled": total_scheduled,
        "skipped_leads": skipped_count
    }

def simulate_send_followup(schedule_id: str, db_path: str = database.DEFAULT_DB_PATH) -> Dict[str, Any]:
    """
    Simulates sending a scheduled follow-up.
    Enforces IDEMPOTENCY: if task is already Sent, Completed, or Cancelled, it rejects duplicate execution.
    Evaluates real-time STOP CONDITIONS before execution.
    """
    task = database.get_followup_by_id(schedule_id, db_path=db_path)
    if not task:
        return {"success": False, "error": f"Schedule task {schedule_id} not found"}
        
    lead_id = task["lead_id"]
    current_status = task["status"]
    
    # 1. Idempotency Check
    if current_status in ["Sent", "Completed"]:
        return {
            "success": False,
            "error": f"Idempotency Guard: Task {schedule_id} has already been executed (status: '{current_status}'). Duplicate dispatch prevented.",
            "status": current_status
        }
    if current_status == "Cancelled":
        return {
            "success": False,
            "error": f"Task {schedule_id} is Cancelled (Stop reason: {task.get('stop_reason')}). Cannot send.",
            "status": "Cancelled"
        }

    # 2. Check Stop Conditions against live lead state
    should_stop, stop_reason = check_stop_conditions(lead_id, db_path=db_path)
    if should_stop:
        now_iso = get_current_time_kolkata().isoformat()
        database.update_followup_status(schedule_id, status="Cancelled", completed_at=now_iso, stop_reason=stop_reason, db_path=db_path)
        database.insert_activity_log(
            lead_id=lead_id,
            activity_type="Follow-up Blocked by Stop Condition",
            activity_description=f"Task {schedule_id} halted: {stop_reason}",
            db_path=db_path
        )
        return {
            "success": False,
            "error": f"Execution halted due to active stop condition: {stop_reason}",
            "status": "Cancelled"
        }

    # 3. Simulate Successful Dispatch
    now_iso = get_current_time_kolkata().isoformat()
    database.update_followup_status(schedule_id, status="Sent", completed_at=now_iso, db_path=db_path)
    
    # Record in Activity Log
    channel = task["channel"]
    attempt = task["attempt_number"]
    database.insert_activity_log(
        lead_id=lead_id,
        activity_type=f"Follow-up Sent ({channel})",
        activity_description=f"Attempt #{attempt} simulated via {channel} to {task['phone']}. Message: \"{task['message'][:80]}...\"",
        db_path=db_path
    )
    
    return {
        "success": True,
        "schedule_id": schedule_id,
        "lead_id": lead_id,
        "status": "Sent",
        "channel": channel,
        "message": f"Follow-up #{attempt} via {channel} simulated successfully.",
        "completed_at": now_iso
    }

def simulate_customer_response(
    lead_id: str,
    response_text: str,
    db_path: str = database.DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """
    Simulates a customer inbound response (e.g. client replies on WhatsApp).
    CRITICAL BEHAVIOR:
    - Records response in CRM lead record and activity log.
    - CANCELS all pending/future automated follow-ups immediately until sales rep responds.
    """
    lead = database.get_lead_by_id(lead_id, db_path=db_path)
    if not lead:
        return {"success": False, "error": f"Lead {lead_id} not found"}
        
    clean_resp = response_text.strip()
    database.record_customer_response(lead_id, clean_resp, db_path=db_path)
    
    # Cancel future follow-ups
    stop_reason = f"Customer Responded: \"{clean_resp[:60]}\" - Automated cadence paused for designer takeover."
    cancelled_count = database.cancel_scheduled_followups_for_lead(lead_id, stop_reason, db_path=db_path)
    
    # Log activity
    database.insert_activity_log(
        lead_id=lead_id,
        activity_type="Customer Inbound Response",
        activity_description=f"Client replied: \"{clean_resp}\". {cancelled_count} future automated follow-up tasks were halted.",
        db_path=db_path
    )
    
    return {
        "success": True,
        "lead_id": lead_id,
        "response_recorded": clean_resp,
        "cancelled_tasks": cancelled_count,
        "message": f"Customer response recorded. Halted {cancelled_count} pending follow-ups."
    }

def mark_lead_opt_out(
    lead_id: str,
    reason: str = "Client requested no further communications",
    db_path: str = database.DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """
    Marks lead as opted out.
    CRITICAL BEHAVIOR: Cancels all future communications and logs compliance activity.
    """
    lead = database.get_lead_by_id(lead_id, db_path=db_path)
    if not lead:
        return {"success": False, "error": f"Lead {lead_id} not found"}
        
    database.update_lead_opt_out(lead_id, is_opted_out=1, reason=reason, db_path=db_path)
    stop_reason = f"Customer Opted Out: {reason}"
    cancelled_count = database.cancel_scheduled_followups_for_lead(lead_id, stop_reason, db_path=db_path)
    
    database.insert_activity_log(
        lead_id=lead_id,
        activity_type="Customer Communication Opt-Out",
        activity_description=f"Client opted out ({reason}). All {cancelled_count} pending follow-ups cancelled permanently.",
        db_path=db_path
    )
    
    return {
        "success": True,
        "lead_id": lead_id,
        "is_opted_out": True,
        "cancelled_tasks": cancelled_count,
        "message": f"Lead marked as opted out. Cancelled {cancelled_count} tasks."
    }

def pause_or_resume_lead_followups(
    lead_id: str,
    pause: bool = True,
    db_path: str = database.DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """Pauses or resumes follow-ups manually for a sales representative."""
    lead = database.get_lead_by_id(lead_id, db_path=db_path)
    if not lead:
        return {"success": False, "error": f"Lead {lead_id} not found"}
        
    database.update_lead_pause_state(lead_id, is_paused=1 if pause else 0, db_path=db_path)
    state_str = "Paused" if pause else "Resumed"
    
    if pause:
        database.cancel_scheduled_followups_for_lead(lead_id, "Manually paused by sales representative", db_path=db_path)
        
    database.insert_activity_log(
        lead_id=lead_id,
        activity_type=f"Follow-ups {state_str}",
        activity_description=f"Sales representative manually {state_str.lower()} automated follow-ups.",
        db_path=db_path
    )
    
    return {
        "success": True,
        "lead_id": lead_id,
        "is_paused": pause,
        "message": f"Follow-ups {state_str.lower()} for lead {lead_id}."
    }

def update_lead_crm_status_with_automation(
    lead_id: str,
    new_status: str,
    db_path: str = database.DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """
    Updates CRM lead status and triggers appropriate follow-up automation lifecycle events.
    If new status is Converted or Lost, all future follow-ups are automatically cancelled!
    """
    lead = database.get_lead_by_id(lead_id, db_path=db_path)
    if not lead:
        return {"success": False, "error": f"Lead {lead_id} not found"}
        
    old_status = lead.get("lead_status", "New")
    database.update_lead_crm_status(lead_id, new_status, db_path=db_path)
    
    cancelled_count = 0
    if new_status.lower() in ["converted", "lost"]:
        reason = f"Lead transitioned to terminal status '{new_status}'"
        cancelled_count = database.cancel_scheduled_followups_for_lead(lead_id, reason, db_path=db_path)
        
    database.insert_activity_log(
        lead_id=lead_id,
        activity_type="CRM Status Change",
        activity_description=f"Lead status changed from '{old_status}' to '{new_status}'. ({cancelled_count} pending follow-ups cancelled).",
        db_path=db_path
    )
    
    return {
        "success": True,
        "lead_id": lead_id,
        "old_status": old_status,
        "new_status": new_status,
        "cancelled_tasks": cancelled_count
    }
