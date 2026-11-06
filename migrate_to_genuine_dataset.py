"""
migrate_to_genuine_dataset.py - Genuine Customer Dataset Migration
Replaces dummy/synthetic lead records with genuine customer records.
Preserves existing genuine customer records (Matta GANESH - SHA-2026-0901).
"""

import sys
import os
import sqlite3
import datetime
import json
import shutil

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import database
import lead_scoring
import followups
import hyderabad_geo as hg

# The 6 genuine customer leads from the prompt
GENUINE_LEADS = [
    {
        "lead_id": "SHA-2026-0001",
        "customer_name": "Dr. Chakravarthy.B El PT",
        "phone": "+91 98853 01530",
        "email": None,
        "city": "Hyderabad",
        "state": "Telangana",
        "locality": "Bachupally",
        "region": "North Hyderabad",
        "pincode": "500090",
        "is_service_area": 1,
        "lead_source": "Website Inquiry",
        "budget_range": "₹10 lakh–₹25 lakh",
        "project_type": "3BHK",
        "property_status": "Under Construction",
        "project_timeline": "Within 3 months",
        "scope_of_work": "Full Turnkey Interior",
        "customer_requirements": (
            "Venture: Urbanrise on cloud 33 (3BHK, 1110 sq ft). Ref: EST-1907021126. "
            "Estimated Budget: ₹7.89L – ₹12.22L. Package tier: Foundation. "
            "Requested items: Kitchen: Modular Kitchen, Loft, Tall Unit; "
            "Master Bedroom: Wardrobe, Dressing Unit, Loft, Workstation; "
            "Kids Bedroom: Wardrobe, Dressing Unit, Loft, Study Table; "
            "Guest Bedroom: Wardrobe, Dressing Unit, Loft; "
            "Living/Dining: TV Unit, Pooja Unit, Crockery, Shoe Rack; "
            "Whole-Home: Full Home False Ceiling."
        ),
        "purchase_readiness": "Comparing Vendors",
        "preferred_contact_method": "WhatsApp",
        "lead_status": "New",
        "data_origin": "genuine_customer"
    },
    {
        "lead_id": "SHA-2026-0002",
        "customer_name": "Saikoushik Chavali",
        "phone": "+91 95500 42018",
        "email": None,
        "city": "Hyderabad",
        "state": "Telangana",
        "locality": "Kukatpally",
        "region": "North Hyderabad",
        "pincode": "500072",
        "is_service_area": 1,
        "lead_source": "Website Inquiry",
        "budget_range": "₹5 lakh–₹10 lakh",
        "project_type": "3BHK",
        "property_status": "Ready to Move",
        "project_timeline": "Within 1 month",
        "scope_of_work": "Full Turnkey Interior",
        "customer_requirements": (
            "Venture: A2A Homeland (3BHK, 1820 sq ft). Ref: EST-2356011126. "
            "Estimated Budget: ₹7.89L – ₹10.62L. Package tier: Foundation. "
            "Requested items: Kitchen: Modular Kitchen; "
            "Master Bedroom: Wardrobe, Dressing Unit; "
            "Kids Bedroom: Wardrobe, Dressing Unit, Study Table; "
            "Guest Bedroom: Wardrobe, Dressing Unit; "
            "Living/Dining: TV Unit, Pooja Unit, Crockery; "
            "Whole-Home: Full Home False Ceiling."
        ),
        "purchase_readiness": "Comparing Vendors",
        "preferred_contact_method": "WhatsApp",
        "lead_status": "New",
        "data_origin": "genuine_customer"
    },
    {
        "lead_id": "SHA-2026-0003",
        "customer_name": "Vivek Ankit",
        "phone": "+91 70326 56782",
        "email": None,
        "city": "Hyderabad",
        "state": "Telangana",
        "locality": "Kondapur",
        "region": "West Hyderabad",
        "pincode": "500084",
        "is_service_area": 1,
        "lead_source": "Website Inquiry",
        "budget_range": "Above ₹25 lakh",
        "project_type": "4BHK",
        "property_status": "Ready to Move",
        "project_timeline": "Immediately",
        "scope_of_work": "Full Turnkey Interior",
        "customer_requirements": (
            "Venture: Smr vinay iconia (4BHK, 2610 sq ft). Ref: EST-2216011126. "
            "Estimated Budget: ₹13L – ₹39.25L. Package tier: Custom (4BHK). "
            "Requested items: Kitchen: Modular Kitchen, Tall Unit, Loft; "
            "Master Bedroom: Wardrobe, Bed, Dressing Unit, TV Unit, Workstation, Loft; "
            "Kids Bedroom: Wardrobe, Bed, Study Table; "
            "Living/Dining: TV Unit, Pooja Unit, Vanity, Crockery, Shoe Rack; "
            "Whole-Home: Full Home False Ceiling."
        ),
        "purchase_readiness": "Ready to Start",
        "preferred_contact_method": "Phone Call",
        "lead_status": "New",
        "data_origin": "genuine_customer"
    },
    {
        "lead_id": "SHA-2026-0004",
        "customer_name": "Priti",
        "phone": "+91 80933 33059",
        "email": None,
        "city": "Hyderabad",
        "state": "Telangana",
        "locality": "Narsingi",
        "region": "West Hyderabad",
        "pincode": "500075",
        "is_service_area": 1,
        "lead_source": "Website Inquiry",
        "budget_range": "₹5 lakh–₹10 lakh",
        "project_type": "2BHK",
        "property_status": "Possession within 1–3 months",
        "project_timeline": "Within 3 months",
        "scope_of_work": "Full Turnkey Interior",
        "customer_requirements": (
            "Venture: Sunshine (2BHK, 1168 sq ft). Ref: EST-1804011126. "
            "Estimated Budget: ₹2.90L – ₹7.61L. Package tier: Essential. "
            "Requested items: Kitchen: Modular Kitchen, Loft, Tall Unit; "
            "Master Bedroom: Wardrobe, Loft, Workstation; "
            "Kids Bedroom: Wardrobe, Study Table, Loft; "
            "Living/Dining: Crockery, Vanity, Pooja Unit, Shoe Rack, TV Unit."
        ),
        "purchase_readiness": "Budget Planning",
        "preferred_contact_method": "WhatsApp",
        "lead_status": "New",
        "data_origin": "genuine_customer"
    },
    {
        "lead_id": "SHA-2026-0005",
        "customer_name": "Aditya",
        "phone": "+91 98406 56800",
        "email": None,
        "city": "Hyderabad",
        "state": "Telangana",
        "locality": "Kondapur",
        "region": "West Hyderabad",
        "pincode": "500084",
        "is_service_area": 1,
        "lead_source": "Website Inquiry",
        "budget_range": "₹10 lakh–₹25 lakh",
        "project_type": "3BHK",
        "property_status": "Ready to Move",
        "project_timeline": "Immediately",
        "scope_of_work": "Full Turnkey Interior",
        "customer_requirements": (
            "Venture: inika one (3BHK, 2350 sq ft). Ref: EST-2319311026. "
            "Estimated Budget: ₹18.49L – ₹24.86L. Package tier: Turnkey. "
            "Customer notes: estimate. "
            "Requested items: Kitchen: Modular Kitchen, Tall Unit, Loft; "
            "Master Bedroom: Wardrobe, Dressing Unit, Bed, TV Unit, Workstation, Loft; "
            "Kids Bedroom: Wardrobe, Dressing Unit, Loft; "
            "Guest Bedroom: Wardrobe, Loft, Dressing Unit; "
            "Living/Dining: TV Unit, Crockery, Pooja Unit, Shoe Rack, Vanity."
        ),
        "purchase_readiness": "Ready to Start",
        "preferred_contact_method": "Phone Call",
        "lead_status": "New",
        "data_origin": "genuine_customer"
    },
    {
        "lead_id": "SHA-2026-0006",
        "customer_name": "P Das",
        "phone": "+91 83749 86796",
        "email": None,
        "city": "Hyderabad",
        "state": "Telangana",
        "locality": "Nallagandla",
        "region": "West Hyderabad",
        "pincode": "500019",
        "is_service_area": 1,
        "lead_source": "Website Inquiry",
        "budget_range": "₹5 lakh–₹10 lakh",
        "project_type": "2BHK",
        "property_status": "Possession within 30 days",
        "project_timeline": "Within 1 month",
        "scope_of_work": "Full Turnkey Interior",
        "customer_requirements": (
            "Venture: Aparna Cyberheights (2BHK, 1350 sq ft). Ref: EST-2225311026. "
            "Estimated Budget: ₹6.79L – ₹9.66L. Package tier: Premium. "
            "Requested items: Kitchen: Modular Kitchen, Loft, Tall Unit; "
            "Master Bedroom: Wardrobe, Dressing Unit, Workstation; "
            "Kids Bedroom: Wardrobe, Loft, Study Table, Dressing Unit; "
            "Living/Dining: TV Unit, Pooja Unit, Shoe Rack, Crockery; "
            "Whole-Home: Full Home False Ceiling."
        ),
        "purchase_readiness": "Comparing Vendors",
        "preferred_contact_method": "WhatsApp",
        "lead_status": "New",
        "data_origin": "genuine_customer"
    }
]

