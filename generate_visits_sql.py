"""
Generate SQL file with all visit history inserts
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import supabase_client
from processors.visit_history import VisitHistoryGenerator

def fetch_all_patients():
    """Fetch all patients from the database."""
    try:
        result = supabase_client.table("patients").select("*").execute()
        return result.data
    except Exception as e:
        print(f"Error fetching patients: {e}")
        return []

def create_patient_object_from_db(patient_data):
    """Create a Patient-like object from database data."""
    class DBPatient:
        def __init__(self, data):
            self.id = data.get("id")
            self.name = data.get("name")
            self.dob = data.get("date_of_birth")
            self.age = data.get("age", 0)
            self.gender = data.get("gender")
            self.height = data.get("height")
            self.weight = data.get("weight")
            self.last_bp = data.get("last_bp")
            
            conditions = data.get("medical_condition", "")
            if isinstance(conditions, str):
                self.medical_condition = [c.strip() for c in conditions.split(",") if c.strip()]
            else:
                self.medical_condition = conditions or []
            
            history = data.get("medical_history", "")
            if isinstance(history, str):
                self.medical_history = [h.strip() for h in history.split(",") if h.strip()]
            else:
                self.medical_history = history or []
            
            chief_concern = data.get("chief_concern", {})
            if isinstance(chief_concern, dict):
                complaints = chief_concern.get("chief_complaint", ["General checkup"])
                self.chief_complaint = complaints[0] if isinstance(complaints, list) else "General checkup"
            else:
                self.chief_complaint = "General checkup"
    
    return DBPatient(patient_data)

def main():
    print("=" * 60)
    print("GENERATING VISIT HISTORY SQL FILE")
    print("=" * 60)
    print()
    
    print("Fetching patients...")
    patients = fetch_all_patients()
    print(f"Found {len(patients)} patients")
    print()
    
    sql_statements = []
    total_visits = 0
    
    print("Generating visit history...")
    print("-" * 60)
    
    for i, patient_data in enumerate(patients, 1):
        patient_id = patient_data.get("id")
        patient_name = patient_data.get("name")
        
        print(f"[{i}/{len(patients)}] {patient_name}...", end=" ")
        
        try:
            patient = create_patient_object_from_db(patient_data)
            generator = VisitHistoryGenerator(patient)
            visits = generator.generate_visit_history()
            
            for visit in visits:
                # Escape single quotes in clinical notes
                notes = visit["clinical_notes"].replace("'", "''")
                
                sql = f"""INSERT INTO patient_visits (patient_id, visit_date, visit_type, clinical_notes, provider_id)
VALUES ('{patient_id}', '{visit["visit_date"]}', '{visit["visit_type"]}', '{notes}', NULL);"""
                
                sql_statements.append(sql)
                total_visits += 1
            
            print(f"✓ {len(visits)} visits")
        
        except Exception as e:
            print(f"✗ ERROR: {e}")
            continue
    
    # Write to file
    output_file = "visit_history_inserts.sql"
    with open(output_file, "w") as f:
        f.write("-- Generated visit history inserts\n")
        f.write("-- Run this file in Supabase SQL Editor\n\n")
        f.write("\n".join(sql_statements))
    
    print()
    print("=" * 60)
    print("COMPLETE!")
    print("=" * 60)
    print(f"Total patients: {len(patients)}")
    print(f"Total visits generated: {total_visits}")
    print(f"SQL file saved to: {output_file}")
    print()
    print("Next steps:")
    print("1. Open the file 'visit_history_inserts.sql'")
    print("2. Copy all the SQL")
    print("3. Paste into Supabase SQL Editor")
    print("4. Click 'Run'")
    print("=" * 60)

if __name__ == "__main__":
    main()