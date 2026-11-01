import pandas as pd

df = pd.read_csv("Leads.csv")

print("=== LEAD ORIGIN vs CONVERSION RATE ===")
print(df.groupby('Lead Origin')['Converted'].agg(['count', 'mean']).sort_values(by='count', ascending=False))

print("\n=== TOP 8 LEAD SOURCES vs CONVERSION RATE ===")
top_sources = df['Lead Source'].value_counts().head(8).index
print(df[df['Lead Source'].isin(top_sources)].groupby('Lead Source')['Converted'].agg(['count', 'mean']).sort_values(by='count', ascending=False))

print("\n=== TOP 10 TAGS vs CONVERSION RATE ===")
top_tags = df['Tags'].value_counts().head(10).index
print(df[df['Tags'].isin(top_tags)].groupby('Tags')['Converted'].agg(['count', 'mean']).sort_values(by='count', ascending=False))

print("\n=== NUMERIC CORRELATION WITH CONVERTED ===")
num_cols = ['TotalVisits', 'Total Time Spent on Website', 'Page Views Per Visit', 'Converted']
print(df[num_cols].corr()['Converted'].sort_values(ascending=False))
