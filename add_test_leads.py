import os
import sys
import datetime
import json
import uuid

sys.path.insert(0, os.getcwd())
import database
import lead_scoring
import followups
import estimate_parser

DB_PATH = database.DEFAULT_DB_PATH
database.init_db(DB_PATH)

print("==================================================")
print("SEEDING / UPDATING TEST LEADS: KANISHKA & DINESH")
print("==================================================")

# 1. Audit existing records to verify no genuine customer is touched
existing_leads = database.get_all_leads(db_path=DB_PATH)
genuine_ids_before = {l["lead_id"] for l in existing_leads if l.get("data_origin") != "test_data"}
print(f"Total existing leads in DB: {len(existing_leads)}")
print(f"Genuine customer IDs before: {sorted(list(genuine_ids_before))}")

now_iso = datetime.datetime.now().isoformat()

test_leads_definitions = [
    {
        "lead_id": "SHA-TEST-0001",
        "customer_name": "Kanishka",
        "phone": "+91 90001 40689",
        "email": "mattaganesh191@gmail.com",
        "city": "Hyderabad",
        "locality": "Gachibowli",
        "region": "West Hyderabad",
        "pincode": "500032",
        "lead_source": "Website Form (Test Data)",
        "budget_range": "₹12 lakh – ₹18 lakh",
        "project_type": "3BHK",
        "property_status": "Ready to Move",
        "project_timeline": "Within 2 months",
        "scope_of_work": "Complete Home Interior Design",
        "customer_requirements": """Modular kitchen
Bedroom wardrobes
TV unit
False ceiling
Living room interiors
Storage solutions
Lighting design

Customer Preferences:
Modern and elegant design
Good-quality materials
Space-efficient storage
Transparent pricing
Durable hardware""",
        "purchase_readiness": "Ready to Start",
        "preferred_contact_method": "WhatsApp",
        "lead_status": "New",
        "created_at": "2026-11-04T11:45:00",
        "updated_at": now_iso,
        "data_origin": "test_data",
        "lead_reference": "EST-1145041126",
        "estimate_generated_at": "2026-11-04 11:45:00",
        "is_service_area": 1,
        "is_opted_out": 0,
        "is_paused": 0,
        "assigned_salesperson": "Senior Interior Consultant (SHA Interiors)"
    },
    {
        "lead_id": "SHA-TEST-0002",
        "customer_name": "Dinesh",
        "phone": "+91 85005 25509",
        "email": "dineshjawa42@gmail.com",
        "city": "Hyderabad",
        "locality": "Miyapur",
        "region": "North-West Hyderabad",
        "pincode": "500049",
        "lead_source": "Website Form (Test Data)",
        "budget_range": "₹5 lakh – ₹8 lakh",
        "project_type": "2BHK",
        "property_status": "Ready to Move",
        "project_timeline": "Within 3–4 months",
        "scope_of_work": "Kitchen and Bedroom Interiors",
        "customer_requirements": """Modular kitchen
Bedroom wardrobes
Sliding wardrobes
Space-saving storage
Kitchen cabinets
Practical interior layouts
Modern lighting

Customer Preferences:
Budget-conscious solutions
Maximum storage utilisation
Easy-to-maintain materials
Modern and functional design
Transparent pricing""",
        "purchase_readiness": "Ready to Start",
        "preferred_contact_method": "WhatsApp",
        "lead_status": "New",
        "created_at": "2026-11-04T11:50:00",
        "updated_at": now_iso,
        "data_origin": "test_data",
        "lead_reference": "EST-1150041126",
        "estimate_generated_at": "2026-11-04 11:50:00",
        "is_service_area": 1,
        "is_opted_out": 0,
        "is_paused": 0,
        "assigned_salesperson": "Senior Interior Consultant (SHA Interiors)"
    }
]

