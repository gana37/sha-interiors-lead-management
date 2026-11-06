# ESTIMATE DATE & TIME EXTRACTION & VALIDATION REPORT
**System:** SHA Interface Interiors – Lead Management System (Hyderabad Edition)  
**Execution Date:** November 3, 2026  
**Status:** Successfully Implemented, Tested & Verified (100% Pass Rate)

---

## 1. Files Created & Modified

| File | Status | Description of Changes |
| :--- | :--- | :--- |
| `estimate_parser.py` | **Created** | Dedicated engine for parsing, validating, and formatting 10-digit estimate reference numbers (`HHMMDDMMYY`), handling prefix stripping, leap years, 24h validation, and user-friendly formatting. |
| `database.py` | **Modified** | Added `lead_reference` and `estimate_generated_at` columns and indexes in `init_db`. Updated `insert_lead` and `batch_insert_leads` to extract and decode references. Added sorting by estimate datetime and date range filters in `get_all_leads`. Added `backfill_estimate_datetimes_from_reference`. |
| `data_loader.py` | **Modified** | Updated `validate_and_prepare_csv` to support both **CSV and Excel (`.xlsx`, `.xls`)**, detect reference columns, validate 10-digit formats, log non-crashing warnings for invalid/missing references, and attach `estimate_generated_at`. |
| `reports.py` | **Modified** | Added `get_estimate_analytics()` calculating telemetry derived exclusively from `estimate_generated_at`: leads today, this week, this month, latest estimate generated, and grouping by estimate generation date. Added trend dataset to `get_chart_data()`. |
| `app.py` | **Modified** | Integrated **Estimate Generated Date & Time** column in the Lead Management table, added estimate date range filters and sorting controls, added interactive telemetry cards and latest estimate banner in Home Dashboard, added estimate details to individual lead view, and enabled `.xlsx`/`.xls` file uploads. |
| `test_estimate_datetime.py` | **Created** | Comprehensive test suite covering all 8 verification requirements (exact parsing, prefixes, invalid boundaries, leap years, CSV/Excel imports, database sorting/filtering). |
| `SHA_Hyderabad_Interior_Design_Leads.csv` & `.xlsx` | **Updated** | Exported active dataset including `lead_reference` and `estimate_generated_at` fields. |

---

## 2. Database Schema Changes

Two new indexed columns were added to the `LEADS` table via backward-compatible migrations:

```sql
-- Schema Migration in database.py
ALTER TABLE LEADS ADD COLUMN lead_reference TEXT;
ALTER TABLE LEADS ADD COLUMN estimate_generated_at TEXT;

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_leads_ref ON LEADS(lead_reference);
CREATE INDEX IF NOT EXISTS idx_leads_estimate_time ON LEADS(estimate_generated_at);
```

### Properties:
- `lead_reference`: Stores the raw estimate reference number (e.g., `EST-2319311026`).
- `estimate_generated_at`: Stores the extracted, validated timestamp in ISO 8601 format (`YYYY-MM-DD HH:MM:SS`), e.g., `2026-10-31 23:19:00`.
- **Backward Compatibility**: Fully non-destructive; existing queries and columns remain completely functional.

---

## 3. Date/Time Parsing & Validation Logic

The decoding engine is implemented in `estimate_parser.py`:

```
Input: [Prefix (optional)] + HHMMDDMMYY
Example: EST-2319311026
```

### Parsing Pipeline:
1. **Prefix Sanitization**: Strips case-insensitive prefixes (`EST-`, `EST_`, `EST `, `EST:`).
2. **Payload Extraction**: Verifies that the remaining string is exactly 10 digits (`^\d{10}$`).
3. **Component Slicing**:
   - `HH` (Digits 0–2): Hour in 24-hour format (`00` to `23`).
   - `MM` (Digits 2–4): Minutes (`00` to `59`).
   - `DD` (Digits 4–6): Day of month (`01` to `31`).
   - `MM` (Digits 6–8): Month (`01` to `12`).
   - `YY` (Digits 8–10): 2-digit Year. Explicit rule: `2000 + YY` (e.g., `26` -> `2026`).
4. **Calendar Validation**:
   - Evaluated via `datetime.datetime(year, month, day, hour, minute, 0)`.
   - Strictly enforces days per month and leap-year rules (e.g., Feb 29 is valid in 2024, but raises an error in 2026).
5. **Formatting**:
   - **Database ISO 8601**: `YYYY-MM-DD HH:MM:SS` (e.g., `2026-10-31 23:19:00`).
   - **Dashboard Display**: `31 Oct 2026 | 11:19 PM` (e.g., `2 Nov 2026 | 7:07 PM`).
   - **Long Display**: `31 October 2026, 11:19 PM`.
6. **Graceful Error Handling**:
   - If reference is missing, empty, or invalid, returns `(None, None, warning_message)`.
   - Never silently assigns the current date/time.
   - Non-crashing behavior: logs a warning and stores the original reference.

---

## 4. Number of References Decoded & Preserved

All 7 genuine customer leads currently in the active database were audited:

