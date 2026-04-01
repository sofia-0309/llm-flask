"""
Standalone script to generate visit history for all existing patients in the database.
Run this once to populate visit history for patients that don't have any.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path so we can import from processors
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import supabase_client
from processors.visit_history import VisitHistoryGenerator
from utils.database.supabase_uploader import SupabaseUploader

def fetch_all_patients():
    """Fetch all patients from the database."""
    try:
        result = supabase_client.table("patients").select("*").execute()
        return result.data
    except Exception as e:
        print(f"Error fetching patients: {e}")
        return []

def patient_has_visits(patient_id):
    """Check if patient already has visit history."""
    try:
        result = supabase_client.table("patient_visits").select("id").eq("patient_id", patient_id).limit(1).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"Error checking visits for patient {patient_id}: {e}")
        return False

def create_patient_object_from_db(patient_data):
    """
    Create a Patient-like object from database data.
    This mimics the Patient class structure without needing NHANES.
    """
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
            
            # Parse medical conditions from text to list
            conditions = data.get("medical_condition", "")
            if isinstance(conditions, str):
                self.medical_condition = [c.strip() for c in conditions.split(",") if c.strip()]
            else:
                self.medical_condition = conditions or []
            
            # Parse medical history
            history = data.get("medical_history", "")
            if isinstance(history, str):
                self.medical_history = [h.strip() for h in history.split(",") if h.strip()]
            else:
                self.medical_history = history or []
            
            # Chief complaint
            chief_concern = data.get("chief_concern", {})
            if isinstance(chief_concern, dict):
                complaints = chief_concern.get("chief_complaint", ["General checkup"])
                self.chief_complaint = complaints[0] if isinstance(complaints, list) else "General checkup"
            else:
                self.chief_complaint = "General checkup"
    
    return DBPatient(patient_data)

def generate_and_upload_visits(patient_data, uploader):
    """Generate visit history for a single patient and upload to database."""
    patient_id = patient_data.get("id")
    patient_name = patient_data.get("name")
    
    try:
        # Create patient object from database data
        patient = create_patient_object_from_db(patient_data)
        
        
        generator = VisitHistoryGenerator(patient)
        visits = generator.generate_visit_history()
        
        # Upload each visit
        success_count = 0
        for visit in visits:
            result = uploader.upload_visit(
                patient_id=patient_id,
                visit_data=visit
            )
            if result["status"] == "success":
                success_count += 1
        
        return {
            "status": "success",
            "patient_name": patient_name,
            "num_visits": len(visits),
            "uploaded": success_count
        }
        
    except Exception as e:
        return {
            "status": "error",
            "patient_name": patient_name,
            "message": str(e)
        }

def main():
    """Main function to backfill visit history for all patients."""
    print("=" * 60)
    print("VISIT HISTORY BACKFILL SCRIPT")
    print("=" * 60)
    print()
    
    # Fetch all patients
    print("Fetching patients from database...")
    patients = fetch_all_patients()
    total_patients = len(patients)
    print(f"Found {total_patients} patients in database")
    print()
    
    if total_patients == 0:
        print("No patients found. Exiting.")
        return
    
    
    uploader = SupabaseUploader()
    
    # Process each patient
    processed = 0
    skipped = 0
    errors = 0
    
    print("Processing patients...")
    print("-" * 60)
    
    for i, patient_data in enumerate(patients, 1):
        patient_id = patient_data.get("id")
        patient_name = patient_data.get("name")
        
        # Check if patient already has visits
        if patient_has_visits(patient_id):
            print(f"[{i}/{total_patients}] SKIP: {patient_name} (already has visit history)")
            skipped += 1
            continue
        
        # Generate and upload visits
        print(f"[{i}/{total_patients}] Processing: {patient_name}...", end=" ")
        result = generate_and_upload_visits(patient_data, uploader)
        
        if result["status"] == "success":
            print(f"✓ Added {result['uploaded']} visits")
            processed += 1
        else:
            print(f"✗ ERROR: {result.get('message', 'Unknown error')}")
            errors += 1
    
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total patients: {total_patients}")
    print(f"Processed: {processed}")
    print(f"Skipped (already have visits): {skipped}")
    print(f"Errors: {errors}")
    print()
    print("Done!")

if __name__ == "__main__":
    main()