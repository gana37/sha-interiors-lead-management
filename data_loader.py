import pandas as pd
import os
import re
import datetime
from typing import Dict, List, Tuple, Any, Optional
import database
import estimate_parser

# Mandatory fields required for an Interior Design lead
REQUIRED_COLUMNS = [
    "Customer_Name",
    "Phone",
    "City",
    "Budget_Range",
    "Project_Type",
    "Property_Status",
    "Project_Timeline",
    "Scope_of_Work",
    "Purchase_Readiness"
]

# Standard allowed categories for validation
VALID_BUDGETS = {
    "Below ₹3 lakh", "₹3 lakh–₹5 lakh", "₹5 lakh–₹10 lakh", "₹10 lakh–₹25 lakh", "Above ₹25 lakh"
}

VALID_PROJECT_TYPES = {
    "1BHK", "2BHK", "3BHK", "4BHK", "Villa", "Modular Kitchen", "Commercial/Office"
}

VALID_PROPERTY_STATUSES = {
    "Ready to Move", "Possession within 30 days", "Possession within 1–3 months", "Under Construction"
}

VALID_TIMELINES = {
    "Immediately", "Within 1 month", "Within 3 months", "Within 6 months", "Just Exploring"
}

VALID_SCOPES = {
    "Full Turnkey Interior", "Modular Kitchen", "Wardrobe", "Renovation", 
    "Furniture and Woodwork", "Commercial Interiors"
}

VALID_READINESS = {
    "Ready to Start", "Comparing Vendors", "Budget Planning", "Just Exploring"
}

def is_education_dataset(df: pd.DataFrame) -> bool:
    """Detects if the user is attempting to upload the legacy education dataset (Leads.csv)."""
    education_markers = ["Specialization", "Total Time Spent on Website", "Lead Origin", "How did you hear about X Education"]
    matching = sum(1 for col in education_markers if col in df.columns)
    return matching >= 2

