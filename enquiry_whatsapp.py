"""
enquiry_whatsapp.py - Website Enquiry WhatsApp Outbound Feature
SHA Interface Interiors - AI-Powered Lead Management System

Provides:
1. Dynamic, professional WhatsApp introduction message generation from actual website enquiry / CRM data.
2. Official Click-to-Chat URL generation (https://wa.me/<countrycode><number>?text=<url_encoded_message>).
3. Indian phone number validation and normalization.
4. Conversation tracking in CUSTOMER_CONVERSATIONS with strict status lifecycles:
   - 'Draft'
   - 'Ready to Send'
   - 'User-Confirmed Sent'
   - 'Cancelled'
5. Deduplication safeguards preventing duplicate conversation rows on multiple preview opens.
6. Integration with LEAD_ACTIVITY_LOG for audit trails upon manual salesperson confirmation.
"""

import os
import sys
import re
import urllib.parse
import datetime
import json
from typing import Dict, List, Optional, Tuple, Any

import database
import whatsapp_assistant
import estimate_parser
import business_config


DEFAULT_TEMPLATE = f"""Hello {{customer_name}},

Greetings from {business_config.BUSINESS_NAME}!

Thank you for expressing your interest in our interior design services. We have received your enquiry regarding {{customer_requirement}} for your {{property_configuration}} property in {{locality}}, Hyderabad.

We would be delighted to assist you in bringing your vision to life.

We would be happy to arrange a meeting at our {business_config.OFFICE_NAME} or schedule a convenient phone call to understand your requirements in more detail and discuss the next steps.

Please let us know your preferred option and a suitable time between {business_config.APPOINTMENT_HOURS_START} and {business_config.APPOINTMENT_HOURS_END} IST (available Monday through Sunday).

We look forward to connecting with you.

Warm regards,
Team {business_config.BUSINESS_NAME}"""


def format_customer_requirement(lead: Dict[str, Any]) -> str:
    """
    Extracts and dynamically formats the customer's actual submitted requirements.
    Preserves exact specifications (modular kitchen, wardrobes, etc.) without inventing facts.
    Omits private CRM notes, venture names, estimates, and lead scores.
    """
    scope = (lead.get("scope_of_work") or "").strip()
    raw_req = (lead.get("customer_requirements") or "").strip()
    
    # Clean scope prefix
    scope_clean = scope
    if scope_clean.lower().endswith(" design"):
        scope_clean = scope_clean[:-7].strip()
    if scope_clean.lower() == "full turnkey interior":
        scope_clean = "full turnkey home interiors"
        
    items = []
    if raw_req:
        lines = raw_req.split("\n")
        for line in lines:
            line = line.strip().lstrip("-*•0123456789. ")
            if not line:
                continue
            # Stop if reached preferences or private CRM metadata
            if any(term in line.lower() for term in ("preference", "venture:", "ref:", "budget:", "timeline:", "status:", "estimated")):
                break
            line_clean = line.lower()
            if "modular kitchen" in line_clean:
                items.append("modular kitchen")
            elif "sliding wardrobe" in line_clean:
                items.append("sliding wardrobes")
            elif "bedroom wardrobe" in line_clean or "wardrobe" in line_clean:
                if "wardrobes" not in items and "sliding wardrobes" not in items:
                    items.append("wardrobes")
            elif "tv unit" in line_clean:
                items.append("TV unit")
            elif "false ceiling" in line_clean:
                items.append("false ceiling")
            elif "space-saving storage" in line_clean or "storage" in line_clean:
                items.append("storage solutions")
            elif "kitchen cabinet" in line_clean:
                if "modular kitchen" not in items:
                    items.append("kitchen cabinets")
            elif "lighting" in line_clean:
                items.append("lighting design")
            else:
                items.append(line)
                
    # Deduplicate preserving order
    seen = set()
    dedup_items = []
    for item in items:
        if item.lower() not in seen:
            seen.add(item.lower())
            dedup_items.append(item)
            
    # Combine scope and extracted items
    if scope_clean and dedup_items:
        key_items = dedup_items[:4]
        if len(key_items) == 1:
            items_str = key_items[0]
        elif len(key_items) == 2:
            items_str = f"{key_items[0]} and {key_items[1]}"
        else:
            items_str = f"{', '.join(key_items[:-1])}, and {key_items[-1]}"
            
        if scope_clean.lower() in ("complete home interiors", "complete home interior"):
            return f"complete home interiors (including {items_str})"
        else:
            return f"{scope_clean.lower()} (including {items_str})"
    elif scope_clean:
        return scope_clean.lower()
    elif dedup_items:
        key_items = dedup_items[:4]
        if len(key_items) == 1:
            return key_items[0]
        elif len(key_items) == 2:
            return f"{key_items[0]} and {key_items[1]}"
        else:
            return f"{', '.join(key_items[:-1])}, and {key_items[-1]}"
    else:
        return "interior design services"


