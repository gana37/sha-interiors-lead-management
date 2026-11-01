import pandas as pd
import numpy as np
import os
import sys

# Ensure UTF-8 output encoding for Windows consoles
sys.stdout.reconfigure(encoding='utf-8')

raw_path = os.path.join('data', 'raw', 'Leads.csv')
df_raw = pd.read_csv(raw_path)
initial_rows, initial_cols = df_raw.shape
print(f"Loaded raw dataset: {initial_rows} rows, {initial_cols} columns.")

# 1. Convert all placeholder 'Select' strings to NaN
total_selects_before = (df_raw == 'Select').sum().sum()
print(f"Total 'Select' placeholder values detected: {total_selects_before}")

df_cleaned = df_raw.replace('Select', np.nan)
assert (df_cleaned == 'Select').sum().sum() == 0, "'Select' placeholders still remain!"

# 2. Check duplicates
dup_rows = df_cleaned.duplicated().sum()
dup_prospect_id = df_cleaned['Prospect ID'].duplicated().sum()
dup_lead_number = df_cleaned['Lead Number'].duplicated().sum()
print(f"Duplicates -> Rows: {dup_rows}, Prospect ID: {dup_prospect_id}, Lead Number: {dup_lead_number}")

# 3. Drop uninformative zero/near-zero variance columns & columns with extreme missingness (>70%)
cols_to_drop = [
    # 100% Constant columns (0 variance)
    'Magazine',
    'Receive More Updates About Our Courses',
    'Update me on Supply Chain Content',
    'Get updates on DM Content',
    'I agree to pay the amount through cheque',
    # >99.8% Constant columns
    'Do Not Call',
    'Search',
    'Newspaper Article',
    'X Education Forums',
    'Newspaper',
    'Digital Advertisement',
    'Through Recommendations',
    # Extreme missingness (>70% uninformative / missing)
    'How did you hear about X Education',  # 78.5% missing after Select->NaN
    'Lead Profile'                         # 74.2% missing after Select->NaN
]

print(f"Dropping {len(cols_to_drop)} uninformative / severely sparse columns.")
df_clean_subset = df_cleaned.drop(columns=cols_to_drop)

# 4. Standardize string columns (strip whitespace)
for col in df_clean_subset.columns:
    if pd.api.types.is_string_dtype(df_clean_subset[col]):
        df_clean_subset[col] = df_clean_subset[col].str.strip()

# 5. Standardize & impute missing values cleanly
# For categorical columns, impute with explicit label 'Unknown / Not Specified'
df_clean_subset['City'] = df_clean_subset['City'].fillna('Unknown / Not Specified')
df_clean_subset['Specialization'] = df_clean_subset['Specialization'].fillna('Other / Not Specified')
df_clean_subset['What is your current occupation'] = df_clean_subset['What is your current occupation'].fillna('Unspecified')
df_clean_subset['What matters most to you in choosing a course'] = df_clean_subset['What matters most to you in choosing a course'].fillna('Not Specified')
df_clean_subset['Country'] = df_clean_subset['Country'].fillna('Unknown')
df_clean_subset['Lead Source'] = df_clean_subset['Lead Source'].fillna('Unknown')
df_clean_subset['Last Activity'] = df_clean_subset['Last Activity'].fillna('Unknown')
df_clean_subset['Tags'] = df_clean_subset['Tags'].fillna('Untagged')
df_clean_subset['Lead Quality'] = df_clean_subset['Lead Quality'].fillna('Not Assessed')

# For continuous numerical features: TotalVisits and Page Views Per Visit (1.48% missing)
visits_median = df_clean_subset['TotalVisits'].median()
views_median = df_clean_subset['Page Views Per Visit'].median()
df_clean_subset['TotalVisits'] = df_clean_subset['TotalVisits'].fillna(visits_median).astype(int)
df_clean_subset['Page Views Per Visit'] = df_clean_subset['Page Views Per Visit'].fillna(views_median).round(2)
df_clean_subset['Total Time Spent on Website'] = df_clean_subset['Total Time Spent on Website'].astype(int)
df_clean_subset['Converted'] = df_clean_subset['Converted'].astype(int)

# 6. Save cleaned dataset
processed_path = os.path.join('data', 'processed', 'education_leads_cleaned.csv')
df_clean_subset.to_csv(processed_path, index=False)
print(f"Saved cleaned dataset to: {processed_path}")
print(f"Final Cleaned Shape: {df_clean_subset.shape} ({df_clean_subset.shape[0]} rows, {df_clean_subset.shape[1]} columns)")

# Verification
df_verify = pd.read_csv(processed_path)
print(f"Verification re-read: {df_verify.shape}")
print("City value counts in cleaned data:")
print(df_verify['City'].value_counts().head(5))
