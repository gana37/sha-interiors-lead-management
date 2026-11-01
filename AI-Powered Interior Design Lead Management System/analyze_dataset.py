import pandas as pd
import json
import os

print("--- ANALYZING LEADS DATA DICTIONARY ---")
dict_path = "Leads Data Dictionary.xlsx"
excel_file = pd.ExcelFile(dict_path)
print(f"Sheet names: {excel_file.sheet_names}")
dict_df = pd.read_excel(dict_path)
print(f"Dictionary shape: {dict_df.shape}")
print(dict_df.to_string())

print("\n--- ANALYZING LEADS.CSV ---")
csv_path = "Leads.csv"
df = pd.read_csv(csv_path)

total_rows, total_cols = df.shape
print(f"Total Rows: {total_rows}")
print(f"Total Columns: {total_cols}")

# Duplicates check
dup_rows = df.duplicated().sum()
dup_prospect = df['Prospect ID'].duplicated().sum() if 'Prospect ID' in df.columns else 0
dup_lead_num = df['Lead Number'].duplicated().sum() if 'Lead Number' in df.columns else 0
print(f"Duplicate rows: {dup_rows}")
print(f"Duplicate Prospect IDs: {dup_prospect}")
print(f"Duplicate Lead Numbers: {dup_lead_num}")

# Missing values (standard nulls)
missing_counts = df.isnull().sum()
missing_pct = (missing_counts / total_rows) * 100

# 'Select' placeholder check (many categorical fields in this dataset have 'Select' as null)
select_counts = {}
for col in df.select_dtypes(include=['object']).columns:
    count = (df[col] == 'Select').sum()
    if count > 0:
        select_counts[col] = int(count)

# Conversion Rate
converted_counts = df['Converted'].value_counts()
conversion_rate = df['Converted'].mean() * 100
print(f"\nTarget Variable 'Converted':")
print(converted_counts)
print(f"Overall Conversion Rate: {conversion_rate:.2f}%")

# Save detailed summary to json
summary = {
    "total_rows": int(total_rows),
    "total_cols": int(total_cols),
    "duplicate_rows": int(dup_rows),
    "duplicate_prospect_ids": int(dup_prospect),
    "duplicate_lead_numbers": int(dup_lead_num),
    "overall_conversion_rate": float(round(conversion_rate, 2)),
    "columns_summary": [],
    "select_values_count": select_counts
}

for col in df.columns:
    n_null = int(missing_counts[col])
    p_null = float(round(missing_pct[col], 2))
    n_select = int((df[col] == 'Select').sum()) if df[col].dtype == 'object' else 0
    total_missing = n_null + n_select
    total_missing_pct = float(round((total_missing / total_rows) * 100, 2))
    
    unique_vals = int(df[col].nunique())
    sample_vals = [str(x) for x in df[col].dropna().unique()[:5]]
    
    col_info = {
        "column": col,
        "dtype": str(df[col].dtype),
        "null_count": n_null,
        "null_percent": p_null,
        "select_count": n_select,
        "effective_missing_pct": total_missing_pct,
        "unique_values_count": unique_vals,
        "sample_values": sample_vals
    }
    summary["columns_summary"].append(col_info)

with open("dataset_analysis_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("\nAnalysis summary written to dataset_analysis_summary.json successfully.")