def generate_enquiry_message(lead: Dict[str, Any], include_date: bool = False) -> str:
    """
    Generates a personalized, professional first outbound WhatsApp message
    grounded in the customer's actual submitted enquiry.
    
    Adheres strictly to safety and privacy rules:
    - Zero private CRM notes, scores, or budgets exposed.
    - Gracefully handles missing names, locations, or configurations.
    """
    # 1. Customer Name
    name = (lead.get("customer_name") or "").strip()
    name_salutation = name if name else "there"
    
    # 2. Submitted Requirement
    req_str = format_customer_requirement(lead)
    
    # 3. Property Configuration
    p_config = (lead.get("project_type") or "").strip()
    
    # 4. Locality
    locality = (lead.get("locality") or "").strip()
    
    # 5. Enquiry Date (optional)
    date_phrase = ""
    if include_date:
        enq_date_raw = lead.get("estimate_generated_at") or lead.get("created_at")
        if enq_date_raw:
            try:
                dt = datetime.datetime.fromisoformat(str(enq_date_raw).replace(" ", "T"))
                date_phrase = f" received on {dt.strftime('%d %B %Y')}"
            except Exception:
                pass

    # Build the acknowledgement sentence with natural grammar
    # Target: "We have received your enquiry regarding {{customer_requirement}} for your {{property_configuration}} property in {{locality}}, Hyderabad."
    
    # Property configuration clause
    if p_config:
        prop_clause = f" for your {p_config} property"
    else:
        prop_clause = " for your property"
        
    # Location clause
    if locality and locality.lower() not in ("hyderabad", "telangana", "unknown"):
        loc_clause = f" in {locality}, Hyderabad"
    else:
        loc_clause = " in Hyderabad"

    msg = f"""Hello {name_salutation},

Greetings from {business_config.BUSINESS_NAME}!

Thank you for expressing your interest in our interior design services. We have received your enquiry{date_phrase} regarding {req_str}{prop_clause}{loc_clause}.

We would be delighted to assist you in bringing your vision to life.

We would be happy to arrange a meeting at our {business_config.OFFICE_NAME} or schedule a convenient phone call to understand your requirements in more detail and discuss the next steps.

Please let us know your preferred option and a suitable time between {business_config.APPOINTMENT_HOURS_START} and {business_config.APPOINTMENT_HOURS_END} IST (available Monday through Sunday).

We look forward to connecting with you.

Warm regards,
Team {business_config.BUSINESS_NAME}"""

    return msg.strip()


