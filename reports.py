import datetime
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import database
import estimate_parser

def get_executive_kpis(
    db_path: str = database.DEFAULT_DB_PATH, 
    active_only: bool = False,
    dataset_scope: str = "all"
) -> Dict[str, Any]:
    """Computes high-level executive CRM and follow-up metrics from SQLite (Hyderabad-aware)."""
    conn = database.get_connection(db_path)
    try:
        cursor = conn.cursor()
        
        # Check if database has partitioned archived records
        try:
            cursor.execute("SELECT COUNT(*) FROM LEADS WHERE is_service_area = 0;")
            archived_c = cursor.fetchone()[0]
        except Exception:
            archived_c = 0
            
        use_active = active_only and archived_c > 0
        conds = []
        if use_active:
            conds.append("(city = 'Hyderabad' OR is_service_area = 1)")
        if dataset_scope in ("genuine_only", "Exclude Test Data"):
            conds.append("data_origin != 'test_data'")
        elif dataset_scope in ("test_only", "Test Data Only"):
            conds.append("data_origin = 'test_data'")
            
        where_clause = f" WHERE {' AND '.join(conds)}" if conds else ""
        and_clause = f" WHERE {' AND '.join(conds)} AND" if conds else " WHERE"

        # 1. Total Leads
        cursor.execute(f"SELECT COUNT(*) as c FROM LEADS{where_clause};")
        total_leads = cursor.fetchone()["c"]
        
        # 1b. Test vs Genuine lead counts
        cursor.execute("SELECT COUNT(*) as c FROM LEADS WHERE data_origin = 'test_data';")
        test_leads_c = cursor.fetchone()["c"]
        cursor.execute("SELECT COUNT(*) as c FROM LEADS WHERE data_origin != 'test_data';")
        genuine_leads_c = cursor.fetchone()["c"]
        
        # 2. Leads by Status
        cursor.execute(f"SELECT lead_status, COUNT(*) as c FROM LEADS{where_clause} GROUP BY lead_status;")
        status_map = {r["lead_status"]: r["c"] for r in cursor.fetchall()}
        
        # 3. Scored Leads & Average Score
        cursor.execute(f"SELECT COUNT(*) as c, AVG(lead_score) as avg_s FROM LEADS{and_clause} lead_score IS NOT NULL;")
        row_score = cursor.fetchone()
        scored_count = row_score["c"]
        avg_score = round(row_score["avg_s"], 1) if row_score["avg_s"] is not None else 0.0
        
        # 4. Leads by Priority
        cursor.execute(f"SELECT priority, COUNT(*) as c FROM LEADS{and_clause} priority IS NOT NULL GROUP BY priority;")
        priority_map = {r["priority"]: r["c"] for r in cursor.fetchall()}
        
        # 5. Follow-up metrics (Hyderabad-partitioned when use_active is True)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today_date = datetime.date.today().isoformat()
        
        if use_active:
            cursor.execute("""
                SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE f 
                JOIN LEADS l ON f.lead_id = l.lead_id 
                WHERE (l.city = 'Hyderabad' OR l.is_service_area = 1);
            """)
            total_fu = cursor.fetchone()["c"]
            
            cursor.execute("""
                SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE f 
                JOIN LEADS l ON f.lead_id = l.lead_id 
                WHERE (l.city = 'Hyderabad' OR l.is_service_area = 1) 
                  AND f.status IN ('Scheduled', 'Due') AND f.scheduled_for <= ?;
            """, (now_str,))
            pending_due_fu = cursor.fetchone()["c"]
            
            cursor.execute("""
                SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE f 
                JOIN LEADS l ON f.lead_id = l.lead_id 
                WHERE (l.city = 'Hyderabad' OR l.is_service_area = 1) 
                  AND f.status = 'Scheduled' AND f.scheduled_for > ?;
            """, (now_str,))
            upcoming_fu = cursor.fetchone()["c"]
            
            cursor.execute("""
                SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE f 
                JOIN LEADS l ON f.lead_id = l.lead_id 
                WHERE (l.city = 'Hyderabad' OR l.is_service_area = 1) 
                  AND f.status IN ('Scheduled', 'Due') AND substr(f.scheduled_for, 1, 10) = ?;
            """, (today_date,))
            today_fu = cursor.fetchone()["c"]
            
            cursor.execute("""
                SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE f 
                JOIN LEADS l ON f.lead_id = l.lead_id 
                WHERE (l.city = 'Hyderabad' OR l.is_service_area = 1) 
                  AND f.status IN ('Scheduled', 'Due') AND f.scheduled_for < ?;
            """, (now_str,))
            overdue_fu = cursor.fetchone()["c"]
            
            cursor.execute("""
                SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE f 
                JOIN LEADS l ON f.lead_id = l.lead_id 
                WHERE (l.city = 'Hyderabad' OR l.is_service_area = 1) 
                  AND f.status IN ('Sent', 'Completed');
            """)
            completed_fu = cursor.fetchone()["c"]
        else:
            cursor.execute("SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE;")
            total_fu = cursor.fetchone()["c"]
            
            cursor.execute("SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE WHERE status IN ('Scheduled', 'Due') AND scheduled_for <= ?;", (now_str,))
            pending_due_fu = cursor.fetchone()["c"]
            
            cursor.execute("SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE WHERE status = 'Scheduled' AND scheduled_for > ?;", (now_str,))
            upcoming_fu = cursor.fetchone()["c"]
            
            cursor.execute("SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE WHERE status IN ('Scheduled', 'Due') AND substr(scheduled_for, 1, 10) = ?;", (today_date,))
            today_fu = cursor.fetchone()["c"]
            
            cursor.execute("SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE WHERE status IN ('Scheduled', 'Due') AND scheduled_for < ?;", (now_str,))
            overdue_fu = cursor.fetchone()["c"]
            
            cursor.execute("SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE WHERE status IN ('Sent', 'Completed');")
            completed_fu = cursor.fetchone()["c"]

        fu_comp_rate = round((completed_fu / total_fu * 100), 1) if total_fu > 0 else 0.0
        
        # 6. Conversion Rate Calculation
        engaged_leads = status_map.get("Converted", 0) + status_map.get("Lost", 0) + status_map.get("Follow-up", 0) + status_map.get("Qualified", 0)
        conversion_rate = (status_map.get("Converted", 0) / engaged_leads * 100) if engaged_leads > 0 else 0.0
        overall_conversion_rate = (status_map.get("Converted", 0) / total_leads * 100) if total_leads > 0 else 0.0
        
        return {
            "total_leads": total_leads,
            "total_test_leads": test_leads_c,
            "total_genuine_leads": genuine_leads_c,
            "new_leads": status_map.get("New", 0),
            "qualified_leads": status_map.get("Qualified", 0),
            "followup_leads": status_map.get("Follow-up", 0),
            "converted_leads": status_map.get("Converted", 0),
            "lost_leads": status_map.get("Lost", 0),
            "high_priority_leads": priority_map.get("High", 0),
            "medium_priority_leads": priority_map.get("Medium", 0),
            "low_priority_leads": priority_map.get("Low", 0),
            "scored_leads_count": scored_count,
            "average_lead_score": avg_score,
            "total_followups": total_fu,
            "pending_due_followups": pending_due_fu,
            "upcoming_followups": upcoming_fu,
            "today_followups": today_fu,
            "overdue_followups": overdue_fu,
            "completed_followups": completed_fu,
            "followup_completion_rate": fu_comp_rate,
            "engaged_conversion_rate": round(conversion_rate, 2),
            "overall_conversion_rate": round(overall_conversion_rate, 2)
        }
    finally:
        conn.close()