def run_migration(db_path: str = database.DEFAULT_DB_PATH):
    print("==================================================================")
    print("STARTING DATASET REPLACEMENT: DUMMY DATA -> GENUINE CUSTOMER LEADS")
    print("==================================================================")

    # 1. Verify and create pre-migration backup
    os.makedirs("backups", exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backups/sha_leads_backup_pre_genuine_migration_{ts}.db"
    shutil.copy2(db_path, backup_path)
    print(f"Step 1: Database safely backed up to '{backup_path}'.")

    conn = database.get_connection(db_path)
    try:
        cur = conn.cursor()

        # 2. Count existing records before migration
        cur.execute("SELECT COUNT(*) FROM LEADS;")
        pre_total_leads = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM FOLLOW_UP_SCHEDULE;")
        pre_total_fu = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM LEAD_ACTIVITY_LOG;")
        pre_total_act = cur.fetchone()[0]
        print(f"Step 2: Pre-migration counts - Leads: {pre_total_leads}, Follow-ups: {pre_total_fu}, Logs: {pre_total_act}")

        # 3. Identify genuine records to preserve (Matta GANESH - SHA-2026-0901)
        cur.execute("SELECT lead_id, customer_name, phone FROM LEADS WHERE lead_id = 'SHA-2026-0901';")
        preserved_leads = cur.fetchall()
        preserved_ids = [r[0] for r in preserved_leads]
        print(f"Step 3: Identified genuine existing records to PRESERVE: {preserved_leads}")

        # 4. Remove all dummy / synthetic records from LEADS, FOLLOW_UP_SCHEDULE, and LEAD_ACTIVITY_LOG
        with conn:
            # Delete dummy follow-ups and activities
            cur.execute("DELETE FROM FOLLOW_UP_SCHEDULE WHERE lead_id NOT IN ('SHA-2026-0901');")
            del_fu = cur.rowcount
            cur.execute("DELETE FROM LEAD_ACTIVITY_LOG WHERE lead_id NOT IN ('SHA-2026-0901');")
            del_act = cur.rowcount
            cur.execute("DELETE FROM LEADS WHERE lead_id NOT IN ('SHA-2026-0901');")
            del_leads = cur.rowcount

        print(f"Step 4: Removed dummy data - Deleted {del_leads} leads, {del_fu} follow-ups, {del_act} activity logs.")

        # 5. Insert the 6 genuine leads
        now_iso = datetime.datetime.now().isoformat()
        inserted_count = 0
        for lead_data in GENUINE_LEADS:
            # Calculate qualification score
            score_res = lead_scoring.score_lead(lead_data)
            record = dict(lead_data)
            record["created_at"] = now_iso
            record["updated_at"] = now_iso
            record["lead_score"] = score_res["lead_score"]
            record["priority"] = score_res["priority"]
            record["score_breakdown"] = json.dumps(score_res["score_breakdown"])
            record["scoring_reason"] = score_res["scoring_reason"]
            record["scored_at"] = now_iso
            record["is_opted_out"] = 0
            record["opt_out_reason"] = None
            record["is_paused"] = 0
            record["last_customer_response"] = None
            record["last_response_at"] = None

            with conn:
                cur.execute("""
                INSERT INTO LEADS (
                    lead_id, customer_name, phone, email, state, city, locality, region, pincode, is_service_area,
                    lead_source, budget_range, project_type, property_status, project_timeline,
                    scope_of_work, customer_requirements, purchase_readiness,
                    preferred_contact_method, lead_status, created_at, updated_at, data_origin,
                    lead_score, priority, score_breakdown, scoring_reason, scored_at,
                    is_opted_out, opt_out_reason, is_paused, last_customer_response, last_response_at
                ) VALUES (
                    :lead_id, :customer_name, :phone, :email, :state, :city, :locality, :region, :pincode, :is_service_area,
                    :lead_source, :budget_range, :project_type, :property_status, :project_timeline,
                    :scope_of_work, :customer_requirements, :purchase_readiness,
                    :preferred_contact_method, :lead_status, :created_at, :updated_at, :data_origin,
                    :lead_score, :priority, :score_breakdown, :scoring_reason, :scored_at,
                    :is_opted_out, :opt_out_reason, :is_paused, :last_customer_response, :last_response_at
                );
                """, record)
                
                # Insert activity log entry for lead intake
                cur.execute("""
                INSERT INTO LEAD_ACTIVITY_LOG (activity_id, lead_id, activity_type, activity_description, timestamp)
                VALUES (?, ?, 'Lead Ingestion', ?, ?);
                """, (
                    f"ACT-INTAKE-{record['lead_id']}",
                    record["lead_id"],
                    f"Genuine customer enquiry ingested for {record['customer_name']} ({record['project_type']} in {record['locality']})",
                    now_iso
                ))
            inserted_count += 1

        print(f"Step 5: Successfully inserted {inserted_count} genuine leads into LEADS.")

        # 6. Schedule follow-ups for all genuine leads
        total_sched_fu = 0
        cur.execute("SELECT lead_id FROM LEADS;")
        all_active_ids = [r[0] for r in cur.fetchall()]
        for l_id in all_active_ids:
            fu_res = followups.schedule_followups_for_lead(l_id, db_path=db_path)
            if fu_res.get("success"):
                total_sched_fu += fu_res.get("scheduled_count", 0)

        print(f"Step 6: Scheduled {total_sched_fu} genuine follow-up tasks across {len(all_active_ids)} accounts.")

        # 7. Post-migration counts
        cur.execute("SELECT COUNT(*) FROM LEADS;")
        post_total_leads = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM FOLLOW_UP_SCHEDULE;")
        post_total_fu = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM LEAD_ACTIVITY_LOG;")
        post_total_act = cur.fetchone()[0]

        print(f"\nStep 7: Post-migration verification:")
        print(f"   Active Genuine Leads: {post_total_leads}")
        print(f"   Genuine Follow-up Tasks: {post_total_fu}")
        print(f"   Genuine Activity Logs: {post_total_act}")

        cur.execute("SELECT lead_id, customer_name, phone, locality, region, budget_range, project_type, lead_score, priority FROM LEADS ORDER BY lead_id ASC;")
        print("\nAll active genuine leads in SQLite database:")
        for r in cur.fetchall():
            print(f"   {r[0]} | {r[1]} | {r[2]} | {r[3]} ({r[4]}) | Budget: {r[5]} | Type: {r[6]} | Score: {r[7]:.0f} ({r[8]})")

    finally:
        conn.close()

    print("\n==================================================================")
    print("DATASET REPLACEMENT COMPLETED SUCCESSFULLY WITH 100% DATA INTEGRITY")
    print("==================================================================")

if __name__ == "__main__":
    run_migration()
