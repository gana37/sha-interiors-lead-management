import re
import datetime
import json
from typing import Dict, Tuple, Optional, List, Any
import streamlit as st
import database
import lead_scoring
import hyderabad_geo as hg

def is_valid_indian_phone(phone_str: str) -> bool:
    """
    Validates Indian phone number format.
    Accepts:
    - 10-digit mobile numbers starting with 6, 7, 8, 9
    - Optional prefixes: +91, 0091, 91, or 0
    - Formatted variants with spaces, hyphens, or parentheses
    - Test series numbers (e.g. +91 91234 XXXXX)
    """
    if not phone_str:
        return False
    cleaned = re.sub(r"[\s\-\(\)\.]", "", phone_str.strip())
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("0091"):
        cleaned = cleaned[4:]
    elif cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    elif cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = cleaned[1:]
    return len(cleaned) == 10 and cleaned.isdigit() and (cleaned[0] in "6789" or cleaned.startswith("91234"))

# Standard RFC 5322 compliant email pattern
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

CITY_OPTIONS = ["Hyderabad", "Secunderabad", "Greater Hyderabad", "Cyberabad", "Other"]
LEAD_SOURCE_OPTIONS = [
    "Website Inquiry", "Instagram Ad", "Google Search", "Architect Referral",
    "Past Client Referral", "Walk-in Studio", "Facebook Campaign", "Housing Portal", "Direct Walk-in"
]
BUDGET_OPTIONS = [
    "Below ₹3 lakh", "₹3 lakh–₹5 lakh", "₹5 lakh–₹10 lakh", "₹10 lakh–₹25 lakh", "Above ₹25 lakh"
]
PROJECT_TYPE_OPTIONS = ["1BHK", "2BHK", "3BHK", "4BHK", "Villa", "Modular Kitchen", "Commercial/Office"]
PROPERTY_STATUS_OPTIONS = [
    "Ready to Move", "Possession within 30 days", "Possession within 1–3 months", "Under Construction"
]
TIMELINE_OPTIONS = [
    "Immediately", "Within 1 month", "Within 3 months", "Within 6 months", "Just Exploring"
]
SCOPE_OPTIONS = [
    "Full Turnkey Interior", "Modular Kitchen", "Wardrobe", "Renovation",
    "Furniture and Woodwork", "Commercial Interiors"
]
READINESS_OPTIONS = [
    "Ready to Start", "Comparing Vendors", "Budget Planning", "Just Exploring"
]
CONTACT_METHOD_OPTIONS = ["Phone Call", "WhatsApp", "Email", "In-Person Consultation"]