def get_hyderabad_kpis(db_path: str = database.DEFAULT_DB_PATH, dataset_scope: str = "all") -> Dict[str, Any]:
    """Convenience accessor for active Hyderabad business KPIs."""
    return get_executive_kpis(db_path=db_path, active_only=True, dataset_scope=dataset_scope)

def get_chart_data(db_path: str = database.DEFAULT_DB_PATH, dataset_scope: str = "all") -> Dict[str, pd.DataFrame]:
    """Generates structured DataFrames for all required analytics charts (including Hyderabad localities and regions)."""
    conn = database.get_connection(db_path)
    try:
        # Check if database has partitioned records
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM LEADS WHERE is_service_area = 0;")
            has_archived = cursor.fetchone()[0] > 0
        except Exception:
            has_archived = False
            
        use_active = has_archived
        conds = []
        if use_active:
            conds.append("(city = 'Hyderabad' OR is_service_area = 1)")
        if dataset_scope in ("genuine_only", "Exclude Test Data"):
            conds.append("data_origin != 'test_data'")
        elif dataset_scope in ("test_only", "Test Data Only"):
            conds.append("data_origin = 'test_data'")
            
        where_active = f" WHERE {' AND '.join(conds)}" if conds else ""
        where_locality = f"{where_active} AND locality IS NOT NULL" if where_active else " WHERE locality IS NOT NULL"
        where_region = f"{where_active} AND region IS NOT NULL" if where_active else " WHERE region IS NOT NULL"

        # 1. Leads by City
        df_city = pd.read_sql_query(f"SELECT city as City, COUNT(*) as Count FROM LEADS{where_active} GROUP BY city ORDER BY Count DESC;", conn)
        
        # 1b. Leads by Locality (Top 10 Hyderabad Localities)
        df_locality = pd.read_sql_query(f"SELECT locality as Locality, COUNT(*) as Count FROM LEADS{where_locality} GROUP BY locality ORDER BY Count DESC LIMIT 10;", conn)
        
        # 1c. Leads by Locality (All Localities with Region & PIN Code)
        df_locality_all = pd.read_sql_query(f"SELECT locality as Locality, region as Region, pincode as 'PIN Code', COUNT(*) as 'Leads Count' FROM LEADS{where_locality} GROUP BY locality, region, pincode ORDER BY 'Leads Count' DESC;", conn)
        
        # 1d. Leads by Region (Hyderabad Metropolitan Regions)
        df_region = pd.read_sql_query(f"SELECT region as Region, COUNT(*) as Count FROM LEADS{where_region} GROUP BY region ORDER BY Count DESC;", conn)

        # 2. Leads by Project Type
        df_pt = pd.read_sql_query(f"SELECT project_type as 'Project Type', COUNT(*) as Count FROM LEADS{where_active} GROUP BY project_type ORDER BY Count DESC;", conn)
        
        # 3. Leads by Budget Range
        df_budget = pd.read_sql_query(f"SELECT budget_range as 'Budget Range', COUNT(*) as Count FROM LEADS{where_active} GROUP BY budget_range ORDER BY Count DESC;", conn)
        
        # 4. Leads by Lead Source
        df_source = pd.read_sql_query(f"SELECT lead_source as 'Lead Source', COUNT(*) as Count FROM LEADS{where_active} GROUP BY lead_source ORDER BY Count DESC;", conn)
        
        # 5. Lead Priority Distribution
        where_prio = f"{where_active} AND priority IS NOT NULL" if where_active else " WHERE priority IS NOT NULL"
        df_priority = pd.read_sql_query(f"SELECT priority as Priority, COUNT(*) as Count FROM LEADS{where_prio} GROUP BY priority ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 3 ELSE 4 END;", conn)
        
        # 6. Lead Status Distribution
        df_status = pd.read_sql_query(f"SELECT lead_status as Status, COUNT(*) as Count FROM LEADS{where_active} GROUP BY lead_status ORDER BY Count DESC;", conn)
        
        # 7. Property Status Analysis
        df_prop = pd.read_sql_query(f"SELECT property_status as 'Property Status', COUNT(*) as Count FROM LEADS{where_active} GROUP BY property_status ORDER BY Count DESC;", conn)
        
        # 8. Purchase Readiness Analysis
        df_ready = pd.read_sql_query(f"SELECT purchase_readiness as 'Purchase Readiness', COUNT(*) as Count FROM LEADS{where_active} GROUP BY purchase_readiness ORDER BY Count DESC;", conn)

        # 9. Monthly Lead Generation Trend
        df_monthly = pd.read_sql_query(f"SELECT substr(created_at, 1, 7) as Month, COUNT(*) as 'Leads Created' FROM LEADS{where_active} GROUP BY Month ORDER BY Month ASC;", conn)

        # 10. Monthly Lead Conversion Trends
        df_conv_trends = pd.read_sql_query(f"""
            SELECT substr(created_at, 1, 7) as Month, 
                   COUNT(*) as 'Total Leads', 
                   SUM(CASE WHEN lead_status = 'Converted' THEN 1 ELSE 0 END) as 'Converted Leads',
                   ROUND(100.0 * SUM(CASE WHEN lead_status = 'Converted' THEN 1 ELSE 0 END) / COUNT(*), 1) as 'Conversion Rate (%)'
            FROM LEADS{where_active} 
            GROUP BY Month 
            ORDER BY Month ASC;
        """, conn)

        # 11. Follow-up Status Distribution (Hyderabad-filtered when partitioned)
        fu_conds = []
        if has_archived:
            fu_conds.append("(l.city = 'Hyderabad' OR l.is_service_area = 1)")
        if dataset_scope in ("genuine_only", "Exclude Test Data"):
            fu_conds.append("l.data_origin != 'test_data'")
        elif dataset_scope in ("test_only", "Test Data Only"):
            fu_conds.append("l.data_origin = 'test_data'")
        
        if fu_conds:
            fu_where = " WHERE " + " AND ".join(fu_conds)
            fu_sql = f"""
                SELECT f.status as 'Follow-up Status', COUNT(*) as Count 
                FROM FOLLOW_UP_SCHEDULE f 
                JOIN LEADS l ON f.lead_id = l.lead_id 
                {fu_where}
                GROUP BY f.status ORDER BY Count DESC;
            """
        else:
            fu_sql = "SELECT status as 'Follow-up Status', COUNT(*) as Count FROM FOLLOW_UP_SCHEDULE GROUP BY status ORDER BY Count DESC;"
        df_fu = pd.read_sql_query(fu_sql, conn)
        
        # 12. Daily & Weekly Lead Creation Trends
        df_daily = pd.read_sql_query(f"SELECT substr(created_at, 1, 10) as Date, COUNT(*) as 'Leads Created' FROM LEADS{where_active} GROUP BY Date ORDER BY Date ASC;", conn)
        df_weekly = pd.read_sql_query(f"SELECT strftime('%Y-W%W', created_at) as Week, COUNT(*) as 'Leads Created' FROM LEADS{where_active} GROUP BY Week ORDER BY Week ASC;", conn)
        df_origin = pd.read_sql_query(f"SELECT data_origin as 'Data Origin', COUNT(*) as Count FROM LEADS{where_active} GROUP BY data_origin ORDER BY Count DESC;", conn)
        
        # 13. Estimate Generation Timeline Trend (Grouped by Estimate Date)
        where_est = f"{where_active} AND estimate_generated_at IS NOT NULL" if where_active else " WHERE estimate_generated_at IS NOT NULL"
        df_est_trend = pd.read_sql_query(f"""
            SELECT substr(estimate_generated_at, 1, 10) as 'Estimate Date',
                   COUNT(*) as 'Estimates Generated',
                   SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END) as 'High Priority',
                   SUM(CASE WHEN priority = 'Medium' THEN 1 ELSE 0 END) as 'Medium Priority'
            FROM LEADS{where_est}
            GROUP BY substr(estimate_generated_at, 1, 10)
            ORDER BY 'Estimate Date' ASC;
        """, conn)

        return {
            "city": df_city,
            "locality": df_locality,
            "locality_all": df_locality_all,
            "region": df_region,
            "project_type": df_pt,
            "budget": df_budget,
            "source": df_source,
            "priority": df_priority,
            "status": df_status,
            "property_status": df_prop,
            "purchase_readiness": df_ready,
            "monthly_generation": df_monthly,
            "conversion_trends": df_conv_trends,
            "followup": df_fu,
            "daily": df_daily,
            "weekly": df_weekly,
            "origin": df_origin,
            "estimate_generation_trend": df_est_trend
        }
    finally:
        conn.close()