def build_enquiry_click_to_chat_url(phone_raw: Optional[str], message_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Generates the official WhatsApp Click-to-Chat URL:
    https://wa.me/<countrycode><number>?text=<url_encoded_message>
    
    Validates Indian phone numbers (10 digits, +91, 0 prefix, etc.).
    Returns (url, None) on success, or (None, error_message) on failure.
    """
    normalized_phone = whatsapp_assistant.normalize_whatsapp_phone(phone_raw)
    if not normalized_phone:
        return None, f"Invalid Indian phone number: '{phone_raw}'. Must be a valid 10-digit Indian mobile number."
        
    encoded_text = urllib.parse.quote(message_text.strip())
    url = f"https://wa.me/{normalized_phone}?text={encoded_text}"
    return url, None


# -------------------------------------------------------------
# CONVERSATION TRACKING & DEDUPLICATION IN CUSTOMER_CONVERSATIONS
# -------------------------------------------------------------

def get_or_create_enquiry_draft(
    lead_id: str,
    message_content: str,
    db_path: str = database.DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """
    Retrieves an existing 'Draft' or 'Ready to Send' enquiry message for this lead,
    or creates a new record if none exists.
    
    Prevents duplicate conversation entries when a user opens the preview multiple times.
    """
    database.init_db(db_path)
    conn = database.get_connection(db_path)
    try:
        cursor = conn.cursor()
        # Check for active non-finalized draft
        cursor.execute("""
            SELECT * FROM CUSTOMER_CONVERSATIONS
            WHERE lead_id = ? 
              AND direction = 'outgoing'
              AND channel = 'WhatsApp'
              AND sending_status IN ('Draft', 'Ready to Send')
            ORDER BY created_at DESC
            LIMIT 1;
        """, (lead_id,))
        row = cursor.fetchone()
        
        now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if row:
            conv_id = row["conversation_id"]
            # Update existing draft with latest message content
            cursor.execute("""
                UPDATE CUSTOMER_CONVERSATIONS
                SET message_content = ?,
                    created_at = ?
                WHERE conversation_id = ?;
            """, (message_content.strip(), now_iso, conv_id))
            conn.commit()
            
            return {
                "conversation_id": conv_id,
                "lead_id": lead_id,
                "message_id": row["message_id"],
                "direction": "outgoing",
                "channel": "WhatsApp",
                "message_content": message_content.strip(),
                "approval_status": row["approval_status"],
                "sending_status": row["sending_status"],
                "sent_at": row["sent_at"],
                "created_at": now_iso,
                "is_existing": True
            }
        else:
            # Create fresh draft
            meta = {"message_type": "enquiry_introduction", "created_via": "crm_send_enquiry_button"}
            res = database.add_conversation_message(
                lead_id=lead_id,
                direction="outgoing",
                message_content=message_content.strip(),
                channel="WhatsApp",
                approval_status="Draft",
                sending_status="Draft",
                metadata=meta,
                db_path=db_path
            )
            res["is_existing"] = False
            return res
    finally:
        conn.close()


def update_enquiry_message_status(
    conversation_id: str,
    new_status: str,
    lead_id: Optional[str] = None,
    edited_message: Optional[str] = None,
    db_path: str = database.DEFAULT_DB_PATH
) -> bool:
    """
    Updates the lifecycle status of an enquiry message:
    - 'Draft'
    - 'Ready to Send'
    - 'User-Confirmed Sent'
    - 'Cancelled'
    
    When marked 'User-Confirmed Sent', logs an activity record into LEAD_ACTIVITY_LOG.
    """
    valid_statuses = ("Draft", "Ready to Send", "User-Confirmed Sent", "Cancelled")
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status '{new_status}'. Must be one of {valid_statuses}")
        
    database.init_db(db_path)
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = database.get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            
            # Fetch current record for lead_id and content
            cursor.execute("SELECT lead_id, message_content FROM CUSTOMER_CONVERSATIONS WHERE conversation_id = ?;", (conversation_id,))
            row = cursor.fetchone()
            if not row:
                return False
                
            actual_lead_id = lead_id or row["lead_id"]
            
            fields = ["sending_status = ?"]
            params: List[Any] = [new_status]
            
            if new_status == "User-Confirmed Sent":
                fields.append("sent_at = ?")
                params.append(now_iso)
                fields.append("approval_status = ?")
                params.append("Approved")
            elif new_status == "Ready to Send":
                fields.append("approval_status = ?")
                params.append("Approved")
            elif new_status == "Cancelled":
                fields.append("approval_status = ?")
                params.append("Rejected")
                
            if edited_message is not None:
                fields.append("message_content = ?")
                params.append(edited_message.strip())
                
            params.append(conversation_id)
            cursor.execute(f"UPDATE CUSTOMER_CONVERSATIONS SET {', '.join(fields)} WHERE conversation_id = ?;", params)
            
            # Audit log on User-Confirmed Sent
            if new_status == "User-Confirmed Sent":
                act_id = f"ACT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(2).hex()}"
                cursor.execute("""
                    INSERT INTO LEAD_ACTIVITY_LOG (activity_id, lead_id, activity_type, activity_description, timestamp)
                    VALUES (?, ?, ?, ?, ?);
                """, (act_id, actual_lead_id, "WhatsApp Enquiry Message Sent", "Salesperson confirmed WhatsApp introduction message sent to customer via Click-to-Chat.", now_iso))
                
            elif new_status == "Cancelled":
                act_id = f"ACT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(2).hex()}"
                cursor.execute("""
                    INSERT INTO LEAD_ACTIVITY_LOG (activity_id, lead_id, activity_type, activity_description, timestamp)
                    VALUES (?, ?, ?, ?, ?);
                """, (act_id, actual_lead_id, "WhatsApp Enquiry Message Cancelled", "Salesperson cancelled the drafted WhatsApp introduction message.", now_iso))
                
        return True
    finally:
        conn.close()


def get_latest_enquiry_message(
    lead_id: str,
    db_path: str = database.DEFAULT_DB_PATH
) -> Optional[Dict[str, Any]]:
    """Retrieves the most recent enquiry introduction message record for a lead."""
    database.init_db(db_path)
    conn = database.get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM CUSTOMER_CONVERSATIONS
            WHERE lead_id = ? 
              AND direction = 'outgoing'
              AND channel = 'WhatsApp'
            ORDER BY created_at DESC
            LIMIT 1;
        """, (lead_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def render_enquiry_message_ui(lead: Dict[str, Any], key_prefix: str = "enq"):
    """
    Renders the 'Send Enquiry Message' button and interactive preview card in Streamlit.
    Allows viewing, editing, launching WhatsApp Click-to-Chat, and confirming sent status.
    """
    import streamlit as st
    
    lead_id = lead.get("lead_id")
    if not lead_id:
        return
        
    is_test = lead.get("data_origin") == "test_data"
    cust_name = lead.get("customer_name") or "Customer"
    phone_raw = lead.get("phone")
    
    state_open = f"{key_prefix}_open_{lead_id}"
    state_msg = f"{key_prefix}_msg_{lead_id}"
    state_conv_id = f"{key_prefix}_conv_id_{lead_id}"
    
    # 1. Main Action Button
    col_btn, col_info = st.columns([2, 3])
    with col_btn:
        if st.button("💬 Send Enquiry Message", key=f"{key_prefix}_btn_open_{lead_id}", type="primary", use_container_width=True):
            st.session_state[state_open] = True
            initial_msg = generate_enquiry_message(lead)
            draft_rec = get_or_create_enquiry_draft(lead_id, initial_msg)
            st.session_state[state_msg] = initial_msg
            st.session_state[state_conv_id] = draft_rec["conversation_id"]
            st.rerun()
            
    with col_info:
        latest = get_latest_enquiry_message(lead_id)
        if latest:
            st_color = "#16A34A" if latest["sending_status"] == "User-Confirmed Sent" else ("#2563EB" if latest["sending_status"] == "Ready to Send" else ("#DC2626" if latest["sending_status"] == "Cancelled" else "#64748B"))
            st.caption(f"Enquiry Outreach: <span style='color:{st_color}; font-weight:700;'>{latest['sending_status']}</span> (Updated: {latest.get('created_at', '—')})", unsafe_allow_html=True)
            
    # 2. Interactive Preview & Dispatch Area
    if st.session_state.get(state_open, False):
        with st.container():
            st.markdown(f"""
            <div style="background-color: #F8FAFC; border: 1.5px solid #CBD5E1; border-radius: 8px; padding: 14px 18px; margin: 12px 0 6px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="color: #0F172A; font-size: 1.05rem;">✉️ First Outbound WhatsApp Introduction &mdash; {cust_name} {'[TEST DATA]' if is_test else ''}</strong>
                </div>
                <p style="margin: 4px 0 0 0; color: #475569; font-size: 0.88rem;">
                    Prepared from the customer's actual submitted website enquiry. <strong>Salesperson must manually press Send inside WhatsApp.</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Context meta row
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.caption(f"📱 **Phone:** `{phone_raw}`")
            with m2:
                st.caption(f"🏡 **Configuration:** {lead.get('project_type') or 'N/A'}")
            with m3:
                loc_txt = lead.get('locality') or 'Hyderabad'
                reg_txt = lead.get('region') or 'Metropolitan'
                st.caption(f"📍 **Locality:** {loc_txt} ({reg_txt})")
            with m4:
                est_raw = lead.get("estimate_generated_at") or lead.get("created_at")
                disp_date = estimate_parser.format_estimate_display(est_raw) if est_raw else "Recent"
                st.caption(f"📅 **Enquiry Date:** {disp_date}")
                
            current_msg = st.session_state.get(state_msg, generate_enquiry_message(lead))
            conv_id = st.session_state.get(state_conv_id)
            if not conv_id:
                draft_rec = get_or_create_enquiry_draft(lead_id, current_msg)
                conv_id = draft_rec["conversation_id"]
                st.session_state[state_conv_id] = conv_id
                
            edited_msg = st.text_area(
                "Personalized Message (Review and edit before opening WhatsApp):",
                value=current_msg,
                height=230,
                key=f"{key_prefix}_ta_{lead_id}"
            )
            
            # Click-to-chat URL
            url, err = build_enquiry_click_to_chat_url(phone_raw, edited_msg)
            
            act_col1, act_col2, act_col3 = st.columns([2, 2, 1])
            with act_col1:
                if err:
                    st.error(f"❌ {err}")
                else:
                    # Provide link to open WhatsApp
                    st.link_button("📲 Open WhatsApp Chat", url=url, use_container_width=True, type="primary")
                    # Update status to Ready to Send
                    update_enquiry_message_status(conv_id, "Ready to Send", lead_id=lead_id, edited_message=edited_msg)
                    st.caption("ℹ️ *Opens WhatsApp Click-to-Chat in a new tab. You must manually press Send.*")
                    
            with act_col2:
                if st.button("✅ Confirm Sent (Record in CRM)", key=f"{key_prefix}_confirm_btn_{lead_id}", use_container_width=True):
                    update_enquiry_message_status(conv_id, "User-Confirmed Sent", lead_id=lead_id, edited_message=edited_msg)
                    st.success("🎉 Confirmed! Message marked as 'User-Confirmed Sent' and logged in customer activity timeline.")
                    st.session_state[state_open] = False
                    st.rerun()
                    
            with act_col3:
                if st.button("❌ Cancel Draft", key=f"{key_prefix}_cancel_btn_{lead_id}", use_container_width=True):
                    update_enquiry_message_status(conv_id, "Cancelled", lead_id=lead_id, edited_message=edited_msg)
                    st.info("Draft cancelled.")
                    st.session_state[state_open] = False
                    st.rerun()

