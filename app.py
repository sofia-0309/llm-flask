import os
import json
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv
from openai import OpenAI
from config import supabase_client
from processors.generation import upload_supabase
from processors.generation import generate_new_patient
from processors.generation import run_generation
from processors.evaluation import run_evaluation
from flask_cors import CORS

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("Missing OpenAI API Key. Please set OPENAI_API_KEY in the .env file.")

client = OpenAI(api_key=openai_api_key)

app = Flask(__name__)
app.debug = True

# Configure CORS with allowed origins
allowed_origins = ["http://localhost:3000"]

# Add production frontend URL if set
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)


CORS(app, origins=allowed_origins)


@app.route("/", methods=["GET"])
def home():
    """
    Basic route to confirm the Flask microservice is up.
    """
    return {"message": "Flask & OpenAI microservice is working !"}


@app.route("/api/patient-concerns", methods=['POST'])
def patient_concerns():
    data = request.get_json() or {}
    age = data.get("age")
    gender = data.get("gender")

    if age == None or gender == "":
        return jsonify({'error': 'age and gender are required'}), 400
    # base case for checking if age or gender is missing

    prompt = (
        '''
        You are a doctor. Using ONLY the patient details below, list 3–5 common medical concerns TRY TO BRING UP SPECIFICS IF POSSIBLE FROM HERE Cervical Cancer:
Screening -- Women aged 21 to 65 years
Colorectal Cancer:
Screening -- Adults aged 50 to 75 years
Folic Acid Supplementation to Prevent Neural Tube Defects:
plan to or could become pregnant
Preventive Medication -- Persons who
Hepatitis B Virus Infection in Pregnant Women:
Screening -- Pregnant women
Human Immunodeficiency Virus (HIV) Infection:
years
Screening -- Adolescents and adults aged 15 to 65
Human Immunodeficiency Virus (HIV) Infection:
Screening -- Pregnant persons
Hypertension in Adults:
Screening -- Adults 18 years or older without known hypertension
Ocular Prophylaxis for Gonococcal Ophthalmia Neonatorum:
Preventive Medication -- Newborns
Prevention of Acquisition of HIV:
Preexposure Prophylaxis -- Adolescents and adults at increased risk of
HIV
Rh(D) Incompatibility:
Screening -- Pregnant women, during the first pregnancy-related care visit
Syphilis Infection During Pregnancy:
Screening -- Asymptomatic pregnant women
Syphilis Infection in Nonpregnant Adolescents and Adults:
adolescents and adults who are at increased risk for syphilis infection
Screening -- Asymptomatic, nonpregnant
Tobacco Smoking Cessation in Adults, Including Pregnant Persons:
Interventions -- Nonpregnant
adults
Tobacco Smoking Cessation in Adults, Including Pregnant Persons:
Interventions -- Pregnant persons
B - Recommended (40)
Abdominal Aortic Aneurysm:
Screening -- Men aged 65 to 75 years who have ever smoked

Anxiety Disorders in Adults:
postpartum persons
Screening -- Adults 64 years or younger, including pregnant and
Anxiety in Children and Adolescents:
Screening -- Children and adolescents aged 8 to 18 years
Aspirin Use to Prevent Preeclampsia and Related Morbidity and Mortality:
Pregnant persons at high risk for preeclampsia
Preventive Medication --
Asymptomatic Bacteriuria in Adults:
Screening -- Pregnant persons
BRCA-Related Cancer:
Risk Assessment, Genetic Counseling, and Genetic Testing -- Women with a
personal or family history of breast, ovarian, tubal, or peritoneal cancer or an ancestry associated with
BRCA1/2 gene mutation
Breast Cancer:
years or older
Medication Use to Reduce Risk -- Women at increased risk for breast cancer aged 35
Breast Cancer:
Screening -- Women aged 40 to 74 years
Breastfeeding:
Primary Care Behavioral Counseling Interventions -- Pregnant and postpartum women
Chlamydia and Gonorrhea:
Screening -- Sexually active women, including pregnant persons
Chlamydia and Gonorrhea:
Screening -- Sexually active women, including pregnant persons
Colorectal Cancer:
Screening -- Adults aged 45 to 49 years
Depression and Suicide Risk in Adults:
and older adults (65 years or older)
Screening -- Adults, including pregnant and postpartum persons,
Depression and Suicide Risk in Children and Adolescents:
Screening -- Adolescents aged 12 to 18
years
Falls Prevention in Community-Dwelling Older Adults:
years or older
Interventions -- Community-dwelling adults 65
Gestational Diabetes:
Screening -- Asymptomatic pregnant persons at 24 weeks of gestation or after
Healthy Diet and Physical Activity for Cardiovascular Disease Prevention in Adults With
Cardiovascular Risk Factors:
Behavioral Counseling Interventions -- Adults with cardiovascular disease
risk factors
Healthy Weight and Weight Gain In Pregnancy:
persons
Behavioral Counseling Interventions -- Pregnant
https://www.uspreventiveservicestaskforce.org/webview/#!/
Page 2 of 9
Prevention TaskForce Search
2/16/26, 6:05 PM
Hepatitis B Virus Infection in Adolescents and Adults:
increased risk for infection
Screening -- Adolescents and adults at
Hepatitis C Virus Infection in Adolescents and Adults:
Screening -- Adults aged 18 to 79 years
High Body Mass Index in Children and Adolescents:
or older
Interventions -- Children and adolescents 6 years
Hypertensive Disorders of Pregnancy:
Screening -- Asymptomatic pregnant persons
Intimate Partner Violence and Caregiver Abuse of Older or Vulnerable Adults:
reproductive age, including pregnant and postpartum women
Screening -- Women of
Latent Tuberculosis Infection in Adults:
tuberculosis infection (LTBI)
Screening -- Asymptomatic adults at increased risk of latent
Lung Cancer:
Screening -- Adults aged 50 to 80 years who have a 20 pack-year smoking history and
currently smoke or have quit within the past 15 years
Osteoporosis to Prevent Fractures:
or more risk factors for osteoporosis
Screening -- Postmenopausal women younger than 65 years with 1
Osteoporosis to Prevent Fractures:
Screening -- Women 65 years or older
Perinatal Depression:
Preventive Interventions -- Pregnant and postpartum persons
Prediabetes and Type 2 Diabetes:
overweight or obesity
Screening -- Asymptomatic adults aged 35 to 70 years who have
Prevention of Dental Caries in Children Younger Than 5 Years:
younger than 5 years
Screening and Interventions -- Children
Prevention of Dental Caries in Children Younger Than 5 Years:
younger than 5 years
Screening and Interventions -- Children
Rh(D) Incompatibility:
Screening -- Unsensitized Rh(D)-negative pregnant women
Sexually Transmitted Infections:
increased risk
Behavioral Counseling -- Sexually active adolescents and adults at
Skin Cancer Prevention:
young children
Behavioral Counseling -- Young adults, adolescents, children, and parents of
Statin Use for the Primary Prevention of Cardiovascular Disease in Adults:
Preventive Medication --
https://www.uspreventiveservicestaskforce.org/webview/#!/
Page 3 of 9
Prevention TaskForce Search
2/16/26, 6:05 PM
Adults aged 40 to 75 years who have 1 or more cardiovascular risk factors and an estimated 10-year
cardiovascular disease (CVD) risk of 10% or greater
Tobacco Use in Children and Adolescents:
adolescents who have not started to use tobacco
Primary Care Interventions -- School-aged children and
Unhealthy Alcohol Use in Adolescents and Adults:
- Adults 18 years or older, including pregnant women
Screening and Behavioral Counseling Interventions -
Unhealthy Drug Use:
Screening -- Adults age 18 years or older
Vision in Children Ages 6 Months to 5 Years:
Screening -- Children aged 3 to 5 years
Weight Loss to Prevent Obesity-Related Morbidity and Mortality in Adults:
Behavioral Interventions --
Adults
C - Selectively Recommended (8)
Abdominal Aortic Aneurysm:
Screening -- Men aged 65 to 75 years who have never smoked
Aspirin Use to Prevent Cardiovascular Disease:
with a 10% or greater 10-year cardiovascular disease (CVD) risk
Preventive Medication -- Adults aged 40 to 59 years
Colorectal Cancer:
Screening -- Adults aged 76 to 85 years
Falls Prevention in Community-Dwelling Older Adults:
years or older
Interventions -- Community-dwelling adults 65
Healthy Diet and Physical Activity for Cardiovascular Disease Prevention in Adults Without
Cardiovascular Disease Risk Factors:
Behavioral Counseling Interventions -- Adults 18 years or older
without known cardiovascular disease risk factors
Prostate Cancer:
Screening -- Men aged 55 to 69 years
Skin Cancer Prevention:
Behavioral Counseling -- Adults older than 24 years with fair skin types
Statin Use for the Primary Prevention of Cardiovascular Disease in Adults:
Preventive Medication --
Adults aged 40 to 75 years who have 1 or more cardiovascular risk factors and an estimated 10-year CVD
risk of 7.5% to less than 10%
D - Not Recommended (22)
Abdominal Aortic Aneurysm:
Screening -- Women who have never smoked
Aspirin Use to Prevent Cardiovascular Disease:
Preventive Medication -- Adults 60 years or older
https://www.uspreventiveservicestaskforce.org/webview/#!/
Page 4 of 9
Prevention TaskForce Search
2/16/26, 6:05 PM
Asymptomatic Bacteriuria in Adults:
Screening -- Nonpregnant adults
Asymptomatic Carotid Artery Stenosis:
Screening -- Asymptomatic adults
Bacterial Vaginosis in Pregnant Persons to Prevent Preterm Delivery:
not at increased risk for preterm delivery
Screening -- Pregnant persons
BRCA-Related Cancer:
Risk Assessment, Genetic Counseling, and Genetic Testing -- Women whose
personal or family history or ancestry is not associated with potential harmful BRCA1/2 gene mutations
Breast Cancer:
years or older
Medication Use to Reduce Risk -- Women not at increased risk for breast cancer aged 35
Cardiovascular Disease Risk:
Screening With Electrocardiography -- Adults at low risk of CVD events
Cervical Cancer:
Screening -- Women older than 65 years
Cervical Cancer:
Screening -- Women who have had a hysterectomy
Cervical Cancer:
Screening -- Women younger than 21 years
Chronic Obstructive Pulmonary Disease:
Screening -- Asymptomatic adults
Genital Herpes Infection:
pregnant persons
Serologic Screening -- Asymptomatic adolescents and adults, including
Hormone Therapy in Postmenopausal Persons:
Postmenopausal persons
Primary Prevention of Chronic Conditions --
Hormone Therapy in Postmenopausal Persons:
Postmenopausal persons who have had a hysterectomy
Primary Prevention of Chronic Conditions --
Ovarian Cancer:
Screening -- Asymptomatic women
Pancreatic Cancer:
Screening -- Adults
Prostate Cancer:
Screening -- Men 70 years and older
Testicular Cancer:
Screening -- Adolescent and Adult Men
Thyroid Cancer:
Screening -- Adults
Vitamin D, Calcium, or Combined Supplementation for the Primary Prevention of Fractures in
Community-Dwelling Adults:
Preventive Medication -- Postmenopausal women

Vitamin, Mineral, and Multivitamin Supplementation to Prevent Cardiovascular Disease and Cancer:
Preventive Medication -- Community-dwelling, nonpregnant adults
I - Uncertain (58)
Abdominal Aortic Aneurysm:
Screening -- Women aged 65 to 75 years who have ever smoked
Adolescent Idiopathic Scoliosis:
Screening -- Children and adolescents aged 10 to 18 years
Anxiety Disorders in Adults:
Screening -- Older adults 65 years or older
Anxiety in Children and Adolescents:
Screening -- Children 7 years or younger
Atrial Fibrillation:
Screening -- Asymptomatic adults 50 years or older
Autism Spectrum Disorder in Young Children:
Screening -- Children aged 18 to 30 months
Bacterial Vaginosis in Pregnant Persons to Prevent Preterm Delivery:
at increased risk for preterm delivery
Screening -- Pregnant persons
Bladder Cancer in Adults:
Screening -- Asymptomatic Adults
Breast Cancer:
Screening -- Women 75 years or older
Breast Cancer:
Screening -- Women with dense breasts
Cardiovascular Disease Risk:
of CVD events
Screening With Electrocardiography -- Adults at intermediate or high risk
Cardiovascular Disease:
Risk Assessment With Nontraditional Risk Factors -- Adults
Celiac Disease:
Screening -- Asymptomatic adults, adolescents, and children
Chlamydia and Gonorrhea:
Screening -- Sexually active men
Cognitive Impairment in Older Adults:
Screening -- Older adults
Depression and Suicide Risk in Adults:
and older adults (65 years or older)
Screening -- Adults, including pregnant and postpartum persons,
Depression and Suicide Risk in Children and Adolescents:
Screening -- Children 11 years or younger
Depression and Suicide Risk in Children and Adolescents:
Screening -- Children and adolescents
Eating Disorders in Adolescents and Adults:
Screening -- Asymptomatic adolescents and adults
Food Insecurity:
Screening -- Children, adolescents, and adults
Gestational Diabetes:
Screening -- Asymptomatic pregnant persons before 24 weeks of gestation
Hearing Loss in Older Adults:
Screening -- Asymptomatic adults 50 years or older
High Blood Pressure in Children and Adolescents:
Screening -- Children and adolescents
Illicit Drug Use in Children, Adolescents, and Young Adults:
Children, adolescents, and young adults
Primary Care-Based Interventions --
Impaired Visual Acuity in Older Adults:
Screening -- Asymptomatic adults 65 years or older
Intimate Partner Violence and Caregiver Abuse of Older or Vulnerable Adults:
vulnerable adults
Screening -- Older or
Iron Deficiency and Iron Deficiency Anemia During Pregnancy:
Asymptomatic pregnant adolescents and adults
Screening and Supplementation --
Iron Deficiency and Iron Deficiency Anemia During Pregnancy:
Asymptomatic pregnant adolescents and adults
Screening and Supplementation --
Iron Deficiency Anemia in Young Children:
Screening -- Children ages 6 to 24 months
Lipid Disorders in Children and Adolescents:
years or younger
Screening -- Asymptomatic children and adolescents 20
Obstructive Sleep Apnea in Adults:
Screening -- General adult population
Oral Cancer:
Screening -- Asymptomatic Adults
Oral Health in Adults:
Screening and Preventive Interventions -- Asymptomatic adults 18 years or older
Oral Health in Adults:
Screening and Preventive Interventions -- Asymptomatic adults 18 years or older
Oral Health in Children and Adolescents Aged 5 to 17 Years:
Asymptomatic children and adolescents aged 5 to 17 years
Screening and Preventive Interventions --
Oral Health in Children and Adolescents Aged 5 to 17 Years:
Asymptomatic children and adolescents aged 5 to 17 years
Screening and Preventive Interventions --
Osteoporosis to Prevent Fractures:
Screening -- Men
Peripheral Artery Disease and Cardiovascular Disease:
Screening and Risk Assessment With the
Ankle-Brachial Index -- Adults
Prediabetes and Type 2 Diabetes in Children and Adolescents:
and adolescents younger than 18 years
Screening -- Asymptomatic children
Prevention of Child Maltreatment:
Primary Care Interventions -- Children and adolescents younger than
18 years without signs and symptoms of or known exposure to maltreatment
Prevention of Dental Caries in Children Younger Than 5 Years:
younger than 5 years
Screening and Interventions -- Children
Primary Open-Angle Glaucoma:
Screening -- Asymptomatic adults 40 years or older
Skin Cancer Prevention:
Behavioral Counseling -- Adults
Skin Cancer:
Screening -- Asymptomatic adolescents and adults
Speech and Language Delay and Disorders in Children:
without signs or symptoms of speech and language delay and disorders
Screening -- Children 5 years or younger
Statin Use for the Primary Prevention of Cardiovascular Disease in Adults:
Adults 76 years or older
Preventive Medication --
Thyroid Dysfunction:
Screening -- Nonpregnant, asymptomatic adults
Tobacco Smoking Cessation in Adults, Including Pregnant Persons:
Interventions -- All adults
Tobacco Smoking Cessation in Adults, Including Pregnant Persons:
Interventions -- Pregnant persons
Tobacco Use in Children and Adolescents:
adolescents who use tobacco
Primary Care Interventions -- School-aged children and
Unhealthy Alcohol Use in Adolescents and Adults:
- Adolescents aged 12 to 17 years
Screening and Behavioral Counseling Interventions -
Unhealthy Drug Use:
Screening -- Adolescents
Vision in Children Ages 6 Months to 5 Years:
Screening -- Children younger than 3 years
Vitamin D Deficiency in Adults:
Screening -- Asymptomatic, community-dwelling, nonpregnant adults
Vitamin D, Calcium, or Combined Supplementation for the Primary Prevention of Fractures in
Community-Dwelling Adults:
Preventive Medication -- Men and premenopausal women
Vitamin D, Calcium, or Combined Supplementation for the Primary Prevention of Fractures in
Community-Dwelling Adults:
Preventive Medication -- Postmenopausal women
Vitamin, Mineral, and Multivitamin Supplementation to Prevent Cardiovascular Disease and Cancer:
Preventive Medication -- Community-dwelling, nonpregnant adults
Vitamin, Mineral, and Multivitamin Supplementation to Prevent Cardiovascular Disease and Cancer:
Preventive Medication -- Community-dwelling, nonpregnant adults







    "or follow up considerations that are relevant to this patients conditions, history, "
    "vitals, or labs. Do NOT include dental or vision care. Do NOT include general preventive advice "
    "unless clearly supported by the patient details. Return ONLY a bullet list. Each bullet must be "
    "short max 10 words and end with a short reason, for example (due to ...). EACH BULLET IS ON A NEW LINE SO FOR AFTER EACH - MAKE A NEWLINE "
    "No full sentences, EACH BULLET IS ON A NEW LINE .\n\n"
    
'''
    )
    
    ## context the ai gets when making correct health 

    response = client.chat.completions.create(model = "gpt-4-turbo", messages = [{"role": 'user', 'content': prompt}], max_tokens=150, temperature=0.4)

    concerns = response.choices[0].message.content.strip()
    return jsonify({'concerns' : concerns})


