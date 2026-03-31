# goal: generate realistic patients for family medicine medical students to practice treating

# need: 
# - Name : text
# - Date of Birth : text
# - Gender : text
# - Medical Condition : text
# - Medical History : text
# - Family Medical History : text
# - Surgical History : text
# - Cholesterol : text
# - Allergies : text
# - PDMP (Prescription Drug Monitoring Program): json : ex. [ { "date_filled": "1 month ago", "date_written": "1 month ago", "days": 30, "drug": "Metformin 500 mg", "qty": 60,"refill": 0 } ]
# - Immunization : json : ex. { "Influenza": "2023-11-01" }
# - Height : text : ex. 5'9
# - Weight : text : ex. 140 lbs
# - Last BP: text : ex. 120/76 mmHg
# - Chief Concern: json : ex. { "chief_complaint": ["Low Back Pain"], "chief_complaint_tags" : ["Musculoskeletal", "Acute"], "context": ["Cancer", "Stroke"]}

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from config import NHANES_PATH, PATIENT_MESSAGE_PROMPT, openai_client

nhanes = pd.read_csv(NHANES_PATH, low_memory=False)


class Patient:
    def __init__(self, row=None,data=None):

        #Allows for initialize from dictionary
        if data:
            #CHECK DATA TYPES
             # will use random row and pull what we can
            self.row = row
            # unique patient identifier
            self.seqn = row.get("SEQN")
            # unique patient age
            self.age = data["age"]
            # height and weight
            self.raw_height_cm = row.get("BMXHT")
            self.raw_weight_kg = row.get("BMXWT")
            # current year
            self.current_year = datetime.now().year
            # patient information - fields we need for database
            
            self.gender = data['gender']
            self.name = data['name']
            self.dob = data['dob']
            self.height = data['height']
            self.weight = data['weight']
            #CHECK THIS
            self.medical_condition = data["chief_concern"]
            self.last_bp = data['last_bp']
            self.cholesterol = self.generate_cholesterol()
            self.family_medical_history = data['family_medical_history']
            # dictionary with chief complaint and tags
            #self.chief_concern = data['chief_concern']
            if isinstance(data['medical_history'],str):
                self.medical_history = data['medical_history'].split(",")
            else:
                self.medical_history = data['medical_history']
            self.surgical_history = self.generate_surgical_history()
            self.allergies = self.generate_allergies()
            self.pdmp = self.generate_pdmp()
            self.immunization = self.generate_immunization_record()
            # Generae chief concern from the data passed and generate tags  
            self.chief_concern = data["chief_concern"]
            self.attach_chief_concern_tags()
            self.patient_message = self.generate_patient_message()
            
            
            self.last_visit = self.generate_last_visit()

        else:

            # will use random row and pull what we can
            self.row = row
            # unique patient identifier
            self.seqn = row.get("SEQN")
            # unique patient age
            self.age = self.row.get("RIDAGEYR", 0)
            # height and weight
            self.raw_height_cm = row.get("BMXHT")
            self.raw_weight_kg = row.get("BMXWT")
            # current year
            self.current_year = datetime.now().year
            
            # patient information - fields we need for database
            self.gender = self.generate_gender()
            self.name = self.generate_name()
            self.dob = self.generate_dob()
            self.height = self.generate_height()
            self.weight = self.generate_weight()
            self.medical_condition = self.generate_medical_condition()
            self.last_bp = self.generate_bp()
            self.cholesterol = self.generate_cholesterol()
            self.family_medical_history = self.generate_family_medical_history()
            # dictionary with chief complaint and tags
            self.chief_concern = self.generate_chief_concern()
            self.medical_history = self.generate_medical_history()
            self.surgical_history = self.generate_surgical_history()
            self.allergies = self.generate_allergies()
            self.pdmp = self.generate_pdmp()
            self.immunization = self.generate_immunization_record()
            self.patient_message = self.generate_patient_message()
            
            self.last_visit = self.generate_last_visit()


    def generate_gender(self):
        """ 
        returns a string containing a gender from the RIAGENDR column 
        in the NHANES dataset.
        
        the value 1 corresponds to male, and the value 2 corresponds
        to female. if niether of those values are present, the function 
        randomly picks one.
        """

        code = self.row.get("RIAGENDR")
        if code == 1:
            return "Male"
        elif code == 2:
            return "Female"
        return random.choice(["Male", "Female"])

    def generate_name(self):
        """
        returns a random first and last name.

        the first and last name come from a pool of generic names
        and use the determined gender to pick.        
        
        """

        male_first_names = [
            "James", "John", "Robert", "Michael", "William",
            "David", "Richard", "Joseph", "Thomas", "Charles",
            "Daniel", "Matthew", "Anthony", "Mark", "Donald",
            "Steven", "Paul", "Andrew", "Joshua", "Kenneth",
            "Kevin", "Brian", "George", "Edward", "Ronald",
            "Timothy", "Jason", "Jeffrey", "Ryan", "Jacob",
            "Gary", "Nicholas", "Eric", "Stephen", "Jonathan",
            "Larry", "Justin", "Scott", "Brandon", "Benjamin",
            "Samuel", "Gregory", "Frank", "Alexander", "Raymond",
            "Patrick", "Jack", "Dennis", "Jerry", "Tyler"
        ]

        female_first_names = [
            "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth",
            "Barbara", "Susan", "Jessica", "Sarah", "Karen",
            "Nancy", "Lisa", "Betty", "Margaret", "Sandra",
            "Ashley", "Kimberly", "Emily", "Donna", "Michelle",
            "Dorothy", "Carol", "Amanda", "Melissa", "Deborah",
            "Stephanie", "Rebecca", "Laura", "Sharon", "Cynthia",
            "Kathleen", "Helen", "Amy", "Shirley", "Angela",
            "Anna", "Brenda", "Pamela", "Nicole", "Samantha",
            "Katherine", "Emma", "Ruth", "Christine", "Catherine",
            "Debra", "Rachel", "Carolyn", "Janet", "Virginia"
        ]

        last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones",
            "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
            "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
            "Thomas", "Taylor", "Moore", "Jackson", "Martin",
            "Lee", "Perez", "Thompson", "White", "Harris",
            "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
            "Walker", "Young", "Allen", "King", "Wright",
            "Scott", "Torres", "Nguyen", "Hill", "Flores",
            "Green", "Adams", "Nelson", "Baker", "Hall",
            "Rivera", "Campbell", "Mitchell", "Carter", "Roberts"
        ]

        if self.gender == "Male":
            first = random.choice(male_first_names)
        else:
            first = random.choice(female_first_names)

        last = random.choice(last_names)
        return f"{first} {last}"



    def generate_dob(self):
        """
        returns a date of birth based on the NHANES datasets RIDAGEYR row, 
        which corresponds to age.

        the function uses the age and a offset value to randomize the exact day
        to calculate the date of birth.
        
        """

        # this condition should always be true but just in case:
        if pd.notna(self.age) and self.age >= 0:
            today = datetime.today()
            days_offset = random.randint(0, 364)
            dob = today - timedelta(days=(self.age * 365 + days_offset))
            return dob.strftime("%Y-%m-%d")
        return None


    def calculate_bmi(self):
        """
        returns the patients bmi based on raw data from NHANES.
        """

        height_str = self.height
        weight_str = self.weight
        
        try:
            # parse height
            feet, inches = height_str.split("'")
            inches = inches.replace('"', '')
            height_in = int(feet) * 12 + int(inches)
            
            # parse weight 
            weight_lbs = int(weight_str.split()[0])
            
            # bmi = (weight_lbs / (height_in ^ 2)) * 703
            bmi = (weight_lbs / (height_in ** 2)) * 703
            return round(bmi, 1)
        
        except:

            return None


    def generate_height(self):
        """
        returns height, first attempting to pull from NHANES
        dataset, then falls back on synthetic realistic generation
        """

        height_cm = self.raw_height_cm

        if pd.isna(height_cm) or height_cm <= 0:
            if self.age < 2:
                height_cm = np.random.normal(85, 5)    # 80–90 cm typical toddlers
            elif self.age < 5:
                height_cm = np.random.normal(105, 7)   # preschool age
            elif self.age < 12:
                height_cm = np.random.normal(135, 10)  # elementary age
            elif self.age < 18:
                if self.gender == "Male":
                    height_cm = np.random.normal(165, 8)  # teen boys
                else:
                    height_cm = np.random.normal(158, 7)  # teen girls
            else:
                if self.gender == "Male":
                    height_cm = np.random.normal(175, 7)
                else:
                    height_cm = np.random.normal(162, 6)

        # Convert cm to feet and inches
        total_inches = height_cm / 2.54
        feet = int(total_inches // 12)
        inches = int(round(total_inches % 12))

        if inches == 12:
            feet += 1
            inches = 0

        return f"{feet}'{inches}\""

    def generate_weight(self):
        """
        returns weight, first attempting to pull from NHANES
        dataset, then falls back on synthetic realistic generation
        """

        weight_kg = self.raw_weight_kg

        # Generate synthetic weight if missing or implausible
        if pd.isna(weight_kg) or weight_kg <= 0:
            if self.age < 2:
                weight_kg = np.random.normal(12, 2)     # toddlers ~10–14 kg
            elif self.age < 5:
                weight_kg = np.random.normal(18, 3)     # preschoolers ~15–21 kg
            elif self.age < 12:
                weight_kg = np.random.normal(35, 8)     # children ~25–45 kg
            elif self.age < 18:
                if self.gender == "Male":
                    weight_kg = np.random.normal(60, 10)   # teen boys
                else:
                    weight_kg = np.random.normal(52, 9)    # teen girls
            else:
                if self.gender == "Male":
                    weight_kg = np.random.normal(85, 12)   # adult men
                else:
                    weight_kg = np.random.normal(72, 10)   # adult women



        weight_lbs = int(round(weight_kg * 2.20462))
        return f"{weight_lbs} lbs"


    def generate_last_visit(self):

        today = datetime.today()
        dob = datetime.strptime(self.dob, "%Y-%m-%d")

        # age in days
        age_days = (today - dob).days

        if self.age < 2:
            # infants/toddlers – frequent checkups, within last 3–6 months
            max_offset = random.randint(90, 180)
        elif self.age < 12:
            # children – annual or biannual visits
            max_offset = random.randint(180, 365)
        elif self.age < 18:
            # teens – may have longer gaps (6–18 months)
            max_offset = random.randint(180, 540)
        elif self.age < 65:
            # adults – 1–2 years typical
            max_offset = random.randint(180, 730)
        else:
            # older adults – likely seen within the past year
            max_offset = random.randint(90, 365)

        # ensure offset doesn't exceed their age span
        offset_days = min(max_offset, age_days - 1) if age_days > 1 else 0

        last_visit_date = today - timedelta(days=offset_days)
        
        return last_visit_date.strftime("%Y-%m-%d")


    def generate_bp(self):
        """
        returns blood pressure, first attempting to pull value from NHANES,
        generating a synthetic value if one doesn't exist
        """

        # systolic
        bp_sys = None
        # diastolic
        bp_dia = None

        # read from the NHANES BP data
        if "BPXOSY1" in self.row and pd.notnull(self.row["BPXOSY1"]):
            bp_sys = int(self.row["BPXOSY1"])
        elif "BPXOSY2" in self.row and pd.notnull(self.row["BPXOSY2"]):
            bp_sys = int(self.row["BPXOSY2"])
        elif "BPXOSY3" in self.row and pd.notnull(self.row["BPXOSY3"]):
            bp_sys = int(self.row["BPXOSY3"])

        if "BPXODI1" in self.row and pd.notnull(self.row["BPXODI1"]):
            bp_dia = int(self.row["BPXODI1"])
        elif "BPXODI2" in self.row and pd.notnull(self.row["BPXODI2"]):
            bp_dia = int(self.row["BPXODI2"])
        elif "BPXODI3" in self.row and pd.notnull(self.row["BPXODI3"]):
            bp_dia = int(self.row["BPXODI3"])


        # synthesize blood pressure
        if bp_sys is None or bp_dia is None:

            age = self.age
            
            # increase with age
            base_sys = 110 + (age - 30) * 0.7
            base_dia = 70 + (age - 30) * 0.3
            
            # adjust with conditions
            if "Hypertension" in self.medical_condition:
                base_sys += 15
                base_dia += 8
            if "Diabetes" in self.medical_condition:
                base_sys += 10
                base_dia += 5
            
            if pd.isna(bp_sys):
                # use bell curve around base_sys, standard deviation of 12
                bp_sys = int(np.random.normal(base_sys, 12))
            
            if pd.isna(bp_dia):
                bp_dia = int(np.random.normal(base_dia, 8))

        return f"{bp_sys}/{bp_dia} mmHg"



    def generate_medical_condition(self):
        """
        returns a list of medical conditions

        first tallies any conditions that are marked from NHANES dataset,
        then falls back on probabilistic age and gender related medical conditions.
        """

        # list to track medical conditions
        conditions = []

        # conditions based on NHANES data
        condition_mapping = {
            "MCQ010": "Asthma",
            "AGQ030": "Hay Fever",
            "MCQ053": "Anemia (on treatment)",
            "MCQ160a": "Arthritis",
            "MCQ160b": "Congestive Heart Failure",
            "MCQ160c": "Coronary Heart Disease",
            "MCQ160d": "Angina",
            "MCQ160e": "Heart Attack",
            "MCQ160f": "Stroke",
            "MCQ160m": "Thyroid Disorder",
            "MCQ160l": "Liver Condition",
            "MCQ500": "Liver Condition",
            "MCQ510a": "Fatty Liver",
            "MCQ510b": "Liver Fibrosis",
            "MCQ510c": "Liver Cirrhosis",
            "MCQ510d": "Viral Hepatitis",
            "MCQ510e": "Autoimmune Hepatitis",
            "MCQ510f": "Other Liver Disease",
            "MCQ550": "Gallstones",
            "MCQ220": "Cancer",
            "BAQ391B": "Migraines",
        }

        # if any of the conditions are marked true, add them to the
        # list of conditions
        for questions, condition_name in condition_mapping.items():
            value = self.row.get(questions)
            if pd.notna(value) and value == 1:
                conditions.append(condition_name)

        # depression screening
        depression_score = 0
        depression_questions = ["DPQ010", "DPQ020", "DPQ030", "DPQ040", "DPQ050", 
                          "DPQ060", "DPQ070", "DPQ080", "DPQ090"]
        
        for questions in depression_questions:
            score = self.row.get(questions)
            if pd.notna(score):
                depression_score += score

        if depression_score >= 20:
            conditions.append("Severe Depression")
        elif depression_score >= 10:
            conditions.append("Moderate Depression")

        # hypertension and hyperlipidemia
        if self.row.get("BPQ020") == 1 or self.row.get("BPQ030") == 1:
            conditions.append("Hypertension")
        if self.row.get("BPQ080") == 1:
            conditions.append("Hyperlipidemia")

        # diabetes and prediabetes
        if self.row.get("DIQ010") == 1:
            conditions.append("Diabetes")
        elif self.row.get("DIQ160") == 1:
            conditions.append("Prediabetes")

        # use BMI for obesity
        bmi = self.calculate_bmi()
        if bmi is not None and bmi >= 30:
            conditions.append("Obesity")


        # synthetic generation!

        conditions = self.add_chronic_conditions(conditions)

        conditions = self.add_acute_conditions(conditions)

        return conditions if conditions else ["No significant medical conditions"]

    
    def add_acute_conditions(self, conditions):

        # probabilities for age groups
        if self.age < 12:
            prob = 0.4
        elif self.age < 20:
            prob = 0.35
        elif self.age < 40:
            prob = 0.25
        elif self.age < 65:
            prob = 0.20
        else:
            prob = 0.30
        
        # no condition
        if random.random() > prob:
            return conditions
        
        # build age-appropriate acute condition pool
        acute_pool = []
        
        if self.age < 12:  # pediatric

            acute_pool = [
                # infections
                "Viral Upper Respiratory Infection",
                "Acute Otitis Media",
                "Pharyngitis",
                "Conjunctivitis",
                "Hand, Foot, and Mouth Disease",
                "Impetigo",
                "Viral Gastroenteritis",
                
                # skin conditions
                "Eczema Flare",
                "Contact Dermatitis",
                "Insect Bite Reaction",
                "Urticaria (Hives)",
                
                # minor injuries
                "Minor Laceration",
                "Abrasion",
                "Contusion",
            ]

            if self.age >= 5 and self.gender == "Female":
                acute_pool.append("Urinary Tract Infection")
            
        elif self.age < 20:  # adolescent
            acute_pool = [

                # infections
                "Upper Respiratory Infection",
                "Strep Pharyngitis",
                "Mononucleosis",
                "Sinusitis",
                "Conjunctivitis",
                
                # skin
                "Acne Vulgaris Flare",
                "Contact Dermatitis",
                "Folliculitis",
                "Tinea Corporis (Ringworm)",
                "Cellulitis",
                "Urticaria (Hives)",
                
                # injuries
                "Ankle Sprain",
                "Minor Laceration",
                "Sports-Related Contusion",
                "Jammed Finger",
            ]

            if self.gender == "Female":
                acute_pool.append("Urinary Tract Infection")
                acute_pool.append("Vaginal Yeast Infection")
            
        elif self.age < 65:  # adult

            acute_pool = [

                # infections
                "Upper Respiratory Infection",
                "Acute Sinusitis",
                "Bronchitis",
                "Urinary Tract Infection",
                "Bacterial Pharyngitis",
                "Conjunctivitis",
                "Acute Otitis Externa (Swimmer's Ear)",
                "Cellulitis",
                "Abscess",
                
                # skin conditions
                "Contact Dermatitis",
                "Seborrheic Dermatitis",
                "Urticaria (Hives)",
                "Shingles (Herpes Zoster)",
                "Acute Eczema Flare",
                "Folliculitis",
                "Fungal Infection (Tinea)",
                "Insect Bite Reaction",
                
                # GI
                "Acute Gastroenteritis",
                "Food Poisoning",
                
                # musculoskeletal
                "Low Back Strain",
                "Neck Strain",
                "Ankle Sprain",
                "Minor Laceration",
                "Contusion",
            ]

            if self.gender == "Female":
                acute_pool.append("Urinary Tract Infection")
                acute_pool.append("Vaginal Yeast Infection")
                acute_pool.append("Bacterial Vaginosis")
            elif self.gender == "Male":
                if random.random() < 0.3: 
                    acute_pool.append("Urinary Tract Infection")
            
        else:  # elderly (65+)

            acute_pool = [
                # infections (more serious in elderly)
                "Upper Respiratory Infection",
                "Bronchitis",
                "Pneumonia",
                "Urinary Tract Infection",
                "Cellulitis",
                "Shingles (Herpes Zoster)",
                
                # skin
                "Stasis Dermatitis",
                "Contact Dermatitis",
                "Seborrheic Dermatitis",
                "Pressure Ulcer",
                "Skin Tear",
                
                # other
                "Acute Gout Flare",
                "Acute Diverticulitis",
                "Fall with Contusion",
            ]
        
        # Select 1 acute condition
        selected = random.choice(acute_pool)
        conditions.append(selected)
        
        return conditions
        


    def add_chronic_conditions(self, conditions):


        if len(conditions) > 0:
            return conditions

        if self.age < 12:  # pediatric

            condition_probs = {
                "Asthma": (0.12, {"Male": 1.3, "Female": 0.8}),  # more common in boys
                "Eczema": (0.15, {"Male": 1.0, "Female": 1.0}),
                "Allergic Rhinitis": (0.10, {"Male": 1.0, "Female": 1.0}),
                "Recurrent Ear Infections": (0.08, {"Male": 1.0, "Female": 1.0}),
                "ADHD": (0.09, {"Male": 2.5, "Female": 0.4}),  # much more common in boys
                "Speech Delay": (0.05, {"Male": 1.5, "Female": 0.7}),
                "Constipation": (0.06, {"Male": 1.0, "Female": 1.0}),
                "Food Allergies": (0.08, {"Male": 1.0, "Female": 1.0}),
            }

        elif self.age < 20:  # adolescent

            condition_probs = {
                "Asthma": (0.10, {"Male": 1.0, "Female": 1.2}),  # shifts to more common in girls
                "Acne": (0.25, {"Male": 1.0, "Female": 1.0}),
                "Anxiety": (0.12, {"Male": 0.6, "Female": 1.6}),  # more common in girls
                "Depression": (0.08, {"Male": 0.5, "Female": 1.8}),  # much more common in girls
                "ADHD": (0.08, {"Male": 2.0, "Female": 0.5}),
                "Social Anxiety": (0.06, {"Male": 0.7, "Female": 1.4}),
                "Menstrual Irregularities": (0.15, {"Male": 0.0, "Female": 1.0}),  # female only
                "Migraine": (0.05, {"Male": 0.5, "Female": 2.0}),
                "IBS": (0.04, {"Male": 0.6, "Female": 1.6}),
            }

        elif self.age < 40:  # young adult

            condition_probs = {
                "Seasonal Allergies": (0.18, {"Male": 1.0, "Female": 1.0}),
                "GERD": (0.08, {"Male": 1.0, "Female": 1.0}),
                "Anxiety": (0.15, {"Male": 0.7, "Female": 1.5}),
                "Depression": (0.12, {"Male": 0.6, "Female": 1.7}),
                "Asthma": (0.09, {"Male": 0.8, "Female": 1.2}),
                "Migraine": (0.10, {"Male": 0.4, "Female": 2.5}),  # 3x more common in women
                "IBS": (0.08, {"Male": 0.5, "Female": 2.0}),
                "Hypothyroidism": (0.06, {"Male": 0.2, "Female": 5.0}),  # much more common in women
                "Low Back Pain": (0.12, {"Male": 1.0, "Female": 1.0}),
                "Insomnia": (0.08, {"Male": 0.8, "Female": 1.3}),
            }

        elif self.age < 65:  # middle age adult

            condition_probs = {
                "Hypertension": (0.30, {"Male": 1.2, "Female": 0.9}),  # more common in men
                "Hyperlipidemia": (0.25, {"Male": 1.3, "Female": 0.8}),
                "Type 2 Diabetes": (0.12, {"Male": 1.3, "Female": 0.8}),
                "Prediabetes": (0.15, {"Male": 1.2, "Female": 0.9}),
                "Obesity": (0.35, {"Male": 1.0, "Female": 1.1}),
                "GERD": (0.15, {"Male": 1.0, "Female": 1.0}),
                "Osteoarthritis": (0.12, {"Male": 0.7, "Female": 1.5}),  # more common in women
                "Low Back Pain": (0.20, {"Male": 1.0, "Female": 1.0}),
                "Anxiety": (0.15, {"Male": 0.6, "Female": 1.6}),
                "Depression": (0.12, {"Male": 0.6, "Female": 1.7}),
                "Migraine": (0.12, {"Male": 0.4, "Female": 2.5}),
                "IBS": (0.10, {"Male": 0.5, "Female": 2.0}),
                "Insomnia": (0.15, {"Male": 0.8, "Female": 1.3}),
                "Hypothyroidism": (0.10, {"Male": 0.2, "Female": 5.0}),
                "Sleep Apnea": (0.08, {"Male": 2.0, "Female": 0.5}),  # more common in men
                "Chronic Fatigue": (0.06, {"Male": 0.5, "Female": 2.0}),
                "Seasonal Allergies": (0.15, {"Male": 1.0, "Female": 1.0}),
            }

        else:  # elderly (65+)

            condition_probs = {
                "Hypertension": (0.60, {"Male": 1.0, "Female": 1.1}),  # very common
                "Hyperlipidemia": (0.45, {"Male": 1.2, "Female": 0.9}),
                "Type 2 Diabetes": (0.25, {"Male": 1.2, "Female": 0.9}),
                "Osteoarthritis": (0.40, {"Male": 0.7, "Female": 1.4}),
                "Chronic Low Back Pain": (0.30, {"Male": 1.0, "Female": 1.0}),
                "Osteoporosis": (0.20, {"Male": 0.2, "Female": 4.0}),  # much more common in women
                "GERD": (0.20, {"Male": 1.0, "Female": 1.0}),
                "Cataracts": (0.25, {"Male": 1.0, "Female": 1.0}),
                "Hearing Loss": (0.35, {"Male": 1.5, "Female": 0.7}),  # more common in men
                "Chronic Kidney Disease": (0.15, {"Male": 1.3, "Female": 0.8}),
                "Heart Failure": (0.08, {"Male": 1.3, "Female": 0.8}),
                "Atrial Fibrillation": (0.10, {"Male": 1.2, "Female": 0.9}),
                "COPD": (0.12, {"Male": 1.0, "Female": 1.0}),
                "Depression": (0.10, {"Male": 0.6, "Female": 1.7}),
                "Insomnia": (0.20, {"Male": 0.8, "Female": 1.3}),
                "Urinary Incontinence": (0.25, {"Male": 0.4, "Female": 2.5}),  # more common in women
                "Benign Prostatic Hyperplasia": (0.50, {"Male": 1.0, "Female": 0.0}),  # male only
                "Cognitive Impairment": (0.12, {"Male": 1.0, "Female": 1.2}),
                "Macular Degeneration": (0.08, {"Male": 0.8, "Female": 1.3}),
                "Peripheral Neuropathy": (0.10, {"Male": 1.0, "Female": 1.0}),
                "Glaucoma": (0.08, {"Male": 1.0, "Female": 1.0}),
            }


        # generate conditions based on probabilities
        for condition, (base_prob, gender_modifiers) in condition_probs.items():

            # apply gender modifier
            gender_modifier = gender_modifiers.get(self.gender, 1.0)
            adjusted_prob = base_prob * gender_modifier
            
            # roll the dice
            if random.random() < adjusted_prob:
                conditions.append(condition)
        
        # limit chronic conditions for realism
        if self.age < 65 and len(conditions) > 3:
            conditions = random.sample(conditions, 3)
        elif self.age >= 65 and len(conditions) > 5:
            conditions = random.sample(conditions, 5)
        
        return conditions



    def generate_medical_history(self):
        """
        generates medical history based on a few factors:
        - conditions that typically precede chief complaint
        - age appropriate conditions that don't relate to the chief complaint
        - resolved conditions from childhood
        """

        # formulate the medical history around the chief complaint
        current_condition = self.chief_complaint
        history = []

        # add all other medical conditions except the chief complaint
        for condition in self.medical_condition:
            if condition != self.chief_complaint and condition != "No significant medical conditions":
                history.append(condition)

        # conditions and potential preconditions that lead to
        # them, with probabilities
        condition_pathways = {
            "Hypertension": [
                ("Prediabetes", 0.4),
                ("Hyperlipidemia", 0.6),
                ("Obesity", 0.5),
                ("Anxiety", 0.3)
            ],
            "Diabetes": [
                ("Prediabetes", 0.8),
                ("Hypertension", 0.7),
                ("Hyperlipidemia", 0.6),
                ("Obesity", 0.7)
            ],
            "Asthma": [
                ("Asthma", 0.9),
                ("Allergic Rhinitis", 0.6),
                ("Eczema", 0.4)
            ],
            "Depression": [
                ("Anxiety", 0.6),
                ("Chronic Pain", 0.4),
                ("Insomnia", 0.5)
            ],
            "Anxiety": [
                ("Depression", 0.5),
                ("Insomnia", 0.4),
                ("GERD", 0.3)
            ],
            "Low Back Pain": [
                ("Obesity", 0.5),
                ("Arthritis", 0.6),
                ("Previous Back Strain", 0.4)
            ],
            "Arthritis": [
                ("Previous Joint Injury", 0.4),
                ("Obesity", 0.5),
                ("Hypertension", 0.3)
            ],
            "Ear Infection": [
                ("Allergic Rhinitis", 0.5),
                ("Family History of Ear Infections", 0.3)
            ],
            "General Visit": [
                ("Hypertension", 0.3 if self.age > 40 else 0.1),
                ("Hyperlipidemia", 0.25 if self.age > 40 else 0.05),
                ("Arthritis", 0.2 if self.age > 50 else 0.05),
                ("Anxiety", 0.15),
                ("GERD", 0.1 if self.age > 30 else 0.02)
            ]
        }

        # add conditions that typically precede the chief complaint
        if current_condition in condition_pathways:
            for past_condition, probability in condition_pathways[current_condition]:

                # adjust probability based on age relevance
                adjusted_prob = probability
                
                if self.age < 30 and past_condition in ["Hypertension", "Hyperlipidemia", "Arthritis"]:
                    adjusted_prob *= 0.2
            
                elif self.age > 60 and past_condition in ["Hypertension", "Arthritis"]:
                    adjusted_prob *= 1.3
                
                if random.random() < adjusted_prob:
                    history.append(past_condition)
        
        # add age-appropriate common conditions that aren't the chief complaint
        age_based_conditions = []
        
        if self.age >= 60:
            age_based_conditions.extend([
                ("Hypertension", 0.5),
                ("Osteoarthritis", 0.5),
                ("Cataracts", 0.5),
                ("GERD", 0.5)
            ])
        elif self.age >= 40:
            age_based_conditions.extend([
                ("Hypertension", 0.5),
                ("Hyperlipidemia", 0.5),
                ("GERD", 0.5),
                ("Allergic Rhinitis", 0.5)
            ])
        elif self.age >= 20:
            age_based_conditions.extend([
                ("Seasonal Allergies", 0.3),
                ("Migraines", 0.3),
                ("GERD", 0.15)
            ])
        else:
            age_based_conditions.extend([
                ("Allergic Rhinitis", 0.2),
                ("Eczema", 0.15),
                ("Previous Fracture", 0.1)
            ])

        # add them to the history        
        for condition, probability in age_based_conditions:
            if condition not in history and condition != current_condition:
                if random.random() < probability:
                    history.append(condition)
        
        # add resolved childhood conditions for adults
        if self.age > 18 and random.random() < 0.4:
            childhood_conditions = [
                "Asthma",
                "Tonsillitis", 
                "Appendicitis"
            ]
            history.append(random.choice(childhood_conditions))
        
        history = list(set(history))
        return history if history else ["No significant past medical history"]



    def generate_cholesterol(self):
        """
        returns a cholesterol measure. 
        first attempts to pull NHANES cholesterol value, if not available, generates
        a synthetic value based on age and medical condition
        """

        cholesterol = self.row.get("LBXTC")  # total cholesterol

        # synthetic generation
        if pd.isna(cholesterol):
            # kids
            if self.age <= 8:
                return "None"
            elif  9 <= self.age <= 18:
                cholesterol = np.random.normal(155, 15)   
            else:
                # adults
                base_cholesterol = 180 + (self.age - 30) * 0.8
                
                # conditions that increase cholesterol
                if "Diabetes" in self.medical_condition:
                    base_cholesterol += 20
                if "Hypertension" in self.medical_condition:
                    base_cholesterol += 15
                if "Hyperlipidemia" in self.medical_condition:
                    base_cholesterol += 40

                cholesterol = np.random.normal(base_cholesterol, 25)

        return f"{round(cholesterol, 0)} mg/dL"


    # synthetic family history
    def generate_family_medical_history(self):
        """
        returns a family medical history record, 
        generated using static probabilities.
        """
        
        family_conditions = []

        # conditions and corresponding probabilities
        common_family_history = {
            "Hypertension": 0.4,
            "Diabetes": 0.35,
            "Heart Disease": 0.3,
            "Stroke": 0.25,
            "Cancer": 0.2,
            "Asthma": 0.15,
            "Depression": 0.1
        }

        # use the prevalance probability to assign conditions to family members
        for condition, prevalence in common_family_history.items():
            if random.random() < prevalence:
                relative = random.choice(["Mother", "Father", "Grandparent", "Sibling"])
                family_conditions.append(f"{relative}: {condition}")

        return family_conditions if family_conditions else ["No significant family history"]



    def generate_surgical_history(self):
        """
        returns a surgical history record based on:
        - age
        - gender
        - medical conditions
        """

        surgeries = []
        current_year = datetime.now().year
        birth_year = int(self.dob.split('-')[0])

        # pediatric surgeries
        if self.age < 18:
            if random.random() < 0.15:  # 15% of kids have had surgery
                pediatric_surgeries = [
                    "Tonsillectomy",
                    "Adenoidectomy", 
                    "Ear tube placement",
                    "Appendectomy",
                    "Fracture repair"
                ]
                
                if self.age >= 2:
                    surgery_age = random.randint(2, self.age)
                else:
                    surgery_age = self.age

                surgery_year = birth_year + surgery_age
                surgeries.append(f"{random.choice(pediatric_surgeries)} ({surgery_year})")


        # obstetric history for females
        if self.gender == "Female" and self.age >= 18:
            # c-section probability increases with age
            if self.age >= 20 and random.random() < min(0.15 + (self.age - 20) * 0.01, 0.4):
                c_section_age = random.randint(20, min(self.age, 45))
                c_section_year = birth_year + c_section_age
                surgeries.append(f"Cesarean section ({c_section_year})")
            
            # hysterectomy - more common after 40
            if self.age >= 40 and random.random() < min(0.1 + (self.age - 40) * 0.02, 0.5):
                hysterectomy_age = random.randint(40, int(self.age))
                hysterectomy_year = birth_year + hysterectomy_age
                surgeries.append(f"Hysterectomy ({hysterectomy_year})")

        # other age-related surgeries
        if self.age >= 50 and random.random() < 0.3:
            surgeries.append(f"Cataract surgery ({current_year - random.randint(1, 8)})")
        
        if self.age >= 50 and random.random() < 0.4:
            surgeries.append(f"Colonoscopy ({current_year - random.randint(1, 10)})")
        
        # joint replacements - common with arthritis/age
        if ("Arthritis" in self.medical_condition or self.age >= 65) and random.random() < 0.25:
            joints = ["Knee", "Hip", "Shoulder"]
            surgery_year = current_year - random.randint(1, 15)
            surgeries.append(f"{random.choice(joints)} replacement ({surgery_year})")

        # condition-specific surgeries
        if "Diabetes" in self.medical_condition and self.age >= 40 and random.random() < 0.15:
            surgeries.append(f"Diabetic foot procedure ({current_year - random.randint(1, 5)})")
        
        if "Gallstones" in self.medical_condition and random.random() < 0.6:
            surgeries.append(f"Cholecystectomy ({current_year - random.randint(1, 10)})")

        return surgeries if surgeries else ["No surgical history"]




    def generate_allergies(self):
        """
        returns a list of allergies, generated based on age,
        medical condition, and general likelihood
        """

        allergies = []
        
        # allergies that are somewhat common in adults and children
        if self.age < 50 and random.random() < 0.3: # 30% chance
            allergies.extend(random.sample(["Pollen", "Dust mites", "Pet dander"], 
                                         random.randint(1, 2)))
        
        # food allergies
        if random.random() < 0.1:  # 10% chance
            food_allergies = ["Shellfish", "Peanuts", "Tree nuts", "Dairy", "Eggs"]
            allergies.append(random.choice(food_allergies))
        
        # drug allergies more common with age and medical conditions
        if self.age > 40 and len(self.medical_condition) > 1:
            if random.random() < 0.2:  # 20% chance
                allergies.append(random.choice(["Penicillin", "Sulfa drugs", "Codeine"]))
        
        return allergies if allergies else ["No known allergies"]



    def get_medication_info(self, med_name, days):
        """
        Returns realistic dose per day and refills for a given medication.
        """

        # Approximate units per day for common meds
        dose_per_day_table = {
            # Cardiovascular
            "Lisinopril": 1, "Losartan": 1, "Amlodipine": 1, "Hydrochlorothiazide": 1,
            "Atorvastatin": 1, "Rosuvastatin": 1, "Metoprolol": 1, "Furosemide": 1,

            # Endocrine / metabolic
            "Metformin": 1, "Insulin Glargine": 1, "Insulin Lispro": 1, "Levothyroxine": 1, "Orlistat": 1,

            # Respiratory / allergy
            "Albuterol Inhaler": 1, "Fluticasone Inhaler": 1, "Montelukast": 1,
            "Cetirizine": 1, "Hydrocortisone Cream": 1, "Fluticasone Nasal Spray": 1,
            "Amoxicillin": 3, "Azithromycin": 1,

            # Neuro / psych
            "Sertraline": 1, "Escitalopram": 1, "Bupropion": 1, "Venlafaxine": 1,
            "Buspirone": 1, "Duloxetine": 1, "Propranolol": 1,
            "Methylphenidate": 1, "Amphetamine-Dextroamphetamine": 1,
            "Trazodone": 1, "Zolpidem": 1, "Topiramate": 1, "Sumatriptan": 2,
            "Modafinil": 1,

            # Pain / musculoskeletal
            "Ibuprofen": 1, "Celecoxib": 1, "Naproxen": 1, "Gabapentin": 1, "Cyclobenzaprine": 1,
            "Alendronate": 1,

            # GI / hepatic
            "Omeprazole": 1, "Famotidine": 1, "Ursodiol": 1, "Vitamin E": 1, "Dicyclomine": 1,

            # Other
            "Ferrous Sulfate": 1, "Ondansetron": 1, "Multivitamin": 1
        }

        # determine dose per day (default 1 if unknown)
        dose_per_day = dose_per_day_table.get(med_name.split()[0], 1)

        # determine realistic refills
        if med_name in ["Sumatriptan", "Albuterol Inhaler", "Amoxicillin", "Azithromycin", "Dicyclomine"]:
            refills = 0
        else:
            if days == 30:
                refills = random.randint(0, 2)
            elif days == 60:
                refills = random.randint(0, 1)
            else:  # 90 days
                refills = 0

        return dose_per_day, refills
    
    def calculate_quantity(self, dose_per_day, days, med_name):
        """
        Returns the total quantity of units to dispense.
        """
        # for inhalers / bottles, approximate 1 per 30 days
        if med_name in ["Albuterol Inhaler", "Fluticasone Inhaler", "Fluticasone Nasal Spray"]:
            return max(1, days // 30)
        else:
            return dose_per_day * days  # total units for pills, capsules, etc.


    def generate_pdmp(self):
        """
        returns a list of controlled substance perscriptions so that
        clinicians can identify patients who are at risk of misuse.
        """
        
        condition_to_medications = {
            # Cardiovascular
            "Hypertension": ["Lisinopril 10 mg", "Losartan 50 mg", "Amlodipine 5 mg", "Hydrochlorothiazide 25 mg"],
            "Hyperlipidemia": ["Atorvastatin 40 mg", "Rosuvastatin 20 mg"],
            "Coronary Heart Disease": ["Clopidogrel 75 mg", "Aspirin 81 mg", "Metoprolol 50 mg"],
            "Heart Failure": ["Furosemide 20 mg", "Metoprolol 50 mg"],
            "Congestive Heart Failure": ["Furosemide 40 mg", "Lisinopril 10 mg"],

            # Endocrine / metabolic
            "Diabetes": ["Metformin 1000 mg", "Insulin Glargine 10 units"],
            "Prediabetes": ["Metformin 500 mg"],
            "Type 2 Diabetes": ["Metformin 1000 mg", "Insulin Lispro 5 units"],
            "Obesity": ["Orlistat 120 mg"],
            "Thyroid Disorder": ["Levothyroxine 75 mcg"],

            # Respiratory / allergy
            "Asthma": ["Albuterol Inhaler 90 mcg", "Fluticasone Inhaler 110 mcg", "Montelukast 10 mg"],
            "Hay Fever": ["Cetirizine 10 mg"],
            "Eczema": ["Hydrocortisone Cream 1%"],
            "Allergic Rhinitis": ["Fluticasone Nasal Spray 50 mcg"],
            "Recurrent Ear Infections": ["Amoxicillin 500 mg"],
            "Tonsillitis": ["Azithromycin 250 mg"],

            # Neurologic / psych
            "Depression": ["Sertraline 50 mg", "Escitalopram 10 mg", "Bupropion 150 mg"],
            "Severe Depression": ["Sertraline 100 mg", "Venlafaxine 75 mg"],
            "Moderate Depression": ["Escitalopram 10 mg"],
            "Anxiety": ["Buspirone 10 mg", "Duloxetine 30 mg"],
            "Social Anxiety": ["Propranolol 10 mg"],
            "ADHD": ["Methylphenidate 10 mg", "Amphetamine-Dextroamphetamine 20 mg"],
            "Insomnia": ["Trazodone 50 mg", "Zolpidem 10 mg"],
            "Migraines": ["Topiramate 50 mg", "Sumatriptan 50 mg"],
            "Chronic Fatigue": ["Modafinil 100 mg"],

            # Musculoskeletal / pain
            "Arthritis": ["Ibuprofen 600 mg", "Celecoxib 200 mg"],
            "Low Back Pain": ["Naproxen 500 mg"],
            "Chronic Low Back Pain": ["Gabapentin 300 mg"],
            "Sports Injury": ["Cyclobenzaprine 10 mg"],
            "Osteoporosis": ["Alendronate 70 mg"],

            # GI / hepatic
            "Gastroesophageal Reflux Disease (GERD)": ["Omeprazole 20 mg", "Famotidine 20 mg"],
            "Liver Condition": ["Ursodiol 300 mg"],
            "Fatty Liver": ["Vitamin E 400 IU"],
            "Gallstones": ["Ursodiol 300 mg"],
            "Irritable Bowel Syndrome (IBS)": ["Dicyclomine 10 mg"],

            # Other
            "Anemia (on treatment)": ["Ferrous Sulfate 325 mg"],
            "Cancer": ["Ondansetron 8 mg"],
            "No significant medical conditions": ["Multivitamin 1 tablet"]
        }

        pdmp = []
        all_conditions = set(getattr(self, "conditions", []) + getattr(self, "medical_history", []))

        # gather all possible medications for this patient
        all_possible_medications = []
        for cond in all_conditions:
            all_possible_medications.extend(condition_to_medications.get(cond, []))

        if not all_possible_medications:
            # if patient has no controlled/relevant meds, PDMP can be empty
            return pdmp

        number_of_medications = random.randint(1, min(len(all_possible_medications), 3))
        chosen_medications = random.sample(all_possible_medications, number_of_medications)

        # get the 
        for med in chosen_medications:
            days = random.choice([30, 60, 90])
            dose_per_day, refills = self.get_medication_info(med, days)
            quantity = self.calculate_quantity(dose_per_day, days, med)
            date_filled = datetime.now() - timedelta(days=random.randint(5, 30))
            date_written = date_filled - timedelta(days=2)

            pdmp.append({
                "drug": med,
                "qty": quantity,
                "days": days,
                "refill": refills,
                "date_written": date_written.strftime("%Y-%m-%d"),
                "date_filled": date_filled.strftime("%Y-%m-%d")
            })

        return pdmp

    def generate_immunization_record(self):
        """
        return True/False based on the likelihood the patient is
        to be up to date with their immunizations.
        """

        if self.age < 18:
            # 70-80% of kids follow AAFP guidelines
            up_to_date = random.random() < 0.75
        elif self.age < 65:
            # 50% for adults
            up_to_date = random.random() < 0.50
        else:
            # 65% for seniors
            up_to_date = random.random() < 0.65
        
        status = "UpToDate" if up_to_date else "Not UpToDate"
    
        # Return a dictionary that holds the simple status
        return {"Status": status}

    def get_tags(self):
        """
        returns a list of tags based off conditions and age
        tags vary from type of condition, to severity, to age group
        """

        condition_tags = {

            # --- Behavioral Health ---
            "Depression": ["Behavioral Health", "Chronic"],
            "Moderate Depression": ["Behavioral Health", "Chronic"],
            "Severe Depression": ["Behavioral Health", "Chronic", "Serious"],
            "Anxiety": ["Behavioral Health", "Chronic"],
            "Social Anxiety": ["Behavioral Health", "Chronic"],
            "ADHD": ["Behavioral Health", "Chronic"],
            "Eating Disorder": ["Behavioral Health", "Chronic", "Serious"],
            "Substance Use Experimentation": ["Behavioral Health", "Acute"],
            "Chronic Fatigue": ["Behavioral Health", "Chronic"],
            "Insomnia": ["Behavioral Health", "Chronic"],

            # --- Nervous System / Neurological ---
            "Migraines": ["Nervous System", "Chronic"],
            "Migraine": ["Nervous System", "Chronic"],
            "Cognitive Impairment": ["Nervous System", "Chronic", "Serious"],
            "Parkinson's Disease": ["Nervous System", "Chronic", "Serious"],
            "Concussion": ["Nervous System", "Acute", "Serious"],
            "Speech Delay": ["Nervous System", "Chronic"],
            "Peripheral Neuropathy": ["Nervous System", "Chronic"],
            "Stroke": ["Nervous System", "History", "Serious"],

            # --- Eye & Ear (Sensory) ---
            "Cataracts": ["Sensory", "Chronic"],
            "Macular Degeneration": ["Sensory", "Chronic"],
            "Glaucoma": ["Sensory", "Chronic"],
            "Hearing Loss": ["Sensory", "Chronic"],

            # --- Dermatologic (Skin & Subcutaneous Tissue) ---
            "Eczema": ["Dermatologic", "Chronic"],
            "Eczema Flare": ["Dermatologic", "Acute"],
            "Acute Eczema Flare": ["Dermatologic", "Acute"],
            "Acne": ["Dermatologic", "Chronic"],
            "Acne Vulgaris Flare": ["Dermatologic", "Acute"],
            "Contact Dermatitis": ["Dermatologic", "Acute"],
            "Seborrheic Dermatitis": ["Dermatologic", "Chronic"],
            "Cellulitis": ["Dermatologic", "Acute", "Serious"],
            "Abscess": ["Dermatologic", "Acute", "Serious"],
            "Folliculitis": ["Dermatologic", "Acute"],
            "Impetigo": ["Dermatologic", "Acute"],
            "Fungal Infection (Tinea)": ["Dermatologic", "Acute"],
            "Tinea Corporis (Ringworm)": ["Dermatologic", "Acute"],
            "Insect Bite Reaction": ["Dermatologic", "Acute"],
            "Urticaria (Hives)": ["Dermatologic", "Acute"],
            "Diaper Rash": ["Dermatologic", "Acute"],
            "Stasis Dermatitis": ["Dermatologic", "Chronic"],
            "Pressure Ulcer": ["Dermatologic", "Acute", "Serious"],
            "Skin Tear": ["Dermatologic", "Acute"],

            # --- Musculoskeletal ---
            "Arthritis": ["Musculoskeletal", "Chronic"],
            "Osteoarthritis": ["Musculoskeletal", "Chronic"],
            "Osteoporosis": ["Musculoskeletal", "Chronic"],
            "Low Back Pain": ["Musculoskeletal", "Acute"],
            "Chronic Low Back Pain": ["Musculoskeletal", "Chronic"],
            "Low Back Strain": ["Musculoskeletal", "Acute"],
            "Neck Strain": ["Musculoskeletal", "Acute"],
            "Sports Injury": ["Musculoskeletal", "Acute"],
            "Ankle Sprain": ["Musculoskeletal", "Acute"],
            "Chronic Pain": ["Musculoskeletal", "Chronic"],
            "Acute Gout Flare": ["Musculoskeletal", "Acute"],
            "Previous Joint Injury": ["Musculoskeletal", "History"],
            "Previous Fracture": ["Musculoskeletal", "History"],
            "Previous Back Strain": ["Musculoskeletal", "History"],
            "Fall with Contusion": ["Musculoskeletal", "Acute"],

            # --- Cardiovascular ---
            "Hypertension": ["Cardiovascular", "Chronic"],
            "Hyperlipidemia": ["Cardiovascular", "Chronic"],
            "Heart Failure": ["Cardiovascular", "Chronic", "Serious"],
            "Congestive Heart Failure": ["Cardiovascular", "Chronic", "Serious"],
            "Coronary Heart Disease": ["Cardiovascular", "Chronic", "Serious"],
            "Heart Disease": ["Cardiovascular", "Chronic", "Serious"],
            "Heart Attack": ["Cardiovascular", "History", "Serious"],
            "Angina": ["Cardiovascular", "Acute", "Serious"],
            "Atrial Fibrillation": ["Cardiovascular", "Chronic"],
            "Peripheral Vascular Disease": ["Cardiovascular", "Chronic"],

            # --- Respiratory ---
            "Asthma": ["Respiratory", "Chronic"],
            "COPD": ["Respiratory", "Chronic", "Serious"],
            "Sleep Apnea": ["Respiratory", "Chronic"],
            "Upper Respiratory Infection": ["Respiratory", "Acute"],
            "Viral Upper Respiratory Infection": ["Respiratory", "Acute"],
            "Bronchitis": ["Respiratory", "Acute"],
            "Pneumonia": ["Respiratory", "Acute", "Serious"],
            "Acute Sinusitis": ["Respiratory", "Acute"],
            "Sinusitis": ["Respiratory", "Acute"],
            "Bacterial Pharyngitis": ["Respiratory", "Acute"],
            "Pharyngitis": ["Respiratory", "Acute"],
            "Strep Pharyngitis": ["Respiratory", "Acute"],
            "Tonsillitis": ["Respiratory", "Acute"],
            "Recurrent Ear Infections": ["Respiratory", "Chronic"],
            "Acute Otitis Media": ["Respiratory", "Acute"],
            "Acute Otitis Externa (Swimmer's Ear)": ["Respiratory", "Acute"],

            # --- Gastrointestinal ---
            "GERD": ["Gastrointestinal", "Chronic"],
            "IBS": ["Gastrointestinal", "Chronic"],
            "Acute Gastroenteritis": ["Gastrointestinal", "Acute"],
            "Viral Gastroenteritis": ["Gastrointestinal", "Acute"],
            "Food Poisoning": ["Gastrointestinal", "Acute"],
            "Constipation": ["Gastrointestinal", "Acute"],
            "Liver Condition": ["Gastrointestinal", "Chronic", "Serious"],
            "Fatty Liver": ["Gastrointestinal", "Chronic"],
            "Liver Fibrosis": ["Gastrointestinal", "Chronic", "Serious"],
            "Liver Cirrhosis": ["Gastrointestinal", "Chronic", "Serious"],
            "Viral Hepatitis": ["Gastrointestinal", "Chronic"],
            "Autoimmune Hepatitis": ["Gastrointestinal", "Chronic"],
            "Other Liver Disease": ["Gastrointestinal", "Chronic"],
            "Gallstones": ["Gastrointestinal", "Acute"],
            "Acute Diverticulitis": ["Gastrointestinal", "Acute"],

            # --- Endocrine & Metabolic ---
            "Diabetes": ["Endocrine", "Chronic"],
            "Type 2 Diabetes": ["Endocrine", "Chronic"],
            "Prediabetes": ["Endocrine", "Chronic"],
            "Obesity": ["Endocrine", "Chronic"],
            "Hypothyroidism": ["Endocrine", "Chronic"],
            "Thyroid Disorder": ["Endocrine", "Chronic"],

            # --- Genitourinary / Urinary ---
            "Urinary Tract Infection": ["Urinary", "Acute"],
            "Urinary Incontinence": ["Urinary", "Chronic"],
            "Chronic Kidney Disease": ["Urinary", "Chronic", "Serious"],
            "Benign Prostatic Hyperplasia": ["Urinary", "Chronic"],

            # --- Female Reproductive System ---
            "Menstrual Irregularities": ["Female Reproductive System", "Chronic"],
            "PMS": ["Female Reproductive System", "Chronic"],
            "Vaginal Yeast Infection": ["Female Reproductive System", "Acute"],
            "Bacterial Vaginosis": ["Female Reproductive System", "Acute"],

            # --- Infectious / Immune ---
            "Mononucleosis": ["Infectious", "Acute"],
            "Hand, Foot, and Mouth Disease": ["Infectious", "Acute"],
            "Shingles (Herpes Zoster)": ["Infectious", "Acute"],
            "Food Allergies": ["Immune", "Chronic"],
            "Allergic Rhinitis": ["Immune", "Chronic"],
            "Seasonal Allergies": ["Immune", "Chronic"],
            "Hay Fever": ["Immune", "Chronic"],

            # --- Hematologic & Oncologic ---
            "Anemia (on treatment)": ["Blood & Lymphoreticular", "Chronic"],
            "Cancer": ["Blood & Lymphoreticular", "Chronic", "Serious"],

            # --- Injury / General Acute ---
            "Minor Laceration": ["Injury", "Acute"],
            "Abrasion": ["Injury", "Acute"],
            "Contusion": ["Injury", "Acute"],
            "Sports-Related Contusion": ["Injury", "Acute"],
            "Jammed Finger": ["Injury", "Acute"],

            # --- Multi-System / General ---
            "Polypharmacy": ["General Principles", "Chronic"],
            "No significant medical conditions": ["General Principles"],
            "Family History of Ear Infections": ["History"],
            "Appendicitis": ["History"],
        }

        tag_map = {}
        print("get_tags",self.medical_condition)
        for condition in self.medical_condition:
            if condition in condition_tags:
                tag_map[condition] = condition_tags[condition]
            else:
                tag_map[condition] = ["Other"]
        print(tag_map)
        return tag_map

    def generate_chief_concern(self):
        """
        Generates Chief Concern and Context for Medical Visit
        Acute Conditions take precedence over Chronic Conditions
        Serious Conditions are used to provide more context to the Patients Visit
        """

        # Edge Case : Patient is completely fine
        if not self.medical_condition or self.medical_condition == ["No significant medical conditions"]:
            self.chief_complaint = "General checkup"
            self.chief_concern = {
                "chief_complaint": ["General checkup"],
                "chief_complaint_tags": ["Routine"],
            }
            return self.chief_concern
        
        tag_map = self.get_tags()

        acute_conditions = []
        chronic_conditions = []
        serious_conditions = []

        for condition, tags in tag_map.items():
            #skips conditions that are part of medical History
            if "Other" in tags:
                continue
            if "History" in tags:
                if "Serious" in tags:
                    serious_conditions.append(condition)
                continue
            if "Acute" in tags:
                acute_conditions.append(condition)
            if "Chronic" in tags:
                chronic_conditions.append(condition)
            #if condition is neither Acute nor Chronic, it is tagged as Serious
            else:
                serious_conditions.append(condition)
        
        chief_complaint = []

        if acute_conditions:
            #selects 1 Acute condition as chief complaint, with a small chance of 2
            num_acute = 1 if len(acute_conditions) == 1 else random.randint(1, min(2, len(acute_conditions)))
            chief_complaint = random.sample(acute_conditions, num_acute)
        else:
            #if no Acute conditions, selects 1-2 Chronic conditions as chief complaint
            num_chronic = min(len(chronic_conditions), random.randint(1, 2))
            chief_complaint = random.sample(chronic_conditions, num_chronic)

        #set of tags associated with chief complaint
        chief_complaint_tags = set()

        for condition in chief_complaint:
            if condition in tag_map:
                chief_complaint_tags.update(tag_map[condition])

        self.chief_complaint = chief_complaint[0] if chief_complaint else "General Checkup"

        chief_concern = {
            "chief_complaint": chief_complaint,
            "chief_complaint_tags": sorted(list(chief_complaint_tags)),
        }

        return chief_concern

    #Function to attach the tags when its passed through user.
    def attach_chief_concern_tags(self):
        tag_map = self.get_tags()
       # print("attach chief",tag_map)
        complaint = self.chief_concern
        #print("complaint: ",complaint)
        self.chief_complaint=complaint
        self.chief_concern={
            "chief_complaint": complaint,
            "chief_complaint_tags": (tag_map[complaint[0]]),
        }

        return self.chief_concern

        

    def generate_patient_message(self, prompt=PATIENT_MESSAGE_PROMPT):
        
        with open(prompt, "r") as f:
            prompt_template = f.read()
        

        # fill in context
        prompt = prompt_template.format(
            name=self.name,
            age=self.age,
            chief_complaint=", ".join(self.chief_complaint),
            medical_conditions=", ".join(self.medical_condition),
            history=", ".join(self.medical_history),
            surgeries=", ".join(self.surgical_history)
        )

        # call openai
        response = openai_client.chat.completions.create(
            model="gpt-4o",  
            messages=[
                {"role": "system", "content": "You are a patient describing your symptoms casually."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.9
        )

        self.message = response.choices[0].message.content.strip()

        return self.message
    


    def to_dict(self):
 
        return {
            "Name": self.name,
            "Date of Birth": self.dob,
            "Gender": self.gender,
            "Chief Complaint": self.chief_complaint,
            "Medical Condition": self.medical_condition,
            "Medical History": self.medical_history,
            "Family Medical History": self.family_medical_history,
            "Surgical History": self.surgical_history,
            "Cholesterol": self.cholesterol,
            "Allergies": self.allergies,
            "PDMP": self.pdmp,
            "Immunization": self.immunization,
            "Height": self.height,
            "Weight": self.weight,
            "Last BP": self.last_bp,
            "Chief Concern": self.chief_concern,
            "Patient Message": self.patient_message
        }

if __name__ == "__main__":
    import pandas as pd
    import random

    # sample a random patient row from NHANES
    row = nhanes.sample(1).iloc[0]

    # generate the patient
    patient = Patient(row)

    print(f"Chief Complaint: {patient.chief_complaint}")  # "Acute Eczema Flare"
    print(f"Image URL: {patient.image_url}")  # URL for eczema flare image