def validate_and_prepare_csv(
    file_or_path: Any,
    db_path: str = database.DEFAULT_DB_PATH,
    data_origin: str = "synthetic_import"
) -> Dict[str, Any]:
    """
    Parses, validates, and prepares CSV records for database ingestion.
    Returns a comprehensive validation report including clean records to insert
    and detailed reasons for any skipped/rejected rows.
    """
    try:
        if isinstance(file_or_path, str):
            if file_or_path.lower().endswith((".xlsx", ".xls")):
                df = pd.read_excel(file_or_path)
            else:
                df = pd.read_csv(file_or_path)
        else:
            filename = getattr(file_or_path, "name", "").lower()
            if filename.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file_or_path)
            else:
                try:
                    df = pd.read_csv(file_or_path)
                except Exception:
                    file_or_path.seek(0)
                    df = pd.read_excel(file_or_path)
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Unable to read file (CSV/Excel): {str(e)}",
            "total_rows": 0,
            "valid_records": [],
            "skipped_records": [],
            "validation_warnings": []
        }

    # Guard against importing legacy education dataset into CRM
    if is_education_dataset(df):
        return {
            "success": False,
            "error_message": (
                "Guardrail Triggered: The uploaded file appears to be the legacy Education dataset "
                "('Leads.csv'). To maintain data integrity, education records must not be imported "
                "into the active Interior Design CRM."
            ),
            "total_rows": len(df),
            "valid_records": [],
            "skipped_records": []
        }

    # Check for missing required columns (case-insensitive column mapping)
    col_mapping = {}
    for col in df.columns:
        norm = col.strip().lower()
        for req in REQUIRED_COLUMNS:
            norm_under = norm.replace(" ", "_")
            if norm == req.lower() or norm_under == req.lower() or (req == "Project_Timeline" and norm in ("timeline", "project timeline")):
                col_mapping[req] = col
                break
                
    missing_required_cols = [req for req in REQUIRED_COLUMNS if req not in col_mapping]
    if missing_required_cols:
        return {
            "success": False,
            "error_message": f"CSV missing required columns: {', '.join(missing_required_cols)}",
            "total_rows": len(df),
            "valid_records": [],
            "skipped_records": []
        }

    # Existing lead IDs in the database to prevent duplicate keys
    existing_db_ids = database.get_existing_lead_ids(db_path)
    
    seen_csv_lead_ids = set()
    valid_records = []
    skipped_records = []
    validation_warnings = []
    decoded_refs_count = 0
    missing_refs_count = 0
    invalid_refs_count = 0

    # Locate optional Lead_Reference column (case-insensitive)
    ref_col = None
    for c in df.columns:
        norm_c = c.strip().lower()
        if norm_c in ("lead_reference", "estimate_reference", "reference_id", "lead_ref", "reference"):
            ref_col = c
            break
    
    now_str = datetime.datetime.now().isoformat()
    auto_id_counter = 1

    for idx, row in df.iterrows():
        row_num = idx + 2 # 1-based index including header
        row_errors = []
        
        # 1. Customer Name check
        cust_name = str(row.get(col_mapping["Customer_Name"], "")).strip()
        if not cust_name or cust_name.lower() in ["nan", "none", ""]:
            row_errors.append("Customer_Name is empty or missing")
            
        # 2. Phone check
        phone_val = str(row.get(col_mapping["Phone"], "")).strip()
        if not phone_val or phone_val.lower() in ["nan", "none", ""]:
            row_errors.append("Phone is missing")
            
        # 3. Required categorical fields check
        for req in ["City", "Budget_Range", "Project_Type", "Property_Status", "Project_Timeline", "Scope_of_Work", "Purchase_Readiness"]:
            val = str(row.get(col_mapping[req], "")).strip()
            if not val or val.lower() in ["nan", "none", ""]:
                row_errors.append(f"{req} is missing")

        # 4. Lead ID handling & duplicate check
        raw_lead_id = str(row.get("Lead_ID", "")).strip() if "Lead_ID" in df.columns else ""
        if raw_lead_id and raw_lead_id.lower() not in ["nan", "none", ""]:
            lead_id = raw_lead_id
            if lead_id in seen_csv_lead_ids:
                row_errors.append(f"Duplicate Lead_ID '{lead_id}' within CSV file")
            elif lead_id in existing_db_ids:
                row_errors.append(f"Lead_ID '{lead_id}' already exists in SQLite database")
            seen_csv_lead_ids.add(lead_id)
        else:
            # Auto-generate temporary unique ID if absent
            lead_id = f"SHA-AUTO-{auto_id_counter:04d}"
            while lead_id in existing_db_ids or lead_id in seen_csv_lead_ids:
                auto_id_counter += 1
                lead_id = f"SHA-AUTO-{auto_id_counter:04d}"
            seen_csv_lead_ids.add(lead_id)
            auto_id_counter += 1

        if row_errors:
            skipped_records.append({
                "row_number": row_num,
                "lead_id": lead_id,
                "customer_name": cust_name or "N/A",
                "phone": phone_val or "N/A",
                "reasons": "; ".join(row_errors)
            })
        else:
            # Safe parsing of optional fields
            email_val = str(row.get("Email", "")).strip() if "Email" in df.columns else ""
            if email_val.lower() in ["nan", "none"]:
                email_val = None
                
            lead_source = str(row.get("Lead_Source", "Website Inquiry")).strip() if "Lead_Source" in df.columns else "Website Inquiry"
            if lead_source.lower() in ["nan", "none", ""]:
                lead_source = "Website Inquiry"
                
            reqs = str(row.get("Customer_Requirements", "")).strip() if "Customer_Requirements" in df.columns else ""
            if reqs.lower() in ["nan", "none"]:
                reqs = None
                
            contact_method = str(row.get("Preferred_Contact_Method", "Phone Call")).strip() if "Preferred_Contact_Method" in df.columns else "Phone Call"
            if contact_method.lower() in ["nan", "none", ""]:
                contact_method = "Phone Call"
                
            lead_status = str(row.get("Lead_Status", "New")).strip() if "Lead_Status" in df.columns else "New"
            if lead_status.lower() in ["nan", "none", ""]:
                lead_status = "New"
                
            created_date = str(row.get("Created_Date", now_str)).strip() if "Created_Date" in df.columns else now_str
            if created_date.lower() in ["nan", "none", ""]:
                created_date = now_str
                
            # Lead Reference & Estimate Datetime extraction
            lead_ref = None
            est_generated_at = None
            if ref_col and pd.notnull(row.get(ref_col)):
                raw_ref = str(row.get(ref_col, "")).strip()
                if raw_ref and raw_ref.lower() not in ("nan", "none", "null", "—", "-"):
                    lead_ref = raw_ref
                    dt_obj, iso_str, warning_msg = estimate_parser.parse_estimate_reference(lead_ref)
                    if iso_str:
                        est_generated_at = iso_str
                        decoded_refs_count += 1
                    else:
                        invalid_refs_count += 1
                        validation_warnings.append({
                            "row_number": row_num,
                            "lead_id": lead_id,
                            "customer_name": cust_name,
                            "lead_reference": lead_ref,
                            "warning": warning_msg
                        })
                else:
                    missing_refs_count += 1
            else:
                missing_refs_count += 1

            record = {
                "lead_id": lead_id,
                "customer_name": cust_name,
                "phone": phone_val,
                "email": email_val,
                "city": str(row[col_mapping["City"]]).strip(),
                "lead_source": lead_source,
                "budget_range": str(row[col_mapping["Budget_Range"]]).strip(),
                "project_type": str(row[col_mapping["Project_Type"]]).strip(),
                "property_status": str(row[col_mapping["Property_Status"]]).strip(),
                "project_timeline": str(row[col_mapping["Project_Timeline"]]).strip(),
                "scope_of_work": str(row[col_mapping["Scope_of_Work"]]).strip(),
                "customer_requirements": reqs,
                "purchase_readiness": str(row[col_mapping["Purchase_Readiness"]]).strip(),
                "preferred_contact_method": contact_method,
                "lead_status": lead_status,
                "created_at": created_date,
                "updated_at": now_str,
                "data_origin": data_origin,
                "lead_reference": lead_ref,
                "estimate_generated_at": est_generated_at
            }
            valid_records.append(record)

    return {
        "success": True,
        "error_message": None,
        "total_rows": len(df),
        "valid_count": len(valid_records),
        "skipped_count": len(skipped_records),
        "valid_records": valid_records,
        "skipped_records": skipped_records,
        "validation_warnings": validation_warnings,
        "decoded_refs_count": decoded_refs_count,
        "missing_refs_count": missing_refs_count,
        "invalid_refs_count": invalid_refs_count
    }