def validate_lead_inputs(
    customer_name: str,
    phone: str,
    email: Optional[str],
    city: str,
    budget_range: str,
    project_type: str,
    property_status: str,
    project_timeline: str,
    scope_of_work: str,
    purchase_readiness: str,
    locality: Optional[str] = None,
    pincode: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """Validates manual form inputs. Returns (is_valid, list_of_error_messages)."""
    errors = []
    
    # 1. Customer Name validation
    cleaned_name = (customer_name or "").strip()
    if not cleaned_name:
        errors.append("Customer Name is required and cannot be empty.")
    elif len(cleaned_name) < 2:
        errors.append("Customer Name must be at least 2 characters long.")
        
    # 2. Phone validation
    cleaned_phone = (phone or "").strip()
    if not cleaned_phone:
        errors.append("Phone Number is required.")
    elif not is_valid_indian_phone(cleaned_phone):
        errors.append("Invalid phone number format. Please provide a valid 10-digit Indian mobile number (e.g. +91 98765 43210 or 9876543210).")
        
    # 3. Email validation (Optional, but if provided must be valid)
    cleaned_email = (email or "").strip()
    if cleaned_email and not EMAIL_REGEX.match(cleaned_email):
        errors.append("Invalid email address format (e.g., client@example.com).")
        
    # 4. Mandatory project details
    if not city:
        errors.append("City is required.")
    if not budget_range:
        errors.append("Budget Range is required.")
    if not project_type:
        errors.append("Project Type is required.")
    if not property_status:
        errors.append("Property Status is required.")
    if not project_timeline:
        errors.append("Project Timeline is required.")
    if not scope_of_work:
        errors.append("Scope of Work is required.")
    if not purchase_readiness:
        errors.append("Purchase Readiness is required.")
        
    return (len(errors) == 0, errors)

def create_manual_lead(
    lead_data: Dict[str, Any],
    db_path: str = database.DEFAULT_DB_PATH,
    return_score: bool = False
) -> Any:
    """
    Validates, calculates initial AI lead score, and persists a manual enquiry into SQLite.
    If return_score is False (default): returns (success, message, lead_id) for backwards compatibility.
    If return_score is True: returns (success, message, lead_id, scoring_result).
    """
    is_valid, errors = validate_lead_inputs(
        customer_name=lead_data.get("customer_name", ""),
        phone=lead_data.get("phone", ""),
        email=lead_data.get("email"),
        city=lead_data.get("city", ""),
        budget_range=lead_data.get("budget_range", ""),
        project_type=lead_data.get("project_type", ""),
        property_status=lead_data.get("property_status", ""),
        project_timeline=lead_data.get("project_timeline", ""),
        scope_of_work=lead_data.get("scope_of_work", ""),
        purchase_readiness=lead_data.get("purchase_readiness", "")
    )
    
    if not is_valid:
        msg = "Validation failed: " + "; ".join(errors)
        if return_score:
            return False, msg, None, None
        return False, msg, None

    # Generate unique lead ID
    lead_id = database.generate_next_lead_id(prefix="SHA", db_path=db_path)
    now = datetime.datetime.now().isoformat()
    
    # Pre-calculate lead score
    scoring_res = lead_scoring.score_lead(lead_data)
    
    loc = (lead_data.get("locality") or "").strip() or None
    reg = (lead_data.get("region") or "").strip() or (hg.get_region_for_locality(loc) if loc else None)
    pin = (lead_data.get("pincode") or "").strip() or (hg.get_pincode_for_locality(loc) if loc else None)
    c_city = lead_data["city"].strip()
    is_serv = 1 if hg.is_hyderabad_service_area(c_city) else 0

    lead_record = {
        "lead_id": lead_id,
        "customer_name": lead_data["customer_name"].strip(),
        "phone": lead_data["phone"].strip(),
        "email": (lead_data.get("email") or "").strip() or None,
        "state": (lead_data.get("state") or "Telangana").strip(),
        "city": c_city,
        "locality": loc,
        "region": reg,
        "pincode": pin,
        "is_service_area": is_serv,
        "lead_source": lead_data.get("lead_source", "Website Inquiry").strip(),
        "budget_range": lead_data["budget_range"].strip(),
        "project_type": lead_data["project_type"].strip(),
        "property_status": lead_data["property_status"].strip(),
        "project_timeline": lead_data["project_timeline"].strip(),
        "scope_of_work": lead_data["scope_of_work"].strip(),
        "customer_requirements": (lead_data.get("customer_requirements") or "").strip() or None,
        "purchase_readiness": lead_data["purchase_readiness"].strip(),
        "preferred_contact_method": lead_data.get("preferred_contact_method", "Phone Call").strip(),
        "lead_status": "New",
        "created_at": now,
        "updated_at": now,
        "data_origin": "manual_entry",
        "lead_score": scoring_res["lead_score"],
        "priority": scoring_res["priority"],
        "score_breakdown": json.dumps(scoring_res["score_breakdown"]),
        "scoring_reason": scoring_res["scoring_reason"],
        "scored_at": now
    }
    
    try:
        database.insert_lead(lead_record, db_path=db_path)
        success_msg = f"Lead successfully captured with ID {lead_id}"
        if return_score:
            return True, success_msg, lead_id, scoring_res
        return True, success_msg, lead_id
    except Exception as e:
        err_msg = f"Database error while saving lead: {str(e)}"
        if return_score:
            return False, err_msg, None, None
        return False, err_msg, None

def render_lead_capture_form(db_path: str = database.DEFAULT_DB_PATH):
    """Renders the Streamlit form for Add New Customer Enquiry (Hyderabad Edition)."""
    st.subheader("Add New Customer Enquiry – Hyderabad Metropolitan Area")
    st.caption("Capture, locate, and qualify incoming customer enquiries across Hyderabad, Secunderabad, and surrounding regions.")

    with st.form("manual_lead_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 👤 Customer Information")
            cust_name = st.text_input("Customer Name *", placeholder="e.g. Aditi Hegde")
            phone = st.text_input("Phone Number *", placeholder="e.g. +91 98765 43210")
            email = st.text_input("Email Address (Optional)", placeholder="e.g. aditi.hegde@example.com")
            
            c_sub1, c_sub2 = st.columns(2)
            with c_sub1:
                city = st.selectbox("City *", options=CITY_OPTIONS, index=0)
            with c_sub2:
                state_val = st.text_input("State", value="Telangana", disabled=True)
                
            all_locs = hg.get_all_localities()
            loc_options = ["-- Select Locality --"] + all_locs + ["+ Add Custom Locality..."]
            sel_loc = st.selectbox("Hyderabad Locality / Sector *", options=loc_options, index=1)
            
            custom_loc_input = ""
            custom_region_input = ""
            if sel_loc == "+ Add Custom Locality...":
                custom_loc_input = st.text_input("Enter New Locality Name *", placeholder="e.g. Puppalaguda")
                custom_region_input = st.selectbox("Assign Region *", options=hg.HYDERABAD_REGIONS, index=0)
                final_locality = custom_loc_input.strip()
                if final_locality:
                    hg.register_custom_locality(final_locality, custom_region_input)
            elif sel_loc != "-- Select Locality --":
                final_locality = sel_loc
            else:
                final_locality = ""
                
            pincode_auto = hg.get_pincode_for_locality(final_locality) if final_locality else ""
            pincode_val = st.text_input("Postal PIN Code (Optional)", value=pincode_auto, placeholder="e.g. 500032")
            
            lead_source = st.selectbox("Lead Source *", options=LEAD_SOURCE_OPTIONS, index=0)
            preferred_contact = st.selectbox("Preferred Contact Method *", options=CONTACT_METHOD_OPTIONS, index=0)
            
        with col2:
            st.markdown("##### 🏡 Project Specifications")
            project_type = st.selectbox("Project Type *", options=PROJECT_TYPE_OPTIONS, index=1)
            budget_range = st.selectbox("Budget Range *", options=BUDGET_OPTIONS, index=2)
            property_status = st.selectbox("Property Status *", options=PROPERTY_STATUS_OPTIONS, index=0)
            project_timeline = st.selectbox("Project Timeline *", options=TIMELINE_OPTIONS, index=1)
            scope_of_work = st.selectbox("Scope of Work *", options=SCOPE_OPTIONS, index=0)
            purchase_readiness = st.selectbox("Purchase Readiness *", options=READINESS_OPTIONS, index=0)

        st.markdown("##### 📝 Requirements & Notes")
        cust_requirements = st.text_area(
            "Customer Requirements / Notes (Optional)",
            placeholder="e.g. Modern minimalist design with false ceiling, acrylic modular kitchen, and kids bedroom study unit.",
            height=100
        )
        
        # Check potential duplicate contact before submission
        if phone:
            duplicates = database.check_duplicate_contact(phone, email=email, db_path=db_path)
            if duplicates:
                st.warning(
                    f"⚠️ Notice: The phone/email entered matches existing lead records in the CRM: "
                    f"**{', '.join([d['lead_id'] + ' (' + d['customer_name'] + ')' for d in duplicates])}**. "
                    f"You may still proceed if this is an updated enquiry or new project."
                )

        submit_btn = st.form_submit_button("Submit & Save Customer Enquiry", type="primary", use_container_width=True)
        
        if submit_btn:
            lead_payload = {
                "customer_name": cust_name,
                "phone": phone,
                "email": email,
                "state": "Telangana",
                "city": city,
                "locality": final_locality,
                "region": hg.get_region_for_locality(final_locality) if final_locality else "Unspecified Hyderabad",
                "pincode": pincode_val,
                "lead_source": lead_source,
                "budget_range": budget_range,
                "project_type": project_type,
                "property_status": property_status,
                "project_timeline": project_timeline,
                "scope_of_work": scope_of_work,
                "customer_requirements": cust_requirements,
                "purchase_readiness": purchase_readiness,
                "preferred_contact_method": preferred_contact
            }
            
            success, msg, new_id, score_data = create_manual_lead(lead_payload, db_path=db_path, return_score=True)
            if success:
                st.success(f"🎉 **{msg}**")
                
                # Show AI qualification card
                if score_data:
                    p = score_data["priority"]
                    badge_color = "#10B981" if p == "High" else "#F59E0B" if p == "Medium" else "#EF4444"
                    st.markdown(f"""
                    <div style="background-color: #F8FAFC; border-left: 5px solid {badge_color}; padding: 12px; border-radius: 6px; margin: 10px 0;">
                        <h4 style="margin: 0; color: #1E293B;">AI Qualification: <span style="color: {badge_color};">{p} Priority</span> (Score: {score_data['lead_score']:.0f}/100)</h4>
                        <p style="margin: 5px 0 0 0; color: #475569; font-size: 0.95rem;">{score_data['scoring_reason']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.info(
                    f"**Lead Details:** {cust_name} | {city} | {project_type} | {budget_range} | Status: **New** (Origin: manual_entry)"
                )
            else:
                st.error(f"❌ {msg}")