| Lead ID | Customer Name | Phone | Raw Reference | Extracted Datetime (ISO 8601) | User Display Format | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SHA-2026-0001` | Dr. Chakravarthy.B El PT | +91 98853 01530 | `EST-1907021126` | `2026-11-02 19:07:00` | `2 Nov 2026 \| 7:07 PM` | ✅ Decoded |
| `SHA-2026-0002` | Saikoushik Chavali | +91 95500 42018 | `EST-2356011126` | `2026-11-01 23:56:00` | `1 Nov 2026 \| 11:56 PM` | ✅ Decoded |
| `SHA-2026-0003` | Vivek Ankit | +91 70326 56782 | `EST-2216011126` | `2026-11-01 22:16:00` | `1 Nov 2026 \| 10:16 PM` | ✅ Decoded |
| `SHA-2026-0004` | Priti | +91 80933 33059 | `EST-1804011126` | `2026-11-01 18:04:00` | `1 Nov 2026 \| 6:04 PM` | ✅ Decoded |
| `SHA-2026-0005` | Aditya | +91 98406 56800 | `EST-2319311026` | `2026-10-31 23:19:00` | `31 Oct 2026 \| 11:19 PM` | ✅ Decoded |
| `SHA-2026-0006` | P Das | +91 83749 86796 | `EST-2225311026` | `2026-10-31 22:25:00` | `31 Oct 2026 \| 10:25 PM` | ✅ Decoded |
| `SHA-2026-0901` | Matta GANESH | +91 98765 43210 | `None` (Manual lead) | `None` | `—` | ℹ️ Preserved (No Ref) |

### Summary Statistics:
- **Total Existing Records Audited**: 7
- **References Successfully Decoded**: **6 (100% of available references)**
- **Missing References Gracefully Handled**: **1** (`Matta GANESH` entered manually via UI)
- **Invalid Reference Numbers**: **0**

---

## 5. Dashboard Analytics & Date-Based Insights

Derived strictly from `estimate_generated_at`:
- **Latest Estimate Generated**: `Dr. Chakravarthy.B El PT` &mdash; `2 Nov 2026 | 7:07 PM` (`EST-1907021126`)
- **Estimates Decoded**: 6 / 7 Leads (85.7%)
- **Leads Generated This Week**: 1 lead
- **Leads Generated This Month**: 4 leads
- **Grouped by Estimate Generation Date**:
  - `2026-11-02`: 1 lead (`Dr. Chakravarthy.B El PT`)
  - `2026-11-01`: 3 leads (`Saikoushik Chavali`, `Vivek Ankit`, `Priti`)
  - `2026-10-31`: 2 leads (`Aditya`, `P Das`)

---

## 6. Test Results & Exit Codes

Executed tests across the system with actual exit codes:

### A. Estimate Extraction Suite (`test_estimate_datetime.py`)
**Exit Code: `0` (Success)**
```text
======================================================================
RUNNING ESTIMATE DATE & TIME EXTRACTION VERIFICATION SUITE
======================================================================
[Test 1] Testing '2319311026' -> 31 October 2026, 11:19 PM...
-> Test 1 PASSED: ISO='2026-10-31 23:19:00' | Display='31 Oct 2026 | 11:19 PM' | Full='31 October 2026, 11:19 PM'

[Test 2] Testing '1907021126' -> 2 November 2026, 7:07 PM...
-> Test 2 PASSED: ISO='2026-11-02 19:07:00' | Display='2 Nov 2026 | 7:07 PM' | Full='2 November 2026, 7:07 PM'

[Test 3] Testing References with and without 'EST-' Prefix...
-> Test 3 PASSED: All 6 prefix variations parsed identically.

[Test 4] Testing Invalid Hours and Minutes...
-> Test 4 PASSED: Hours [00-23] and Minutes [00-59] strictly enforced.

[Test 5] Testing Invalid Dates and Months (with Leap Year Check)...
-> Test 5 PASSED: Calendar validity and leap-year rules verified.

[Test 6] Testing Missing & Malformed Reference Numbers...
-> Test 6 PASSED: Missing/malformed references never crash and never assign current time.

[Test 7] Testing CSV and Excel Import Pipeline...
-> Test 7 PASSED: CSV and Excel imports validated with graceful warning capture.

[Test 8] Testing Active Database Records, Sorting & Date Range Filtering...
-> Test 8 PASSED: All 7 existing records verified, sorting and date filtering validated.

======================================================================
ALL 8 ESTIMATE DATE & TIME EXTRACTION TESTS PASSED WITH 100% SUCCESS!
======================================================================
```

### B. Genuine Dataset Verification Suite (`test_genuine_dataset.py`)
**Exit Code: `0` (Success)**
- All 7 verification tests passed (Zero dummy data, 7 genuine customer records, AI Lead Scoring, 21 follow-up tasks, Startup protection, AI Assistant grounding, Executive KPIs).

### C. Lead Scoring Test Suite (`test_lead_scoring.py`)
**Exit Code: `0` (Success)**
- All 12 tests passed (Max/min boundaries, budget tiers, Hyderabad location scoring, completeness, rescoring, immobility).

---

## 7. Confirmation of Customer Data & Functional Integrity

1. **Customer Records Preserved**: Exactly 7 customer leads exist in `sha_leads.db` (no duplicate leads, zero dummy data re-introduced).
2. **Dashboard Layout & Design**: All existing UI elements, styles, fonts, color palettes, and navigation structures were preserved.
3. **No Unrelated Code Affected**: Lead scoring, follow-up automations, AI Assistant, and n8n webhook integrations remain untouched and fully operational.
4. **Safety Backups Retained**: Pre-migration database backup archived at:
   `backups/sha_leads_backup_pre_estimate_datetime_20261103_180414.db`.
