# responsible for the generation of patients and 
# USMLE Step 2 questions

import os
import argparse
import pandas as pd
from .patient import Patient
from .lab_results import LabResults
from .prescriptions import Prescriptions
from .images import ImageGenerator
from utils.database.supabase_uploader import SupabaseUploader
from utils.generation.mcq_generator import MCQGenerator
from utils.generation.task_runner import run_async 
import random
import uuid
from flask import jsonify
from config import supabase_client
from utils.generation.staff_generator import StaffGenerator


def pick_dermnet_image(condition):
    """
    Returns the first available DermNet image for the condition.
    Assumes images were uploaded into the dermnet_images table.
    """

    condition = condition.lower().strip()

    try:
        result = (
            supabase_client.table("dermnet_images")
            .select("image_url")
            .eq("condition", condition)
            .limit(1)
            .execute()
        )

        if result.data:
            return result.data[0]["image_url"]
    except:
        pass

    return None



def run_generation(task_type, data):
    """
    seperates tasks
    """
    if task_type == "mcq":
        worker = MCQGenerator(data['topics'])
        questions = run_async(worker.generate_questions())
        return questions
    elif task_type == "single_mcq":
        worker = MCQGenerator(data['topics'])
        question = []
        try:
            questions = run_async(worker.generate_one_question(0))
            question.append({
                "question": questions.question,
                "A": questions.A,
                "B": questions.B,
                "C": questions.C,
                "D": questions.D,
                "Answer": questions.Answer,
            })
        except Exception as e:
            this = e;
        return question

    elif task_type == "patient_case":
        return generate_patient_case()
    elif task_type == "lab_result":
        return {"status": "lab_result placeholder"}
    elif task_type == "staff_message":
        return generate_staff_message()
    else:
        return {"error": f"Unknown task_type: {task_type}"}
    
def generate_patient_case(featured = False):
    """
    generates a patient case and uploads it
    to supabase
    """

    # VISUAL_CONDITIONS = [
    #     "Eczema",
    #     "Eczema Flare",
    #     "Acute Eczema Flare",
    #     "Acne",
    #     "Acne Vulgaris Flare",
    #     "Contact Dermatitis",
    #     "Seborrheic Dermatitis",
    #     "Cellulitis",
    #     "Abscess",
    #     "Folliculitis",
    #     "Impetigo",
    #     "Fungal Infection (Tinea)",
    #     "Tinea Corporis (Ringworm)",
    #     "Insect Bite Reaction",
    #     "Urticaria (Hives)",
    #     "Diaper Rash",
    #     "Stasis Dermatitis",
    #     "Pressure Ulcer",
    #     "Skin Tear",
    #     "Ankle Sprain",
    #     "Acute Gout Flare",
    #     "Fall with Contusion",
    #     "Sports-Related Contusion",
    #     "Contusion",
    #     "Minor Laceration",
    #     "Abrasion",
    #     "Jammed Finger",
    #     "Shingles (Herpes Zoster)",
    #     "Hand, Foot, and Mouth Disease",
    #     "Acute Otitis Externa (Swimmer's Ear)",
    #     "Peripheral Vascular Disease",
    #     "Chronic Kidney Disease"
    # ]

    # load in NHANES dataset
    nhanes_path = "NHANES.csv"
    nhanes = pd.read_csv(nhanes_path)
    row = nhanes.sample(1).iloc[0]

    # create a patient object
    patient = Patient(row)

    primary_condition = str(patient.chief_complaint)
    patient.condition_image = pick_dermnet_image(primary_condition)

    
    # upload patient to supabase
    uploader = SupabaseUploader()
    if not featured:
        result = uploader.upload_single_patient(patient)
    else:
        result = uploader.upload_single_patient(patient,True)


    if result["status"] == "success":
        new_patient_id = result["patient_id"]

        # generate profile picture
        profile_result = generate_profile_picture(new_patient_id, uploader, patient)
        if profile_result["status"] == "success":
            print(f"Profile picture uploaded: {profile_result['image_url']}")
        else:
            print("Profile picture failed to upload")
        
        # feed each generate function the supabase uploader and patient objectsx
        generate_lab_results(new_patient_id, uploader, patient)
        generate_prescriptions(new_patient_id, uploader, patient)
        generate_staff_messages(new_patient_id, uploader, patient)

        # # condition to check if patient.chief_complaint == visual condition
        # if patient.chief_complaint in VISUAL_CONDITIONS:
        #     # if true, call generate image, which generates a picture to go along
        #     # with the patient message
        #     try:
        #         image_result = generate_images(new_patient_id, uploader, patient)
                
        #         if image_result["status"] == "success":
        #             print(f"Image uploaded: {image_result['image_url']}")
        #     except Exception as e:
        #         print(f"Image generation error: {e}")
        # else:
        #     print(f"Non-visual condition: {patient.chief_complaint}")

    patient_d={
        "name":patient.name,
        "dob":patient.dob,
        "gender":patient.gender,
        "height":patient.height,
        "weight":patient.weight,
        "last_bp":patient.last_bp,
        "medical_history":patient.medical_history,
        "chief_concern":patient.chief_concern,
        "family_medical_history":patient.family_medical_history
    }
    return {
        "patient_info":patient_d,
        "status": "success", 
        
        "patient_name": patient.name,
        "patient_id": new_patient_id,  
        "message": "Patient generated and uploaded"

    }

