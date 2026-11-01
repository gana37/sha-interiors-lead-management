import pandas as pd

df = pd.read_csv("Leads.csv")

total = len(df)
print(f"Total Rows: {total}")

results = []
for col in df.columns:
    nulls = int(df[col].isna().sum())
    selects = int((df[col].astype(str).str.strip() == 'Select').sum())
    combined = nulls + selects
    results.append({
        "column": col,
        "dtype": str(df[col].dtype),
        "nulls": nulls,
        "nulls_pct": round(nulls / total * 100, 2),
        "selects": selects,
        "selects_pct": round(selects / total * 100, 2),
        "combined_missing": combined,
        "combined_pct": round(combined / total * 100, 2),
        "unique": int(df[col].nunique()),
        "sample": [str(x) for x in df[col].dropna().unique()[:4]]
    })

res_df = pd.DataFrame(results)
print("\n--- COLUMNS SORTED BY COMBINED MISSING PERCENTAGE ---")
sorted_df = res_df.sort_values(by="combined_pct", ascending=False)
for _, r in sorted_df.iterrows():
    if r['combined_pct'] > 0:
        print(f"{r['column']:<42} | Null: {r['nulls_pct']:>5}% | Select: {r['selects_pct']:>5}% | Combined: {r['combined_pct']:>5}%")

print("\n--- SKEWED / CONSTANT COLUMNS (Single Value or almost single value) ---")
for col in df.columns:
    top_val_pct = df[col].value_counts(normalize=True, dropna=False).iloc[0] * 100
    top_val = df[col].value_counts(dropna=False).index[0]
    if top_val_pct > 95:
        print(f"{col:<42} | Dominant: '{top_val}' ({top_val_pct:.2f}%)")