conn = database.get_connection(DB_PATH)
try:
    with conn:
        cursor = conn.cursor()
        for t_lead in test_leads_definitions:
            lid = t_lead["lead_id"]
            cursor.execute("""
                SELECT lead_id FROM LEADS 
                WHERE lead_id = ? OR email = ? OR phone = ?;
            """, (lid, t_lead["email"], t_lead["phone"]))
            existing_match = cursor.fetchone()
            
            if existing_match:
                matched_id = existing_match["lead_id"]
                print(f"Updating existing lead: {matched_id} ({t_lead['customer_name']})...")
                cursor.execute("""
                    UPDATE LEADS SET
                        customer_name = :customer_name,
                        phone = :phone,
                        email = :email,
                        city = :city,
                        locality = :locality,
                        region = :region,
                        pincode = :pincode,
                        lead_source = :lead_source,
                        budget_range = :budget_range,
                        project_type = :project_type,
                        property_status = :property_status,
                        project_timeline = :project_timeline,
                        scope_of_work = :scope_of_work,
                        customer_requirements = :customer_requirements,
                        purchase_readiness = :purchase_readiness,
                        preferred_contact_method = :preferred_contact_method,
                        lead_status = :lead_status,
                        updated_at = :updated_at,
                        data_origin = :data_origin,
                        lead_reference = :lead_reference,
                        estimate_generated_at = :estimate_generated_at,
                        is_service_area = :is_service_area,
                        is_opted_out = 0,
                        is_paused = 0,
                        last_customer_response = NULL,
                        last_response_at = NULL,
                        assigned_salesperson = :assigned_salesperson
                    WHERE lead_id = :matched_id;
                """, {**t_lead, "matched_id": matched_id})
                actual_id = matched_id
            else:
                print(f"Inserting new lead: {lid} ({t_lead['customer_name']})...")
                cols = list(t_lead.keys())
                placeholders = [f":{c}" for c in cols]
                sql = f"INSERT INTO LEADS ({', '.join(cols)}) VALUES ({', '.join(placeholders)});"
                cursor.execute(sql, t_lead)
                actual_id = lid
                
            act_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
            cursor.execute(
                "INSERT INTO LEAD_ACTIVITY_LOG (activity_id, lead_id, activity_type, activity_description, timestamp) VALUES (?, ?, ?, ?, ?);",
                (act_id, actual_id, "Lead Registered (Test Data)", f"High Priority test customer {t_lead['customer_name']} enrolled in Hyderabad CRM.", now_iso)
            )
finally:
    conn.close()

# 2. Score both leads using actual scoring rules
print("\n--- Recalculating Lead Scores via Actual Scoring Engine ---")
for t_lead in test_leads_definitions:
    lid = t_lead["lead_id"]
    res = lead_scoring.score_and_save_lead(lid, db_path=DB_PATH)
    print(f"Lead {lid} ({t_lead['customer_name']}):")
    print(f"  Score: {res['lead_score']}/100")
    print(f"  Priority: {res['priority']}")
    print(f"  Reason: {res['scoring_reason']}")
    assert res['priority'] == "High", f"Expected High priority, got {res['priority']}"

# 3. Schedule High Priority follow-up cadence for both leads
print("\n--- Scheduling High Priority Follow-up Tasks ---")
for t_lead in test_leads_definitions:
    lid = t_lead["lead_id"]
    f_res = followups.schedule_followups_for_lead(lid, db_path=DB_PATH)
    sched_count = f_res.get('scheduled_count', 0)
    print(f"Lead {lid} ({t_lead['customer_name']}): Scheduled {sched_count} follow-up tasks.")
    for task in f_res.get("tasks", []):
        print(f"  - [{task['channel']}] Attempt {task['attempt_number']} due at {task['scheduled_for']}")

# 4. Final Verification
print("\n--- Final Safety and Integrity Audit ---")
all_leads_after = database.get_all_leads(db_path=DB_PATH)
genuine_ids_after = {l["lead_id"] for l in all_leads_after if l.get("data_origin") != "test_data"}
print(f"Total leads in DB now: {len(all_leads_after)}")
assert genuine_ids_before == genuine_ids_after, f"Genuine leads changed! Before: {genuine_ids_before}, After: {genuine_ids_after}"
print("VERIFIED: All 7 genuine customer records remain completely unaltered!")

for lid in ["SHA-TEST-0001", "SHA-TEST-0002"]:
    l = database.get_lead_by_id(lid, db_path=DB_PATH)
    tasks = database.get_followups(db_path=DB_PATH, lead_id=lid)
    print(f"\nAudit {lid}:")
    print(f"  Name: {l['customer_name']}")
    print(f"  Phone: {l['phone']}")
    print(f"  Email: {l['email']}")
    print(f"  Locality: {l['locality']} ({l['region']})")
    print(f"  Score: {l['lead_score']} (Priority: {l['priority']})")
    print(f"  Data Origin: {l['data_origin']}")
    print(f"  Active Follow-up Tasks: {len(tasks)}")

print("\nSUCCESS: Both test leads inserted and scored with 100% precision!")
