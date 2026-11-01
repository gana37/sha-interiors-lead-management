# Final Project Report: SHA Interface Interiors Lead Management System

**Client:** SHA Interface Interiors  
**Author:** Senior Full-Stack Python & AI Systems Engineer  
**Date:** November 2026  
**Status:** Completed & Production Verified  

---

## 1. Executive Summary

This report delivers the completed, end-to-end **AI-Powered Lead Management System** for **SHA Interface Interiors**. 

The system transitions the firm from disjointed inquiry handling to an automated, intelligent lead operating system. It features real-time qualification scoring, priority categorization, automated follow-up cadences with compliance stop triggers, an analytics dashboard, and an AI Sales Consultant assistant.

All 10 project milestones were achieved, verified by automated unit, integration, and end-to-end test suites.

---

## 2. Stage-by-Stage Implementation Summary

### Step 1 & 2: Dataset Auditing, Hygiene & Domain Enrichment
* **Legacy Benchmark Audited:** 9,240 records in `Leads.csv` analyzed. Identified and replaced 13,380 `"Select"` dropdown placeholders. Removed 14 zero-variance or severely sparse columns.
* **Data Leakage Prevented:** Investigated `Tags`, `Lead Quality`, and `Last Activity`. Documented that post-conversion disposition tags (e.g. "Closed by Horizzon", "Lost to EINS") cannot be used as features during initial lead qualification.
* **Synthetic Interior Design Leads Generated:** Created 250 domain-specific records in `data/synthetic/interior_design_leads.csv` covering Indian cities, project types (1BHK to Villa), budget ranges (₹3L to ₹25L+), and possession stages with 0 missing values.
* **Preservation:** Original raw files preserved byte-for-byte in `data/raw/`.

### Step 3: Lead Capture & Data Ingestion Module
* **SQLite Core Storage:** Established `sha_leads.db` with indexed schema.
* **Ingestion Engine (`data_loader.py`):** Transactional CSV bulk loader with column validation, internal deduplication, and database key checking. Includes a security guardrail preventing the legacy education dataset from being imported into the active CRM.
* **Intake Form (`lead_capture.py`):** Form with robust Indian phone validation (`+91`, `91`, leading `0`, space/hyphen formatting), email validation, and duplicate contact detection.

### Step 4: Rule-Based AI Lead Qualification & Scoring
* **100-Point Scoring Engine (`lead_scoring.py`):**
  * Budget Suitability: **30 Points**
  * Location Suitability: **20 Points**
  * Requirements Clarity: **20 Points**
  * Purchase Readiness: **30 Points**
* **Priority Categorization:** High Priority (80–100), Medium Priority (50–79), Low Priority (0–49).
* **Explainability:** Generates human-readable rationales directly from the mathematical factor breakdown without language model hallucinations.
* **Status Immobility:** Guaranteed that scoring calculations never alter the customer's CRM `lead_status`.

### Step 5: Automated Follow-Up Management System
* **Cadence Engine (`followups.py`):** Priority-specific cadences (High: 3 touches over 7 days; Medium: 3 touches over 10 days; Low: 2 touches over 14 days) in `Asia/Kolkata` time.
* **Personalized Drafts (`followup_templates.py`):** 7 context-aware templates (acknowledgement, budget alignment, site visit, portfolio sharing, etc.).
* **Automated Stop Conditions:** Follow-ups are halted when:
  1. A customer responds (inbound response simulator halts pending touches).
  2. A customer opts out.
  3. The lead transitions to `Converted` or `Lost`.
  4. A sales rep manually pauses outreach.
* **Idempotency Guard:** Prevents duplicate message dispatch.

### Step 6: n8n Workflow Automation
* **Folder Created:** `n8n_workflows/` with 4 production workflow JSON definitions:
  * Workflow 1: New Lead Notification
  * Workflow 2: High Priority Lead Alert (Score $\ge 80$)
  * Workflow 3: Follow-up Reminder & Stop Condition Guard
  * Workflow 4: Lead Status Lifecycle Update
* **Dispatcher (`n8n_dispatcher.py`):** Supports webhook dispatches with seamless local fallback logging when n8n is offline.