def import_csv_to_db(
    file_or_path: Any,
    db_path: str = database.DEFAULT_DB_PATH,
    data_origin: str = "synthetic_import"
) -> Dict[str, Any]:
    """
    Executes an atomic database import of a validated CSV file.
    Uses an SQLite transaction: if any error occurs during insertion, all records are rolled back.
    """
    validation_res = validate_and_prepare_csv(file_or_path, db_path=db_path, data_origin=data_origin)
    if not validation_res["success"]:
        return validation_res

    valid_records = validation_res["valid_records"]
    if not valid_records:
        return {
            "success": True,
            "total_rows": validation_res["total_rows"],
            "imported_count": 0,
            "skipped_count": validation_res["skipped_count"],
            "skipped_records": validation_res["skipped_records"],
            "message": "No new valid records to import."
        }

    try:
        # Atomic batch insertion
        inserted_count = database.batch_insert_leads(valid_records, db_path=db_path)
        return {
            "success": True,
            "total_rows": validation_res["total_rows"],
            "imported_count": inserted_count,
            "skipped_count": validation_res["skipped_count"],
            "skipped_records": validation_res["skipped_records"],
            "message": f"Successfully imported {inserted_count} leads into SQLite database."
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Database transaction failed and was rolled back: {str(e)}",
            "total_rows": validation_res["total_rows"],
            "imported_count": 0,
            "skipped_count": validation_res["total_rows"],
            "skipped_records": []
        }


def import_excel_to_db(
    file_or_path: Any,
    db_path: str = database.DEFAULT_DB_PATH,
    data_origin: str = "excel_import"
) -> Dict[str, Any]:
    """Convenience wrapper to import an Excel workbook into the leads database."""
    return import_csv_to_db(file_or_path, db_path=db_path, data_origin=data_origin)