@app.route("/api/message-request", methods=["POST"])
def message_request():
    """
    1) If task_type == "patient_question", the LLM sees patient_message in both sample_response & feedback.
    2) If task_type != "patient_question", remove patient_message so the LLM never sees it.
    3) The sample_response ALWAYS omits user_message.
    4) The feedback ALWAYS uses the complete final JSON plus user_message to grade the student's response.
    5) The LLM must output exactly one JSON object with only the two keys:
         "sample_response" and "feedback_response"
       and each of their values must be plain text (no nested key values).
    6) NEW: The new student_refilled field is only considered if task_type is "prescription". For non-prescription tasks, any false value is treated as null.
    7) NEW: If a mission is provided, include it in the sample response instructions so the response adheres to the specific task instruction.
    8) NEW: In the feedback instructions, refer to the complete JSON as "comprehensive patient information" instead of "giga json."
    9) NEW: Regardless of task type, include the base instructions:
         "You are a medical student replying to an EHR message from a patient who is under your care. You are their primary healthcare provider."
         "Your response should be professional, concise, patient-friendly, and authoritative. Ask the patient questions if necessary."
    10) NEW: Additionally, if task_type is patient_question, add:
         "If the patient message is related to mental health, give them a disclaimer about calling the Suicide & Crisis Lifeline at 988."
    """
    original_data = request.get_json() or {}
    user_message = original_data.get("user_message", "")
    task_type = original_data.get("task_type", "patient_question")

    # 1) Remove patient_message if task_type is not patient_question
    if task_type != "patient_question":
        original_data.pop("patient_message", None)
        if "patient" in original_data:
            original_data["patient"].pop("patient_message", None)

    # 6) For non-prescription tasks, remove the student_refilled field so that false is treated as null.
    if task_type != "prescription":
        original_data.pop("student_refilled", None)

    # 2) Prepare data for the sample response: remove user_message and task_type.
    data_for_first_paragraph = dict(original_data)
    data_for_first_paragraph.pop("user_message", None)
    data_for_first_paragraph.pop("task_type", None)
    data_for_first_str = json.dumps(data_for_first_paragraph, indent=2)

    # 3) Prepare full JSON string for feedback.
    full_json_str = json.dumps(original_data, indent=2)

    # 7) Retrieve the mission if provided.
    mission_text = original_data.get("mission", "")

    # 9) Base instructions added regardless of task type.
    base_instructions = (
        "You are a medical student replying to an EHR message from a patient who is under your care. "
        "You are their primary healthcare provider. "
        "Your response should be professional, concise, patient-friendly, and authoritative. "
        "Ask the patient questions if necessary."
    )

    universal_intro = f"""
You are an AI assistant. You must return EXACTLY one JSON object with the two keys:
"sample_response" and "feedback_response".

No markdown, no bold text, no italics. Plain text only.

Below is partial GIGA JSON (without user_message and, if task_type is not patient_question, without patient_message):
{data_for_first_str}

{base_instructions}
"""
    if mission_text:
        universal_intro += f"\nThe mission for this task is: {mission_text}\nEnsure your sample response adheres to this instruction."
    universal_intro += "\nCraft the sample response as if you were a medical student. Be concise, professional, and end quickly.\nPut this text in the \"sample_response\" field of your JSON output."

    # Task-specific instructions.
    if task_type == "patient_question":
        task_specific_part = """
Since task_type is patient_question, this is a direct patient inquiry. Provide a succinct, 
patient-friendly explanation or plan. No farewell or filler.
If the patient message is related to mental health, give them a disclaimer about calling the Suicide & Crisis Lifeline at 988.
        """
    elif task_type == "lab_result":
        task_specific_part = """
Since task_type is lab_result, provide a succinct interpretation of the lab results 
and relevant next steps. No concluding phrases or farewells.
        """
    elif task_type == "prescription":
        task_specific_part = """
Since task_type is prescription, provide a concise plan for prescription changes, 
refills, or dosage. (Note: the student_refilled field indicates if the prescription should be refilled: true means refill, false means not refill.)
Avoid farewells or fluff.
        """
    else:
        task_specific_part = """
Unknown task_type. Provide a concise, professional response with no concluding words or farewells.
        """

    first_paragraph = universal_intro + task_specific_part

    # 8) Build the prompt for feedback, referring to the complete JSON as "comprehensive patient information".
    second_paragraph = f"""
Now create the "feedback_response" in plain text, based on the COMPLETE comprehensive patient information:
{full_json_str}

The student's actual response was: "{user_message}"

Write SHORT feedback that is still medically correct.

Format exactly like this:
Top issues:
    max three bullet points less than or equal to 12 words each.
Better Version rewrite:
    one short improved response that takes into account all context given from patient, 1-4 sentences max
Questions to ask:
    Ask 0-2 bullets less than 12 words each



Rules for you to follow:
-Total length must be 160 words or less
-Do NOT restate unnesscessary patient information.
-No greetings or goodbyes, these are 3rd year medical students they know that.

REMEMBER: Output must be valid JSON with exactly these 2 keys:
"sample_response" and "feedback_response"
No extra keys, no markup.
"""

    prompt = f"""
FIRST PARAGRAPH (Sample Response Instructions):
{first_paragraph}

SECOND PARAGRAPH (Feedback Instructions):
{second_paragraph}
"""

    # Reprompt up to 10 times until valid JSON is produced.
    max_attempts = 10
    attempts = 0
    valid_output = None

    while attempts < max_attempts:
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.2
            )
            text_output = response.choices[0].message.content.strip()
            # Check if the output is valid JSON.
            json.loads(text_output)
            valid_output = text_output
            break
        except json.JSONDecodeError:
            attempts += 1

    if valid_output is None:
        return jsonify({"error": "Failed to produce valid JSON after 10 attempts"}), 500

    return Response(valid_output, mimetype="application/json")

