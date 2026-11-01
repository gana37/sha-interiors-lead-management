import json

with open('dataset_analysis_summary.json') as f:
    d = json.load(f)

print(f"Total Leads: {d['total_rows']}")
print(f"Total Attributes: {d['total_cols']}")
print(f"Duplicate Leads: {d['duplicate_rows']}")
print(f"Duplicate Prospect IDs: {d['duplicate_prospect_ids']}")
print(f"Duplicate Lead Numbers: {d['duplicate_lead_numbers']}")
print(f"Overall Conversion Rate: {d['overall_conversion_rate']}%")

print("\n=== COLUMNS WITH HIGH EFFECTIVE MISSINGNESS (> 30%) ===")
for col in d['columns_summary']:
    if col['effective_missing_pct'] > 30:
        print(f"- {col['column']}: Total Missing = {col['effective_missing_pct']}% (Null: {col['null_percent']}%, 'Select': {col['select_count']})")

print("\n=== COLUMNS WITH MODERATE EFFECTIVE MISSINGNESS (5% - 30%) ===")
for col in d['columns_summary']:
    if 5 < col['effective_missing_pct'] <= 30:
        print(f"- {col['column']}: Total Missing = {col['effective_missing_pct']}% (Null: {col['null_percent']}%, 'Select': {col['select_count']})")

print("\n=== COLUMNS WITH LOW OR NO MISSINGNESS (<= 5%) ===")
for col in d['columns_summary']:
    if col['effective_missing_pct'] <= 5:
        print(f"- {col['column']}: Missing = {col['effective_missing_pct']}%, Unique Count = {col['unique_values_count']}, Samples = {col['sample_values'][:3]}")
