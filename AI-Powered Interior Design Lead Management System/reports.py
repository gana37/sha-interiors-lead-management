import datetime
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import database

def get_executive_kpis(db_path: str = database.DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Computes high-level executive CRM and follow-up metrics from SQLite."""
    conn = database.get_connection(db_path)
    try:
        cursor = conn.cursor()
        
        # 1. Total Leads
        cursor.execute("SELECT COUNT(*) as c FROM LEADS;")
        total_leads = cursor.fetchone()["c"]
        
        # 2. Leads by Status
        cursor.execute("SELECT lead_status, COUNT(*) as c FROM LEADS GROUP BY lead_status;")
        status_map = {r["lead_status"]: r["c"] for r in cursor.fetchall()}
        
        # 3. Scored Leads & Average Score
        cursor.execute("SELECT COUNT(*) as c, AVG(lead_score) as avg_s FROM LEADS WHERE lead_score IS NOT NULL;")
        row_score = cursor.fetchone()
        scored_count = row_score["c"]
        avg_score = round(row_score["avg_s"], 1) if row_score["avg_s"] is not None else 0.0
        
        # 4. Leads by Priority
        cursor.execute("SELECT priority, COUNT(*) as c FROM LEADS WHERE priority IS NOT NULL GROUP BY priority;")
        priority_map = {r["priority"]: r["c"] for r in cursor.fetchall()}
        
        # 5. Follow-up metrics
        cursor.execute("SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE;")
        total_fu = cursor.fetchone()["c"]
        
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE WHERE status IN ('Scheduled', 'Due') AND scheduled_for <= ?;", (now_str,))
        pending_due_fu = cursor.fetchone()["c"]
        
        cursor.execute("SELECT COUNT(*) as c FROM FOLLOW_UP_SCHEDULE WHERE status IN ('Sent', 'Completed');")
        completed_fu = cursor.fetchone()["c"]
        
        # 6. Conversion Rate Calculation
        # Definition: Converted Leads / (Converted + Lost + Follow-up + Qualified) * 100
        # Excludes unprocessed 'New' leads that haven't been contacted yet.
        engaged_leads = status_map.get("Converted", 0) + status_map.get("Lost", 0) + status_map.get("Follow-up", 0) + status_map.get("Qualified", 0)
        conversion_rate = (status_map.get("Converted", 0) / engaged_leads * 100) if engaged_leads > 0 else 0.0
        overall_conversion_rate = (status_map.get("Converted", 0) / total_leads * 100) if total_leads > 0 else 0.0
        
        return {
            "total_leads": total_leads,
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
            "completed_followups": completed_fu,
            "engaged_conversion_rate": round(conversion_rate, 2),
            "overall_conversion_rate": round(overall_conversion_rate, 2)
        }
    finally:
        conn.close()

def get_chart_data(db_path: str = database.DEFAULT_DB_PATH) -> Dict[str, pd.DataFrame]:
    """Generates structured DataFrames for all 9 required analytics charts."""
    conn = database.get_connection(db_path)
    try:
        # 1. Leads by City
        df_city = pd.read_sql_query("SELECT city as City, COUNT(*) as Count FROM LEADS GROUP BY city ORDER BY Count DESC;", conn)
        
        # 2. Leads by Project Type
        df_pt = pd.read_sql_query("SELECT project_type as 'Project Type', COUNT(*) as Count FROM LEADS GROUP BY project_type ORDER BY Count DESC;", conn)
        
        # 3. Leads by Budget Range
        df_budget = pd.read_sql_query("SELECT budget_range as 'Budget Range', COUNT(*) as Count FROM LEADS GROUP BY budget_range ORDER BY Count DESC;", conn)
        
        # 4. Leads by Lead Source
        df_source = pd.read_sql_query("SELECT lead_source as 'Lead Source', COUNT(*) as Count FROM LEADS GROUP BY lead_source ORDER BY Count DESC;", conn)
        
        # 5. Lead Priority Distribution
        df_priority = pd.read_sql_query("SELECT priority as Priority, COUNT(*) as Count FROM LEADS WHERE priority IS NOT NULL GROUP BY priority;", conn)
        
        # 6. Lead Status Distribution
        df_status = pd.read_sql_query("SELECT lead_status as Status, COUNT(*) as Count FROM LEADS GROUP BY lead_status ORDER BY Count DESC;", conn)
        
        # 7. Follow-up Status Distribution
        df_fu = pd.read_sql_query("SELECT status as 'Follow-up Status', COUNT(*) as Count FROM FOLLOW_UP_SCHEDULE GROUP BY status ORDER BY Count DESC;", conn)
        
        # 8. Daily Lead Creation Trend
        df_daily = pd.read_sql_query("SELECT substr(created_at, 1, 10) as Date, COUNT(*) as 'Leads Created' FROM LEADS GROUP BY Date ORDER BY Date ASC;", conn)
        
        # 9. Weekly Lead Creation Trend
        df_weekly = pd.read_sql_query("SELECT strftime('%Y-W%W', created_at) as Week, COUNT(*) as 'Leads Created' FROM LEADS GROUP BY Week ORDER BY Week ASC;", conn)
        
        return {
            "city": df_city,
            "project_type": df_pt,
            "budget": df_budget,
            "source": df_source,
            "priority": df_priority,
            "status": df_status,
            "followup": df_fu,
            "daily": df_daily,
            "weekly": df_weekly
        }
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