def get_hyderabad_followup_queue(
    filter_type: str = "all",
    limit: int = 50,
    db_path: str = database.DEFAULT_DB_PATH
) -> pd.DataFrame:
    """
    Returns upcoming or pending follow-ups for Hyderabad service area leads with customer details.
    filter_type: 'all', 'today', 'overdue', 'upcoming'
    """
    conn = database.get_connection(db_path)
    try:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today_date = datetime.date.today().isoformat()
        
        where_conds = ["(l.city = 'Hyderabad' OR l.is_service_area = 1)"]
        params: List[Any] = []
        
        if filter_type == "today":
            where_conds.append("f.status IN ('Scheduled', 'Due') AND substr(f.scheduled_for, 1, 10) = ?")
            params.append(today_date)
        elif filter_type == "overdue":
            where_conds.append("f.status IN ('Scheduled', 'Due') AND f.scheduled_for < ?")
            params.append(now_str)
        elif filter_type == "upcoming":
            where_conds.append("f.status = 'Scheduled' AND f.scheduled_for > ?")
            params.append(now_str)
            
        where_clause = " WHERE " + " AND ".join(where_conds)
        
        sql = f"""
            SELECT f.schedule_id as 'Schedule ID',
                   l.customer_name as 'Customer Name',
                   COALESCE(l.locality, 'Hyderabad') as 'Locality',
                   COALESCE(l.region, 'West Hyderabad') as 'Region',
                   l.phone as 'Phone',
                   f.scheduled_for as 'Scheduled Time',
                   f.channel as 'Channel',
                   f.status as 'Status',
                   substr(f.message, 1, 75) || '...' as 'Message Preview'
            FROM FOLLOW_UP_SCHEDULE f
            JOIN LEADS l ON f.lead_id = l.lead_id
            {where_clause}
            ORDER BY f.scheduled_for ASC
            LIMIT ?;
        """
        params.append(limit)
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()