### Step 7: Reporting & Analytics Dashboard
* **Module (`reports.py`):** Executive KPIs, pipeline funnels, and 9 analytical views (City, Project Type, Budget, Source, Priority, Status, Follow-ups, Daily & Weekly Trends).
* **Conversion Analytics:** Documented conversion rate formula:
  $$\text{Engaged Conversion Rate} = \frac{\text{Converted Leads}}{\text{Engaged Leads}} \times 100$$
  $$(26 / 195) \times 100 = 13.33\%$$
* **Periodic Reports:** Daily, weekly, and custom date range filters with 1-click CSV export.

### Step 8: CRM AI Sales Consultant Assistant
* **Module (`ai_assistant.py`):**
  * Gemini API integration when configured.
  * Local deterministic SQLite intelligence engine when offline.
  * Natural language query answering ("How many high priority leads?", "Show leads in Hyderabad", etc.).
  * Client requirement summarization and next-best-action recommendation.
  * Personalized follow-up message drafter.

### Step 9 & 10: Testing, Documentation & Demo
* **Automated Test Coverage:** 4 test suites covering 39 individual test cases with **100% pass rate**.
* **Unified UI (`app.py`):** 9 professional navigation modules.
* **Documentation:** `README.md`, `final_project_report.md`, and `demo_script.md`.

---

## 3. Production Lead Database Statistics (`sha_leads.db`)

* **Total Leads:** 250
* **Data Origin:** `synthetic_import` (250) + live manual intake ready
* **Scored Leads:** 250 / 250 (100%)
* **Average Qualification Score:** **72.4 / 100**
* **Priority Breakdown:**
  * 🟢 High Priority: **94 leads (37.6%)**
  * 🟡 Medium Priority: **137 leads (54.8%)**
  * 🔴 Low Priority: **19 leads (7.6%)**
* **Pipeline Status Distribution:**
  * New Inquiries: 55
  * Qualified: 70
  * Follow-up: 81
  * Converted: 26
  * Lost: 18
* **Scheduled Follow-up Tasks:** 603 active touchpoints across eligible leads (44 converted/lost leads excluded).

---

## 4. Automated Test Results Summary

| Test Suite | Scenarios / Cases Tested | Execution Time | Result |
| :--- | :--- | :---: | :---: |
| **`test_step3.py`** | 9 tests: DB creation, CSV parsing, deduplication, field validation, manual lead creation, persistence, query filters, data origin, education guardrail. | ~8s | **100% PASSED** |
| **`test_lead_scoring.py`** | 12 tests: Bounds (0-100), budget scoring, location tiers, requirements clarity, readiness, priority thresholds, null safety, mathematical sum consistency, rescoring updates, status immobility, historical status independence. | ~10s | **100% PASSED** |
| **`test_followups.py`** | 8 tests: Priority cadences (High 3, Medium 3, Low 2), converted stop condition, lost stop condition, opt-out cancellation, customer response halt, status transition trigger, idempotency duplicate guard, activity logging. | ~11s | **100% PASSED** |
| **`test_end_to_end.py`** | 10 scenarios: Full customer journey from intake, real-time scoring, CSV deduplication, follow-up dispatch, customer response simulation, opt-out, conversion, analytics, AI assistant Q&A, and connection reliability. | ~12s | **100% PASSED** |
| **Total Test Suite** | **39 Test Cases Across 4 Suites** | **~41s** | **100% SUCCESS** |

---

## 5. Business Assumptions Pending Client Sign-Off

1. **Target Minimum Budget:** Currently configured to demo default `₹5 lakh–₹10 lakh`. Confirmation required on whether single-room modular renovations under ₹3 Lakhs should be pursued.
2. **City Tier Classifications:** Bangalore and Hyderabad are currently weighted as Tier 1 (20 pts); Chennai, Mumbai, and Pune as Tier 2 (14 pts); Delhi NCR as Tier 3 (8 pts). These weights can be updated in `lead_scoring.py` to match the company's regional branch structure.
3. **Follow-up Timing:** Current intervals use 1, 3, and 7-day offsets. These can be adjusted per sales manager preferences in `followups.py`.
