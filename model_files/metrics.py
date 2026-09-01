"""
Dataset Metrics & Alignment Utility for MedAI.

Evaluates disease dataset consistency and cross-references unique disease entries
between precautions and symptom mapping files.
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

def evaluate_dataset_consistency():
    precaution_file = BASE_DIR / "Disease precaution.csv"
    symptom_file = BASE_DIR / "DiseaseAndSymptoms.csv"

    if not precaution_file.exists() or not symptom_file.exists():
        print("[MedAI Metrics] Dataset files missing from model_files directory.")
        return

    df_precaution = pd.read_csv(precaution_file)
    df_symptoms = pd.read_csv(symptom_file)

    df_precaution["Disease"] = df_precaution["Disease"].astype(str).str.strip().str.lower()
    df_symptoms["Disease"] = df_symptoms["Disease"].astype(str).str.strip().str.lower()

    set_precaution = set(df_precaution["Disease"])
    set_symptoms = set(df_symptoms["Disease"])
    common_diseases = set_precaution.intersection(set_symptoms)

    print("=== MedAI Dataset Consistency Report ===")
    print(f"Unique diseases in precautions dataset : {len(set_precaution)}")
    print(f"Unique diseases in symptoms dataset    : {len(set_symptoms)}")
    print(f"Matching disease overlap               : {len(common_diseases)}")


if __name__ == "__main__":
    evaluate_dataset_consistency()

