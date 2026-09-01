import sys
from pathlib import Path
import os
import csv
import django
import pickle

project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_healthcare.settings")
django.setup()

from core.models import Disease, Symptom, Medication, Precaution

model_dir = project_root.parent / "model_files"
csv_path = model_dir / "DiseaseAndSymptoms.csv"
precaution_csv_path = model_dir / "Disease precaution.csv"
symptoms_pkl_path = model_dir / "all_symptoms.pkl"

# All 41 diseases predicted by the RandomForest model
DISEASE_MEDICATIONS = {
    "Fungal infection": ["Clotrimazole Cream", "Ketoconazole Shampoo", "Fluconazole (Diflucan)"],
    "Allergy": ["Cetirizine (Zyrtec)", "Diphenhydramine (Benadryl)", "Fluticasone Nasal Spray"],
    "GERD": ["Omeprazole (Prilosec)", "Famotidine (Pepcid)", "Tums Antacid"],
    "Chronic cholestasis": ["Ursodeoxycholic Acid", "Cholestyramine"],
    "Drug Reaction": ["Diphenhydramine (Benadryl)", "Prednisone (Steroid)", "Stop offending medication immediately"],
    "Peptic ulcer diseae": ["Omeprazole (Prilosec)", "Amoxicillin (Antibiotic)", "Clarithromycin"],
    "AIDS": ["Dolutegravir (ART)", "Tenofovir disoproxil", "Emtricitabine"],
    "Diabetes": ["Metformin (Glucophage)", "Insulin Glargine (Lantus)", "Glipizide"],
    "Gastroenteritis": ["Oral Rehydration Salts (ORS)", "Loperamide (Imodium)", "Zinc Supplements"],
    "Bronchial Asthma": ["Albuterol Inhaler (Ventolin)", "Fluticasone Inhaler (Flovent)", "Montelukast (Singulair)"],
    "Hypertension": ["Amlodipine (Norvasc)", "Lisinopril (Zestril)", "Losartan (Cozaar)"],
    "Migraine": ["Sumatriptan (Imitrex)", "Ibuprofen (Advil)", "Propranolol"],
    "Cervical spondylosis": ["Ibuprofen (Advil)", "Cyclobenzaprine (Muscle Relaxer)", "Physical therapy"],
    "Paralysis (brain hemorrhage)": ["Mannitol", "Antihypertensive agents", "Physiotherapy"],
    "Jaundice": ["Intravenous Fluids", "Vitamin K supplements", "Avoid paracetamol/acetaminophen"],
    "Malaria": ["Artemether-Lumefantrine (Coartem)", "Chloroquine", "Paracetamol (for fever)"],
    "Chicken pox": ["Calamine Lotion", "Acyclovir (Zovirax)", "Paracetamol (Avoid aspirin)"],
    "Dengue": ["Paracetamol (Avoid ibuprofen/aspirin)", "Oral Rehydration Salts (ORS)", "Intravenous Fluids"],
    "Typhoid": ["Ciprofloxacin (Antibiotic)", "Ceftriaxone", "Azithromycin"],
    "hepatitis A": ["Supportive care & hydration", "Rest", "Avoid alcohol & fatty food"],
    "Hepatitis B": ["Tenofovir alafenamide", "Entecavir", "Interferon alfa-2b"],
    "Hepatitis C": ["Sofosbuvir", "Velpatasvir", "Ledipasvir"],
    "Hepatitis D": ["Pegylated Interferon-alpha", "Liver support therapy"],
    "Hepatitis E": ["Ribavirin", "Supportive care & hydration"],
    "Alcoholic hepatitis": ["Corticosteroids (Prednisolone)", "Nutritional support", "Complete alcohol abstinence"],
    "Tuberculosis": ["Isoniazid", "Rifampin", "Pyrazinamide", "Ethambutol"],
    "Common Cold": ["Paracetamol (Tylenol)", "Pseudoephedrine (Decongestant)", "Vitamin C & Zinc"],
    "Pneumonia": ["Amoxicillin (Antibiotic)", "Azithromycin (Zithromax)", "Albuterol Inhaler"],
    "Dimorphic hemmorhoids(piles)": ["Witch hazel cream", "Psyllium husk fiber", "Hydrocortisone suppository"],
    "Heart attack": ["Aspirin (chew immediately)", "Nitroglycerin", "Clopidogrel", "CALL EMERGENCY IMMEDIATELY"],
    "Varicose veins": ["Compression stockings", "Flavonoid supplements", "Sclerotherapy (consult surgeon)"],
    "Hypothyroidism": ["Levothyroxine (Synthroid)", "Liothyronine"],
    "Hyperthyroidism": ["Methimazole (Tapazole)", "Propylthiouracil", "Propranolol (Beta blocker)"],
    "Hypoglycemia": ["Glucose tablets", "Glucagon injection", "Fruit juice or honey"],
    "Osteoarthristis": ["Acetaminophen (Tylenol)", "Naproxen (Aleve)", "Glucosamine"],
    "Arthritis": ["Ibuprofen (Advil)", "Methotrexate", "Celecoxib (Celebrex)"],
    "(vertigo) paroymsal  positional vertigo": ["Meclizine (Antivert)", "Epley maneuver therapy", "Betahistine"],
    "Acne": ["Benzoyl Peroxide Gel", "Salicylic Acid wash", "Tretinoin Cream (Retin-A)"],
    "Urinary tract infection": ["Nitrofurantoin (Macrobid)", "Sulfamethoxazole-Trimethoprim (Bactrim)", "Phenazopyridine (for pain)"],
    "Psoriasis": ["Clobetasol topical steroid", "Coal tar ointment", "Adalimumab (Humira)"],
    "Impetigo": ["Mupirocin Ointment (Bactroban)", "Cephalexin (Keflex)", "Warm compress therapy"]
}