def generate_staff_message():
    # read the nhanes file
    nhanes_path = "NHANES.csv"
    nhanes = pd.read_csv(nhanes_path)
    # get one random row from the dataset
    row = nhanes.sample(1).iloc[0]

    # build a patient object from that row, uploader, and staff gen
    patient = Patient(row)
    uploader = SupabaseUploader()
    staff_generator = StaffGenerator(patient=patient)

    # generate the staff message and upload it
    res = staff_generator.generate_and_upload(uploader)

    # build the final response
    fin = {
        "status": res.get("status", "error"), "staff_id": res.get("staff_id"), "message": res.get("message", "staff message generated"),
    }
    # return the final result
    return fin


def generate_staff_messages(patient_id, uploader, patient, count=2):
    staff_generator = StaffGenerator(patient=patient, patient_id=patient_id)
    return staff_generator.generate_and_upload_batch(uploader, count=count)
#Generate patient information but not submit
def generate_new_patient():
    # load in NHANES dataset
    nhanes_path = "NHANES.csv"
    nhanes = pd.read_csv(nhanes_path)
    row = nhanes.sample(1).iloc[0]
    patient = Patient(row)
    primary_condition = str(patient.chief_complaint)
    print(primary_condition)
   


    patient_d={
        "name":patient.name,
        "dob":patient.dob,
        "age":patient.age,
        "gender":patient.gender,
        "height":patient.height,
        "weight":patient.weight,
        "last_bp":patient.last_bp,
        "medical_history":patient.medical_history,
        "chief_concern":patient.chief_concern["chief_complaint"],
        "family_medical_history":patient.family_medical_history
    }

    print(patient_d["chief_concern"])

    return {
        "patient_info":patient_d,
        "status": "success", 
        
        
        "message": "Patient generated "

    }

def upload_supabase(data):
    #print(data)
    nhanes_path = "NHANES.csv"
    nhanes = pd.read_csv(nhanes_path)
    row = nhanes.sample(1).iloc[0]
    #Creates patient object from data
    patient =Patient(row=row, data=data)
    primary_condition = str(patient.chief_complaint)
    patient.condition_image = pick_dermnet_image(primary_condition)
    # upload patient to supabase with asigned id to add foreign key
    uploader = SupabaseUploader()
    new_id = str(uuid.uuid4())
    #print("uuid: ",new_id)
    result1 = uploader.upload_single_patient(patient,new_id)
    
    result2 = uploader.upload_single_patient(patient,new_id,True)


    if result1["status"] == "success" and result2['status']=="success":
        new_patient_id = result1["patient_id"]

        # generate profile picture
        profile_result = generate_profile_picture(new_patient_id, uploader, patient)
        if profile_result["status"] == "success":
            print(f"Profile picture uploaded: {profile_result['image_url']}")
        else:
            print("Profile picture failed to upload")
        
        # feed each generate function the supabase uploader and patient objectsx
        generate_lab_results(new_patient_id, uploader, patient)
        generate_prescriptions(new_patient_id, uploader, patient)
        generate_staff_messages(new_patient_id, uploader, patient)

    return {
        "status":"success",
        "patient_info":patient
    }



def generate_lab_results(patient_id, uploader, patient):
    """
    generates lab results and uploads into supabase
    """
    # lab results get patient_id: uuid, test_name: text, test_date: text, test_result: json

    # create a lab results object
    lab_results = LabResults(patient_id, patient) 

    # upload lab results to supabase
    result = uploader.upload_lab_results(lab_results)


    return


def generate_prescriptions(patient_id, uploader, patient):
    """
    generates prescription information and uploads into supabase
    """
    # prescriptions get patient_id: uuid, medication: text, dose: text

    # create prescriptions object
    prescription = Prescriptions(patient_id, patient)

    # upload prescriptions to supabase
    result = uploader.upload_prescriptions(prescription)

    return


def generate_images(patient_id, uploader, patient):
    """
    generate images of certain medical conditions
    """

    try:
        # initialize the image generator
        generator = ImageGenerator(patient)
        
        # build the prompt based on patient data
        prompt = generator.build_prompt()
        
        # generate the image
        image_bytes = generator.generate_image(prompt)
        
        # upload to Supabase
        result = uploader.upload_picture(
            patient_id=patient_id,
            image_bytes=image_bytes,
            condition=patient.chief_complaint
        )
        
        return result
        
    except Exception as e:
        print(f"Error generating image: {e}")
        return {"status": "error", "message": str(e)}
    

def generate_profile_picture(patient_id, uploader, patient):
    """
    Generate and upload a patient's profile picture.
    """

    try:
        generator = ImageGenerator(patient)
        image_bytes = generator.generate_profile_picture()

        result = uploader.upload_profile_picture(
            patient_id=patient_id,
            image_bytes=image_bytes
        )

        return result

    except Exception as e:
        print(f"Error generating profile picture: {e}")
        return {"status": "error", "message": str(e)}