def generate_periodic_report(
    period_type: str = "daily",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db_path: str = database.DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """
    Generates a filtered periodic summary report for a selected date window.
    period_type: 'daily', 'weekly', or 'custom'.
    """
    today = datetime.date.today()
    if period_type == "daily":
        s_date = (today - datetime.timedelta(days=1)).isoformat()
        e_date = today.isoformat()
        period_label = f"Daily Snapshot ({s_date} to {e_date})"
    elif period_type == "weekly":
        s_date = (today - datetime.timedelta(days=7)).isoformat()
        e_date = today.isoformat()
        period_label = f"Weekly Report ({s_date} to {e_date})"
    else: # custom
        s_date = start_date or (today - datetime.timedelta(days=30)).isoformat()
        e_date = end_date or today.isoformat()
        period_label = f"Custom Window ({s_date} to {e_date})"

    conn = database.get_connection(db_path)
    try:
        # Filter leads by creation date
        query = "SELECT * FROM LEADS WHERE substr(created_at, 1, 10) BETWEEN ? AND ?;"
        df_period_leads = pd.read_sql_query(query, conn, params=(s_date, e_date))
        
        total_new = len(df_period_leads)
        if total_new > 0:
            priority_dist = dict(df_period_leads["priority"].value_counts())
            status_dist = dict(df_period_leads["lead_status"].value_counts())
            converted = int((df_period_leads["lead_status"] == "Converted").sum())
            lost = int((df_period_leads["lead_status"] == "Lost").sum())
            conv_rate = round((converted / total_new * 100), 2)
            avg_score = round(float(df_period_leads["lead_score"].dropna().mean()), 1) if not df_period_leads["lead_score"].dropna().empty else 0.0
        else:
            priority_dist = {}
            status_dist = {}
            converted = 0
            lost = 0
            conv_rate = 0.0
            avg_score = 0.0

        # Follow-ups during period
        fu_query = "SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE WHERE substr(scheduled_for, 1, 10) BETWEEN ? AND ?;"
        cursor = conn.cursor()
        cursor.execute(fu_query, (s_date, e_date))
        fu_due = cursor.fetchone()["c"]
        
        fu_comp_query = "SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE WHERE status IN ('Sent', 'Completed') AND substr(completed_at, 1, 10) BETWEEN ? AND ?;"
        cursor.execute(fu_comp_query, (s_date, e_date))
        fu_completed = cursor.fetchone()["c"]

        return {
            "period_label": period_label,
            "start_date": s_date,
            "end_date": e_date,
            "new_leads_count": total_new,
            "priority_distribution": priority_dist,
            "status_distribution": status_dist,
            "converted_count": converted,
            "lost_count": lost,
            "period_conversion_rate": conv_rate,
            "average_period_score": avg_score,
            "followups_due_in_period": fu_due,
            "followups_completed_in_period": fu_completed,
            "leads_table": df_period_leads
        }
    finally:
        conn.close()


def get_estimate_analytics(
    db_path: str = database.DEFAULT_DB_PATH, 
    active_only: bool = True,
    dataset_scope: str = "all"
) -> Dict[str, Any]:
    """
    Computes date-based insights using extracted estimate_generated_at:
    - Leads generated today
    - Leads generated this week
    - Leads generated this month
    - Latest estimate generated
    - Leads grouped by estimate generation date
    """
    conn = database.get_connection(db_path)
    try:
        cursor = conn.cursor()
        now = datetime.datetime.now()
        today_date = now.strftime("%Y-%m-%d")
        # Start of current week (Monday)
        start_of_week = (now - datetime.timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        current_month = now.strftime("%Y-%m")

        where_conds = ["estimate_generated_at IS NOT NULL"]
        if active_only:
            where_conds.append("(city = 'Hyderabad' OR is_service_area = 1)")
        if dataset_scope in ("genuine_only", "Exclude Test Data"):
            where_conds.append("data_origin != 'test_data'")
        elif dataset_scope in ("test_only", "Test Data Only"):
            where_conds.append("data_origin = 'test_data'")
        where_clause = " WHERE " + " AND ".join(where_conds)

        # 1. Total estimates decoded
        cursor.execute(f"SELECT COUNT(*) FROM LEADS{where_clause};")
        total_with_est = cursor.fetchone()[0]

        # 2. Today's estimates
        cursor.execute(f"SELECT COUNT(*) FROM LEADS{where_clause} AND substr(estimate_generated_at, 1, 10) = ?;", (today_date,))
        leads_today = cursor.fetchone()[0]

        # 3. This week's estimates
        cursor.execute(f"SELECT COUNT(*) FROM LEADS{where_clause} AND substr(estimate_generated_at, 1, 10) >= ?;", (start_of_week,))
        leads_this_week = cursor.fetchone()[0]

        # 4. This month's estimates
        cursor.execute(f"SELECT COUNT(*) FROM LEADS{where_clause} AND substr(estimate_generated_at, 1, 7) = ?;", (current_month,))
        leads_this_month = cursor.fetchone()[0]

        # 5. Latest estimate generated
        cursor.execute(f"""
            SELECT lead_id, customer_name, locality, region, phone, lead_reference, estimate_generated_at, budget_range, priority
            FROM LEADS{where_clause}
            ORDER BY estimate_generated_at DESC
            LIMIT 1;
        """)
        latest_row = cursor.fetchone()
        latest_est = None
        if latest_row:
            latest_est = {
                "lead_id": latest_row["lead_id"],
                "customer_name": latest_row["customer_name"],
                "locality": latest_row["locality"] or "Hyderabad",
                "region": latest_row["region"] or "Hyderabad",
                "phone": latest_row["phone"],
                "lead_reference": latest_row["lead_reference"],
                "estimate_generated_at": latest_row["estimate_generated_at"],
                "display_time": estimate_parser.format_estimate_display(latest_row["estimate_generated_at"]),
                "display_long": estimate_parser.format_estimate_display_long(latest_row["estimate_generated_at"]),
                "budget_range": latest_row["budget_range"],
                "priority": latest_row["priority"]
            }

        # 6. Grouped by estimate generation date
        df_grouped = pd.read_sql_query(f"""
            SELECT substr(estimate_generated_at, 1, 10) as 'Date',
                   COUNT(*) as 'Lead Count',
                   SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END) as 'High Priority',
                   SUM(CASE WHEN priority = 'Medium' THEN 1 ELSE 0 END) as 'Medium Priority',
                   GROUP_CONCAT(customer_name, ', ') as 'Customers'
            FROM LEADS{where_clause}
            GROUP BY substr(estimate_generated_at, 1, 10)
            ORDER BY 'Date' DESC;
        """, conn)

        return {
            "total_with_estimates": total_with_est,
            "leads_today": leads_today,
            "leads_this_week": leads_this_week,
            "leads_this_month": leads_this_month,
            "latest_estimate": latest_est,
            "grouped_by_date": df_grouped
        }
    finally:
        conn.close()
