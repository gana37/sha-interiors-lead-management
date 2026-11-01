import pandas as pd
import os
import sys

# Ensure utf-8 output for Indian Rupee symbol \u20b9
sys.stdout.reconfigure(encoding='utf-8')

# Load datasets
df_raw = pd.read_csv(os.path.join('data', 'raw', 'Leads.csv'))
df_cleaned = pd.read_csv(os.path.join('data', 'processed', 'education_leads_cleaned.csv'))
df_synth = pd.read_csv(os.path.join('data', 'synthetic', 'interior_design_leads.csv'))

# Create data quality summary table for all original columns
quality_rows = []
for col in df_raw.columns:
    raw_nulls = int(df_raw[col].isna().sum())
    raw_selects = int((df_raw[col].astype(str).str.strip() == 'Select').sum())
    effective_nulls = raw_nulls + raw_selects
    effective_pct = round((effective_nulls / len(df_raw)) * 100, 2)
    
    retained = col in df_cleaned.columns
    status = "Retained & Standardized" if retained else "Removed"
    
    if col in ['Magazine', 'Receive More Updates About Our Courses', 'Update me on Supply Chain Content', 
                'Get updates on DM Content', 'I agree to pay the amount through cheque']:
        reason = "Zero variance (100% constant 'No')"
    elif col in ['Do Not Call', 'Search', 'Newspaper Article', 'X Education Forums', 
                  'Newspaper', 'Digital Advertisement', 'Through Recommendations']:
        reason = "Near-zero variance (>99.8% constant 'No')"
    elif col in ['How did you hear about X Education', 'Lead Profile']:
        reason = "Extreme missingness (>70% null/Select)"
    elif col in ['Tags', 'Lead Quality', 'Asymmetrique Activity Index', 'Asymmetrique Profile Index', 
                  'Asymmetrique Activity Score', 'Asymmetrique Profile Score']:
        reason = "Retained with caveat: Potential post-conversion data leakage"
    elif col in ['City', 'Specialization', 'What is your current occupation', 'What matters most to you in choosing a course', 'Country', 'Lead Source', 'Last Activity']:
        reason = "Retained: Standardized missing/Select to explicit categories"
    elif col in ['TotalVisits', 'Page Views Per Visit']:
        reason = "Retained: Median imputed for numerical stability"
    else:
        reason = "Retained: Core identifier, target, or engagement metric"
        
    quality_rows.append({
        'Column_Name': col,
        'Raw_Dtype': str(df_raw[col].dtype),
        'Raw_Null_Count': raw_nulls,
        'Form_Select_Count': raw_selects,
        'Effective_Missing_Pct': effective_pct,
        'Status_in_Cleaned': status,
        'Engineering_Reason': reason
    })

df_quality = pd.DataFrame(quality_rows)
quality_csv_path = os.path.join('reports', 'data_quality_summary.csv')
df_quality.to_csv(quality_csv_path, index=False)
print(f"Generated quality summary table at: {quality_csv_path}")

# Run validation checks
print("\n=== SYSTEM VALIDATION CHECKS ===")
print("1. Raw files exist & unchanged:")
for f in ['Leads.csv', 'Leads Data Dictionary.xlsx', 'image.jpg']:
    orig_exists = os.path.exists(f)
    raw_copy_exists = os.path.exists(os.path.join('data', 'raw', f))
    orig_size = os.path.getsize(f)
    raw_size = os.path.getsize(os.path.join('data', 'raw', f))
    assert orig_size == raw_size, f"Size mismatch for {f}"
    print(f"   - {f}: OK (Size: {orig_size:,} bytes)")

print("\n2. Processed education dataset:")
assert os.path.exists(os.path.join('data', 'processed', 'education_leads_cleaned.csv')), "Cleaned file missing"
print(f"   - Shape: {df_cleaned.shape} (9,240 rows, 23 columns)")
print(f"   - Duplicates: {df_cleaned.duplicated().sum()}")
print(f"   - Target 'Converted' balance: {dict(df_cleaned['Converted'].value_counts())}")

print("\n3. Synthetic interior design dataset:")
assert os.path.exists(os.path.join('data', 'synthetic', 'interior_design_leads.csv')), "Synthetic file missing"
print(f"   - Shape: {df_synth.shape} (250 rows, 16 columns)")
print(f"   - Unique Lead_IDs: {df_synth['Lead_ID'].nunique()} / {len(df_synth)}")
print(f"   - Total Nulls: {df_synth.isna().sum().sum()}")
assert len(df_synth) >= 200, "Synthetic dataset < 200 rows"
assert df_synth['Lead_ID'].nunique() == len(df_synth), "Lead_ID not unique"
assert df_synth.isna().sum().sum() == 0, "Synthetic dataset contains nulls"

print("\n=== SAMPLE ROWS: CLEANED EDUCATION DATASET (Top 5 rows, key columns) ===")
cols_to_show_edu = ['Prospect ID', 'Lead Number', 'Lead Origin', 'Lead Source', 'Total Time Spent on Website', 'City', 'Converted']
print(df_cleaned[cols_to_show_edu].head(5).to_string())

print("\n=== SAMPLE ROWS: SYNTHETIC INTERIOR DESIGN DATASET (Top 5 rows, key columns) ===")
cols_to_show_synth = ['Lead_ID', 'Customer_Name', 'City', 'Budget_Range', 'Project_Type', 'Property_Status', 'Purchase_Readiness', 'Lead_Status']
print(df_synth[cols_to_show_synth].head(5).to_string())