def seed():
    print("Starting database seeding for all 41 diseases...")
    
    print("Clearing existing data...")
    Precaution.objects.all().delete()
    Medication.objects.all().delete()
    Disease.objects.all().delete()
    Symptom.objects.all().delete()

    sintomas_created = 0
    diseases_created = 0
    meds_created = 0
    precautions_created = 0

    if symptoms_pkl_path.exists():
        print("Loading symptoms from all_symptoms.pkl...")
        with open(symptoms_pkl_path, 'rb') as f:
            all_symptoms = pickle.load(f)
        for symp_name in all_symptoms:
            symp_name = symp_name.strip().replace(' ', '_').lower()
            if symp_name:
                Symptom.objects.get_or_create(name=symp_name)
                sintomas_created += 1
        print(f"Created {sintomas_created} symptoms from pickle.")
    else:
        print("Warning: all_symptoms.pkl not found!")

    for disease_name, meds in DISEASE_MEDICATIONS.items():
        # Match disease name casing/normalization (e.g. "Diabetes " to "Diabetes")
        normalized_name = disease_name.strip()
        disease_obj, created_d = Disease.objects.get_or_create(
            name=normalized_name
        )
        if created_d:
            diseases_created += 1
            
        for med_name in meds:
            med_obj, created_m = Medication.objects.get_or_create(
                name=med_name,
                disease=disease_obj,
                defaults={'dosage_instructions': "Take as prescribed by your consulting physician."}
            )
            if created_m:
                meds_created += 1

    if precaution_csv_path.exists():
        print("Loading precautions from Disease precaution.csv...")
        with open(precaution_csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                if not row:
                    continue
                raw_disease = row[0].strip()
                if not raw_disease:
                    continue
                
                # Match disease name case-insensitively/normalization
                disease_obj = Disease.objects.filter(name__iexact=raw_disease).first()
                if not disease_obj:
                    # Let's create it if missing
                    disease_obj = Disease.objects.create(name=raw_disease)
                    diseases_created += 1
                
                # Extract precautions (columns 1 to 4)
                for i in range(1, len(row)):
                    precaution_text = row[i].strip()
                    if precaution_text:
                        Precaution.objects.create(
                            disease=disease_obj,
                            description=precaution_text
                        )
                        precautions_created += 1
        print(f"Created {precautions_created} precautions.")
    else:
        print("Warning: Disease precaution.csv not found!")

    if csv_path.exists():
        print("Linking symptoms to diseases from DiseaseAndSymptoms.csv...")
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            symptom_indices = [i for i, col in enumerate(header) if col.lower().startswith('symptom')]
            
            for row in reader:
                if not row:
                    continue
                raw_disease = row[0].strip()
                if not raw_disease:
                    continue
                
                disease_obj = Disease.objects.filter(name__iexact=raw_disease).first()
                if disease_obj:
                    disease_symptoms = []
                    for idx in symptom_indices:
                        if idx < len(row):
                            raw_symptom = row[idx].strip().replace(' ', '_').lower()
                            if raw_symptom and raw_symptom != 'nan':
                                # Fetch or create the symptom to be safe
                                symptom_obj, created_s = Symptom.objects.get_or_create(
                                    name=raw_symptom
                                )
                                disease_symptoms.append(symptom_obj)
                    if disease_symptoms:
                        disease_obj.symptoms.add(*disease_symptoms)
        print("Symptom-Disease linking completed.")

    print("\nSeeding finished successfully!")
    print(f"Total symptoms in DB: {Symptom.objects.count()}")
    print(f"Total diseases in DB: {Disease.objects.count()}")
    print(f"Total medications in DB: {Medication.objects.count()}")
    print(f"Total precautions in DB: {Precaution.objects.count()}")

if __name__ == "__main__":
    seed()
