import asyncio
import random
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
from pydantic import BaseModel
import time
from config import supabase_client

load_dotenv()
family_medicine_topics = [
        "General Principles, Including Normal Age-Related Findings and Care of the Well Patient",
        "Immune System",
        "Blood & Lymphoreticular System",
        "Behavioral Health",
        "Nervous System & Special Senses",
        "Skin & Subcutaneous Tissue",
        "Musculoskeletal System",
        "Cardiovascular System",
        "Respiratory System",
        "Gastrointestinal System",
        "Renal & Urinary System",
        "Pregnancy, Childbirth, & the Puerperium",
        "Female Reproductive System & Breast",
        "Male Reproductive System",
        "Endocrine System",
        "Multisystem Processes & Disorders",
        "Biostatistics, Epidemiology/Population Health, & Interpretation of the Medical Literature",
        "Social Sciences - Communication and interpersonal skills",
        "Social Sciences - Medical ethics and jurisprudence",
        "Social Sciences - Systems-based practice and patient safety"
]
class MCQGenerator:
    def __init__(self, topics):
        # Define openai async connection
        
        
        self.topics = topics

    async def generate_one_question(self,i: int):
    
        key = os.getenv("OPENAI_API_KEY")
        client = AsyncOpenAI(api_key=key)

        # Indexing on list of topics
        print(self.topics)
        if len(self.topics) < 10:
            topic = self.topics[0]
        else:
            
            topic = self.topics[i]   
        
        # Structured output defined
        class MCQ(BaseModel):
            question: str
            A: str
            B: str
            C: str
            D: str
            Answer: str

        # Prompt hardcoded for now
        prompt = f"""
        Generate 1 USMLE step 2 multiple-choice clinic (not ER based) diagnosis family medicine question in {topic}.
        The scenario has to be complex. 
        Following is a few example for the question:

        1. A 6-year-old girl is brought to the office by her mother for a well-child examination. The mother is concerned about nighttime bedwetting, reporting that although the patient has been toilet-trained for the past 2 years during the daytime, she has “never had a dry night.” The patient has three siblings who the mother states were all dry through the night by age 5 years. The patient is otherwise healthy and vaccinations are up-to-date. Vital signs are within normal limits and physical examination shows no abnormalities. Fasting fingerstick blood glucose concentration is 62 mg/dL, and urinalysis is within the reference ranges. Which of the following is the most appropriate next step in management?
        A) Desmopressin therapy
        B) Fluid restriction after 2 PM
        C) Renal ultrasonography
        D) Urine culture
        E) Reassurance only
        2. A 37-year-old man comes to the physician because of a 6-week history of epigastric pain. The pain is most severe 1 hour after eating and is relieved by over-the-counter antacids. He has had no fever, nausea, or weight loss. He has hypertension treated with hydrochlorothiazide. He does not smoke and drinks one glass of wine with dinner daily. His pulse is 76/min, and blood pressure is 136/88 mm Hg. There is mild epigastric tenderness without rebound or guarding. The stool is brown, and test for occult blood is negative. His hemoglobin concentration is 13.8 g/dL. Liver function tests show no abnormalities. Which of the following is the most appropriate next step in diagnosis?
        A) Esophageal pH monitoring
        B) Measurement of serum amylase activity
        C) Serum Helicobacter pylori antibody assay
        D) Abdominal ultrasonography
        E) Abdominal CT scan
        3. A 24-year-old man comes to the office because of a 1-week history of fever, sore throat, and diarrhea. The patient says that he was evaluated in an urgent care clinic 3 days ago; results of a rapid streptococcal test and heterophilic antibody test for infectious mononucleosis obtained at that time were negative. Symptomatic treatment for viral respiratory infections was recommended, but the patient did not obtain any from his pharmacy. He has no history of serious illness and takes no medications. The patient reports that he has had oral-receptive and anal-receptive sex with men and that his most recent sexual encounter was 2 weeks ago. He does not use condoms. Today, temperature is 38.5°C (101.3°F), pulse is 60/min, respirations are 16/min, and blood pressure is 124/76 mm Hg. Physical examination shows three oral ulcerations and anterior cervical lymph nodes that are slightly tender to palpation. The remainder of the physical examination shows no abnormalities. Which of the following studies is most likely to establish the diagnosis?
        A) Epstein-Barr virus DNA detection
        B) Epstein-Barr virus specific antibodies
        C) HIV antibody testing
        D) HIV viral load
        E) Throat culture for Neisseria gonorrhoeae
        F) Throat culture for streptococcal pharyngitis
        4. A state-supported academic health and insurance system is contracted across a large state in the western United States to cover the aspects of care for patients of all ages and income levels, including the Medicaid and Medicare populations. The system's goal is to provide the highest quality of care in the most efficient manner to all patients equally and to support the productivity of the population in that state. The organization already has many skilled providers within every specialty, but they also wish to prioritize key areas for proactive improvement. Which of the following strategies is most likely to be effective in achieving this goal?
        A) Eliminate prior authorization requirements and expand drug formularies to include more prescription options
        B) Establish a mobile clinic to bring specialty services directly to underserved areas of the state
        C) Expand insurance access for specialty, advanced imaging, and surgical services
        D) Expand telemedicine services
        E) Increase relative investment in primary care services
        5. A 52-year-old woman comes to the office for a health maintenance examination. She has no history of serious illness and takes no medications. Menopause occurred 1 year ago. She does not exercise. Her diet consists mainly of meat and potatoes with very few vegetables. She drinks one beer daily and four to five large cups of coffee daily. She had smoked one pack of cigarettes daily for 20 years, but quit 10 years ago. She works as a mechanic. She has no family history of cancer, but wishes to know what she can do to reduce her risk for breast cancer. The patient appears well. She is 168 cm (5 ft 6 in) tall and weighs 95 kg (210 lb); BMI is 34 kg/m². Vital signs are within normal limits. Physical examination shows no abnormalities. Which of the following is most likely to reduce this patient's risk for breast cancer?
        A) Abstinence from caffeine
        B) Alcohol cessation
        C) Exercising and reducing her caloric intake
        D) Increasing her intake of soy
        E) Raloxifene therapy


        Don't pay attention to the sample question topic, BUT pay attention to
        - how the questions gives enough information and evidence for a human doctor to came up with conclusion 
        - the varieties in how scenarios are constructed
        - that you are encouraged to give cases of young or pediatrics patients 45% of the time. The rest will be old age.
        - the complexity of the scenarios
        - all of the ways the question is asking(diagnosis, next steps, cause of something ...), and that all of them are clinic and not ER
        - the difficulty, depth of the problem in general


        For response format:
        Include 4 options labeled A/B/C/D and the correct answer as 'Answer'.
        Using only abbreviations for medical terms in the answer choices WHEN APPROPRIATE ONLY. (e.g., use 'CKD', not 'Chronic Kidney Disease'). 
        Be medically accurate.
        """
        
        try:
            response = await client.responses.parse(
                model="gpt-4o-mini",
                input=[
                    {"role": "system", "content": "You are an expert in creating USMLE question. You should answer in the given structure"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_output_tokens=800,
                text_format=MCQ
            )
            
            question = response.output_parsed
            
            return question
        except Exception as e:
            return f"Error generating question {i}: {e}"
        
    async def generate_questions(self):

        start = time.perf_counter()
        tasks = []

        # Generate 10 questions parallel
        import random

        numbers = random.sample(range(20), 9)
        for i in numbers:
            tasks.append(self.generate_one_question(i))
        results = await asyncio.gather(*tasks)
        print(results)
        end = time.perf_counter()    
        print(f"All finished in {end - start:.2f} seconds")  
        l = []
        for q in results:
            l.append({
            "question": q.question,
            "A": q.A,
            "B": q.B,
            "C": q.C,
            "D": q.D,
            "Answer": q.Answer,
        })
        return l



        pass