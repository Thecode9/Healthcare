import pandas as pd

# Adjust working directory if running from Healthcare/model_files

df = pd.read_csv("Disease precaution.csv")

df2 = pd.read_csv("DiseaseAndSymptoms.csv")

unique_diseases = df["Disease"].nunique()
unique_diseases2 = df2["Disease"].nunique()

df["Disease"] = df["Disease"].str.strip().str.lower()
df2["Disease"] = df2["Disease"].str.strip().str.lower()

# print("Unique diseases in the dataset:", unique_diseases)
# print("Unique diseases in the second dataset:", unique_diseases2)

set1 = set(df["Disease"])
set2 = set(df2["Disease"])

common = set1.intersection(set2)

print("Matching diseases:", len(common))
