import database
import sys

sys.stdout.reconfigure(encoding='utf-8')

stats = database.get_lead_stats()
print("=== PRODUCTION DB STATS ===")
print("Total leads:", stats["total_leads"])
print("Scored leads:", stats["scored_count"])
print("Average score:", stats["avg_score"])
print("Priority counts:", stats["priority_counts"])
print("Status counts:", stats["status_counts"])

leads = database.get_all_leads(order_by="lead_score DESC")
print("\n=== TOP 3 HIGH PRIORITY LEADS ===")
for l in leads[:3]:
    print(f"{l['lead_id']} | {l['customer_name']} | {l['city']} | {l['budget_range']} | Score: {l['lead_score']:.0f} ({l['priority']})")
    print(f"   Reason: {l['scoring_reason']}")

print("\n=== BOTTOM 3 LOW PRIORITY LEADS ===")
for l in leads[-3:]:
    print(f"{l['lead_id']} | {l['customer_name']} | {l['city']} | {l['budget_range']} | Score: {l['lead_score']:.0f} ({l['priority']})")
    print(f"   Reason: {l['scoring_reason']}")
