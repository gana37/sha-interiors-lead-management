import pandas as pd

df = pd.read_csv("Leads.csv")

for col in ['City', 'Specialization', 'How did you hear about X Education', 'Lead Profile']:
    vc = df[col].value_counts(dropna=False).head(5)
    print(f"--- {col} ---")
    print(vc)
    print()
