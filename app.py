import streamlit as st
import pandas as pd
import json
import os
import datetime
import database
import data_loader
import lead_capture
import lead_scoring
import followups
import followup_templates
import reports
import ai_assistant
import n8n_dispatcher

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
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #64748B;
        margin-bottom: 1.2rem;
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

# Auto-seed database if empty (ensures seamless startup on fresh cloud deployments like Streamlit Community Cloud)
try:
    _init_stats = database.get_lead_stats()
    if _init_stats.get('total_leads', 0) == 0:
        _base_dir = os.path.dirname(os.path.abspath(__file__))
        _synthetic_csv = os.path.join(_base_dir, "data", "synthetic", "interior_design_leads.csv")
        if os.path.exists(_synthetic_csv):
            data_loader.import_csv_to_db(_synthetic_csv, data_origin="synthetic_import")
            lead_scoring.score_all_leads()
            followups.schedule_followups_for_all_eligible_leads()
except Exception as _seed_err:
    pass

# Navigation Sidebar
with st.sidebar:
    st.markdown("## 🏡 SHA Interiors")
    st.caption("AI-Powered Lead Management & CRM")
    st.divider()
    
    page = st.radio(
        "Navigation",
        options=[
            "Home Dashboard",
            "AI Lead Scoring",
            "Follow-up Management",
            "Reports and Analytics",
            "AI Assistant",
            "View All Leads",
            "Add New Lead",
            "Import Leads",
            "Settings"
        ],
        index=0
    )
    
    st.divider()
    st.markdown("### 📊 System Status")
    stats = database.get_lead_stats()
    st.write(f"**CRM Leads:** {stats['total_leads']}")
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
    st.markdown('<div class="main-header">Executive CRM & Lead Intelligence Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Comprehensive pipeline overview, qualification scoring, and automated follow-ups.</div>', unsafe_allow_html=True)
    
    kpis = reports.get_executive_kpis()
    
    # Row 1: Pipeline Funnel
    st.markdown("##### 📈 CRM Pipeline Snapshot")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{kpis["total_leads"]}</div><div class="metric-lbl">Total Leads</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{kpis["new_leads"]}</div><div class="metric-lbl">New Inquiries</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{kpis["qualified_leads"]}</div><div class="metric-lbl">Qualified</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color: #16A34A;">{kpis["converted_leads"]}</div><div class="metric-lbl">Converted</div></div>', unsafe_allow_html=True)
    with c5:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color: #DC2626;">{kpis["lost_leads"]}</div><div class="metric-lbl">Lost</div></div>', unsafe_allow_html=True)

    # Row 2: AI Scoring & Follow-up KPIs
    st.markdown("<br>##### 🎯 AI Qualification & Follow-up Cadence", unsafe_allow_html=True)
    a1, a2, a3, a4, a5 = st.columns(5)
    with a1:
        st.markdown(f'<div class="metric-card" style="border-top: 4px solid #3B82F6;"><div class="metric-val">{kpis["average_lead_score"]}<span style="font-size: 0.9rem; color: #64748B;">/100</span></div><div class="metric-lbl">Average Score</div></div>', unsafe_allow_html=True)
    with a2:
        st.markdown(f'<div class="metric-card" style="border-top: 4px solid #10B981;"><div class="metric-val" style="color: #10B981;">{kpis["high_priority_leads"]}</div><div class="metric-lbl">High Priority</div></div>', unsafe_allow_html=True)
    with a3:
        st.markdown(f'<div class="metric-card" style="border-top: 4px solid #F59E0B;"><div class="metric-val" style="color: #D97706;">{kpis["medium_priority_leads"]}</div><div class="metric-lbl">Medium Priority</div></div>', unsafe_allow_html=True)
    with a4:
        st.markdown(f'<div class="metric-card" style="border-top: 4px solid #EF4444;"><div class="metric-val" style="color: #DC2626;">{kpis["low_priority_leads"]}</div><div class="metric-lbl">Low Priority</div></div>', unsafe_allow_html=True)
    with a5:
        st.markdown(f'<div class="metric-card" style="border-top: 4px solid #8B5CF6;"><div class="metric-val" style="color: #7C3AED;">{kpis["pending_due_followups"]}</div><div class="metric-lbl">Due Follow-ups</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # Charts
    chart_data = reports.get_chart_data()
    ch1, ch2 = st.columns(2)
    with ch1:
        st.markdown("##### 🎯 Lead Priority Distribution")
        st.bar_chart(chart_data["priority"].set_index("Priority"), color="#2563EB", use_container_width=True)
    with ch2:
        st.markdown("##### 📍 Inquiries by Top Cities")
        st.dataframe(chart_data["city"], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("##### 💡 Conversion Intelligence")
    st.info(
        f"**Engaged Conversion Rate:** **{kpis['engaged_conversion_rate']}%** "
        f"(Calculated as `Converted Leads ({kpis['converted_leads']}) / Engaged Leads ({kpis['converted_leads'] + kpis['lost_leads'] + kpis['followup_leads'] + kpis['qualified_leads']}) × 100`). "
        f"Overall Pipeline Rate: **{kpis['overall_conversion_rate']}%** across {kpis['total_leads']} total records."
    )

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
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    with fcol1:
        priority_filter = st.selectbox("Priority Tier", options=["All", "High", "Medium", "Low"])
    with fcol2:
        city_filter = st.selectbox("City", options=["All"] + lead_capture.CITY_OPTIONS)
    with fcol3:
        sort_by = st.selectbox("Sort By", options=["Highest Score First", "Lowest Score First", "Customer Name"])
    with fcol4:
        search_kw = st.text_input("Search Lead", placeholder="Name or Lead ID...")

    order_map = {"Highest Score First": "lead_score DESC", "Lowest Score First": "lead_score ASC", "Customer Name": "customer_name ASC"}
    leads = database.get_all_leads(city=city_filter, priority=priority_filter, search_query=search_kw, order_by=order_map[sort_by])

    st.markdown(f"**Showing {len(leads)} leads**")
    if leads:
        df = pd.DataFrame(leads)
        df["lead_score"] = df["lead_score"].apply(lambda x: f"{x:.0f}" if pd.notnull(x) else "—")
        df["priority"] = df["priority"].fillna("Pending")
        
        display_cols = ["lead_id", "customer_name", "city", "budget_range", "project_type", "purchase_readiness", "lead_score", "priority", "lead_status"]
        st.dataframe(df[display_cols].rename(columns={
            "lead_id": "Lead ID", "customer_name": "Customer Name", "city": "City", "budget_range": "Budget",
            "project_type": "Project Type", "purchase_readiness": "Readiness", "lead_score": "Score (/100)",
            "priority": "Priority", "lead_status": "CRM Status"
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
                    st.caption(f"{lead_item.get('city')}")
                with b3:
                    st.metric("📋 Requirements", f"{breakdown.get('requirements_score', 0)} / 20", help=breakdown.get("requirements_detail"))
                    st.caption(f"{lead_item.get('project_type')}")
                with b4:
                    st.metric("🚀 Readiness", f"{breakdown.get('readiness_score', 0)} / 30", help=breakdown.get("readiness_detail"))
                    st.caption(f"{lead_item.get('purchase_readiness')}")

# ==============================================================================
# 3. FOLLOW-UP MANAGEMENT
# ==============================================================================
elif page == "Follow-up Management":
    st.markdown('<div class="main-header">Automated Follow-up Management System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Priority-driven cadences, stop condition enforcement, idempotency, and response handling.</div>', unsafe_allow_html=True)

    fu_stats = database.get_followup_stats()
    
    # KPI Row
    f1, f2, f3, f4, f5 = st.columns(5)
    with f1:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{fu_stats["total_followups"]}</div><div class="metric-lbl">Total Tasks</div></div>', unsafe_allow_html=True)
    with f2:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color: #2563EB;">{fu_stats["scheduled_count"]}</div><div class="metric-lbl">Scheduled</div></div>', unsafe_allow_html=True)
    with f3:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color: #D97706;">{fu_stats["due_count"]}</div><div class="metric-lbl">Due Now</div></div>', unsafe_allow_html=True)
    with f4:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color: #16A34A;">{fu_stats["completed_count"]}</div><div class="metric-lbl">Dispatched</div></div>', unsafe_allow_html=True)
    with f5:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color: #DC2626;">{fu_stats["cancelled_count"]}</div><div class="metric-lbl">Cancelled (Halted)</div></div>', unsafe_allow_html=True)

    st.markdown("""
    > [!IMPORTANT]
    > **Critical Stop Conditions Active**: Follow-ups are automatically cancelled or prevented if a customer **responds**, **opts out**, or if the lead is marked **Converted** or **Lost**. All dispatch operations enforce **idempotency**.
    """)

    tabs = st.tabs(["📅 Upcoming Follow-up Schedule", "💬 Customer Response Simulation", "✋ Opt-Out & Pause Controls", "⚡ Mass Cadence Scheduler"])
    
    with tabs[0]:
        st.markdown("##### Scheduled Follow-up Tasks")
        status_filter = st.selectbox("Filter Task Status", options=["All", "Scheduled", "Sent", "Completed", "Cancelled"])
        followups_list = database.get_followups(status=status_filter, limit=100)
        
        if followups_list:
            df_fu = pd.DataFrame(followups_list)
            cols_show = ["schedule_id", "customer_name", "city", "priority", "channel", "attempt_number", "scheduled_for", "status", "stop_reason"]
            st.dataframe(df_fu[cols_show], use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("##### 🚀 Simulate Task Execution")
            sched_ids = [f["schedule_id"] for f in followups_list if f["status"] == "Scheduled"]
            if sched_ids:
                sel_task_id = st.selectbox("Select Scheduled Task to Execute:", options=sched_ids)
                task_data = database.get_followup_by_id(sel_task_id)
                if task_data:
                    st.info(f"**Customer:** {task_data['customer_name']} ({task_data['phone']}) | **Channel:** {task_data['channel']} (Attempt #{task_data['attempt_number']})\n\n**Message Preview:**\n\"{task_data['message']}\"")
                    if st.button("Simulate Send Message", type="primary"):
                        send_res = followups.simulate_send_followup(sel_task_id)
                        if send_res["success"]:
                            st.success(f"✅ {send_res['message']}")
                        else:
                            st.error(f"❌ {send_res['error']}")
                        st.rerun()
            else:
                st.info("No tasks currently in 'Scheduled' state.")
        else:
            st.info("No follow-up tasks found.")

    with tabs[1]:
        st.markdown("##### 📥 Inbound Customer Response Simulator")
        st.caption("Simulate a customer replying on WhatsApp or Phone. This immediately halts all future automated touches and alerts the sales team.")
        
        all_leads_for_resp = database.get_all_leads()
        active_leads = [l for l in all_leads_for_resp if l.get("lead_status") not in ["Converted", "Lost"]]
        
        sel_resp_lead = st.selectbox("Select Client who responded:", options=[f"{l['lead_id']} - {l['customer_name']} ({l['city']})" for l in active_leads])
        resp_text = st.text_area("Customer Inbound Message:", "Hello! Yes, I am interested in scheduling a site visit this Saturday at 11 AM.")
        
        if st.button("Record Customer Response & Halt Automated Outreach", type="primary"):
            target_id = sel_resp_lead.split(" - ")[0]
            resp_res = followups.simulate_customer_response(target_id, resp_text)
            if resp_res["success"]:
                st.success(f"🎉 {resp_res['message']}")
                st.info(f"Lead **{target_id}** is now flagged as 'Responded'. Assigned designer must take over personal consultation.")
                st.rerun()
            else:
                st.error(f"❌ {resp_res['error']}")

    with tabs[2]:
        st.markdown("##### 🛡️ Compliance & Sales Controls (Opt-Out / Pause)")
        c_opt1, c_opt2 = st.columns(2)
        with c_opt1:
            st.markdown("###### Customer Opt-Out")
            opt_lead_sel = st.selectbox("Select Lead to Opt-Out:", options=[f"{l['lead_id']} - {l['customer_name']}" for l in all_leads_for_resp], key="opt_sel")
            opt_reason = st.text_input("Opt-Out Reason:", "Customer chose another design firm / requested no calls")
            if st.button("Mark as Opted-Out", type="secondary"):
                t_id = opt_lead_sel.split(" - ")[0]
                opt_res = followups.mark_lead_opt_out(t_id, reason=opt_reason)
                st.warning(f"⚠️ {opt_res['message']}")
                st.rerun()
                
        with c_opt2:
            st.markdown("###### Pause / Resume Outreach")
            pause_lead_sel = st.selectbox("Select Lead to Pause/Resume:", options=[f"{l['lead_id']} - {l['customer_name']}" for l in all_leads_for_resp], key="pause_sel")
            p_action = st.radio("Action:", options=["Pause Automated Outreach", "Resume Automated Outreach"])
            if st.button("Apply Pause / Resume Setting"):
                t_id = pause_lead_sel.split(" - ")[0]
                pause_res = followups.pause_or_resume_lead_followups(t_id, pause=("Pause" in p_action))
                st.success(f"✅ {pause_res['message']}")
                st.rerun()

    with tabs[3]:
        st.markdown("##### ⚡ Schedule Cadences for All Eligible Leads")
        st.write("Generates automated multi-touch sequences (High: 3 touches, Medium: 3 touches, Low: 2 touches) for all unfinalized leads.")
        if st.button("Run Batch Follow-up Scheduler Now", type="primary"):
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

    kpis = reports.get_executive_kpis()
    charts = reports.get_chart_data()

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
            st.markdown("##### 1. Leads by City")
            st.bar_chart(charts["city"].set_index("City"), color="#10B981")
        with col_g2:
            st.markdown("##### 2. Leads by Lead Source")
            st.bar_chart(charts["source"].set_index("Lead Source"), color="#6366F1")
            
    with c_tab2:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("##### 3. Leads by Project Type")
            st.bar_chart(charts["project_type"].set_index("Project Type"), color="#F59E0B")
        with col_p2:
            st.markdown("##### 4. Leads by Budget Range")
            st.dataframe(charts["budget"], use_container_width=True, hide_index=True)
            
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
        st.dataframe(rep["leads_table"][["lead_id", "customer_name", "city", "project_type", "budget_range", "lead_score", "priority", "lead_status"]], use_container_width=True, hide_index=True)
        
        # CSV Export
        csv_data = rep["leads_table"].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Report as CSV",
            data=csv_data,
            file_name=f"sha_report_{rep['start_date']}_to_{rep['end_date']}.csv",
            mime="text/csv"
        )

# ==============================================================================
# 5. AI ASSISTANT
# ==============================================================================
elif page == "AI Assistant":
    st.markdown('<div class="main-header">CRM AI Sales Consultant Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Natural language query engine, personalized requirement summarization, and next-action advice.</div>', unsafe_allow_html=True)

    if ai_assistant.is_ai_api_available():
        st.success("🟢 Google Gemini API connection active. Natural language queries powered by Gemini 1.5 Flash.")
    else:
        st.info("🟡 Running on Built-in CRM Intelligence Engine (Deterministic SQLite rules & intent parser). Configure `GEMINI_API_KEY` in `.env` to enable multi-turn generative Q&A.")

    ai_tabs = st.tabs(["💬 Ask CRM Assistant", "📋 Client Requirement Summarizer", "✍️ Personalized Message Drafter"])
    
    with ai_tabs[0]:
        st.markdown("##### Ask Questions About Your Leads & Pipeline")
        
        # Pre-set prompt buttons
        b_c1, b_c2, b_c3, b_c4 = st.columns(4)
        selected_prompt = None
        if b_c1.button("🔥 High-Priority Leads?"):
            selected_prompt = "How many high-priority leads do we have?"
        if b_c2.button("📍 Leads in Hyderabad?"):
            selected_prompt = "Show high-priority leads in Hyderabad"
        if b_c3.button("⚠️ Attention Required?"):
            selected_prompt = "Which leads need immediate attention?"
        if b_c4.button("⏰ Scheduled Follow-ups?"):
            selected_prompt = "What follow-ups are due?"

        user_query = st.text_input("Enter your question:", value=selected_prompt or "", placeholder="e.g. How many high-priority leads do we have in Bangalore?")
        if user_query:
            with st.spinner("Analyzing CRM data..."):
                answer = ai_assistant.answer_crm_query(user_query)
                st.markdown("##### Assistant Response:")
                st.markdown(answer)

    with ai_tabs[1]:
        st.markdown("##### Generate Client Requirement Summary & Recommended Next Action")
        all_leads = database.get_all_leads()
        lead_options = [f"{l['lead_id']} - {l['customer_name']} ({l['city']} | {l['project_type']})" for l in all_leads]
        sel_lead = st.selectbox("Select Customer Enquiry:", options=lead_options, key="ai_lead_sel")
        
        if sel_lead:
            lead_id_target = sel_lead.split(" - ")[0]
            lead_obj = database.get_lead_by_id(lead_id_target)
            if lead_obj:
                summary_text = ai_assistant.summarize_customer_requirements(lead_obj)
                next_act = ai_assistant.recommend_next_action(lead_obj)
                
                st.markdown(summary_text)
                st.markdown(f"""
                <div style="background-color: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 14px; margin-top: 10px;">
                    <h4 style="margin: 0; color: #166534;">🎯 Recommended Next Sales Action: {next_act['recommended_action']}</h4>
                    <p style="margin: 4px 0 0 0; color: #15803D;"><strong>Urgency:</strong> {next_act['urgency']}</p>
                    <p style="margin: 4px 0 0 0; color: #374151;"><strong>Rationale:</strong> {next_act['rationale']}</p>
                </div>
                """, unsafe_allow_html=True)

    with ai_tabs[2]:
        st.markdown("##### Personalised Follow-up Message Drafter")
        tmpl_cat = followup_templates.get_template_catalog()
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            sel_l_draft = st.selectbox("Select Client:", options=lead_options, key="draft_l_sel")
        with col_t2:
            sel_tmpl = st.selectbox("Message Goal:", options=list(tmpl_cat.keys()), format_func=lambda x: tmpl_cat[x])
            
        if sel_l_draft:
            l_id = sel_l_draft.split(" - ")[0]
            l_data = database.get_lead_by_id(l_id)
            if l_data:
                draft_msg = followup_templates.generate_personalized_message(sel_tmpl, l_data)
                st.text_area("Draft Message (Ready to copy or send):", value=draft_msg, height=140)

# ==============================================================================
# 6. VIEW ALL LEADS
# ==============================================================================
elif page == "View All Leads":
    st.markdown('<div class="main-header">View All CRM Leads</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Searchable and filterable registry of all customer enquiries in SQLite.</div>', unsafe_allow_html=True)
    
    with st.expander("🔍 Filters & Search Options", expanded=True):
        fcol1, fcol2, fcol3, fcol4 = st.columns(4)
        with fcol1:
            city_filter = st.selectbox("Filter by City", options=["All"] + lead_capture.CITY_OPTIONS)
        with fcol2:
            type_filter = st.selectbox("Filter by Project Type", options=["All"] + lead_capture.PROJECT_TYPE_OPTIONS)
        with fcol3:
            budget_filter = st.selectbox("Filter by Budget", options=["All"] + lead_capture.BUDGET_OPTIONS)
        with fcol4:
            priority_filter = st.selectbox("Filter by Priority", options=["All", "High", "Medium", "Low"])
            
        status_col, origin_col, search_col = st.columns([1, 1, 2])
        with status_col:
            status_filter = st.selectbox("Filter by Status", options=["All", "New", "Qualified", "Follow-up", "Converted", "Lost"])
        with origin_col:
            origin_filter = st.selectbox("Data Origin", options=["All", "synthetic_import", "manual_entry", "csv_import"])
        with search_col:
            search_query = st.text_input("Search Customer Name, Lead ID, Phone, or Email", placeholder="Type name, ID, or phone...")

    leads = database.get_all_leads(
        city=city_filter,
        project_type=type_filter,
        budget_range=budget_filter,
        lead_status=status_filter,
        priority=priority_filter,
        data_origin=origin_filter,
        search_query=search_query,
        order_by="lead_score DESC"
    )
    
    st.markdown(f"**Showing {len(leads)} matching leads**")
    
    if leads:
        df_display = pd.DataFrame(leads)
        df_display["lead_score"] = df_display["lead_score"].apply(lambda x: f"{x:.0f}" if pd.notnull(x) else "—")
        df_display["priority"] = df_display["priority"].fillna("—")
        
        display_cols = [
            "lead_id", "customer_name", "phone", "city", "budget_range", 
            "project_type", "purchase_readiness", "lead_score", "priority", "lead_status", "created_at"
        ]
        
        formatted_df = df_display[display_cols].rename(columns={
            "lead_id": "Lead ID", "customer_name": "Customer Name", "phone": "Phone", "city": "City",
            "budget_range": "Budget Range", "project_type": "Project Type", "purchase_readiness": "Readiness",
            "lead_score": "Score (/100)", "priority": "Priority", "lead_status": "Status", "created_at": "Created Date"
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
                    st.write(f"**Customer:** {lead_detail['customer_name']}")
                    st.write(f"**Phone:** {lead_detail['phone']}")
                    st.write(f"**City:** {lead_detail['city']}")
                with dcol2:
                    st.write(f"**Project Type:** {lead_detail['project_type']}")
                    st.write(f"**Budget:** {lead_detail['budget_range']}")
                    st.write(f"**Score:** {lead_detail.get('lead_score') or '—'}/100 ({lead_detail.get('priority') or '—'})")
                with dcol3:
                    st.write(f"**Timeline:** {lead_detail['project_timeline']}")
                    st.write(f"**Readiness:** {lead_detail['purchase_readiness']}")
                    st.write(f"**Lead Status:** {lead_detail['lead_status']}")
                    
                st.info(f"**Requirements:** {lead_detail['customer_requirements'] or 'None provided.'}")
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
        uploaded_file = st.file_uploader("Select an Interior Design Leads CSV file", type=["csv"])
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
        synth_path = os.path.join("data", "synthetic", "interior_design_leads.csv")
        st.markdown(f"Import pre-generated synthetic interior design leads: `{synth_path}`.")
        if os.path.exists(synth_path):
            if st.button("Import 250 Synthetic Leads", type="primary"):
                res = data_loader.import_csv_to_db(synth_path, data_origin="synthetic_import")
                if res["success"]:
                    lead_scoring.score_all_leads()
                    st.success(f"✅ {res['message']} Leads scored.")
                else:
                    st.error(f"❌ {res['error_message']}")

# ==============================================================================
# 9. SETTINGS
# ==============================================================================
elif page == "Settings":
    st.markdown('<div class="main-header">System Settings & Configuration</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Manage business assumptions, service areas, scoring thresholds, and integrations.</div>', unsafe_allow_html=True)

    st.markdown("""
    > [!NOTE]
    > **Demo Assumptions**: Current parameters reflect demo defaults designed for SHA Interface Interiors and can be adjusted here or via environment variables upon management confirmation.
    """)

    set_tab1, set_tab2, set_tab3 = st.tabs(["🏙️ Serviceable Cities & Hubs", "🎯 Scoring & Priority Thresholds", "🔌 Integrations (AI & n8n)"])
    
    with set_tab1:
        st.markdown("##### Serviceable Territory Configuration")
        st.write("**Tier 1 Primary Hubs (20 pts):** Bangalore, Hyderabad (Full Design Studios & In-house Teams)")
        st.write("**Tier 2 Secondary Hubs (14 pts):** Chennai, Mumbai, Pune (Design Studios & Verified Partner Teams)")
        st.write("**Tier 3 Expansion Hubs (8 pts):** Delhi NCR (Remote Architectural Consultation)")
        st.info("To add custom cities, modify `DEFAULT_LOCATION_TIERS` in `lead_scoring.py`.")

    with set_tab2:
        st.markdown("##### Lead Priority Cutoff Thresholds")
        st.write("🟢 **High Priority Threshold:** $\\ge 80$ Points (Immediate Sales Rep Assignment)")
        st.write("🟡 **Medium Priority Threshold:** $50 - 79$ Points (Nurturing Sequence & Portfolio)")
        st.write("🔴 **Low Priority Threshold:** $< 50$ Points (Automated Catalog Re-engagement)")
        st.write(f"**Target Minimum Budget Assumption:** {lead_scoring.CONFIGURABLE_MIN_TARGET_BUDGET}")

    with set_tab3:
        st.markdown("##### External Integration Status")
        st.write(f"**Google Gemini API Status:** {'🟢 Connected' if ai_assistant.is_ai_api_available() else '🟡 Not Configured (Using Local AI Fallback Engine)'}")
        st.write(f"**n8n Webhook Host:** {'🟢 ' + n8n_dispatcher.N8N_BASE_URL if n8n_dispatcher.is_n8n_configured() else '🟡 Not Configured (Local Event Logging Active)'}")
        st.caption("See `.env.example` to configure credentials.")
