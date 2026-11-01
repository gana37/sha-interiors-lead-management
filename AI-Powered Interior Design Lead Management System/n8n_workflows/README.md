# n8n Workflow Automation Architecture: SHA Interface Interiors

This directory contains production-ready JSON workflow definitions for integrating **n8n** (self-hosted or n8n Cloud) with the SHA Interface Interiors Lead Management System.

---

## 1. Exported Workflows Catalog

| File | Trigger | Actions | Target System |
| :--- | :--- | :--- | :--- |
| **`workflow_1_new_lead_notification.json`** | Webhook (`POST /webhook/sha-new-lead`) | Validates payload, formats enquiry summary, alerts sales consultants. | Slack / Email / CRM |
| **`workflow_2_high_priority_lead_alert.json`** | Webhook (`POST /webhook/sha-high-priority-alert`) | Filters for Score $\ge$ 80, broadcasts urgent notification to principal designer. | Slack `#high-priority-leads` |
| **`workflow_3_followup_reminder.json`** | Webhook / Cron (`POST /webhook/sha-followup-trigger`) | Enforces stop conditions (opt-out, converted, responded), generates message dispatch. | Outbound WhatsApp / SMS |
| **`workflow_4_lead_status_update.json`** | Webhook (`POST /webhook/sha-status-update`) | Broadcasts won deals (`Converted`) or auto-archives lost leads. | Team Slack / Audit Channel |

---

## 2. How to Import Workflows into n8n

1. Open your n8n web instance (e.g. `http://localhost:5678` or your cloud URL).
2. Click **Workflows** in the left sidebar $\rightarrow$ Click **+ Add Workflow**.
3. In the top-right menu (three dots `...`), select **Import from File**.
4. Select any of the JSON files in this directory (e.g., `workflow_1_new_lead_notification.json`).
5. Activate the workflow by toggling the switch in the top right to **Active**.
6. Note the generated Webhook Production URL (e.g., `https://n8n.yourdomain.com/webhook/sha-new-lead`).

---

## 3. Configuring the CRM Application

In your project environment or `.env` file, specify:
```bash
N8N_BASE_URL=https://n8n.yourdomain.com
N8N_API_KEY=your_optional_n8n_api_key
```

*Fallback Resilience:* If `N8N_BASE_URL` is omitted or the n8n container is offline, the internal `n8n_dispatcher.py` automatically routes all events through local database logging with zero user-facing errors or performance degradation.
