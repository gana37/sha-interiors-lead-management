import streamlit as st
import pandas as pd
import json
import os
import datetime
import database
import estimate_parser
import hyderabad_geo as hg
import data_loader
import lead_capture
import lead_scoring
import followups
import followup_templates
import whatsapp_assistant
import reports
import ai_assistant
import ai_service
import n8n_dispatcher
import db_intelligence
import design_knowledge
import material_knowledge
import cost_estimator
import sales_intelligence
import customer_intelligence
import followup_intelligence
import enquiry_whatsapp
import business_config
import crm_search
import whatsapp_importer
import shadow_mode
import voice_assistant
import sha_rag_engine
import sha_agent
import multilingual_engine
import india_interior_knowledge

# Page configuration
st.set_page_config(
    page_title="SHA Interface Interiors | AI Lead Management System",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom UI Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.02em;
        line-height: 1.15;
        margin-bottom: 0.2rem;
    }
    .main-header-accent {
        color: #2563EB;
    }
    .sub-header {
        font-size: 1.05rem;
        font-weight: 500;
        color: #64748B;
        margin-bottom: 1.3rem;
    }
    .metric-card-modern {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 14px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        margin-bottom: 8px;
    }
    .metric-card-modern:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    .metric-val-modern {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.2;
    }
    .metric-lbl-modern {
        font-size: 0.76rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 6px;
    }
    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1E293B;
        margin-top: 1.6rem;
        margin-bottom: 0.8rem;
    }
    /* Permanent Bottom Fixed AI Chat Input Composer */
    .stChatFloatingInputContainer {
        position: sticky !important;
        bottom: 0 !important;
        background: #FFFFFF !important;
        z-index: 100 !important;
        padding-top: 10px !important;
        padding-bottom: 12px !important;
        border-top: 1px solid #E2E8F0 !important;
        box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.04) !important;
    }
    [data-testid="stChatInput"] {
        border-radius: 12px !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05) !important;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-val {
        font-size: 1.7rem;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-lbl {
        font-size: 0.8rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database schema
database.init_db()

# Automatic generation or insertion of dummy/synthetic leads during startup is disabled.
# Genuine customer records in SQLite database are preserved.

# Navigation Sidebar
with st.sidebar:
    st.markdown("### 🏛️ SHA Interiors – Lead Management Dashboard")
    st.caption("AI CRM & Intelligence Suite &mdash; **Hyderabad Edition**")
    st.divider()
    
    page = st.radio(
        "Navigation",
        options=[
            "Home Dashboard",
            "AI Lead Scoring",
            "Follow-up Management",
            "Reports and Analytics",
            "AI Assistant",
            "AI Shadow Mode",
            "View All Leads",
            "Add New Lead",
            "Import Leads",
            "Settings"
        ],
        index=0
    )
    

    st.divider()
    st.markdown("### 📊 System Status")
    stats = database.get_lead_stats(active_only=True)
    st.write(f"**Active Leads:** {stats['total_leads']} (Hyderabad)")
    st.write(f"**Territory:** Hyderabad & Secunderabad")
    st.write(f"**Avg Score:** {stats['avg_score']}/100")
    st.write(f"**Follow-ups:** {stats.get('total_followups', 0)}")
    
    ai_status = "🟢 Active (Gemini API)" if ai_assistant.is_ai_api_available() else "🟡 Local Rule Engine (Active)"
    n8n_status = "🟢 Configured" if n8n_dispatcher.is_n8n_configured() else "🟡 Local Fallback (Active)"
    st.caption(f"AI: {ai_status}")
    st.caption(f"n8n: {n8n_status}")
    st.divider()
    st.caption("SHA Interface Interiors © 2026")

# ==============================================================================
# 1. HOME DASHBOARD
# ==============================================================================
if page == "Home Dashboard":
    st.markdown('<div class="main-header">SHA Interiors<br><span class="main-header-accent">Lead Management Dashboard</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Hyderabad Metropolitan Edition &mdash; Real-Time Lead Analytics, Locality Intelligence & Conversion Pipeline</div>', unsafe_allow_html=True)
    
    # Dataset Scope Filter for Dashboard (Genuine vs Test Data)
    dscope_col1, dscope_col2 = st.columns([2.5, 1.5])
    with dscope_col1:
        dash_scope_choice = st.radio(
            "📊 Dashboard Dataset Scope:",
            options=["All Leads (Including Test Data)", "Genuine Customer Leads Only", "Test Leads Only"],
            horizontal=True,
            index=0,
            key="dash_dataset_scope_radio"
        )
    with dscope_col2:
        scope_map = {
            "All Leads (Including Test Data)": "all",
            "Genuine Customer Leads Only": "genuine_only",
            "Test Leads Only": "test_only"
        }
        active_dash_scope = scope_map[dash_scope_choice]
        if active_dash_scope == "genuine_only":
            st.info("👤 Genuine Customers Only (Test data excluded)")
        elif active_dash_scope == "test_only":
            st.warning("🧪 Test Leads Only (Kanishka & Dinesh)")
        else:
            st.success("🌐 Complete Unified Dataset (Genuine + Test)")

    kpis = reports.get_hyderabad_kpis(dataset_scope=active_dash_scope)
    chart_data = reports.get_chart_data(dataset_scope=active_dash_scope)

    # 1. Dashboard Overview Cards (8 Metrics)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card-modern" style="border-top: 4px solid #2563EB;"><div class="metric-val-modern" style="color: #2563EB;">{kpis["total_leads"]}</div><div class="metric-lbl-modern">Total Active Hyderabad Leads</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card-modern" style="border-top: 4px solid #0284C7;"><div class="metric-val-modern" style="color: #0284C7;">{kpis["new_leads"]}</div><div class="metric-lbl-modern">New Leads</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card-modern" style="border-top: 4px solid #0D9488;"><div class="metric-val-modern" style="color: #0D9488;">{kpis["qualified_leads"]}</div><div class="metric-lbl-modern">Qualified Leads</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card-modern" style="border-top: 4px solid #D97706;"><div class="metric-val-modern" style="color: #D97706;">{kpis["high_priority_leads"]}</div><div class="metric-lbl-modern">High Priority Leads</div></div>', unsafe_allow_html=True)

    st.write("")
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.markdown(f'<div class="metric-card-modern" style="border-top: 4px solid #16A34A;"><div class="metric-val-modern" style="color: #16A34A;">{kpis["converted_leads"]}</div><div class="metric-lbl-modern">Converted Leads</div></div>', unsafe_allow_html=True)
    with col6:
        st.markdown(f'<div class="metric-card-modern" style="border-top: 4px solid #DC2626;"><div class="metric-val-modern" style="color: #DC2626;">{kpis["lost_leads"]}</div><div class="metric-lbl-modern">Lost Leads</div></div>', unsafe_allow_html=True)
    with col7:
        st.markdown(f'<div class="metric-card-modern" style="border-top: 4px solid #7C3AED;"><div class="metric-val-modern" style="color: #7C3AED;">{kpis["overall_conversion_rate"]}%</div><div class="metric-lbl-modern">Conversion Rate</div></div>', unsafe_allow_html=True)
    with col8:
        st.markdown(f'<div class="metric-card-modern" style="border-top: 4px solid #059669;"><div class="metric-val-modern" style="color: #059669;">{kpis["upcoming_followups"]}</div><div class="metric-lbl-modern">Upcoming Follow-ups</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # 2. Hyderabad Geographical Analytics
    st.markdown('<div class="section-title">📍 Hyderabad Geographical Analytics</div>', unsafe_allow_html=True)
    
    geo_col1, geo_col2 = st.columns([2, 1])
    with geo_col1:
        loc_options = [f"All Localities ({len(hg.get_all_localities())} Localities)"] + hg.get_all_localities()
        selected_locality = st.selectbox("🔍 Searchable Locality Filter", options=loc_options, index=0)
    with geo_col2:
        reg_options = [f"All Regions ({len(hg.HYDERABAD_REGIONS)} Regions)"] + sorted(hg.HYDERABAD_REGIONS)
        selected_region = st.selectbox("🌐 Metropolitan Region Filter", options=reg_options, index=0)

    # Dynamic contextual summary banner when filtering
    if not selected_locality.startswith("All Localities"):
        loc_meta = hg.get_locality_metadata(selected_locality)
        loc_leads = [l for l in database.get_all_leads(active_only=True) if l.get("locality") == selected_locality]
        loc_count = len(loc_leads)
        loc_high = sum(1 for l in loc_leads if l.get("priority") == "High")
        loc_avg = round(sum(l.get("lead_score", 0) for l in loc_leads) / loc_count, 1) if loc_count > 0 else 0.0
        st.info(f"📍 **{selected_locality}** ({loc_meta.get('region', 'Hyderabad')} | PIN: {loc_meta.get('pincode', 'N/A')} | Tier {loc_meta.get('tier', 1)}) — **{loc_count} Active Leads** | High Priority: **{loc_high}** | Avg Qualification Score: **{loc_avg}/100**")
    elif selected_region != "All Regions (6 Regions)":
        reg_leads = [l for l in database.get_all_leads(active_only=True) if l.get("region") == selected_region]
        reg_count = len(reg_leads)
        reg_high = sum(1 for l in reg_leads if l.get("priority") == "High")
        st.info(f"🌐 **{selected_region}** — **{reg_count} Active Leads** | High Priority: **{reg_high}** across {len(hg.LOCALITY_CATALOG.get(selected_region, []))} reference localities")

    g_c1, g_c2 = st.columns(2)
    with g_c1:
        st.markdown("##### 🌐 Region-Wise Lead Distribution")
        if "region" in chart_data and not chart_data["region"].empty:
            st.bar_chart(chart_data["region"].set_index("Region"), color="#10B981", use_container_width=True)
    with g_c2:
        st.markdown("##### 🏆 Top 10 Localities by Lead Count")
        if "locality" in chart_data and not chart_data["locality"].empty:
            st.bar_chart(chart_data["locality"].set_index("Locality"), color="#2563EB", use_container_width=True)

    with st.expander("📋 View Complete Locality-Wise Distribution Directory (60 Localities)", expanded=False):
        if "locality_all" in chart_data and not chart_data["locality_all"].empty:
            st.dataframe(chart_data["locality_all"], use_container_width=True, hide_index=True)

    st.markdown("---")

    # 3. Business Analytics & Customer Intelligence
    st.markdown('<div class="section-title">📊 Business Analytics & Customer Intelligence</div>', unsafe_allow_html=True)
    
    b_r1_c1, b_r1_c2 = st.columns(2)
    with b_r1_c1:
        st.markdown("##### 🎯 Lead Priority Distribution")
        if "priority" in chart_data and not chart_data["priority"].empty:
            st.bar_chart(chart_data["priority"].set_index("Priority"), color="#3B82F6", use_container_width=True)
    with b_r1_c2:
        st.markdown("##### 💰 Budget Range Distribution")
        if "budget" in chart_data and not chart_data["budget"].empty:
            st.bar_chart(chart_data["budget"].set_index("Budget Range"), color="#F59E0B", use_container_width=True)

    b_r2_c1, b_r2_c2 = st.columns(2)
    with b_r2_c1:
        st.markdown("##### 🏡 Project Type Distribution")
        if "project_type" in chart_data and not chart_data["project_type"].empty:
            st.bar_chart(chart_data["project_type"].set_index("Project Type"), color="#8B5CF6", use_container_width=True)
    with b_r2_c2:
        st.markdown("##### 🏗️ Property Status Analysis")
        if "property_status" in chart_data and not chart_data["property_status"].empty:
            st.bar_chart(chart_data["property_status"].set_index("Property Status"), color="#06B6D4", use_container_width=True)

    b_r3_c1, b_r3_c2 = st.columns(2)
    with b_r3_c1:
        st.markdown("##### ⏱️ Purchase Readiness Analysis")
        if "purchase_readiness" in chart_data and not chart_data["purchase_readiness"].empty:
            st.bar_chart(chart_data["purchase_readiness"].set_index("Purchase Readiness"), color="#EC4899", use_container_width=True)
    with b_r3_c2:
        st.markdown("##### 📈 Monthly Lead Generation Trend")
        if "monthly_generation" in chart_data and not chart_data["monthly_generation"].empty:
            st.bar_chart(chart_data["monthly_generation"].set_index("Month"), color="#10B981", use_container_width=True)

    st.markdown("##### 🔄 Lead Conversion Trends")
    if "conversion_trends" in chart_data and not chart_data["conversion_trends"].empty:
        st.dataframe(chart_data["conversion_trends"], use_container_width=True, hide_index=True)
        st.caption(f"Overall Pipeline Conversion: **{kpis['overall_conversion_rate']}%** | Engaged Inquiries Conversion: **{kpis['engaged_conversion_rate']}%** across {kpis['total_leads']} active Hyderabad leads.")

    st.markdown("---")

    # 4. Follow-Up Overview & Action Queue
    st.markdown('<div class="section-title">📅 Follow-Up Overview & Action Queue</div>', unsafe_allow_html=True)
    st.caption("Active follow-up task tracking restricted exclusively to Hyderabad metropolitan service area leads.")

    fu_c1, fu_c2, fu_c3, fu_c4 = st.columns(4)
    with fu_c1:
        st.markdown(f'<div class="metric-card-modern" style="border-top: 4px solid #F59E0B;"><div class="metric-val-modern" style="color: #D97706;">{kpis["today_followups"]}</div><div class="metric-lbl-modern">Today\'s Follow-ups</div></div>', unsafe_allow_html=True)
    with fu_c2:
        st.markdown(f'<div class="metric-card-modern" style="border-top: 4px solid #EF4444;"><div class="metric-val-modern" style="color: #DC2626;">{kpis["overdue_followups"]}</div><div class="metric-lbl-modern">Overdue Follow-ups</div></div>', unsafe_allow_html=True)
    with fu_c3:
        st.markdown(f'<div class="metric-card-modern" style="border-top: 4px solid #10B981;"><div class="metric-val-modern" style="color: #059669;">{kpis["upcoming_followups"]}</div><div class="metric-lbl-modern">Upcoming Scheduled</div></div>', unsafe_allow_html=True)
    with fu_c4:
        st.markdown(f'<div class="metric-card-modern" style="border-top: 4px solid #6366F1;"><div class="metric-val-modern" style="color: #4F46E5;">{kpis["completed_followups"]} / {kpis["total_followups"]} <span style="font-size: 0.95rem; font-weight: 500; color: #64748B;">({kpis["followup_completion_rate"]}%)</span></div><div class="metric-lbl-modern">Completion Statistics</div></div>', unsafe_allow_html=True)

    st.write("")
    fu_tab1, fu_tab2, fu_tab3 = st.tabs(["⚡ Due Today & Upcoming (Next 15)", "⚠️ Overdue Follow-ups", "📋 Complete Follow-up Schedule (Next 50)"])

    with fu_tab1:
        df_due = reports.get_hyderabad_followup_queue("upcoming", limit=15)
        if not df_due.empty:
            st.dataframe(df_due, use_container_width=True, hide_index=True)
        else:
            st.info("No upcoming follow-ups scheduled.")

    with fu_tab2:
        df_overdue = reports.get_hyderabad_followup_queue("overdue", limit=25)
        if not df_overdue.empty:
            st.warning(f"Found {len(df_overdue)} overdue follow-up tasks requiring sales action.")
            st.dataframe(df_overdue, use_container_width=True, hide_index=True)
        else:
            st.success("🎉 Excellent! Zero overdue follow-up tasks.")

    with fu_tab3:
        df_all_fu = reports.get_hyderabad_followup_queue("all", limit=50)
        if not df_all_fu.empty:
            st.dataframe(df_all_fu, use_container_width=True, hide_index=True)
        else:
            st.info("No follow-up records found.")

    st.markdown("---")

    # 5. Estimate Generation Timeline & Insights
    st.markdown('<div class="section-title">⏱️ Estimate Generation Timeline & Insights</div>', unsafe_allow_html=True)
    st.caption("Telemetry extracted automatically from 10-digit estimate reference numbers (HHMMDDMMYY).")

    est_analytics = reports.get_estimate_analytics()
    latest_est = est_analytics.get("latest_estimate")

    e_c1, e_c2, e_c3, e_c4 = st.columns(4)
    with e_c1:
        st.markdown(f'<div class="metric-card-modern" style="border-top: 4px solid #3B82F6;"><div class="metric-val-modern" style="color: #2563EB;">{est_analytics["leads_today"]}</div><div class="metric-lbl-modern">Leads Generated Today</div></div>', unsafe_allow_html=True)
    with e_c2:
        st.markdown(f'<div class="metric-card-modern" style="border-top: 4px solid #10B981;"><div class="metric-val-modern" style="color: #059669;">{est_analytics["leads_this_week"]}</div><div class="metric-lbl-modern">Leads Generated This Week</div></div>', unsafe_allow_html=True)
    with e_c3:
        st.markdown(f'<div class="metric-card-modern" style="border-top: 4px solid #8B5CF6;"><div class="metric-val-modern" style="color: #7C3AED;">{est_analytics["leads_this_month"]}</div><div class="metric-lbl-modern">Leads Generated This Month</div></div>', unsafe_allow_html=True)
    with e_c4:
        st.markdown(f'<div class="metric-card-modern" style="border-top: 4px solid #F59E0B;"><div class="metric-val-modern" style="color: #D97706;">{est_analytics["total_with_estimates"]} / {kpis["total_leads"]}</div><div class="metric-lbl-modern">Estimates Decoded</div></div>', unsafe_allow_html=True)

    if latest_est:
        st.markdown(f"""
        <div style="background-color: #EFF6FF; border: 1px solid #BFDBFE; border-left: 6px solid #2563EB; border-radius: 8px; padding: 14px 18px; margin: 12px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <span style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: #1D4ED8; letter-spacing: 0.05em;">⚡ Latest Estimate Generated</span>
                    <h4 style="margin: 4px 0 2px 0; color: #0F172A;">{latest_est['customer_name']} &mdash; <span style="font-weight: 500; font-size: 1rem; color: #475569;">{latest_est['locality']} ({latest_est['region']})</span></h4>
                    <span style="font-size: 0.9rem; color: #334155;">Reference: <code>{latest_est['lead_reference']}</code> &nbsp;|&nbsp; Budget: <strong>{latest_est['budget_range']}</strong> &nbsp;|&nbsp; Priority: <strong>{latest_est['priority']}</strong></span>
                </div>
                <div style="text-align: right; margin-top: 6px;">
                    <div style="font-size: 1.25rem; font-weight: 800; color: #1E40AF;">{latest_est['display_time']}</div>
                    <span style="font-size: 0.78rem; color: #64748B;">{latest_est['display_long']}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("##### 📅 Leads Grouped by Estimate Generation Date")
    df_grp = est_analytics.get("grouped_by_date")
    if df_grp is not None and not df_grp.empty:
        st.dataframe(df_grp, use_container_width=True, hide_index=True)

# ==============================================================================
# 2. AI LEAD SCORING
# ==============================================================================
elif page == "AI Lead Scoring":
    st.markdown('<div class="main-header">AI Lead Qualification & Scoring Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Explainable multi-factor scoring: Budget (30), Location (20), Requirements (20), Readiness (30).</div>', unsafe_allow_html=True)

    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        if st.button("⚡ Score / Recalculate All Leads", type="primary", use_container_width=True):
            with st.spinner("Scoring all eligible leads against SHA business rules..."):
                res = lead_scoring.score_all_leads(force_rescore=True)
                st.success(f"✅ {res['message']}")
                st.rerun()
    with col_info:
        st.caption("Evaluates budget adequacy, geographical service tier, space planning details, and urgency.")

    st.divider()

    # Filter & Sort
    fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns([1.2, 1.6, 1.6, 1.4, 1.6])
    with fcol1:
        priority_filter = st.selectbox("Priority Tier", options=["All", "High", "Medium", "Low"])
    with fcol2:
        region_filter = st.selectbox("Hyderabad Region", options=hg.DISPLAY_REGION_OPTIONS, index=0)
    with fcol3:
        available_locs = hg.get_localities_for_region(region_filter)
        loc_options = ["All Localities"] + available_locs
        locality_filter = st.selectbox("Hyderabad Locality", options=loc_options, index=0)
    with fcol4:
        sort_by = st.selectbox("Sort By", options=["Highest Score First", "Lowest Score First", "Customer Name"])
    with fcol5:
        search_kw = st.text_input("Search Lead", placeholder="Name, Locality, or ID...")

    order_map = {"Highest Score First": "lead_score DESC", "Lowest Score First": "lead_score ASC", "Customer Name": "customer_name ASC"}
    leads = database.get_all_leads(
        locality=locality_filter if locality_filter != "All Localities" else None,
        region=region_filter if region_filter != "All Regions" else None,
        priority=priority_filter,
        search_query=search_kw,
        order_by=order_map[sort_by],
        active_only=True
    )

    st.markdown(f"**Showing {len(leads)} leads**")
    if leads:
        df = pd.DataFrame(leads)
        df["lead_score"] = df["lead_score"].apply(lambda x: f"{x:.0f}" if pd.notnull(x) else "—")
        df["priority"] = df["priority"].fillna("Pending")
        df["locality"] = df["locality"].fillna("Unmapped")
        df["region"] = df["region"].fillna("Unspecified")
        
        df["origin_label"] = df["data_origin"].apply(
            lambda x: "🧪 TEST DATA" if x == "test_data" else ("👤 Genuine" if x in ("genuine_customer", "manual_entry") else str(x))
        )
        display_cols = ["lead_id", "customer_name", "origin_label", "locality", "region", "budget_range", "project_type", "purchase_readiness", "lead_score", "priority", "lead_status"]
        st.dataframe(df[display_cols].rename(columns={
            "lead_id": "Lead ID", "customer_name": "Customer Name", "origin_label": "Origin", "locality": "Locality", "region": "Region",
            "budget_range": "Budget", "project_type": "Project Type", "purchase_readiness": "Readiness",
            "lead_score": "Score (/100)", "priority": "Priority", "lead_status": "CRM Status"
        }), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### 🔬 Inspect Explainable Scoring Breakdown")
        
        sel_col1, sel_col2 = st.columns([3, 1])
        with sel_col1:
            selected_lead_id = st.selectbox("Select Lead to inspect scoring drivers:", options=[l["lead_id"] for l in leads])
        with sel_col2:
            st.write("")
            st.write("")
            if st.button("🔄 Rescore Selected Lead", use_container_width=True):
                lead_scoring.score_and_save_lead(selected_lead_id)
                st.success(f"Lead {selected_lead_id} rescored successfully.")
                st.rerun()

        if selected_lead_id:
            lead_item = database.get_lead_by_id(selected_lead_id)
            if lead_item and lead_item.get("score_breakdown"):
                try:
                    breakdown = json.loads(lead_item["score_breakdown"]) if isinstance(lead_item["score_breakdown"], str) else lead_item["score_breakdown"]
                except Exception:
                    breakdown = {}

                p = lead_item.get("priority", "Pending")
                badge_bg = "#DCFCE7" if p == "High" else "#FEF3C7" if p == "Medium" else "#FEE2E2"
                badge_border = "#16A34A" if p == "High" else "#D97706" if p == "Medium" else "#DC2626"
                score_val = lead_item.get('lead_score', 0)

                st.markdown(f"""
                <div style="background-color: {badge_bg}; border-left: 6px solid {badge_border}; padding: 14px; border-radius: 6px; margin: 12px 0;">
                    <h3 style="margin: 0; color: #0F172A;">{lead_item['customer_name']} &mdash; <span style="color: {badge_border};">{p} Priority</span> ({score_val:.0f}/100 Points)</h3>
                    <p style="margin: 6px 0 0 0; color: #334155; font-size: 0.95rem;">
                        💡 <strong>Scoring Rationale:</strong> {lead_item.get('scoring_reason', 'Evaluation completed.')}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    st.metric("💰 Budget", f"{breakdown.get('budget_score', 0)} / 30", help=breakdown.get("budget_detail"))
                    st.caption(f"{lead_item.get('budget_range')}")
                with b2:
                    st.metric("📍 Location", f"{breakdown.get('location_score', 0)} / 20", help=breakdown.get("location_detail"))
                    loc_val = lead_item.get('locality') or 'Unmapped'
                    reg_val = lead_item.get('region') or 'Hyderabad'
                    st.caption(f"{loc_val} ({reg_val})")
                with b3:
                    st.metric("📋 Requirements", f"{breakdown.get('requirements_score', 0)} / 20", help=breakdown.get("requirements_detail"))
                    st.caption(f"{lead_item.get('project_type')}")
                with b4:
                    st.metric("🚀 Readiness", f"{breakdown.get('readiness_score', 0)} / 30", help=breakdown.get("readiness_detail"))
                    st.caption(f"{lead_item.get('purchase_readiness')}")

                # Quick outreach from scoring card
                with st.expander("💬 **Send Website Enquiry Message to this Customer**", expanded=False):
                    enquiry_whatsapp.render_enquiry_message_ui(lead_item, key_prefix="scoring_inspect")

# ==============================================================================
# 3. FOLLOW-UP MANAGEMENT & AI WHATSAPP ASSISTANT
# ==============================================================================
elif page == "Follow-up Management":
    st.markdown('<div class="main-header">Follow-up Management & AI WhatsApp Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Priority cadences, conversational AI sales assistant, and normal WhatsApp Click-to-Chat integration.</div>', unsafe_allow_html=True)

    fu_stats = database.get_followup_stats(active_only=True)
    
    # 8-Card Overview Telemetry (Phase 3A)
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    with fcol1:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{fu_stats["total_followups"]}</div><div class="metric-lbl">Total Tasks</div></div>', unsafe_allow_html=True)
    with fcol2:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color: #D97706;">{fu_stats["due_today"]}</div><div class="metric-lbl">Due Today</div></div>', unsafe_allow_html=True)
    with fcol3:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color: #DC2626;">{fu_stats["overdue"]}</div><div class="metric-lbl">Overdue</div></div>', unsafe_allow_html=True)
    with fcol4:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color: #2563EB;">{fu_stats["upcoming"]}</div><div class="metric-lbl">Upcoming</div></div>', unsafe_allow_html=True)

    fcol5, fcol6, fcol7, fcol8 = st.columns(4)
    with fcol5:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color: #16A34A;">{fu_stats["completed_count"]}</div><div class="metric-lbl">Completed</div></div>', unsafe_allow_html=True)
    with fcol6:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color: #25D366;">{fu_stats["pending_whatsapp"]}</div><div class="metric-lbl">Pending WhatsApp</div></div>', unsafe_allow_html=True)
    with fcol7:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color: #8B5CF6;">{fu_stats["pending_calls"]}</div><div class="metric-lbl">Pending Phone Calls</div></div>', unsafe_allow_html=True)
    with fcol8:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color: #6366F1;">{fu_stats["pending_emails"]}</div><div class="metric-lbl">Pending Emails</div></div>', unsafe_allow_html=True)

    st.markdown("""
    > [!IMPORTANT]
    > **Click-to-Chat Protocol**: Opening WhatsApp launches the conversation in your desktop/laptop WhatsApp with the draft prefilled. **The salesperson must manually press Send inside WhatsApp**. After sending, click **Mark as Sent** in the CRM to record confirmation.
    """)

    tabs = st.tabs([
        "💬 Customer Conversation Assistant",
        "📅 Task Management & Schedule",
        "📥 Inbound Response Simulator",
        "🛡️ Compliance & Opt-Out Controls",
        "⚡ Mass Cadence Scheduler"
    ])
    
    # -------------------------------------------------------------
    # TAB 1: CUSTOMER CONVERSATION ASSISTANT (PHASES 4, 6, 7, 8, 9, 10, 12)
    # -------------------------------------------------------------
    with tabs[0]:
        st.markdown("### 💬 Conversational AI Sales Assistant")
        st.caption("Understand natural customer WhatsApp queries, ground responses in CRM intelligence, and open Click-to-Chat in your logged-in WhatsApp session.")
        
        all_active_leads = database.get_all_leads(active_only=True, order_by="customer_name ASC")
        if not all_active_leads:
            st.info("No active leads found in the CRM.")
        else:
            lead_options = {
                f"{'🧪 [TEST DATA] ' if l.get('data_origin') == 'test_data' else '👤 '}{l['customer_name']} ({l.get('locality') or 'Hyderabad'} - {l.get('project_type') or 'Interior'}) [ID: {l['lead_id']}]": l['lead_id']
                for l in all_active_leads
            }
            selected_label = st.selectbox(
                "Select Customer to Converse With:",
                options=list(lead_options.keys()),
                key="wa_conv_lead_sel"
            )
            sel_lead_id = lead_options[selected_label]
            lead_rec = database.get_lead_by_id(sel_lead_id)
            
            # Customer Context Dossier Card
            with st.container():
                is_test_lead = lead_rec.get('data_origin') == 'test_data'
                if is_test_lead:
                    st.warning("🧪 **TEST DATA RECORD**: This customer record is designated for end-to-end follow-up testing. WhatsApp Click-to-Chat will open your local WhatsApp session; the salesperson must manually press Send.")
                st.markdown("##### 📋 Customer CRM Dossier")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown(f"**Customer:** {lead_rec.get('customer_name')}")
                    st.markdown(f"**Phone:** `{lead_rec.get('phone')}`")
                    st.markdown(f"**Email:** `{lead_rec.get('email') or 'N/A'}`")
                with c2:
                    loc_name = lead_rec.get('locality') or 'Hyderabad'
                    reg_name = lead_rec.get('region') or 'Metropolitan'
                    st.markdown(f"**Location:** {loc_name} ({reg_name})")
                    st.markdown(f"**Property:** {lead_rec.get('project_type')} ({lead_rec.get('property_status')})")
                with c3:
                    st.markdown(f"**Budget:** {lead_rec.get('budget_range')}")
                    prio_color = "#DC2626" if lead_rec.get('priority') == 'High' else "#D97706"
                    st.markdown(f"**Priority:** <span style='color:{prio_color}; font-weight:700;'>{lead_rec.get('priority')}</span> (Score: {lead_rec.get('lead_score', '—')}/100)", unsafe_allow_html=True)
                with c4:
                    ref_val = lead_rec.get('lead_reference') or "—"
                    est_disp = estimate_parser.format_estimate_display(lead_rec.get('estimate_generated_at'))
                    st.markdown(f"**Estimate Ref:** `{ref_val}`")
                    st.markdown(f"**Generated:** {est_disp}")
                    
                if lead_rec.get("is_opted_out"):
                    st.warning(f"⚠️ **Customer Opted Out**: {lead_rec.get('opt_out_reason') or 'Client requested no further communications'}. Automated follow-ups are halted.")
                    
            # ---------------------------------------------------------
            # INTELLIGENT FOLLOW-UP RECOMMENDATION CARD
            # ---------------------------------------------------------
            rec = followup_intelligence.generate_intelligent_followup_recommendation(sel_lead_id)
            if rec.get("success"):
                rec_prio = rec.get("priority", "Medium")
                prio_bg = "#FEE2E2" if rec_prio == "High" else ("#FEF3C7" if rec_prio == "Medium" else "#F3F4F6")
                prio_fg = "#DC2626" if rec_prio == "High" else ("#D97706" if rec_prio == "Medium" else "#4B5563")
                prio_border = "#EF4444" if rec_prio == "High" else ("#F59E0B" if rec_prio == "Medium" else "#9CA3AF")
                
                cust_analysis = rec.get("customer_analysis", {})
                last_inter = cust_analysis.get("last_interaction_date", "None")
                current_stg = cust_analysis.get("current_project_stage", "Active Follow-up")
                pending_q = cust_analysis.get("pending_customer_question") or "None identified"
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #F8FAFC 0%, #F0FDF4 100%); border: 1px solid #CBD5E1; border-left: 6px solid {prio_border}; border-radius: 10px; padding: 16px 20px; margin-top: 12px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                        <span style="font-size: 1.1rem; font-weight: 700; color: #0F172A;">🧠 Intelligent Follow-up Recommendation</span>
                        <span style="background-color: {prio_bg}; color: {prio_fg}; border: 1px solid {prio_border}; padding: 3px 12px; border-radius: 12px; font-size: 0.82rem; font-weight: 700;">{rec_prio} Priority</span>
                    </div>
                    <div style="font-size: 0.95rem; color: #1E293B; margin-bottom: 6px;">
                        <strong>Why Follow-up is Needed:</strong> {rec.get('followup_reason')}
                    </div>
                    <div style="font-size: 0.95rem; color: #0F766E; margin-bottom: 6px;">
                        <strong>Recommended Next Action:</strong> {rec.get('next_action')}
                    </div>
                    <div style="font-size: 0.88rem; color: #475569; margin-bottom: 10px; line-height: 1.45;">
                        <em>{rec.get('explanation')}</em>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; background: rgba(255,255,255,0.7); padding: 10px 14px; border-radius: 8px; border: 1px solid #E2E8F0; font-size: 0.86rem; color: #334155;">
                        <div><strong>📅 Recommended Due:</strong> {rec.get('recommended_date')}</div>
                        <div><strong>🏗️ Project Stage:</strong> {current_stg}</div>
                        <div><strong>🕒 Last Interaction:</strong> {last_inter}</div>
                        <div style="grid-column: span 2;"><strong>❓ Pending Question:</strong> {pending_q}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"⚡ **Recommended WhatsApp Outreach & Quick Schedule ({rec.get('task_summary')})**", expanded=False):
                    st.caption("AI-drafted message incorporating customer requirements and adhering strictly to SHA Business Rules.")
                    rec_draft_val = st.text_area(
                        "Review / Refine Recommended Message:",
                        value=rec.get("suggested_whatsapp_message", ""),
                        height=130,
                        key=f"rec_draft_text_{sel_lead_id}"
                    )
                    
                    r_act1, r_act2, r_act3 = st.columns([1.8, 1.5, 1.5])
                    with r_act1:
                        if st.button("📅 Schedule Recommended Task", type="primary", key=f"btn_sched_rec_{sel_lead_id}", use_container_width=True):
                            s_res = database.schedule_single_followup(
                                lead_id=sel_lead_id,
                                scheduled_for=rec.get("recommended_date"),
                                channel="WhatsApp",
                                message=rec_draft_val.strip(),
                                followup_reason=rec.get("followup_reason"),
                                next_action=rec.get("next_action"),
                                priority=rec_prio,
                                task_summary=rec.get("task_summary")
                            )
                            if s_res["success"]:
                                st.success(f"✅ Follow-up task scheduled (ID: `{s_res['schedule_id']}`). View in 'Task Management & Schedule' tab.")
                                st.rerun()
                    with r_act2:
                        rec_norm_phone = whatsapp_assistant.normalize_whatsapp_phone(lead_rec.get("phone"))
                        wa_rec_url, wa_rec_err = whatsapp_assistant.build_whatsapp_click_to_chat_url(rec_norm_phone, rec_draft_val)
                        if wa_rec_url:
                            st.markdown(f'<a href="{wa_rec_url}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366;color:white;border:none;padding:9px 16px;border-radius:6px;font-weight:700;width:100%;cursor:pointer;">💬 Open in WhatsApp</button></a>', unsafe_allow_html=True)
                        else:
                            st.caption(f"No WhatsApp: {wa_rec_err}")
                    with r_act3:
                        if st.button("📥 Use as Inbound Reply Draft", key=f"btn_adopt_draft_{sel_lead_id}", use_container_width=True):
                            st.session_state[f"active_draft_{sel_lead_id}"] = rec_draft_val.strip()
                            st.info("Adopted message into WhatsApp Reply editor below!")
                            st.rerun()
                    
            # ---------------------------------------------------------
            # FIRST OUTBOUND CONTACT: WEBSITE ENQUIRY WHATSAPP FEATURE
            # ---------------------------------------------------------
            with st.expander("✉️ **Website Enquiry Quick Action: Send Enquiry Message**", expanded=False):
                st.caption("First outbound introduction for newly submitted website enquiries. Prepares a personalized WhatsApp greeting from the customer's actual submitted requirements.")
                enquiry_whatsapp.render_enquiry_message_ui(lead_rec, key_prefix="conv_dossier")

            st.divider()
            
            # Incoming Message Input & Quick Chips
            st.markdown("##### 📥 Customer WhatsApp Message")
            st.caption("Paste the message you received from the customer on WhatsApp below, or test with quick sample queries:")
            
            # Quick query sample chips
            qc1, qc2, qc3, qc4, qc5 = st.columns(5)
            with qc1:
                if st.button("🍳 Kitchen Quote", key=f"qc1_{sel_lead_id}", use_container_width=True):
                    st.session_state[f"inbound_msg_{sel_lead_id}"] = "Can you explain the kitchen quotation and what is included?"
                    st.rerun()
            with qc2:
                if st.button("💰 Reduce Price", key=f"qc2_{sel_lead_id}", use_container_width=True):
                    st.session_state[f"inbound_msg_{sel_lead_id}"] = "The quote seems slightly high. Can you reduce the price?"
                    st.rerun()
            with qc3:
                if st.button("⏱️ When Start?", key=f"qc3_{sel_lead_id}", use_container_width=True):
                    st.session_state[f"inbound_msg_{sel_lead_id}"] = "When can you start the project and how long will it take?"
                    st.rerun()
            with qc4:
                if st.button("🗓️ Decide Later", key=f"qc4_{sel_lead_id}", use_container_width=True):
                    st.session_state[f"inbound_msg_{sel_lead_id}"] = "I need some time to decide and discuss with my family."
                    st.rerun()
            with qc5:
                if st.button("📞 Call Me", key=f"qc5_{sel_lead_id}", use_container_width=True):
                    st.session_state[f"inbound_msg_{sel_lead_id}"] = "Can someone call me today to discuss the details?"
                    st.rerun()
                    
            current_inbound = st.session_state.get(f"inbound_msg_{sel_lead_id}", "")
            inbound_input = st.text_area(
                "Customer Inbound Message:",
                value=current_inbound,
                height=90,
                placeholder="Paste incoming message from WhatsApp here...",
                key=f"inbound_text_area_{sel_lead_id}"
            )
            
            # AI Generation Action
            if st.button("🤖 Generate AI Conversational Reply", type="primary", key=f"btn_gen_ai_{sel_lead_id}"):
                if not inbound_input.strip():
                    st.error("Please paste or type an incoming customer message first.")
                else:
                    with st.spinner("AI Sales Consultant is analyzing CRM context and drafting natural response..."):
                        reply_result = whatsapp_assistant.generate_conversational_reply(
                            sel_lead_id,
                            inbound_input.strip()
                        )
                        if reply_result["success"]:
                            st.session_state[f"active_draft_{sel_lead_id}"] = reply_result["reply"]
                            st.session_state[f"reply_source_{sel_lead_id}"] = reply_result.get("source", "gemini")
                            # Record incoming message in database
                            database.add_conversation_message(
                                lead_id=sel_lead_id,
                                direction="incoming",
                                message_content=inbound_input.strip(),
                                channel="WhatsApp",
                                ai_generated_response=reply_result["reply"],
                                approval_status="Draft",
                                sending_status="Draft"
                            )
                            st.success(f"✨ Reply drafted successfully via {reply_result.get('source', 'AI engine').upper()}!")
                            st.rerun()
                        else:
                            st.error(f"Failed to generate reply: {reply_result.get('error')}")

            # Human-in-the-Loop Review & WhatsApp Dispatch
            active_draft = st.session_state.get(f"active_draft_{sel_lead_id}", "")
            if active_draft:
                st.markdown("##### ✍️ Review & Refine WhatsApp Reply (Human-in-the-Loop)")
                edited_reply = st.text_area(
                    "Edit draft reply before sending:",
                    value=active_draft,
                    height=140,
                    key=f"edit_draft_box_{sel_lead_id}"
                )
                
                # Normalize phone and build Click-to-Chat URL
                norm_phone = whatsapp_assistant.normalize_whatsapp_phone(lead_rec.get("phone"))
                wa_url, wa_err = whatsapp_assistant.build_whatsapp_click_to_chat_url(norm_phone, edited_reply)
                
                # Actions Row
                act_col1, act_col2, act_col3 = st.columns([1.6, 1.4, 1.4])
                with act_col1:
                    if wa_url:
                        # Open WhatsApp Click-to-Chat
                        wa_btn_html = f"""
                        <a href="{wa_url}" target="_blank" style="text-decoration:none;">
                            <div style="background-color:#25D366;color:#FFFFFF;text-align:center;padding:10px 18px;border-radius:8px;font-weight:700;font-size:1rem;box-shadow:0 2px 4px rgba(0,0,0,0.1);margin-top:4px;">
                                💬 Open WhatsApp Chat
                            </div>
                        </a>
                        """
                        st.markdown(wa_btn_html, unsafe_allow_html=True)
                        st.caption("Opens chat in your desktop WhatsApp app with message prefilled.")
                    else:
                        st.error(f"Cannot generate WhatsApp link: {wa_err}")
                        
                with act_col2:
                    if st.button("✅ Mark as Sent", type="secondary", key=f"btn_mark_sent_{sel_lead_id}", use_container_width=True):
                        # Save outgoing message to CUSTOMER_CONVERSATIONS
                        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        database.add_conversation_message(
                            lead_id=sel_lead_id,
                            direction="outgoing",
                            message_content=edited_reply.strip(),
                            channel="WhatsApp",
                            ai_generated_response=active_draft.strip(),
                            approval_status="Approved",
                            sending_status="User-Confirmed Sent",
                            sent_at=now_str
                        )
                        # Add activity log
                        database.insert_activity_log(
                            lead_id=sel_lead_id,
                            activity_type="WhatsApp Message Sent",
                            activity_description=f"Salesperson confirmed WhatsApp reply sent to {lead_rec.get('phone')}."
                        )
                        st.success("✅ Recorded message as 'User-Confirmed Sent' in CRM!")
                        st.rerun()
                        
                with act_col3:
                    if st.button("🔄 Regenerate Reply", key=f"btn_regen_{sel_lead_id}", use_container_width=True):
                        with st.spinner("Regenerating reply..."):
                            reply_result = whatsapp_assistant.generate_conversational_reply(
                                sel_lead_id,
                                inbound_input.strip() or "Please provide update on my quotation"
                            )
                            if reply_result["success"]:
                                st.session_state[f"active_draft_{sel_lead_id}"] = reply_result["reply"]
                                st.rerun()

            st.markdown("---")
            
            # Smart Follow-up Scheduler Expander (Phase 9)
            with st.expander("⏱️ Smart Follow-up Scheduler", expanded=False):
                st.markdown("###### Schedule Next Touchpoint for this Customer")
                sc_col1, sc_col2 = st.columns(2)
                with sc_col1:
                    timing_choice = st.radio(
                        "When to follow up:",
                        options=["Tomorrow (+1 Day)", "In 3 Days", "In 1 Week", "Custom Date"],
                        key=f"timing_{sel_lead_id}"
                    )
                    now_dt = datetime.datetime.now()
                    if timing_choice == "Tomorrow (+1 Day)":
                        target_dt = now_dt + datetime.timedelta(days=1)
                        target_iso = target_dt.strftime("%Y-%m-%d 11:00:00")
                    elif timing_choice == "In 3 Days":
                        target_dt = now_dt + datetime.timedelta(days=3)
                        target_iso = target_dt.strftime("%Y-%m-%d 11:00:00")
                    elif timing_choice == "In 1 Week":
                        target_dt = now_dt + datetime.timedelta(days=7)
                        target_iso = target_dt.strftime("%Y-%m-%d 11:00:00")
                    else:
                        cust_date = st.date_input("Select Date:", value=now_dt.date() + datetime.timedelta(days=2), key=f"cust_d_{sel_lead_id}")
                        cust_time = st.time_input("Select Time:", value=datetime.time(11, 0), key=f"cust_t_{sel_lead_id}")
                        target_iso = f"{cust_date.isoformat()} {cust_time.strftime('%H:%M:%S')}"
                        
                with sc_col2:
                    fu_channel = st.selectbox("Channel:", options=["WhatsApp", "Phone Call", "Email", "In-Person Consultation"], key=f"fu_chan_{sel_lead_id}")
                    fu_note = st.text_input("Follow-up Note / Objective:", value="Follow up on quotation & schedule meeting at Miyapur office", key=f"fu_note_{sel_lead_id}")
                    
                if st.button("📅 Schedule Follow-up Task", type="primary", key=f"btn_sched_task_{sel_lead_id}"):
                    res_sch = database.schedule_single_followup(
                        lead_id=sel_lead_id,
                        scheduled_for=target_iso,
                        channel=fu_channel,
                        message=fu_note
                    )
                    if res_sch["success"]:
                        st.success(f"✅ Follow-up task scheduled for **{target_iso}** via **{fu_channel}** (Task ID: `{res_sch['schedule_id']}`).")
                        st.rerun()

            # Expandable WhatsApp Customer Chat History (Part 5)
            with st.expander("💬 Chat History", expanded=False):
                history_records = database.get_conversation_history(sel_lead_id, limit=50)
                if not history_records:
                    st.info("No recorded conversation messages yet for this customer.")
                else:
                    st.caption(f"Showing complete conversation history for **{lead_rec.get('customer_name')}** ({len(history_records)} recorded interactions):")
                    # Display messages in chronological order, with newest at bottom
                    for msg in reversed(history_records):
                        direction = msg.get("direction", "incoming")
                        status = msg.get("sending_status", "Draft")
                        created = msg.get("created_at", "")
                        content = msg.get("message_content", "")
                        ai_reply = msg.get("ai_generated_response", "")

                        if direction == "incoming":
                            st.markdown(f"""
                            <div style="background-color:#F8FAFC; border-left:4px solid #3B82F6; padding:12px 16px; border-radius:8px; margin-bottom:10px; box-shadow:0 1px 2px rgba(0,0,0,0.04);">
                                <div style="display:flex; justify-content:space-between; font-size:0.78rem; color:#64748B; font-weight:600;">
                                    <span>📥 INCOMING CUSTOMER MESSAGE</span>
                                    <span>🕒 {created}</span>
                                </div>
                                <div style="font-size:0.95rem; color:#0F172A; margin-top:6px; line-height:1.45;">{content}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            status_color = "#16A34A" if status == "User-Confirmed Sent" else ("#2563EB" if status == "Ready to Send" else "#D97706")
                            st.markdown(f"""
                            <div style="background-color:#F0FDF4; border-left:4px solid {status_color}; padding:12px 16px; border-radius:8px; margin-bottom:10px; box-shadow:0 1px 2px rgba(0,0,0,0.04);">
                                <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.78rem; color:#64748B; font-weight:600;">
                                    <span>📤 OUTGOING WHATSAPP REPLY • 🕒 {created}</span>
                                    <span style="background-color:{status_color}; color:white; padding:2px 10px; border-radius:12px; font-size:0.72rem; font-weight:700;">{status}</span>
                                </div>
                                <div style="font-size:0.95rem; color:#0F172A; margin-top:6px; line-height:1.45;">{content}</div>
                            </div>
                            """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # TAB 2: TASK MANAGEMENT & SCHEDULE (PHASES 3B, 3C, 3D)
    # -------------------------------------------------------------
    with tabs[1]:
        st.markdown("### 📅 Follow-up Task Management")
        st.caption("Active priority tasks across Hyderabad localities. Filter by status, channel, priority, and locality.")
        
        # Interactive Filter Bar
        f_exp = st.expander("🔍 Task Filters & Search", expanded=True)
        with f_exp:
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                status_filter = st.selectbox("Task Status", options=["All", "Scheduled", "Due", "Sent", "Completed", "Cancelled"], key="task_stat_sel")
            with fc2:
                fu_reg_filter = st.selectbox("Hyderabad Region", options=hg.DISPLAY_REGION_OPTIONS, key="task_reg_sel")
            with fc3:
                fu_locs = ["All Localities"] + hg.get_localities_for_region(fu_reg_filter)
                fu_loc_filter = st.selectbox("Hyderabad Locality", options=fu_locs, key="task_loc_sel")
                
            fc4, fc5, fc6 = st.columns(3)
            with fc4:
                prio_filter = st.selectbox("Lead Priority", options=["All", "High", "Medium", "Low"], key="task_prio_sel")
            with fc5:
                chan_filter = st.selectbox("Follow-up Channel", options=["All", "WhatsApp", "Phone Call", "Email"], key="task_chan_sel")
            with fc6:
                due_filter = st.selectbox("Due Timing Window", options=["All Tasks", "Due Today", "Overdue", "Upcoming", "Completed"], key="task_due_sel")

        # Query Database with All Applied Filters
        mapped_due = None
        if due_filter == "Due Today":
            mapped_due = "today"
        elif due_filter == "Overdue":
            mapped_due = "overdue"
        elif due_filter == "Upcoming":
            mapped_due = "upcoming"
        elif due_filter == "Completed":
            mapped_due = "completed"

        followups_list = database.get_followups(
            status=status_filter if status_filter != "All" else None,
            locality=fu_loc_filter if fu_loc_filter != "All Localities" else None,
            region=fu_reg_filter if fu_reg_filter != "All Regions" else None,
            priority=prio_filter if prio_filter != "All" else None,
            channel=chan_filter if chan_filter != "All" else None,
            due_filter=mapped_due,
            active_only=True,
            limit=150
        )
        
        st.markdown(f"**Showing {len(followups_list)} matching follow-up tasks**")
        
        if followups_list:
            df_fu = pd.DataFrame(followups_list)
            df_fu["locality"] = df_fu["locality"].fillna("Unmapped")
            df_fu["region"] = df_fu["region"].fillna("Hyderabad")
            df_fu["assigned_salesperson"] = df_fu["assigned_salesperson"].fillna("Senior Interior Consultant")
            
            # Format display dataframe with rich intelligent task columns
            cols_show = [
                "schedule_id", "customer_name", "phone", "locality", "priority",
                "channel", "scheduled_for", "status", "next_action", "followup_reason", "completion_notes"
            ]
            cols_existing = [c for c in cols_show if c in df_fu.columns]
            rename_map = {
                "schedule_id": "Task ID",
                "customer_name": "Customer Name",
                "phone": "Phone Number",
                "locality": "Locality",
                "priority": "Priority",
                "channel": "Channel",
                "scheduled_for": "Due Date & Time",
                "status": "Task Status",
                "next_action": "Recommended Next Action",
                "followup_reason": "Reason for Follow-up",
                "completion_notes": "Completion Notes"
            }
            display_fu = df_fu[cols_existing].rename(columns=rename_map)
            st.dataframe(display_fu, use_container_width=True, hide_index=True)
            
            # Action Panel for Selected Task (Phase 3D & Upgraded Task Management)
            st.markdown("---")
            st.markdown("##### ⚡ Execute & Manage Selected Follow-up Task")
            task_choice_map = {
                f"{t['schedule_id']} — {t['customer_name']} ({t.get('locality') or 'Hyderabad'}) • {t['channel']} [{t['status']}]": t['schedule_id']
                for t in followups_list
            }
            selected_task_label = st.selectbox("Select Task to Manage / Execute:", options=list(task_choice_map.keys()))
            selected_sched_id = task_choice_map[selected_task_label]
            task_detail = database.get_followup_by_id(selected_sched_id)
            
            if task_detail:
                # Display task summary cards
                prio_val = task_detail.get('priority') or 'Medium'
                prio_c = "#DC2626" if prio_val == "High" else ("#D97706" if prio_val == "Medium" else "#4B5563")
                status_c = "#16A34A" if task_detail['status'] == "Completed" else ("#2563EB" if task_detail['status'] == "Scheduled" else "#DC2626")
                
                st.markdown(f"""
                <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">
                        <span style="font-weight:700; font-size:1.05rem; color:#0F172A;">Task {task_detail['schedule_id']} — {task_detail['customer_name']}</span>
                        <div>
                            <span style="background-color:{prio_c}; color:white; padding:2px 10px; border-radius:10px; font-size:0.75rem; font-weight:700; margin-right:6px;">{prio_val}</span>
                            <span style="background-color:{status_c}; color:white; padding:2px 10px; border-radius:10px; font-size:0.75rem; font-weight:700;">{task_detail['status']}</span>
                        </div>
                    </div>
                    <div style="font-size:0.9rem; color:#334155; margin-bottom:4px;">
                        <strong>Phone:</strong> {task_detail['phone']} | <strong>Locality:</strong> {task_detail.get('locality', 'Hyderabad')} | <strong>Channel:</strong> {task_detail['channel']} | <strong>Scheduled:</strong> {task_detail['scheduled_for']}
                    </div>
                    <div style="font-size:0.9rem; color:#1E3A8A; margin-bottom:4px;">
                        <strong>Reason:</strong> {task_detail.get('followup_reason') or 'Routine Follow-up'}
                    </div>
                    <div style="font-size:0.9rem; color:#0F766E; margin-bottom:6px;">
                        <strong>Next Action:</strong> {task_detail.get('next_action') or 'Follow up with customer'}
                    </div>
                    <div style="font-size:0.88rem; color:#1E293B; background:white; padding:8px 12px; border-radius:6px; border:1px solid #E2E8F0;">
                        <strong>Message:</strong> "{task_detail['message']}"
                    </div>
                    {f"<div style='font-size:0.85rem; color:#166534; margin-top:6px;'><strong>Completion Notes:</strong> {task_detail.get('completion_notes')}</div>" if task_detail.get('completion_notes') else ""}
                    {f"<div style='font-size:0.85rem; color:#D97706; margin-top:6px;'><strong>Rescheduled from:</strong> {task_detail.get('rescheduled_from')} (Reason: {task_detail.get('rescheduled_reason')})</div>" if task_detail.get('rescheduled_from') else ""}
                </div>
                """, unsafe_allow_html=True)
                
                # Management Sub-tabs: 1. Complete Task, 2. Reschedule Task, 3. Edit Task, 4. WhatsApp & Cancel
                mgmt_tab1, mgmt_tab2, mgmt_tab3, mgmt_tab4 = st.tabs([
                    "✅ Complete Task",
                    "📅 Reschedule Task",
                    "✍️ Edit Task Details",
                    "💬 WhatsApp & Cancel"
                ])
                
                with mgmt_tab1:
                    st.markdown("###### Record Task Completion & Notes")
                    comp_notes = st.text_area(
                        "Completion Notes (Mandatory for record-keeping):",
                        placeholder="e.g., Spoke with customer. Discussed 3D floor plan layout. Customer booked an appointment at Miyapur office.",
                        key=f"comp_notes_{selected_sched_id}"
                    )
                    if st.button("Mark Task as Completed", type="primary", key=f"btn_mark_comp_{selected_sched_id}"):
                        if not comp_notes.strip():
                            st.error("Please enter completion notes describing the outcome before marking completed.")
                        else:
                            ok = database.complete_followup_task(selected_sched_id, comp_notes.strip())
                            if ok:
                                st.success(f"✅ Task {selected_sched_id} completed successfully!")
                                st.rerun()
                                
                with mgmt_tab2:
                    st.markdown("###### Reschedule Follow-up to a New Date/Time")
                    rc1, rc2 = st.columns(2)
                    with rc1:
                        new_resched_date = st.date_input("New Due Date:", value=datetime.date.today() + datetime.timedelta(days=2), key=f"resched_d_{selected_sched_id}")
                        new_resched_time = st.time_input("New Due Time:", value=datetime.time(11, 0), key=f"resched_t_{selected_sched_id}")
                    with rc2:
                        ch_opts = ["WhatsApp", "Phone Call", "Email", "In-Person Consultation"]
                        curr_ch_idx = ch_opts.index(task_detail["channel"]) if task_detail["channel"] in ch_opts else 0
                        new_resched_channel = st.selectbox("Channel:", options=ch_opts, index=curr_ch_idx, key=f"resched_c_{selected_sched_id}")
                        resched_reason = st.text_input("Reason for Rescheduling:", placeholder="e.g., Customer requested call next Tuesday after site handover", key=f"resched_r_{selected_sched_id}")
                        
                    if st.button("Confirm Reschedule", type="primary", key=f"btn_confirm_resched_{selected_sched_id}"):
                        if not resched_reason.strip():
                            st.error("Please provide a reason for rescheduling.")
                        else:
                            new_iso = f"{new_resched_date.isoformat()} {new_resched_time.strftime('%H:%M:%S')}"
                            res_resched = database.reschedule_followup_task(
                                schedule_id=selected_sched_id,
                                new_scheduled_for=new_iso,
                                reschedule_reason=resched_reason.strip(),
                                new_channel=new_resched_channel
                            )
                            if res_resched.get("success"):
                                st.success(f"✅ Task rescheduled to {new_iso}!")
                                st.rerun()
                                
                with mgmt_tab3:
                    st.markdown("###### Edit Task Content & Priority")
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        p_opts = ["High", "Medium", "Low"]
                        curr_p_idx = p_opts.index(task_detail.get("priority", "Medium")) if task_detail.get("priority", "Medium") in p_opts else 1
                        edit_prio = st.selectbox("Priority:", options=p_opts, index=curr_p_idx, key=f"edit_prio_{selected_sched_id}")
                        edit_reason = st.text_input("Follow-up Reason:", value=task_detail.get("followup_reason") or "", key=f"edit_reason_{selected_sched_id}")
                    with ec2:
                        edit_action = st.text_input("Next Action:", value=task_detail.get("next_action") or "", key=f"edit_action_{selected_sched_id}")
                        edit_summary = st.text_input("Task Summary:", value=task_detail.get("task_summary") or "", key=f"edit_sum_{selected_sched_id}")
                        
                    edit_msg = st.text_area("Task Message / Draft:", value=task_detail.get("message") or "", height=90, key=f"edit_msg_{selected_sched_id}")
                    
                    if st.button("Save Task Updates", type="primary", key=f"btn_save_edit_{selected_sched_id}"):
                        ok = database.edit_followup_task(
                            schedule_id=selected_sched_id,
                            message=edit_msg.strip(),
                            followup_reason=edit_reason.strip(),
                            next_action=edit_action.strip(),
                            priority=edit_prio,
                            task_summary=edit_summary.strip()
                        )
                        if ok:
                            st.success("✅ Task updated successfully!")
                            st.rerun()
                            
                with mgmt_tab4:
                    st.markdown("###### Dispatch & Status Actions")
                    act_c1, act_c2, act_c3 = st.columns(3)
                    with act_c1:
                        if task_detail["channel"] == "WhatsApp":
                            task_wa_url, task_wa_err = whatsapp_assistant.build_whatsapp_click_to_chat_url(
                                task_detail["phone"],
                                task_detail["message"]
                            )
                            if task_wa_url:
                                st.markdown(f'<a href="{task_wa_url}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366;color:white;border:none;padding:9px 16px;border-radius:6px;font-weight:700;width:100%;cursor:pointer;">💬 Open WhatsApp Chat</button></a>', unsafe_allow_html=True)
                            else:
                                st.caption(f"No WhatsApp: {task_wa_err}")
                        else:
                            st.caption(f"Channel is {task_detail['channel']}")
                    with act_c2:
                        if st.button("✅ Mark as Sent", key=f"btn_sent_{selected_sched_id}", use_container_width=True):
                            now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            database.update_followup_status(selected_sched_id, status="Sent", completed_at=now_iso)
                            database.insert_activity_log(
                                lead_id=task_detail["lead_id"],
                                activity_type=f"Follow-up Dispatched ({task_detail['channel']})",
                                activity_description=f"Task {selected_sched_id} marked as Sent via {task_detail['channel']}."
                            )
                            st.success(f"Task {selected_sched_id} marked as Sent!")
                            st.rerun()
                    with act_c3:
                        if st.button("🚫 Cancel Task", key=f"btn_cancel_{selected_sched_id}", use_container_width=True):
                            now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            database.update_followup_status(selected_sched_id, status="Cancelled", completed_at=now_iso, stop_reason="Manually cancelled by sales representative")
                            st.warning(f"Task {selected_sched_id} cancelled.")
                            st.rerun()
        else:
            st.info("No follow-up tasks match the selected filters.")

    # -------------------------------------------------------------
    # TAB 3: INBOUND CUSTOMER RESPONSE SIMULATOR (PRESERVED)
    # -------------------------------------------------------------
    with tabs[2]:
        st.markdown("### 📥 Inbound Customer Response Simulator")
        st.caption("Simulate a customer replying on WhatsApp or Phone. This immediately halts all future automated touches and alerts the sales team.")
        
        all_leads_for_resp = database.get_all_leads(active_only=True)
        active_leads = [l for l in all_leads_for_resp if l.get("lead_status") not in ["Converted", "Lost"]]
        
        sel_resp_lead = st.selectbox(
            "Select Client who responded:",
            options=[f"{l['lead_id']} - {l['customer_name']} ({l.get('locality') or 'Hyderabad'})" for l in active_leads],
            key="inbound_sim_sel"
        )
        resp_text = st.text_area(
            "Customer Inbound Message:",
            "Hello! Yes, I am interested in scheduling a site visit this Saturday at 11 AM.",
            key="inbound_sim_text"
        )
        
        if st.button("Record Customer Response & Halt Automated Outreach", type="primary", key="btn_inbound_sim"):
            target_id = sel_resp_lead.split(" - ")[0]
            resp_res = followups.simulate_customer_response(target_id, resp_text)
            if resp_res["success"]:
                st.success(f"🎉 {resp_res['message']}")
                st.info(f"Lead **{target_id}** is now flagged as 'Responded'. Assigned designer must take over personal consultation.")
                st.rerun()
            else:
                st.error(f"❌ {resp_res['error']}")

    # -------------------------------------------------------------
    # TAB 4: COMPLIANCE & OPT-OUT CONTROLS (PRESERVED & ENHANCED)
    # -------------------------------------------------------------
    with tabs[3]:
        st.markdown("### 🛡️ Compliance & Sales Controls (Opt-Out / Pause)")
        st.caption("Record customer communication preferences, opt-out requests, or temporary outreach pauses.")
        c_opt1, c_opt2 = st.columns(2)
        with c_opt1:
            st.markdown("###### Customer Communication Opt-Out")
            opt_lead_sel = st.selectbox(
                "Select Lead to Opt-Out:",
                options=[f"{l['lead_id']} - {l['customer_name']}" for l in all_leads_for_resp],
                key="opt_sel"
            )
            opt_reason = st.text_input("Opt-Out Reason:", "Customer chose another design firm / requested no calls")
            if st.button("Mark as Opted-Out", type="secondary", key="btn_apply_optout"):
                t_id = opt_lead_sel.split(" - ")[0]
                opt_res = followups.mark_lead_opt_out(t_id, reason=opt_reason)
                st.warning(f"⚠️ {opt_res['message']}")
                st.rerun()
                
        with c_opt2:
            st.markdown("###### Pause / Resume Outreach")
            pause_lead_sel = st.selectbox(
                "Select Lead to Pause/Resume:",
                options=[f"{l['lead_id']} - {l['customer_name']}" for l in all_leads_for_resp],
                key="pause_sel"
            )
            p_action = st.radio("Action:", options=["Pause Automated Outreach", "Resume Automated Outreach"])
            if st.button("Apply Pause / Resume Setting", key="btn_apply_pause"):
                t_id = pause_lead_sel.split(" - ")[0]
                pause_res = followups.pause_or_resume_lead_followups(t_id, pause=("Pause" in p_action))
                st.success(f"✅ {pause_res['message']}")
                st.rerun()

    # -------------------------------------------------------------
    # TAB 5: MASS CADENCE SCHEDULER (PRESERVED)
    # -------------------------------------------------------------
    with tabs[4]:
        st.markdown("### ⚡ Schedule Cadences for All Eligible Leads")
        st.write("Generates automated multi-touch sequences (High: 3 touches, Medium: 3 touches, Low: 2 touches) for all unfinalized leads.")
        if st.button("Run Batch Follow-up Scheduler Now", type="primary", key="btn_run_batch"):
            with st.spinner("Scheduling cadences across all eligible CRM leads..."):
                batch_res = followups.schedule_followups_for_all_eligible_leads()
                st.success(f"✅ Scheduled **{batch_res['total_tasks_scheduled']} tasks** across **{batch_res['eligible_leads']} eligible leads**. (Skipped {batch_res['skipped_leads']} converted/lost/opted-out leads).")
                st.rerun()

# ==============================================================================
# 4. REPORTS AND ANALYTICS
# ==============================================================================
elif page == "Reports and Analytics":
    st.markdown('<div class="main-header">Reports & Conversion Analytics Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Comprehensive studio analytics, conversion rates, and downloadable operational reports.</div>', unsafe_allow_html=True)

    # Dataset Scope Selector (Requirements 83 & 84)
    rscope_col1, rscope_col2 = st.columns([2.5, 1.5])
    with rscope_col1:
        rep_scope_choice = st.radio(
            "📊 Analytics Dataset Scope:",
            options=["All Leads (Including Test Data)", "Genuine Customer Leads Only", "Test Leads Only"],
            horizontal=True,
            index=0,
            key="reports_dataset_scope_radio"
        )
    with rscope_col2:
        scope_map = {
            "All Leads (Including Test Data)": "all",
            "Genuine Customer Leads Only": "genuine_only",
            "Test Leads Only": "test_only"
        }
        active_rep_scope = scope_map[rep_scope_choice]
        if active_rep_scope == "genuine_only":
            st.info("👤 Genuine Customers Only (Excludes Test Data)")
        elif active_rep_scope == "test_only":
            st.warning("🧪 Test Leads Only (Isolated Test Environment)")
        else:
            st.success("🌐 Unified Dataset (Genuine Customers + Test Leads)")

    kpis = reports.get_executive_kpis(dataset_scope=active_rep_scope)
    charts = reports.get_chart_data(dataset_scope=active_rep_scope)

    # Metric Row
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.metric("Total Active Leads", kpis["total_leads"])
    with r2:
        st.metric("Engaged Conversion Rate", f"{kpis['engaged_conversion_rate']}%", help="Converted / (Converted + Lost + Follow-up + Qualified) * 100")
    with r3:
        st.metric("Overall Conversion Rate", f"{kpis['overall_conversion_rate']}%", help="Converted / Total Leads * 100")
    with r4:
        st.metric("Avg Lead Score", f"{kpis['average_lead_score']}/100")

    st.markdown("---")
    st.markdown("### 📊 Studio Lead Breakdown (9 Analytics Dimensions)")
    
    c_tab1, c_tab2, c_tab3 = st.tabs(["🏙️ Geography & Demographics", "🏡 Project Type & Budget", "📅 Timeline & Trends"])
    
    with c_tab1:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("##### 1. Leads by Hyderabad Region")
            if "region" in charts and not charts["region"].empty:
                st.bar_chart(charts["region"].set_index("Region"), color="#10B981")
            else:
                st.info("No regional data available.")
        with col_g2:
            st.markdown("##### 2. Top 10 Hyderabad Localities")
            if "locality" in charts and not charts["locality"].empty:
                st.bar_chart(charts["locality"].set_index("Locality"), color="#6366F1")
            else:
                st.info("No locality data available.")
            
    with c_tab2:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("##### 3. Leads by Project Type")
            st.bar_chart(charts["project_type"].set_index("Project Type"), color="#F59E0B")
        with col_p2:
            st.markdown("##### 4. Leads by Budget Range")
            st.dataframe(charts["budget"], use_container_width=True, hide_index=True)
            if "origin" in charts and not charts["origin"].empty:
                st.markdown("##### 4b. Leads by Data Origin (Genuine vs Test Data)")
                st.dataframe(charts["origin"], use_container_width=True, hide_index=True)
            
    with c_tab3:
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("##### 5. Lead Status Pipeline Distribution")
            st.dataframe(charts["status"], use_container_width=True, hide_index=True)
        with col_t2:
            st.markdown("##### 6. Follow-up Status Distribution")
            st.dataframe(charts["followup"], use_container_width=True, hide_index=True)
            
        st.markdown("##### 7. Daily Lead Creation Trend")
        st.line_chart(charts["daily"].set_index("Date"), color="#2563EB")
        st.markdown("##### 8. Weekly Lead Creation Trend")
        st.line_chart(charts["weekly"].set_index("Week"), color="#8B5CF6")

    st.markdown("---")
    st.markdown("### 📑 Periodic Performance Reports")
    
    p_type = st.radio("Select Report Window:", options=["Daily Report", "Weekly Report", "Custom Date Range"], horizontal=True)
    if p_type == "Daily Report":
        rep = reports.generate_periodic_report("daily")
    elif p_type == "Weekly Report":
        rep = reports.generate_periodic_report("weekly")
    else:
        dcol1, dcol2 = st.columns(2)
        with dcol1:
            s_d = st.date_input("Start Date", datetime.date(2026, 7, 1))
        with dcol2:
            e_d = st.date_input("End Date", datetime.date(2026, 10, 31))
        rep = reports.generate_periodic_report("custom", str(s_d), str(e_d))

    st.markdown(f"#### {rep['period_label']}")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.metric("New Leads in Period", rep["new_leads_count"])
    with p2:
        st.metric("Converted in Period", rep["converted_count"])
    with p3:
        st.metric("Period Conversion Rate", f"{rep['period_conversion_rate']}%")
    with p4:
        st.metric("Average Score", f"{rep['average_period_score']}/100")

    if not rep["leads_table"].empty:
        rep_df = rep["leads_table"].copy()
        if "locality" not in rep_df.columns:
            rep_df["locality"] = "Unmapped"
        else:
            rep_df["locality"] = rep_df["locality"].fillna("Unmapped")
        if "region" not in rep_df.columns:
            rep_df["region"] = "Unspecified"
        else:
            rep_df["region"] = rep_df["region"].fillna("Unspecified")
        show_cols = ["lead_id", "customer_name", "locality", "region", "project_type", "budget_range", "lead_score", "priority", "lead_status"]
        st.dataframe(rep_df[show_cols].rename(columns={
            "lead_id": "Lead ID", "customer_name": "Customer Name", "locality": "Locality", "region": "Region",
            "project_type": "Project Type", "budget_range": "Budget", "lead_score": "Score", "priority": "Priority", "lead_status": "Status"
        }), use_container_width=True, hide_index=True)
        
        # CSV Export
        csv_data = rep["leads_table"].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Report as CSV",
            data=csv_data,
            file_name=f"sha_report_{rep['start_date']}_to_{rep['end_date']}.csv",
            mime="text/csv"
        )

# ==============================================================================
# 5. AI ASSISTANT - ADVANCED AI CRM & INTERIOR DESIGN INTELLIGENCE SUITE
# ==============================================================================
elif page == "AI Assistant":
    st.markdown('<div class="main-header">SHA Interiors AI Intelligence Suite</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Unified CRM Data Analyst, Interior Design Specialist, Materials Consultant, Cost Estimator & Sales Copilot.</div>', unsafe_allow_html=True)

    ai_info = ai_assistant.get_ai_status_info()
    if ai_info["gemini_active"]:
        st.success(f"🟢 **Google Gemini AI Active** (Model: `{ai_info['model']}`). Conversational reasoning grounded in live SQLite database records and verified business knowledge bases.")
    else:
        st.info("🟡 **Built-in CRM & Interior Intelligence Engine Active** (Deterministic SQL rules & offline expert repository). Configure `GEMINI_API_KEY` in `.env` to enable generative synthesis.")

    ai_tabs = st.tabs([
        "💬 Conversational Copilot",
        "👤 Customer 360° Brief",
        "💰 Project Cost Estimator",
        "📐 Interior Styles & Layouts",
        "🪵 Materials & Hardware Reference",
        "📅 Follow-Up Command Center"
    ])
    
    # --------------------------------------------------------------------------
    # TAB 1: Conversational Copilot & Advanced CRM Search Engine
    # --------------------------------------------------------------------------
    with ai_tabs[0]:
        st.markdown("##### 🤖 Intelligent CRM Search Engine & Conversational Sales Copilot")
        st.caption("Ask natural-language questions across CRM records, or use the Advanced Filters panel to query leads in real-time.")

        # Initialize session states
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "filter_search_results" not in st.session_state:
            st.session_state.filter_search_results = None


        # ----------------------------------------------------------------------
        # PART 3: ADVANCED SEARCH FILTERS PANEL (EXPANDABLE)
        # ----------------------------------------------------------------------
        with st.expander("🔍 Advanced CRM Search & Lead Filters", expanded=False):
            st.markdown("Filter actual CRM leads across multiple dimensions simultaneously:")
            
            f_row1_c1, f_row1_c2, f_row1_c3 = st.columns(3)
            with f_row1_c1:
                af_name = st.text_input("Customer Name:", value=st.session_state.get("af_name", ""), placeholder="e.g. Kanishka, Dinesh...", key="input_af_name")
            with f_row1_c2:
                af_phone = st.text_input("Phone Number:", value=st.session_state.get("af_phone", ""), placeholder="e.g. 90001, 85005...", key="input_af_phone")
            with f_row1_c3:
                all_locs = ["All"] + hg.get_all_localities()
                af_loc_idx = all_locs.index(st.session_state.get("af_loc", "All")) if st.session_state.get("af_loc", "All") in all_locs else 0
                af_loc = st.selectbox("Locality / Corridor:", options=all_locs, index=af_loc_idx, key="input_af_loc")

            f_row2_c1, f_row2_c2, f_row2_c3 = st.columns(3)
            with f_row2_c1:
                pt_opts = ["All", "1BHK", "2BHK", "3BHK", "4BHK", "Villa", "Commercial"]
                af_pt_idx = pt_opts.index(st.session_state.get("af_pt", "All")) if st.session_state.get("af_pt", "All") in pt_opts else 0
                af_pt = st.selectbox("Project Type:", options=pt_opts, index=af_pt_idx, key="input_af_pt")
            with f_row2_c2:
                prio_opts = ["All", "High", "Medium", "Low"]
                af_prio_idx = prio_opts.index(st.session_state.get("af_prio", "All")) if st.session_state.get("af_prio", "All") in prio_opts else 0
                af_prio = st.selectbox("Lead Priority:", options=prio_opts, index=af_prio_idx, key="input_af_prio")
            with f_row2_c3:
                st_opts = ["All", "New", "Qualified", "Follow-up", "Converted", "Lost"]
                af_st_idx = st_opts.index(st.session_state.get("af_st", "All")) if st.session_state.get("af_st", "All") in st_opts else 0
                af_st = st.selectbox("Lead Status:", options=st_opts, index=af_st_idx, key="input_af_st")

            f_row3_c1, f_row3_c2, f_row3_c3, f_row3_c4 = st.columns(4)
            with f_row3_c1:
                conv_opts = ["All", "Active / Not Converted", "Converted", "Lost"]
                af_conv_idx = conv_opts.index(st.session_state.get("af_conv", "All")) if st.session_state.get("af_conv", "All") in conv_opts else 0
                af_conv = st.selectbox("Conversion Status:", options=conv_opts, index=af_conv_idx, key="input_af_conv")
            with f_row3_c2:
                fu_opts = ["All", "Pending / Upcoming Follow-up", "Overdue Follow-up", "No Follow-up Scheduled"]
                af_fu_idx = fu_opts.index(st.session_state.get("af_fu", "All")) if st.session_state.get("af_fu", "All") in fu_opts else 0
                af_fu = st.selectbox("Follow-up Status:", options=fu_opts, index=af_fu_idx, key="input_af_fu")
            with f_row3_c3:
                af_min_b = st.number_input("Min Budget (₹ Lakh):", min_value=0.0, max_value=100.0, value=float(st.session_state.get("af_min_b", 0.0)), step=1.0, key="input_af_min_b")
            with f_row3_c4:
                af_max_b = st.number_input("Max Budget (₹ Lakh):", min_value=0.0, max_value=100.0, value=float(st.session_state.get("af_max_b", 100.0)), step=1.0, key="input_af_max_b")

            f_row4_c1, f_row4_c2 = st.columns(2)
            with f_row4_c1:
                af_d_from = st.date_input("Created From Date:", value=datetime.date(2026, 1, 1), key="input_af_d_from")
            with f_row4_c2:
                af_d_to = st.date_input("Created To Date:", value=datetime.date(2026, 12, 31), key="input_af_d_to")

            btn_fcol1, btn_fcol2, btn_fcol3 = st.columns([1.5, 1.5, 3])
            with btn_fcol1:
                if st.button("🔍 Apply Filters", type="primary", use_container_width=True, key="btn_apply_filters"):
                    search_criteria = {
                        "name": af_name,
                        "phone": af_phone,
                        "locality": af_loc if af_loc != "All" else None,
                        "project_type": af_pt if af_pt != "All" else None,
                        "priority": af_prio if af_prio != "All" else None,
                        "lead_status": af_st if af_st != "All" else None,
                        "conversion_status": af_conv,
                        "followup_status": af_fu,
                        "min_budget_lakh": af_min_b if af_min_b > 0.0 else None,
                        "max_budget_lakh": af_max_b if af_max_b < 100.0 else None,
                        "date_from": str(af_d_from),
                        "date_to": str(af_d_to)
                    }
                    res = crm_search.search_crm_leads(search_criteria)
                    st.session_state.filter_search_results = res
                    st.rerun()

            with btn_fcol2:
                if st.button("🧹 Clear Filters", use_container_width=True, key="btn_clear_filters"):
                    st.session_state.filter_search_results = None
                    st.session_state.af_name = ""
                    st.session_state.af_phone = ""
                    st.session_state.af_loc = "All"
                    st.session_state.af_pt = "All"
                    st.session_state.af_prio = "All"
                    st.session_state.af_st = "All"
                    st.session_state.af_conv = "All"
                    st.session_state.af_fu = "All"
                    st.session_state.af_min_b = 0.0
                    st.session_state.af_max_b = 100.0
                    st.rerun()

            # Display Filter Results if present
            if st.session_state.filter_search_results:
                f_res = st.session_state.filter_search_results
                total_f = f_res.get("total_count", 0)
                hp_f = f_res.get("high_priority_count", 0)
                mp_f = f_res.get("medium_priority_count", 0)
                lp_f = f_res.get("low_priority_count", 0)
                f_leads = f_res.get("leads", [])

                st.markdown("---")
                st.markdown(f"#### 🎯 Matching Results: **{total_f} Lead{'s' if total_f != 1 else ''} Found**")
                st.caption(f"**Applied Filters:** {f_res.get('filter_summary', 'None')}")

                m_col1, m_col2, m_col3 = st.columns(3)
                m_col1.metric("🟢 High Priority", hp_f)
                m_col2.metric("🟡 Medium Priority", mp_f)
                m_col3.metric("🔴 Low Priority", lp_f)

                if total_f > 0:
                    import pandas as pd
                    display_rows = []
                    for l in f_leads:
                        display_rows.append({
                            "Lead ID": l.get("lead_id"),
                            "Customer Name": l.get("customer_name"),
                            "Phone": l.get("phone"),
                            "Locality": l.get("locality") or l.get("city"),
                            "Project Type": l.get("project_type"),
                            "Budget": l.get("budget_range"),
                            "Score": f"{float(l.get('lead_score') or 0.0):.0f}",
                            "Priority": l.get("priority"),
                            "Status": l.get("lead_status"),
                            "Next Follow-up": l.get("next_followup_desc")
                        })
                    st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)

                    # Individual Lead Inspector
                    st.markdown("##### 👤 Inspect Lead Details:")
                    lead_choices = [f"{l['lead_id']} — {l['customer_name']} ({l.get('locality') or 'Hyderabad'})" for l in f_leads]
                    chosen_lead_str = st.selectbox("Select lead to inspect:", options=lead_choices, key="sel_filter_inspect")
                    if chosen_lead_str:
                        target_lid = chosen_lead_str.split(" — ")[0]
                        insp_lead = database.get_lead_by_id(target_lid)
                        if insp_lead:
                            st.markdown(f"""
                            <div style="background-color:#F8FAFC; border:1px solid #CBD5E1; border-radius:8px; padding:14px 18px; margin-top:8px;">
                                <div style="font-weight:700; font-size:1.05rem; color:#0F172A;">{insp_lead.get('customer_name')} ({insp_lead.get('lead_id')})</div>
                                <div style="font-size:0.85rem; color:#475569; margin-top:4px;">
                                    📞 <b>Phone:</b> {insp_lead.get('phone')} &nbsp;|&nbsp; ✉️ <b>Email:</b> {insp_lead.get('email') or 'N/A'} &nbsp;|&nbsp; 📍 <b>Locality:</b> {insp_lead.get('locality')} ({insp_lead.get('region')})
                                </div>
                                <div style="font-size:0.85rem; color:#475569; margin-top:4px;">
                                    🏡 <b>Property:</b> {insp_lead.get('project_type')} ({insp_lead.get('property_status')}) &nbsp;|&nbsp; 💰 <b>Budget:</b> {insp_lead.get('budget_range')} &nbsp;|&nbsp; 🎯 <b>Score:</b> {insp_lead.get('lead_score')}/100 ({insp_lead.get('priority')} Priority)
                                </div>
                                <div style="font-size:0.85rem; color:#334155; margin-top:8px; background:#FFFFFF; padding:8px 12px; border-radius:6px; border:1px solid #E2E8F0;">
                                    <b>Customer Requirements Notes:</b><br>{insp_lead.get('customer_requirements') or 'No custom notes.'}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("No leads in the CRM database matched the selected combination of filters. Try clearing or relaxing some criteria.")

        st.divider()

        # ----------------------------------------------------------------------
        # PART 1: CONVERSATION MESSAGES (SCROLLS INDEPENDENTLY)
        # ----------------------------------------------------------------------
        st.markdown("##### 💬 AI Assistant Conversation")

        # Fixed-height scrollable container: messages scroll smoothly inside
        chat_container = st.container(height=520)
        with chat_container:
            if not st.session_state.chat_history:
                st.caption("💬 Conversation history is empty. Ask a question or click a suggestion below to begin.")
            else:
                for idx_m, msg in enumerate(st.session_state.chat_history):
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
                        if msg["role"] == "assistant":
                            tts_code = voice_assistant.get_tts_html_snippet(msg["content"], snippet_id=f"tts_{idx_m}")
                            st.components.v1.html(tts_code, height=36)

        # ----------------------------------------------------------------------
        # COMPACT CLICKABLE AI SUGGESTIONS (NEAR INPUT BOX)
        # ----------------------------------------------------------------------
        st.markdown("<div style='font-size:0.8rem; color:#64748B; margin-bottom:4px; font-weight:600;'>💡 Suggestions:</div>", unsafe_allow_html=True)
        sug_col1, sug_col2, sug_col3, sug_col4, sug_col5 = st.columns(5)
        quick_query = None
        if sug_col1.button("🔥 High Priority", use_container_width=True, key="sug_high_prio"):
            quick_query = "Show all high-priority leads"
        if sug_col2.button("📍 Gachibowli", use_container_width=True, key="sug_gachibowli"):
            quick_query = "Find customers in Gachibowli"
        if sug_col3.button("💰 > ₹10 Lakh", use_container_width=True, key="sug_above_10l"):
            quick_query = "Show customers with budgets above ₹10 lakh"
        if sug_col4.button("🍳 3BHK Leads", use_container_width=True, key="sug_3bhk"):
            quick_query = "Find all 3BHK customers"
        if sug_col5.button("⏰ Pending F/U", use_container_width=True, key="sug_pending_fu"):
            quick_query = "Show leads with pending follow-ups"

        # ----------------------------------------------------------------------
        # UNIFIED CHAT COMPOSER (TEXT INPUT + INLINE MICROPHONE + SEND BUTTON)
        # ----------------------------------------------------------------------
        user_input = st.chat_input("Ask CRM Assistant anything or speak your question...")
        st.components.v1.html(voice_assistant.get_unified_chat_composer_bridge(), height=0)
        active_query = user_input or quick_query

        if active_query:
            # Append user turn
            st.session_state.chat_history.append({"role": "user", "content": active_query})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(active_query)

            # Generate assistant response
            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("Searching CRM database & analyzing context..."):
                        history_for_api = st.session_state.chat_history[:-1]
                        answer = ai_assistant.answer_crm_query(active_query, history=history_for_api)
                        st.markdown(answer)
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()

        if st.session_state.chat_history:
            if st.button("🧹 Clear Chat History", key="clear_chat_history"):
                st.session_state.chat_history = []
                st.rerun()

    # --------------------------------------------------------------------------
    # TAB 2: Customer 360° & Consultation Brief
    # --------------------------------------------------------------------------
    with ai_tabs[1]:
        st.markdown("##### Customer 360° Profile & Sales Consultation Dossier")
        st.caption("Deep client analysis, factor-by-factor score explanations, missing data detection, and discovery questions.")

        all_leads_360 = database.get_all_leads(active_only=True)
        lead_options_360 = [f"{l['lead_id']} - {l['customer_name']} ({l.get('locality') or 'Hyderabad'} | {l['project_type']})" for l in all_leads_360]
        sel_lead_360 = st.selectbox("Select Customer to Review:", options=lead_options_360, key="lead_360_selector")

        if sel_lead_360:
            target_lead_id = sel_lead_360.split(" - ")[0]
            dossier = customer_intelligence.build_customer_360_dossier(target_lead_id)
            if dossier:
                st.markdown(customer_intelligence.format_customer_360_markdown(dossier))

                # Generative AI Executive Brief Button
                if ai_assistant.is_ai_api_available():
                    st.divider()
                    if st.button("✨ Generate AI Executive Design Brief (Gemini)", key="btn_gen_brief_tab2"):
                        lead_obj = database.get_lead_by_id(target_lead_id)
                        with st.spinner("Generating bespoke design brief with Gemini..."):
                            ai_brief = ai_assistant.summarize_customer_requirements_ai(lead_obj)
                            st.markdown("##### 🏛️ AI Executive Design Brief:")
                            st.markdown(ai_brief)

    # --------------------------------------------------------------------------
    # TAB 3: Interactive Project Cost Estimator
    # --------------------------------------------------------------------------
    with ai_tabs[2]:
        st.markdown("##### Parametric Interior Project Cost Estimator")
        st.caption("Estimate approximate budgeting across Essential, Premium, and Luxury packages based on square footage and city index.")

        ecol1, ecol2, ecol3 = st.columns(3)
        with ecol1:
            prop_type_sel = st.selectbox("Property Type:", ["1BHK", "2BHK", "3BHK", "4BHK", "Villa", "Studio", "Commercial"], index=2)
            default_area = cost_estimator.DEFAULT_PROPERTY_AREAS.get(prop_type_sel, 1500)
        with ecol2:
            city_sel = st.selectbox("Project City / Hub:", ["Hyderabad", "Secunderabad", "Cyberabad", "Other"], index=0)
        with ecol3:
            area_input = st.number_input("Built-up Area (Sq Ft):", min_value=300, max_value=15000, value=default_area, step=50)

        scope_sel = st.selectbox("Scope of Work:", [
            "Complete Turnkey Interiors (Woodwork + False Ceiling + Civil + Paint)",
            "Modular Woodwork Only (Kitchen + Wardrobes + Consoles)",
            "Modular Kitchen Only"
        ])

        custom_w = st.slider("Number of Custom Wardrobes:", min_value=1, max_value=8, value=3 if "3BHK" in prop_type_sel else (2 if "2BHK" in prop_type_sel else 4))

        if st.button("⚡ Calculate Project Estimate", key="btn_calc_estimate"):
            with st.spinner("Calculating parametric estimates across quality tiers..."):
                est = cost_estimator.estimate_project_cost(
                    property_type=prop_type_sel,
                    built_up_area=area_input,
                    city=city_sel,
                    scope_of_work=scope_sel,
                    custom_wardrobes_count=custom_w
                )
                st.markdown(cost_estimator.format_cost_estimate_markdown(est))

    # --------------------------------------------------------------------------
    # TAB 4: Interior Styles & Layouts Guide
    # --------------------------------------------------------------------------
    with ai_tabs[3]:
        st.markdown("##### Interior Design Styles & Spatial Planning Guide")
        st.caption("Authoritative design principles, room-by-room space planning rules, and Vastu directional orientations.")

        style_choice = st.selectbox("Explore Design Style:", list(design_knowledge.DESIGN_STYLES.keys()), format_func=lambda k: design_knowledge.DESIGN_STYLES[k]["title"])
        style_info = design_knowledge.get_style_info(style_choice)
        if style_info:
            st.markdown(f"### {style_info['title']}")
            st.markdown(style_info["description"])
            
            scol1, scol2 = st.columns(2)
            with scol1:
                st.markdown("**Key Design Elements:**")
                for c in style_info["key_characteristics"]:
                    st.write(f"- {c}")
            with scol2:
                st.markdown(f"**Cost Tier:** `{style_info['cost_tier']}`")
                st.markdown(f"**Ideal For:** {', '.join(style_info['ideal_for'])}")
                st.markdown(f"**Signature Materials:** {', '.join(style_info['materials'])}")
                st.markdown(f"**Recommended Color Palette:** {', '.join(style_info['color_palette'])}")

        st.divider()
        st.markdown("##### Room-by-Room Spatial Planning & Ergonomics")
        room_choice = st.selectbox("Select Functional Zone:", list(design_knowledge.ROOM_GUIDELINES.keys()), format_func=lambda k: design_knowledge.ROOM_GUIDELINES[k]["title"])
        room_info = design_knowledge.get_room_guidelines(room_choice)
        if room_info:
            st.markdown(f"### {room_info['title']}")
            if "work_triangle" in room_info:
                st.info(f"**Golden Work Triangle:** {room_info['work_triangle']}")
            if "common_layouts" in room_info:
                st.markdown("**Layout Options:**")
                for l_name, l_desc in room_info["common_layouts"].items():
                    st.write(f"- **{l_name}:** {l_desc}")
            if "cabinetry_zones" in room_info:
                st.markdown("**Ergonomic Zones:**")
                for z in room_info["cabinetry_zones"]:
                    st.write(f"- {z}")

    # --------------------------------------------------------------------------
    # TAB 5: Materials & Hardware Reference
    # --------------------------------------------------------------------------
    with ai_tabs[4]:
        st.markdown("##### Interior Materials, Finishes & Hardware Technical Reference")
        st.caption("Engineering standards, moisture ratings, hardware systems, and side-by-side material comparisons.")

        m_subtab1, m_subtab2, m_subtab3, m_subtab4 = st.tabs(["🪵 Core Boards", "🎨 Surface Finishes", "🔩 Architectural Hardware", "⚖️ Material Comparison Tool"])

        with m_subtab1:
            for b_key, b in material_knowledge.CORE_BOARDS.items():
                with st.expander(f"{b['name']} ({b['cost_tier']})", expanded=(b_key == "bwp_plywood")):
                    st.markdown(f"**Standard:** {b['standard']} | **Density:** {b['density']} | **Resin:** {b['adhesive']}")
                    st.markdown("**Advantages:**")
                    for a in b["advantages"]:
                        st.write(f"- ✅ {a}")
                    st.markdown(f"**Recommended Applications:** {', '.join(b['applications'])}")
                    st.markdown(f"**Durability:** {b['durability_years']} | **Cost Range:** `{b['cost_tier']}`")

        with m_subtab2:
            for f_key, f in material_knowledge.SURFACE_FINISHES.items():
                with st.expander(f"{f['name']}", expanded=(f_key == "laminate")):
                    st.markdown(f"**Specifications:** {f.get('thickness', 'Standard')}")
                    st.markdown("**Advantages:**")
                    for a in f["advantages"]:
                        st.write(f"- ✅ {a}")
                    st.markdown(f"**Applications:** {', '.join(f['applications'])}")
                    st.markdown(f"**Cost Index:** `{f['cost_index']}`")

        with m_subtab3:
            for h_key, h in material_knowledge.HARDWARE_CATALOG.items():
                with st.expander(f"{h['brand']} ({h['cost_bracket']})", expanded=(h_key == "blum")):
                    st.markdown(f"**Market Position:** {h['market_position']}")
                    st.markdown("**Flagship Fittings:**")
                    for p in h["key_products"]:
                        st.write(f"- 🔩 {p}")
                    st.markdown(f"**Warranty:** {h['warranty']}")

        with m_subtab4:
            st.markdown("##### Side-by-Side Material Comparison")
            comp_type = st.selectbox("Comparison Subject:", [
                "BWP Marine Plywood vs. HDHMR Board",
                "High-Gloss Acrylic vs. 1.0mm Laminate",
                "Engineered Quartz vs. Natural Granite"
            ])
            if comp_type == "BWP Marine Plywood vs. HDHMR Board":
                st.markdown(material_knowledge.compare_materials("bwp_plywood", "hdhmr"))
            elif comp_type == "High-Gloss Acrylic vs. 1.0mm Laminate":
                st.markdown(material_knowledge.compare_materials("acrylic", "laminate"))
            else:
                st.markdown(material_knowledge.search_material_knowledge("quartz vs granite"))

    # --------------------------------------------------------------------------
    # TAB 6: Follow-Up Command Center & Multichannel Drafter
    # --------------------------------------------------------------------------
    with ai_tabs[5]:
        st.markdown("##### Follow-Up Command Center & Multichannel Drafter")
        st.caption("Operational follow-up queues and personalized WhatsApp & Email drafts with review-and-approve safeguards.")

        f_q1, f_q2, f_q3, f_q4 = st.columns(4)
        overdue_list = followup_intelligence.get_overdue_queue()
        due_today_list = followup_intelligence.get_due_today_queue()
        never_contacted_list = followup_intelligence.get_never_contacted_queue()
        awaiting_list = followup_intelligence.get_awaiting_response_queue()

        f_q1.metric("⚠️ Overdue Tasks", len(overdue_list))
        f_q2.metric("⏰ Due Today", len(due_today_list))
        f_q3.metric("🆕 Never Contacted", len(never_contacted_list))
        f_q4.metric("⏳ Awaiting Reply", len(awaiting_list))

        st.divider()
        st.markdown("##### Personalized Message Drafter (Human Review Required)")
        col_dr1, col_dr2, col_dr3 = st.columns(3)
        with col_dr1:
            sel_l_draft = st.selectbox("Select Customer:", options=lead_options_360, key="draft_lead_selector")
        with col_dr2:
            msg_goal = st.selectbox("Message Goal:", [
                "site_visit",
                "budget_alignment",
                "portfolio_lookbook",
                "consultation_invitation"
            ], format_func=lambda x: x.replace("_", " ").title())
        with col_dr3:
            channel_sel = st.radio("Draft Channel:", ["WhatsApp", "Email"], horizontal=True)

        if sel_l_draft:
            l_id_draft = sel_l_draft.split(" - ")[0]
            l_rec = database.get_lead_by_id(l_id_draft)
            if l_rec:
                if channel_sel == "WhatsApp":
                    wa_draft = followup_intelligence.generate_personalized_whatsapp_draft(l_rec, goal=msg_goal)
                    st.text_area("WhatsApp Draft (Ready to review & copy):", value=wa_draft, height=160, key="wa_draft_area")
                    if st.button("📝 Log WhatsApp Draft to Activity Log", key="btn_log_wa"):
                        followup_intelligence.record_communication_draft(l_id_draft, "WhatsApp", msg_goal, wa_draft)
                        st.success(f"Draft logged to activity history for {l_rec['customer_name']}. Ready for sales rep review.")
                else:
                    em_draft = followup_intelligence.generate_personalized_email_draft(l_rec, goal=msg_goal)
                    st.text_input("Subject Line:", value=em_draft["subject"])
                    st.text_area("Email Body:", value=em_draft["body"], height=260, key="em_draft_area")
                    if st.button("📝 Log Email Draft to Activity Log", key="btn_log_em"):
                        followup_intelligence.record_communication_draft(l_id_draft, "Email", em_draft["subject"], em_draft["body"])
                        st.success(f"Email draft logged to activity history for {l_rec['customer_name']}. Ready for sales rep review.")


# ==============================================================================
# 6. VIEW ALL LEADS
# ==============================================================================
elif page == "View All Leads":
    st.markdown('<div class="main-header">View All CRM Leads – Hyderabad Service Area</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Active customer enquiries across Hyderabad, Secunderabad, and surrounding metropolitan regions.</div>', unsafe_allow_html=True)
    
    with st.expander("🔍 Filters & Search Options", expanded=True):
        fcol1, fcol2, fcol3, fcol4 = st.columns(4)
        with fcol1:
            region_filter = st.selectbox("Filter by Region", options=["All"] + hg.HYDERABAD_REGIONS)
        with fcol2:
            locality_filter = st.selectbox("Filter by Locality", options=["All"] + hg.get_all_localities())
        with fcol3:
            budget_filter = st.selectbox("Filter by Budget", options=["All"] + lead_capture.BUDGET_OPTIONS)
        with fcol4:
            priority_filter = st.selectbox("Filter by Priority", options=["All", "High", "Medium", "Low"])
            
        status_col, type_col, origin_col, search_col = st.columns([1, 1, 1, 2])
        with status_col:
            status_filter = st.selectbox("Filter by Status", options=["All", "New", "Qualified", "Follow-up", "Converted", "Lost"])
        with type_col:
            type_filter = st.selectbox("Project Type", options=["All"] + lead_capture.PROJECT_TYPE_OPTIONS)
        with origin_col:
            origin_filter = st.selectbox("Data Origin", options=["All", "Exclude Test Data", "Test Data Only", "genuine_customer", "test_data", "manual_entry", "csv_import", "synthetic_import"])
        with search_col:
            search_query = st.text_input("Search Name, Locality, Phone, Reference or Lead ID", placeholder="Search customer, reference, locality...")

        # Estimate Date Filters & Sorting Controls
        st.markdown("##### ⏱️ Estimate Generation Date Filters & Sorting")
        sort_col, date_from_col, date_to_col = st.columns([1.6, 1.2, 1.2])
        with sort_col:
            sort_by = st.selectbox(
                "Sort Leads By",
                options=[
                    "Estimate Date (Newest First)",
                    "Estimate Date (Oldest First)",
                    "Lead Score (Highest First)",
                    "Lead Score (Lowest First)",
                    "Creation Date (Newest First)",
                    "Customer Name (A-Z)"
                ],
                index=0
            )
        with date_from_col:
            est_from_val = st.date_input("Estimate Date From", value=None)
        with date_to_col:
            est_to_val = st.date_input("Estimate Date To", value=None)

        show_archived = st.checkbox("Show Archived Non-Hyderabad Leads", value=False)

    sort_order_map = {
        "Estimate Date (Newest First)": "estimate_generated_at DESC",
        "Estimate Date (Oldest First)": "estimate_generated_at ASC",
        "Lead Score (Highest First)": "lead_score DESC",
        "Lead Score (Lowest First)": "lead_score ASC",
        "Creation Date (Newest First)": "created_at DESC",
        "Customer Name (A-Z)": "customer_name ASC"
    }

    leads = database.get_all_leads(
        locality=locality_filter if locality_filter != "All" else None,
        region=region_filter if region_filter != "All" else None,
        project_type=type_filter,
        budget_range=budget_filter,
        lead_status=status_filter,
        priority=priority_filter,
        data_origin=origin_filter,
        search_query=search_query,
        order_by=sort_order_map.get(sort_by, "estimate_generated_at DESC"),
        active_only=(not show_archived),
        estimate_date_from=est_from_val.isoformat() if est_from_val else None,
        estimate_date_to=est_to_val.isoformat() if est_to_val else None
    )
    
    st.markdown(f"**Showing {len(leads)} matching leads**")
    
    if leads:
        df_display = pd.DataFrame(leads)
        df_display["lead_score"] = df_display["lead_score"].apply(lambda x: f"{x:.0f}" if pd.notnull(x) else "—")
        df_display["priority"] = df_display["priority"].fillna("—")
        
        # Ensure locality and region columns exist in dataframe
        for col_def in ["locality", "region", "pincode"]:
            if col_def not in df_display.columns:
                df_display[col_def] = "—"
            else:
                df_display[col_def] = df_display[col_def].fillna("—")

        df_display["estimate_display"] = df_display["estimate_generated_at"].apply(
            lambda x: estimate_parser.format_estimate_display(x) if pd.notnull(x) else "—"
        )
        if "lead_reference" not in df_display.columns:
            df_display["lead_reference"] = "—"
        else:
            df_display["lead_reference"] = df_display["lead_reference"].fillna("—")

        df_display["origin_label"] = df_display["data_origin"].apply(
            lambda x: "🧪 TEST DATA" if x == "test_data" else ("👤 Genuine Customer" if x in ("genuine_customer", "manual_entry") else str(x))
        )
        display_cols = [
            "lead_id", "customer_name", "origin_label", "locality", "region", "pincode", "budget_range", 
            "project_type", "estimate_display", "lead_score", "priority", "lead_status"
        ]
        
        formatted_df = df_display[display_cols].rename(columns={
            "lead_id": "Lead ID", "customer_name": "Customer Name", "origin_label": "Data Origin", "locality": "Locality",
            "region": "Region", "pincode": "PIN Code", "budget_range": "Budget Range",
            "project_type": "Project Type", "estimate_display": "Estimate Generated Date & Time",
            "lead_score": "Score (/100)", "priority": "Priority", "lead_status": "Status"
        })
        st.dataframe(formatted_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("##### 🔍 Inspect Full Lead Requirement & Activity History")
        selected_lead_id = st.selectbox("Select Lead ID to view details:", options=[l["lead_id"] for l in leads])
        
        if selected_lead_id:
            lead_detail = database.get_lead_by_id(selected_lead_id)
            activities = database.get_lead_activities(selected_lead_id)
            if lead_detail:
                dcol1, dcol2, dcol3 = st.columns(3)
                with dcol1:
                    is_t = lead_detail.get('data_origin') == 'test_data'
                    name_tag = f"🧪 {lead_detail['customer_name']} [TEST DATA]" if is_t else lead_detail['customer_name']
                    st.write(f"**Customer:** {name_tag}")
                    st.write(f"**Phone:** {lead_detail['phone']}")
                    st.write(f"**Email:** {lead_detail.get('email') or '—'}")
                    st.write(f"**Locality:** {lead_detail.get('locality') or lead_detail['city']}")
                with dcol2:
                    st.write(f"**Project Type:** {lead_detail['project_type']}")
                    st.write(f"**Budget:** {lead_detail['budget_range']}")
                    st.write(f"**Score:** {lead_detail.get('lead_score') or '—'}/100 ({lead_detail.get('priority') or '—'})")
                with dcol3:
                    st.write(f"**Timeline:** {lead_detail['project_timeline']}")
                    st.write(f"**Readiness:** {lead_detail['purchase_readiness']}")
                    st.write(f"**Lead Status:** {lead_detail['lead_status']}")

                # Estimate Generation Metadata Block
                est_raw = lead_detail.get("estimate_generated_at")
                est_disp = estimate_parser.format_estimate_display(est_raw)
                est_long = estimate_parser.format_estimate_display_long(est_raw)
                ref_num = lead_detail.get("lead_reference") or "—"
                
                st.markdown(f"""
                <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px 16px; margin: 10px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <div>
                            <span style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: #64748B;">Estimate Reference</span>
                            <div style="font-size: 1.05rem; font-weight: 700; color: #1E293B;"><code>{ref_num}</code></div>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: #2563EB;">Estimate Generated Date & Time</span>
                            <div style="font-size: 1.05rem; font-weight: 700; color: #2563EB;">{est_disp}</div>
                            <span style="font-size: 0.75rem; color: #64748B;">{est_long}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                    
                st.info(f"**Requirements:** {lead_detail['customer_requirements'] or 'None provided.'}")
                
                # ---------------------------------------------------------
                # FIRST OUTBOUND CONTACT: WEBSITE ENQUIRY WHATSAPP FEATURE
                # ---------------------------------------------------------
                st.markdown("##### 🚀 First Outbound Outreach: Website Enquiry Introduction")
                enquiry_whatsapp.render_enquiry_message_ui(lead_detail, key_prefix="leads_detail")
                
                if activities:
                    st.markdown("###### Activity Timeline:")
                    for a in activities[:5]:
                        st.caption(f"⏱️ **{a['timestamp']}** &mdash; *{a['activity_type']}*: {a['activity_description']}")

        csv_export = formatted_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download Filtered Leads as CSV", data=csv_export, file_name=f"sha_leads_export_{datetime.date.today()}.csv", mime="text/csv")
    else:
        st.info("No leads match the selected criteria.")

# ==============================================================================
# 7. ADD NEW LEAD
# ==============================================================================
elif page == "Add New Lead":
    st.markdown('<div class="main-header">Add New Customer Enquiry</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Direct intake form with real-time AI scoring and lead qualification.</div>', unsafe_allow_html=True)
    lead_capture.render_lead_capture_form()

# ==============================================================================
# 8. IMPORT LEADS
# ==============================================================================
elif page == "Import Leads":
    st.markdown('<div class="main-header">Import Leads from CSV</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Batch ingestion module with schema validation, deduplication, and atomic transactions.</div>', unsafe_allow_html=True)

    tabs = st.tabs(["📁 Upload Custom CSV", "⚡ Quick Import Synthetic Leads"])
    with tabs[0]:
        uploaded_file = st.file_uploader("Select an Interior Design Leads CSV or Excel file", type=["csv", "xlsx", "xls"])
        if uploaded_file is not None:
            validation_res = data_loader.validate_and_prepare_csv(uploaded_file, data_origin="csv_import")
            if not validation_res["success"]:
                st.error(f"❌ {validation_res['error_message']}")
            else:
                st.success(f"✅ CSV structure valid: **{validation_res['valid_count']}** new records, **{validation_res['skipped_count']}** duplicates.")
                if st.button("Execute Batch Import", type="primary"):
                    uploaded_file.seek(0)
                    import_res = data_loader.import_csv_to_db(uploaded_file, data_origin="csv_import")
                    if import_res["success"]:
                        lead_scoring.score_all_leads()
                        st.success(f"🎉 {import_res['message']} Leads qualified.")
                    else:
                        st.error(f"❌ {import_res['error_message']}")

    with tabs[1]:
        hyd_csv_path = "SHA_Hyderabad_Interior_Design_Leads.csv"
        st.markdown(f"Import verified Hyderabad interior design leads dataset: `{hyd_csv_path}`.")
        if os.path.exists(hyd_csv_path):
            if st.button("Import Hyderabad Leads Dataset", type="primary"):
                res = data_loader.import_csv_to_db(hyd_csv_path, data_origin="csv_import")
                if res["success"]:
                    database.migrate_hyderabad_schema_and_leads()
                    lead_scoring.score_all_leads()
                    st.success(f"✅ {res['message']} Leads qualified.")
                else:
                    st.error(f"❌ {res['error_message']}")
                res = data_loader.import_csv_to_db(synth_path, data_origin="synthetic_import")
                if res["success"]:
                    lead_scoring.score_all_leads()
                    st.success(f"✅ {res['message']} Leads scored.")
                else:
                    st.error(f"❌ {res['error_message']}")

# ==============================================================================
# 9. SETTINGS
# ==============================================================================

# ==============================================================================
# AI SHADOW MODE PAGE
# ==============================================================================
elif page == "AI Shadow Mode":
    st.markdown('<div class="main-header">🕵️ AI Shadow Mode Intelligence & Background Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Monitors customer conversations non-intrusively in the background. Detects triggers, formulates strategic next actions, and prepares English WhatsApp drafts for human review. AI never auto-sends messages.</div>', unsafe_allow_html=True)

    s_ctrl1, s_ctrl2 = st.columns([2, 1])
    with s_ctrl1:
        is_enabled = shadow_mode.is_shadow_mode_enabled()
        toggle_val = st.toggle("🟢 Shadow Mode Enabled (Background Conversation Analysis)", value=is_enabled, key="shadow_mode_toggle_btn")
        if toggle_val != is_enabled:
            shadow_mode.set_shadow_mode_enabled(toggle_val)
            st.rerun()
    with s_ctrl2:
        if st.button("🔄 Analyze Conversations on All Leads", type="primary", key="btn_run_shadow_all"):
            with st.spinner("Analyzing recent conversations for all leads..."):
                all_leads = database.get_all_leads()
                total_new = 0
                for l in all_leads:
                    recs = shadow_mode.analyze_conversation_for_shadow_recommendations(l["lead_id"])
                    total_new += len(recs)
                st.success(f"Analysis complete! Generated {total_new} new strategic recommendations for review.")
                st.rerun()

    st.markdown("---")

    status_filter = st.radio("Filter Recommendations by Status:", ["Pending Review", "Approved", "Modified", "Rejected", "All"], horizontal=True, index=0)
    actual_status = None if status_filter == "All" else status_filter

    recs = database.get_shadow_recommendations(status=actual_status)
    st.markdown(f"##### 📋 Strategic Recommendations ({len(recs)} Found)")

    if not recs:
        st.info(f"No recommendations currently in '{status_filter}' status.")
    else:
        for r in recs:
            lead_info = database.get_lead_by_id(r["lead_id"])
            cust_name = lead_info.get("customer_name", "Customer") if lead_info else r["lead_id"]
            prio = r.get("priority", "Medium")
            prio_color = "#DC2626" if prio in ["High", "Urgent"] else ("#D97706" if prio == "Medium" else "#16A34A")

            with st.container():
                st.markdown(f"""
                <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:5px solid {prio_color}; border-radius:8px; padding:16px; margin-bottom:12px; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:700; font-size:1.1rem; color:#0F172A;">{cust_name} ({r['lead_id']}) &mdash; <span style="color:#2563EB;">{r['scenario']}</span></span>
                        <span style="background:{prio_color}22; color:{prio_color}; padding:3px 8px; border-radius:12px; font-size:0.8rem; font-weight:700;">{prio} Priority</span>
                    </div>
                    <div style="margin-top:6px; font-size:0.9rem; color:#475569;">
                        <b>Reason:</b> {r['reason']}<br>
                        <b>Recommended Action:</b> {r['next_action']}<br>
                        <b>Target Follow-up Date:</b> {r['recommended_date']} &bull; <b>Status:</b> <code>{r['status']}</code>
                    </div>
                    <div style="margin-top:8px; background:#F8FAFC; border:1px solid #E2E8F0; border-radius:6px; padding:10px 14px; font-size:0.9rem; color:#1E293B;">
                        <b>English WhatsApp Draft:</b><br>{r['english_whatsapp_draft']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if r["status"] == "Pending Review":
                    btn_c1, btn_c2, btn_c3 = st.columns([1.5, 1.5, 3])
                    with btn_c1:
                        if st.button(f"✅ Approve & Schedule", key=f"appr_{r['recommendation_id']}"):
                            res = shadow_mode.review_shadow_recommendation(r['recommendation_id'], "Approved")
                            if res["success"]:
                                st.success("Recommendation approved and scheduled!")
                                st.rerun()
                    with btn_c2:
                        if st.button(f"❌ Reject", key=f"rej_{r['recommendation_id']}"):
                            res = shadow_mode.review_shadow_recommendation(r['recommendation_id'], "Rejected", reviewer_notes="Dismissed by user")
                            if res["success"]:
                                st.info("Recommendation dismissed.")
                                st.rerun()
                    with btn_c3:
                        with st.expander("✏️ Modify Draft Before Approving"):
                            new_draft = st.text_area("Edit Draft:", value=r["english_whatsapp_draft"], key=f"draft_{r['recommendation_id']}")
                            if st.button("Save & Approve Modified", key=f"mod_{r['recommendation_id']}"):
                                res = shadow_mode.review_shadow_recommendation(r['recommendation_id'], "Modified", modified_draft=new_draft)
                                if res["success"]:
                                    st.success("Modified draft approved and scheduled!")
                                    st.rerun()

elif page == "Settings":
    st.markdown('<div class="main-header">System Settings & Configuration</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Manage business assumptions, service areas, scoring thresholds, and integrations.</div>', unsafe_allow_html=True)

    st.markdown("""
    > [!NOTE]
    > **Demo Assumptions**: Current parameters reflect demo defaults designed for SHA Interface Interiors and can be adjusted here or via environment variables upon management confirmation.
    """)

    set_tab1, set_tab2, set_tab3 = st.tabs(["🏙️ Serviceable Cities & Hubs", "🎯 Scoring & Priority Thresholds", "🔌 Integrations (AI & n8n)"])
    
    with set_tab1:
        st.markdown("##### Hyderabad Metropolitan Locality Tiers")
        st.write("**Tier 1 Prime IT & Luxury Corridors (20 pts):** Gachibowli, Jubilee Hills, Banjara Hills, Madhapur, Financial District, Kokapet, HITEC City, Kondapur, Nanakramguda")
        st.write("**Tier 2 High-Demand Established Residential Corridors (17 pts):** Narsingi, Tellapur, Manikonda, Nallagandla, Kukatpally, Miyapur, Bachupally, Nizampet, Kompally, Begumpet, Somajiguda, Secunderabad, Sainikpuri, Himayatnagar, Serilingampally")
        st.write("**Tier 3 Core Urban & Established Communities (14 pts):** Ameerpet, Punjagutta, Suchitra, Bowenpally, Chandanagar, Hafeezpet, Alwal, Uppal, Nagole, Habsiguda, Tarnaka, Attapur, Mehdipatnam, ECIL, AS Rao Nagar, Trimulgherry, Moula Ali")
        st.write("**Tier 4 Greater Metropolitan Corridors (12 pts):** LB Nagar, Kothapet, Saroornagar, Saidabad, Jeedimetla, Quthbullapur, Nacharam, Ghatkesar, Boduppal, Peerzadiguda, Pocharam, Rajendra Nagar, Shamshabad, Bandlaguda, Chandrayangutta, Falaknuma, Malkajgiri, Kapra, Yapral, Khairatabad, Lakdikapul, Abids")
        st.caption("Locality qualifications are centrally managed in `hyderabad_geo.py`.")

    with set_tab2:
        st.markdown("##### Lead Priority Cutoff Thresholds")
        st.write("🟢 **High Priority Threshold:** $\\ge 80$ Points (Immediate Sales Rep Assignment)")
        st.write("🟡 **Medium Priority Threshold:** $50 - 79$ Points (Nurturing Sequence & Portfolio)")
        st.write("🔴 **Low Priority Threshold:** $< 50$ Points (Automated Catalog Re-engagement)")
        st.write(f"**Target Minimum Budget Assumption:** {lead_scoring.CONFIGURABLE_MIN_TARGET_BUDGET}")

    with set_tab3:
        st.markdown("##### External Integration Status")
        ai_info = ai_assistant.get_ai_status_info()
        st.write(f"**Google Gemini API Status:** {'🟢 Connected (' + ai_info['model'] + ')' if ai_info['gemini_active'] else '🟡 Not Configured (Using Local AI Fallback Engine)'}")
        st.write(f"**n8n Webhook Host:** {'🟢 ' + n8n_dispatcher.N8N_BASE_URL if n8n_dispatcher.is_n8n_configured() else '🟡 Not Configured (Local Event Logging Active)'}")
        
        st.markdown("---")
        st.markdown("###### Test Google Gemini Connection")
        if st.button("🔌 Test Gemini API Connection", key="btn_test_gemini"):
            with st.spinner("Pinging Google Gemini API..."):
                conn_res = ai_service.verify_connection()
                if conn_res.get("connected"):
                    st.success(f"🟢 **Success!** Connected to Gemini API successfully using model `{conn_res.get('model')}`.")
                else:
                    st.warning(f"🟡 **Notice:** {conn_res.get('error')}")
                    st.info("💡 **How to configure:**\n- **Local:** Run `python setup_gemini_key.py` in your terminal or add `GEMINI_API_KEY=your_key` to `.env`.\n- **Streamlit Cloud:** Go to App Settings ➔ Secrets and add `GEMINI_API_KEY = \"your_key\"`.")

        st.caption("See `.env.example` to configure credentials.")
