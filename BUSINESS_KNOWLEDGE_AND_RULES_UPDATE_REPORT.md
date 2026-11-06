# SHA Interface Interiors — Central Business Knowledge & Communication Rules Update Report

**System:** AI-Powered Interior Design Lead Management System (Hyderabad Edition)  
**Execution Date:** 4 November 2026  
**Status:** Successfully Implemented, Tested & Verified (100% Pass Rate across 12 Test Cases)  
**Conducted By:** Antigravity AI Assistant  

---

## Executive Summary

The central business knowledge and mandatory AI communication rules for **SHA Interface Interiors** have been established in a single reusable configuration module ([`business_config.py`](file:///C:/Users/User/Downloads/AI-Powered%20Interior%20Design%20Lead%20Management%20System/business_config.py)) and applied across all conversational AI prompts, local expert fallback engines, website enquiry outbound message templates, and follow-up drafters.

All 9 mandatory rules were verified via the new automated test suite [`test_business_knowledge_and_rules.py`](file:///C:/Users/User/Downloads/AI-Powered%20Interior%20Design%20Lead%20Management%20System/test_business_knowledge_and_rules.py) (12 / 12 tests passed, 100% success rate), with zero regressions across existing test suites (`test_enquiry_whatsapp.py`, `test_estimate_datetime.py`, `test_lead_scoring.py`).

---

## 1. Official Business Information Configured

The central configuration in [`business_config.py`](file:///C:/Users/User/Downloads/AI-Powered%20Interior%20Design%20Lead%20Management%20System/business_config.py) establishes:

| Parameter | Official Value | Usage in System |
|:---|:---|:---|
| **Business Name** | `SHA Interface Interiors` | Canonical business name across all prompts and templates. |
| **Office Name** | `Miyapur office` | **Strict mandatory term**. The obsolete term *"Hyderabad Studio"* and *"Experience Center"* have been eliminated. |
| **Working Hours** | `10:00 AM to 6:00 PM IST` | Indian Standard Time (IST) business window. |
| **Working Days** | `Monday through Sunday (All seven days)` | Open all 7 days of the week. Never claimed closed on Sundays or weekdays. |
| **Official Office Location** | `https://maps.app.goo.gl/Ybuctd1ghqFiQ69D6` | The official Google Maps link. Invented street addresses are strictly prohibited. |
| **Appointment Options** | 1) Meeting at our **Miyapur office**<br>2) Convenient **phone call** | Standard consultative options offered when discussing appointments. |
| **Confirmation Boundary** | Explicit salesperson confirmation required | AI never promises an appointment is confirmed until the salesperson confirms it. |

---

## 2. Canonical Customer Benchmark Response

```text
"Thank you for your interest in SHA Interface Interiors! We would be happy to arrange a meeting at our Miyapur office or schedule a phone call to discuss your requirements.

Our working hours are 10:00 AM to 6:00 PM, Monday through Sunday.

Please let us know your preferred date and time, and our team will assist you with the appointment."
```

---

## 3. Files Created and Modified

| File | Status | Description of Changes |
|:---|:---:|:---|
| [`business_config.py`](file:///C:/Users/User/Downloads/AI-Powered%20Interior%20Design%20Lead%20Management%20System/business_config.py) | **Created** | Reusable central business configuration module holding business constants, prompt blocks (`AI_SYSTEM_INSTRUCTION_BLOCK`), canonical response builders, and automated compliance validator (`validate_message_compliance`). |
| [`test_business_knowledge_and_rules.py`](file:///C:/Users/User/Downloads/AI-Powered%20Interior%20Design%20Lead%20Management%20System/test_business_knowledge_and_rules.py) | **Created** | 12-test automated verification suite testing office name rules, hours, seven-day schedule, Google Maps link, and compliance validation. |
| [`whatsapp_assistant.py`](file:///C:/Users/User/Downloads/AI-Powered%20Interior%20Design%20Lead%20Management%20System/whatsapp_assistant.py) | **Modified** | Imported `business_config`. Injected `business_config.AI_SYSTEM_INSTRUCTION_BLOCK` into `SYSTEM_SALES_INSTRUCTION`. Updated local expert engine with dedicated appointment, working hours, and Google Maps direction intent handlers; removed all mentions of *"Hyderabad studio"* and *"experience centre"*. |
| [`enquiry_whatsapp.py`](file:///C:/Users/User/Downloads/AI-Powered%20Interior%20Design%20Lead%20Management%20System/enquiry_whatsapp.py) | **Modified** | Imported `business_config`. Configured `DEFAULT_TEMPLATE` and `generate_enquiry_message` to use `business_config.BUSINESS_NAME` and `business_config.OFFICE_NAME`. |
| [`followup_templates.py`](file:///C:/Users/User/Downloads/AI-Powered%20Interior%20Design%20Lead%20Management%20System/followup_templates.py) | **Modified** | Imported `business_config`. Updated `consultation_scheduling` template to offer meeting at Miyapur office or phone call, 10:00 AM to 6:00 PM IST (Monday through Sunday), with official Maps link. |
| [`followup_intelligence.py`](file:///C:/Users/User/Downloads/AI-Powered%20Interior%20Design%20Lead%20Management%20System/followup_intelligence.py) | **Modified** | Imported `business_config`. Updated executive email draft consultation invitation and office signature block to reference Miyapur office, 7-day schedule, and Google Maps link. |
| [`ai_service.py`](file:///C:/Users/User/Downloads/AI-Powered%20Interior%20Design%20Lead%20Management%20System/ai_service.py) | **Modified** | Imported `business_config`. Injected mandatory office rules and `business_config.AI_SYSTEM_INSTRUCTION_BLOCK` into default system prompt and consultant prompt formatting. |
| [`ai_assistant.py`](file:///C:/Users/User/Downloads/AI-Powered%20Interior%20Design%20Lead%20Management%20System/ai_assistant.py) | **Modified** | Imported `business_config`. Updated `recommend_next_action` to recommend *"Schedule Meeting at Miyapur Office or Phone Call"*. |
| [`sales_intelligence.py`](file:///C:/Users/User/Downloads/AI-Powered%20Interior%20Design%20Lead%20Management%20System/sales_intelligence.py) | **Modified** | Imported `business_config`. Updated sales upgrade recommendation to invite clients for meeting at Miyapur office. |
| [`app.py`](file:///C:/Users/User/Downloads/AI-Powered%20Interior%20Design%20Lead%20Management%20System/app.py) | **Modified** | Imported `business_config`. Updated default follow-up task note from *"schedule studio visit"* to *"schedule meeting at Miyapur office"*. |

---

## 4. Mandatory Rule Implementation Verification

### Rule 1 & 2: Always "Miyapur office", Never "Hyderabad Studio"
- **Implementation:** `business_config.OFFICE_NAME = "Miyapur office"`. `FORBIDDEN_OFFICE_TERMS` specifically includes `"Hyderabad Studio"` and `"Experience Center"`.
- **System Instructions:** Explicitly forbids the phrase in prompt block: `"NEVER call it 'Hyderabad Studio', 'Experience Center', or any other title"`.
- **Local Fallback Engine:** Pricing objection and portfolio walkthrough handlers updated to reference `Miyapur office`.

### Rule 3: Meeting Options (Miyapur office or Phone Call)
- **Implementation:** Both Gemini system instructions and local expert intent handlers propose:
  `"...we would be happy to arrange a meeting at our Miyapur office or schedule a convenient phone call..."`

### Rule 4 & 5: Hours (10:00 AM to 6:00 PM IST) within Business Hours
- **Implementation:** Communicated across all templates as:
  `"Our working hours are 10:00 AM to 6:00 PM IST, Monday through Sunday (all seven days). Please let us know your preferred date and time within business hours..."`

### Rule 6: Use Indian Standard Time (IST)
- **Implementation:** Explicitly mentions `IST` in prompt instructions, templates, and conversational responses.

### Rule 7: Open All 7 Days (Never Claim Closed on Sundays)
- **Implementation:** Added specific intent handler in `whatsapp_assistant.py` for queries like *"Are you open on Sunday?"*:
  `"Hello {name}, yes! Our Miyapur office is open all seven days of the week, Monday through Sunday, from 10:00 AM to 6:00 PM IST. We would be happy to arrange a meeting at our Miyapur office or schedule a convenient phone call on Sunday or any day that suits you best."`

### Rule 8: Official Google Maps Link (Never Invent Street Addresses)
- **Implementation:** Uses `https://maps.app.goo.gl/Ybuctd1ghqFiQ69D6`. When location or directions are queried, the official link is returned without fabricating plot numbers or street names.

### Rule 9: Confirmation Boundary
- **Implementation:** Responses conclude with:
  `"...and our team will assist you with confirming the appointment."`
  The AI explicitly does not promise an appointment is booked until verified by the salesperson.

---

## 5. Automated Test Results

### Test Suite: `test_business_knowledge_and_rules.py`
All 12 unit tests executed and passed:

```text
test_01_central_business_constants .................................... OK
test_02_mandatory_communication_rules_block ........................... OK
test_03_canonical_example_customer_response ........................... OK
test_04_whatsapp_assistant_system_instruction ......................... OK
test_05_whatsapp_assistant_appointment_scheduling ..................... OK
test_06_whatsapp_assistant_sunday_and_timings ......................... OK
test_07_whatsapp_assistant_directions_and_maps_link ................... OK
test_08_whatsapp_assistant_pricing_and_portfolio_rules ................ OK
test_09_enquiry_whatsapp_outbound_messages ............................. OK
test_10_followup_templates_and_intelligence ........................... OK
test_11_ai_service_system_prompt_instruction .......................... OK
test_12_compliance_validator_detection ................................ OK

Ran 12 tests in 0.138s -- OK (100% Pass Rate)
```

### Regression Verification:
1. `test_enquiry_whatsapp.py`: **6 / 6 Passed (100%)**
2. `test_estimate_datetime.py`: **8 / 8 Passed (100%)**
3. `test_lead_scoring.py`: **12 / 12 Passed (100%)**

---

## 6. Safety & Non-Disruption Guarantees

1. **Customer Context Preserved:** Lead records for Kanishka, Dinesh, and all 7 genuine customer leads remain unaltered.
2. **Message History Preserved:** SQLite table `CUSTOMER_CONVERSATIONS` was not overwritten or cleared.
3. **No Automatic Dispatch:** All message generation remains in preview/draft mode; no WhatsApp messages or emails are sent automatically.
4. **n8n Untouched:** No n8n workflows were modified or started.
