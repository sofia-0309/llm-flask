from config import supabase_client
import base64
from datetime import datetime, timezone
import random


# establishes supabase client and uploads patients, lab results, prescriptions
class SupabaseUploader:

    def __init__(self):
        # supabase client
        self.client = supabase_client
    # Added parameter to allow to add to featured_patients

    def upload_single_patient(self, patient, uuid, featured = False):
        """
        patient: object from generate_patient, representing the patient class
        and containing 16 fields
        
        upload_single_patient uploads a patient into the Supabase
        """

        def list_to_text(data):

            if isinstance(data, list):
                # join the list elements into a single string
                return ", ".join(data)
            # if it's already a single string or None, just return it
            return data

        data = {
            "id":uuid,
            "name": str(patient.name),
            "date_of_birth": str(patient.dob),
            "age": int(patient.age),  
            "gender": str(patient.gender),
            # just use chief complaint for medical condition
            "medical_condition": str(patient.chief_complaint),
            "medical_history": list_to_text(patient.medical_history),
            "family_medical_history": list_to_text(patient.family_medical_history),
            "surgical_history": list_to_text(patient.surgical_history),
            "allergies": list_to_text(patient.allergies),
            "cholesterol": str(patient.cholesterol) if patient.cholesterol else None,
            "patient_message": str(patient.patient_message),
            "pdmp": patient.pdmp if patient.pdmp is not None else {},
            "immunization": patient.immunization,
            "chief_concern": patient.chief_concern,  
            "height": str(patient.height), 
            "weight": str(patient.weight),  
            "last_bp": str(patient.last_bp),
            "last_visit_date": str(patient.last_visit),
            "condition_image": patient.condition_image
 
        }

        # If user is adding patient, add into featured_patients instead
        if featured:
            response = self.client.table('featured_patients').upsert(data).execute()

            patient_response = self.client.table('featured_patients')\
                .select('id')\
                .eq('name', data['name'])\
                .order('id', desc=True)\
                .limit(1)\
                .execute()
        

        response = self.client.table('patients').upsert(data).execute()

        patient_response = self.client.table('patients')\
            .select('id')\
            .eq('name', data['name'])\
            .order('id', desc=True)\
            .limit(1)\
            .execute()

        # grab the patient_id
        patient_id = patient_response.data[0]['id']

        return {"status": "success", "patient_id": patient_id}
                

        

    # create lab results and prescription uploaders
    
    def upload_lab_results(self, lab_results):

        data = {
            "patient_id": str(lab_results.patient_id),
            "test_name": lab_results.test_name,
            "test_date": lab_results.test_date,
            "test_result": lab_results.test_result
        }
        
        response = self.client.table('results').insert(data).execute()

        # update tasks table with new result id
        result_id = response.data[0]['id']

        #######################################################################################
        # assigns me the newly generated lab results task (for testing)
        #self.client.table("tasks").insert({
        #    "patient_id": str(lab_results.patient_id),
        #    "user_id" : "66ebfc87-6456-4401-9626-4f75f77f88c8", # me (noah)
        #    "result_id": result_id,
        #    "completed": False,
        #    "task_type": "lab_result",
        #    "created_at": datetime.now(timezone.utc).isoformat()
        #}).execute()
        ######################################################################################


        return {"status": "success", "result_id": result_id}

    
    def upload_prescriptions(self, prescription):
        
        data = {
            "patient_id": str(prescription.patient_id),
            "medication": prescription.medication,
            "dose": prescription.dose
        }

        response = self.client.table('prescriptions').insert(data).execute()

        # get the prescription id from response
        prescription_id = response.data[0]['id']

        #######################################################################################
        # assigns me the newly generated prescription task (for testing)
        #self.client.table("tasks").insert({
        #    "patient_id": str(prescription.patient_id),
        #    "user_id": "66ebfc87-6456-4401-9626-4f75f77f88c8", 
        #    "prescription_id": prescription_id,
        #    "completed": False,
        #    "task_type": "prescription",
        #    "created_at": datetime.now(timezone.utc).isoformat()
        #}).execute()
        ######################################################################################

        return {"status": "success", "prescription_id": prescription_id}

    def upload_staff_message(self, staff_message):
        data = {
            "patient_id": str(staff_message.patient_id), "name": staff_message.name,
            "role": staff_message.role, "specialty": staff_message.specialty, "staff_message": staff_message.staff_message,
            "profile_picture": staff_message.profile_picture,
        }

        resp = self.client.table("staff").insert(data).execute()
        staff_id = resp.data[0]["id"]

        fin = {"status": "success", "staff_id": staff_id}
        return fin
    

    def upload_picture(self, patient_id, image_bytes, condition):

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"patient_{patient_id}_{timestamp}.png"

        try:
            
            storage_response = self.client.storage.from_('patient-images').upload(
                filename,
                image_bytes,
                file_options={"content-type": "image/png"}
            )
            
            # Get the public URL for the uploaded image
            image_url = self.client.storage.from_('patient-images').get_public_url(filename)
            

            data = {
                "patient_id": str(patient_id),
                "image_url": image_url,
                "condition": condition,
                "filename": filename,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = self.client.table('images').insert(data).execute()
            image_id = response.data[0]['id']
            
            return {"status": "success", "image_id": image_id, "image_url": image_url}
            
        except Exception as e:
            print(f"Error uploading image: {e}")
            return {"status": "error", "message": str(e)}


    def upload_profile_picture(self, patient_id, image_bytes):
        """
        Uploads a patient's profile picture to the 'profile-pictures' bucket and updates the record.
        """

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"profile_{patient_id}_{timestamp}.png"

        try:
            # upload to 'profile-pictures' bucket
            storage_response = self.client.storage.from_('profile-pictures').upload(
                filename,
                image_bytes,
                file_options={"content-type": "image/png"}
            )

            # get public url
            image_url = self.client.storage.from_('profile-pictures').get_public_url(filename)

            # will be uploaded to profile_picture table
            data = {
                "patient_id": str(patient_id),
                "image_url": image_url,
                "filename": filename,
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            response = self.client.table('profile_pictures').insert(data).execute()
            image_id = response.data[0]['id']

            self.client.table('patients').update({"profile_picture": image_url}).eq("id", patient_id).execute()

            return {
                "status": "success",
                "image_id": image_id,
                "image_url": image_url
            }

        except Exception as e:
            print(f"Error uploading profile picture: {e}")
            return {"status": "error", "message": str(e)}  

    def upload_visit(self, patient_id, visit_data):
        """
        Upload a single visit to the patient_visits table.
        """
        try:
            data = {
                "patient_id": patient_id,
                "visit_date": visit_data["visit_date"],
                "visit_type": visit_data["visit_type"],
                "clinical_notes": visit_data["clinical_notes"],
                "provider_id": visit_data.get("provider_id")
            }
            
            result = self.client.table("patient_visits").insert(data).execute()
            
            return {"status": "success", "visit_id": result.data[0]["id"]}
            
        except Exception as e:
            print(f"Error uploading visit: {e}")
            return {"status": "error", "message": str(e)}  
        


