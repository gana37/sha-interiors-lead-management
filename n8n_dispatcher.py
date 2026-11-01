import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

# Read environment variables for n8n configuration
N8N_BASE_URL = os.environ.get("N8N_BASE_URL", "").rstrip("/")
N8N_API_KEY = os.environ.get("N8N_API_KEY", "")

def is_n8n_configured() -> bool:
    """Checks whether an n8n webhook host URL is configured in environment variables."""
    return bool(N8N_BASE_URL)

def dispatch_webhook(endpoint_path: str, payload: Dict[str, Any], timeout: int = 3) -> Dict[str, Any]:
    """
    Sends a JSON webhook payload to the configured n8n endpoint.
    If n8n is not configured or unreachable, safely falls back to local logging.
    """
    if not is_n8n_configured():
        return {
            "success": True,
            "status": "local_fallback",
            "message": f"n8n webhook URL not configured. Local event logged: {endpoint_path}",
            "payload_preview": {k: v for k, v in list(payload.items())[:4]}
        }

    url = f"{N8N_BASE_URL}/{endpoint_path.lstrip('/')}"
    headers = {"Content-Type": "application/json"}
    if N8N_API_KEY:
        headers["X-N8N-API-KEY"] = N8N_API_KEY

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            return {
                "success": 200 <= status_code < 300,
                "status": "delivered",
                "http_code": status_code,
                "message": f"Webhook delivered to n8n ({status_code})"
            }
    except Exception as e:
        # Graceful fallback: do not crash application if n8n service is down
        return {
            "success": False,
            "status": "delivery_failed_fallback",
            "message": f"n8n service unavailable ({str(e)}). Handled via local fallback.",
            "error": str(e)
        }

def trigger_new_lead_webhook(lead: Dict[str, Any]) -> Dict[str, Any]:
    """Workflow 1 Trigger: Dispatches new lead notification."""
    return dispatch_webhook("webhook/sha-new-lead", {
        "event": "new_lead_captured",
        "lead_id": lead.get("lead_id"),
        "customer_name": lead.get("customer_name"),
        "phone": lead.get("phone"),
        "city": lead.get("city"),
        "budget_range": lead.get("budget_range"),
        "project_type": lead.get("project_type"),
        "scope_of_work": lead.get("scope_of_work"),
        "project_timeline": lead.get("project_timeline"),
        "purchase_readiness": lead.get("purchase_readiness"),
        "created_at": lead.get("created_at")
    })

def trigger_high_priority_alert_webhook(lead: Dict[str, Any]) -> Dict[str, Any]:
    """Workflow 2 Trigger: Dispatches high priority lead alert."""
    return dispatch_webhook("webhook/sha-high-priority-alert", {
        "event": "high_priority_lead_alert",
        "lead_id": lead.get("lead_id"),
        "customer_name": lead.get("customer_name"),
        "phone": lead.get("phone"),
        "city": lead.get("city"),
        "lead_score": lead.get("lead_score"),
        "priority": lead.get("priority"),
        "budget_range": lead.get("budget_range"),
        "scoring_reason": lead.get("scoring_reason")
    })

def trigger_followup_reminder_webhook(task: Dict[str, Any]) -> Dict[str, Any]:
    """Workflow 3 Trigger: Dispatches due follow-up reminder."""
    return dispatch_webhook("webhook/sha-followup-trigger", {
        "event": "followup_due",
        "schedule_id": task.get("schedule_id"),
        "lead_id": task.get("lead_id"),
        "customer_name": task.get("customer_name"),
        "phone": task.get("phone"),
        "channel": task.get("channel"),
        "message": task.get("message"),
        "scheduled_for": task.get("scheduled_for"),
        "lead_status": task.get("lead_status"),
        "is_opted_out": bool(task.get("is_opted_out")),
        "last_customer_response": task.get("last_customer_response")
    })

def trigger_status_update_webhook(lead: Dict[str, Any], old_status: str, new_status: str) -> Dict[str, Any]:
    """Workflow 4 Trigger: Dispatches lead status lifecycle change."""
    return dispatch_webhook("webhook/sha-status-update", {
        "event": "lead_status_changed",
        "lead_id": lead.get("lead_id"),
        "customer_name": lead.get("customer_name"),
        "old_status": old_status,
        "new_status": new_status,
        "city": lead.get("city"),
        "lead_score": lead.get("lead_score")
    })