@app.route("/api/explain-request", methods=["POST"])
def explain_request():
    print("haha") # <-- check if this prints
    original_data = request.get_json() or {}
    task_type = original_data.get("task_type")
    print(task_type)
    # send data to respective processors based on task type
    if task_type in ["mcq", "single_mcq", "patient_case"]:
        result = run_generation(task_type, original_data)
    elif task_type in ["patient_question","prescription","lab_result", "explain", "follow", "analyze"]:
        print("pick up evaluation")
        result = run_evaluation(task_type, original_data)
    else:
        print("else he")
        return jsonify({"error": f"Unknown task_type {task_type}"}), 400

    return jsonify(result)


# @app.route("/patients/<patient_id>/image")
# def get_patient_image(patient_id):
    
#     # query the images table for this patient
#     response = supabase_client.table("images").select("image_url").eq("patient_id", patient_id).execute()
    
#     if response.data and len(response.data) > 0:
#         image_url = response.data[0]["image_url"]
#         return jsonify({"image_url": image_url})
#     else:
#         return jsonify({"image_url": None})


@app.route("/patients/<patient_id>/dermnet_image", methods=["GET"])
def get_dermnet_image(patient_id):
    try:
        # Fetch only the stored URL
        patient = (
            supabase_client.table("patients")
            .select("condition_image")
            .eq("id", patient_id)
            .single()
            .execute()
        )

        if not patient.data:
            return jsonify({"image_url": None})

        url = patient.data.get("condition_image")
        return jsonify({"image_url": url})

    except Exception as e:
        return jsonify({"image_url": None, "error": str(e)}), 500

    

@app.route("/patients/<patient_id>/profile_picture", methods=["GET"])
def get_profile_picture(patient_id):

    print(f"GET /patients/{patient_id}/profile_picture")
    
    try:
        result = supabase_client.table("profile_pictures") \
            .select("image_url") \
            .eq("patient_id", patient_id) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        if result.data and len(result.data) > 0:
            return jsonify({"image_url": result.data[0]["image_url"]})
        else:
            return jsonify({"image_url": None})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#DB ACCESS PAGE
@app.route("/api/genPatient", methods=["GET"])
def generate_patient():
    ret=generate_new_patient()
    
   # print("generate patient",ret['patient_info'])
    return jsonify(ret)

#DB ACCESS PAGE
@app.route("/api/uploadPatient", methods=["POST"])
def uplaod_patient():
    data = request.get_json() or {}
    #Normalize data type to generate chief complaint and tags in Patient()
    if isinstance(data["chief_concern"],str):
        data["chief_concern"]=(data["chief_concern"]).split(",")
    #print("upload patient",data)
    response_patient = upload_supabase(data)
    
    #print(response_patient['patient_info'])
    return jsonify(response_patient["status"])
    

if __name__ == "__main__":
    # Use PORT from environment (Railway) or default to 5001
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port)