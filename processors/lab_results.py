import uuid
from datetime import datetime, timedelta
import random
import json
from config import LAB_RESULTS_PROMPT, openai_client


# lab results get patient_id: uuid, test_name: text, test_date: text, test_result: json
class LabResults:

    def __init__(self, patient_id: uuid.UUID, patient_object):
        
        self.patient_id = patient_id
        self.patient = patient_object

        self.test_name = self.generate_test_name()
        self.test_date = self.generate_test_date()
        self.test_result = self.generate_test_result()


    def generate_test_name(self):

        # grab patient fields
        conditions = [c for c in self.patient.medical_condition]
        gender = self.patient.gender.lower()
        age = self.patient.age
        possible_tests = []

        # newborn
        if age < 1:
            possible_tests = ["Newborn Screening Panel","Bilirubin Test", "Blood Typing", "Basic Metabolic Panel"]

        # toddler
        elif age < 6:
            possible_tests = ["Lead Screening", "Hemoglobin Test", "Iron Panel", "CBC (Complete Blood Count)"]

        # child
        elif age < 12:
            if any(c in conditions for c in ["Asthma", "Eczema", "Allergic Rhinitis"]):
                possible_tests = ["Allergy Panel", "Pulmonary Function Test"]
            elif any(c in conditions for c in ["Tonsillitis", "Ear Infection"]):
                possible_tests = ["Rapid Strep Test", "Throat Culture"]
            else:
                possible_tests = ["CBC (Complete Blood Count)", "Basic Metabolic Panel", "Urinalysis"]

        # teenager
        elif 12 <= age < 20:
            if any(c in conditions for c in ["Anxiety", "Depression"]):
                possible_tests = ["Thyroid Panel", "Vitamin D", "Toxicology Screen"]
            elif any(c in conditions for c in ["Sports Injury", "Concussion"]):
                possible_tests = ["MRI (Brain)", "CT Scan", "CBC"]
            else:
                possible_tests = ["CBC (Complete Blood Count)", "Basic Metabolic Panel", "Urine Drug Screen"]

        # adult
        elif 20 <= age < 65:
            if any(c in conditions for c in ["Hypertension", "Heart Failure"]):
                possible_tests = ["Basic Metabolic Panel", "Renal Function Test"]
            if any(c in conditions for c in ["Asthma", "COPD", "Chronic Cough", "Shortness of Breath"]):
                possible_tests = ["Pulmonary Function Test", "CBC (Complete Blood Count)"]
            elif any(c in conditions for c in ["Diabetes", "Type 2 Diabetes", "Prediabetes"]):
                possible_tests = ["Hemoglobin A1C", "Fasting Glucose", "Urine Microalbumin", "Basic Metabolic Panel"]
            elif any(c in conditions for c in ["Hyperlipidemia"]):
                possible_tests = ["Lipid Panel"]
            elif any(c in conditions for c in ["Obesity"]):
                possible_tests = ["Lipid Panel", "Liver Function Test"]
            elif any(c in conditions for c in ["Hypothyroidism", "Hyperthyroidism", "Thyroid Disease"]):
                possible_tests = ["Thyroid Stimulating Hormone"]
            elif any(c in conditions for c in ["Anxiety", "Depression"]):
                possible_tests = ["Thyroid Stimulating Hormone", "Vitamin D"]
            elif any(c in conditions for c in ["Liver Condition", "Fatty Liver", "Viral Hepatitis", "Autoimmune Hepatitis"]):
                possible_tests = ["Liver Function Test", "Hepatitis Panel"]
            elif any(c in conditions for c in ["Infection", "Pneumonia", "Inflammation", "Viral Illness"]):
                possible_tests = ["CBC (Complete Blood Count)", "Basic Metabolic Panel"]
            elif gender == "female" and 15 <= age <= 45:
                possible_tests = ["Pregnancy Test", "Urine Drug Screen"]
            else:
                possible_tests = [
                    "CBC (Complete Blood Count)",
                    "Comprehensive Metabolic Panel",
                    "Urine Drug Screen",
                    "Thyroid Stimulating Hormone"
                ]

        # elderly
        else:
            if any(c in conditions for c in ["Arthritis", "Osteoporosis"]):
                possible_tests = ["Vitamin D", "Calcium Level", "Inflammatory Markers"]
            elif any(c in conditions for c in ["Hypertension", "Heart Failure"]):
                possible_tests = ["Renal Function Test", "BNP"]
            elif any(c in conditions for c in ["Cognitive Impairment", "Parkinson's Disease"]):
                possible_tests = ["Thyroid Panel", "Vitamin B12", "MRI (Brain)"]
            else:
                possible_tests = ["CBC (Complete Blood Count)", "Comprehensive Metabolic Panel", "Lipid Panel"]

        return random.choice(possible_tests)

    
    def generate_test_date(self):

        current_date = datetime.now()
        days_ago = random.randint(1, 180)
        test_date = current_date - timedelta(days=days_ago)
        return test_date.strftime("%Y-%m-%d")



    def generate_test_result(self):
        """
        Generate medically realistic lab results
        """
        
        age = self.patient.age
        gender = self.patient.gender.lower()
        conditions = self.patient.medical_condition
        
        # map test names to generation functions
        test_generators = {
            # newborn tests
            "Newborn Screening Panel": self.generate_newborn_screening,
            "Bilirubin Test": self.generate_bilirubin_test,
            "Blood Typing": self.generate_blood_typing,
            "Basic Metabolic Panel": self.generate_basic_metabolic_panel,
            
            # toddler tests
            "Lead Screening": self.generate_lead_screening,
            "Hemoglobin Test": self.generate_hemoglobin_test,
            "Iron Panel": self.generate_iron_panel,
            "CBC (Complete Blood Count)": self.generate_cbc,
            
            # child tests
            "Allergy Panel": self.generate_allergy_panel,
            "Pulmonary Function Test": self.generate_pulmonary_function,
            "Rapid Strep Test": self.generate_strep_test,
            "Throat Culture": self.generate_strep_test,
            "Urinalysis": self.generate_urinalysis,
            
            # teenager tests
            "Thyroid Panel": self.generate_thyroid_panel,
            "Vitamin D": self.generate_vitamin_d,
            "Toxicology Screen": self.generate_toxicology_screen,
            "MRI (Brain)": self.generate_mri_brain,
            "CT Scan": self.generate_ct_scan,
            "Urine Drug Screen": self.generate_urine_drug_screen,
            
            # adult tests
            "Renal Function Test": self.generate_renal_function,
            "Hemoglobin A1C": self.generate_hemoglobin_a1c,
            "Fasting Glucose": self.generate_fasting_glucose,
            "Urine Microalbumin": self.generate_urine_microalbumin,
            "Lipid Panel": self.generate_lipid_panel,
            "Liver Function Test": self.generate_liver_function,
            "Thyroid Stimulating Hormone": self.generate_tsh,
            "Pregnancy Test": self.generate_pregnancy_test,
            "Comprehensive Metabolic Panel": self.generate_comprehensive_metabolic,
            "Hepatitis Panel": self.generate_hepatitis_panel,
            
            # elderly tests
            "Calcium Level": self.generate_calcium_level,
            "Inflammatory Markers": self.generate_inflammatory_markers,
            "BNP": self.generate_bnp,
            "Vitamin B12": self.generate_vitamin_b12
        }
        
        generator_function = test_generators.get(self.test_name)
            
        if generator_function:
            return generator_function(age, gender, conditions)
        else:
            return self.generate_default_result(age, gender, conditions)

    ############################################################################################
    # Test specific generators 
    ############################################################################################

    def generate_cbc(self, age, gender, conditions):
        """
        Generate Complete Blood Count with age/gender adjustments
        """
        if age < 1:  # newborn
            return {
                "WBC": f"{round(random.uniform(9.0, 30.0), 1)} x10^3/µL",
                "RBC": f"{round(random.uniform(4.0, 5.8), 1)} x10^6/µL",
                "Hemoglobin": f"{round(random.uniform(14.0, 18.0), 1)} g/dL",
                "Hematocrit": f"{round(random.uniform(44.0, 64.0), 1)}%",
                "Platelets": f"{random.randint(150, 450)} x10^3/µL"
            }
        elif age < 18:  # pediatric
            return {
                "WBC": f"{round(random.uniform(5.0, 15.0), 1)} x10^3/µL",
                "RBC": f"{round(random.uniform(4.0, 5.2), 1)} x10^6/µL",
                "Hemoglobin": f"{round(random.uniform(11.5, 14.5), 1)} g/dL",
                "Hematocrit": f"{round(random.uniform(35.0, 43.0), 1)}%",
                "Platelets": f"{random.randint(150, 450)} x10^3/µL"
            }
        else:  # adult
            if any(c in conditions for c in ["Infection", "Pneumonia", "Inflammation", "Viral Illness"]):
                wbc = round(random.uniform(11.1, 14.5), 1)
            else:
                wbc = round(random.uniform(4.5, 11.0), 1)

            if gender == "female":
                return {
                    "WBC": f"{wbc} x10^3/µL",
                    "RBC": f"{round(random.uniform(4.2, 5.4), 1)} x10^6/µL",
                    "Hemoglobin": f"{round(random.uniform(12.0, 15.5), 1)} g/dL",
                    "Hematocrit": f"{round(random.uniform(36.0, 48.0), 1)}%",
                    "Platelets": f"{random.randint(150, 450)} x10^3/µL"
                }
            else:  # male
                return {
                    "WBC": f"{wbc} x10^3/µL",
                    "RBC": f"{round(random.uniform(4.5, 6.1), 1)} x10^6/µL",
                    "Hemoglobin": f"{round(random.uniform(13.5, 17.5), 1)} g/dL",
                    "Hematocrit": f"{round(random.uniform(41.0, 53.0), 1)}%",
                    "Platelets": f"{random.randint(150, 450)} x10^3/µL"
                }


    def generate_basic_metabolic_panel(self, age, gender, conditions):
        """
        Generate Basic Metabolic Panel with condition adjustments
        """

        # base values
        glucose = random.randint(70, 110)
        creatinine = round(random.uniform(0.6, 1.3), 1)
        
        # condition adjustments
        if any(d in conditions for d in ["Diabetes", "Type 2 Diabetes", "Prediabetes"]):
            glucose = random.randint(110, 160)
        if any(c in conditions for c in ["Hypertension", "Heart Failure", "Renal Disease"]):
            creatinine = round(random.uniform(1.2, 2.0), 1)
        if age > 65:
            creatinine = round(random.uniform(0.8, 1.5), 1)
        
        return {
            "Glucose": f"{glucose} mg/dL",
            "Calcium": f"{round(random.uniform(8.5, 10.2), 1)} mg/dL",
            "Sodium": f"{random.randint(135, 145)} mmol/L",
            "Potassium": f"{round(random.uniform(3.5, 5.2), 1)} mmol/L",
            "CO2": f"{random.randint(22, 30)} mmol/L",
            "Chloride": f"{random.randint(98, 107)} mmol/L",
            "BUN": f"{random.randint(7, 25)} mg/dL",
            "Creatinine": f"{creatinine} mg/dL"
        }


    def generate_lipid_panel(self, age, gender, conditions):
        """
        Generate Lipid Panel with condition adjustments
        """

        # base lipid values
        total_chol = random.randint(150, 220)
        hdl = random.randint(40, 70)
        ldl = random.randint(70, 160)
        trig = random.randint(70, 200)
        
        # adjust for hyperlipidemia
        if any(c in conditions for c in ["Hyperlipidemia", "Obesity"]):
            total_chol = random.randint(200, 280)
            ldl = random.randint(130, 220)
            trig = random.randint(150, 400)
            hdl = random.randint(30, 50)  # lower HDL
        
        return {
            "Total Cholesterol": f"{total_chol} mg/dL",
            "HDL": f"{hdl} mg/dL",
            "LDL": f"{ldl} mg/dL",
            "Triglycerides": f"{trig} mg/dL"
        }

    def generate_thyroid_panel(self, age, gender, conditions):
        """
        Generate Thyroid Panel with condition adjustments
        """

        # base thyroid function
        tsh = round(random.uniform(0.4, 4.0), 2)
        free_t4 = round(random.uniform(0.8, 1.8), 1)
        t3 = random.randint(80, 200)
        
        # adjust for thyroid conditions
        if any(c in conditions for c in ["Hypothyroidism"]):
            tsh = round(random.uniform(4.5, 12.0), 2)
            free_t4 = round(random.uniform(0.5, 0.9), 1)
            t3 = random.randint(60, 95)
        elif any(c in conditions for c in ["Hyperthyroidism"]):
            tsh = round(random.uniform(0.01, 0.3), 2)
            free_t4 = round(random.uniform(1.9, 3.0), 1)
            t3 = random.randint(210, 320)
        

        return {
            "TSH": f"{tsh} µIU/mL",
            "Free T4": f"{free_t4} ng/dL",
            "T3": f"{t3} ng/dL"
        }


    def generate_liver_function(self, age, gender, conditions):
        """
        Generate Liver Function Tests with condition adjustments
        """

        # base values
        alt = random.randint(10, 40)
        ast = random.randint(10, 35)
        alp = random.randint(45, 115)
        bilirubin = round(random.uniform(0.2, 1.2), 1)
        
        # adjust for liver conditions
        if any(c in conditions for c in ["Liver Condition", "Fatty Liver", "Viral Hepatitis"]):
            alt = random.randint(50, 300)
            ast = random.randint(45, 250)
            alp = random.randint(100, 250)
            bilirubin = round(random.uniform(1.5, 5.0), 1)
        
        return {
            "ALT": f"{alt} U/L",
            "AST": f"{ast} U/L",
            "ALP": f"{alp} U/L",
            "Bilirubin": f"{bilirubin} mg/dL"
        }

    def generate_urinalysis(self, age, gender, conditions):
        """
        Generate Urinalysis with realistic variations
        """

        # occasional abnormalities (15% chance)
        has_abnormality = random.random() < 0.15
        
        return {
            "Color": random.choice(["Yellow", "Straw", "Amber", "Pale yellow"]),
            "Clarity": random.choice(["Clear", "Slightly hazy", "Hazy"]),
            "pH": f"{round(random.uniform(5.0, 7.5), 1)}",
            "Protein": "Trace" if has_abnormality and random.random() < 0.3 else "Negative",
            "Glucose": "1+" if has_abnormality and random.random() < 0.2 else "Negative",
            "Ketones": "Trace" if has_abnormality and random.random() < 0.1 else "Negative",
            "Blood": "Occult" if has_abnormality and random.random() < 0.25 else "Negative"
        }

    def generate_blood_typing(self, age, gender, conditions):
        """
        Generate blood type with realistic distribution
        """
        abo = random.choices(["A", "B", "O", "AB"], weights=[0.42, 0.10, 0.44, 0.04])[0]
        rh = "Positive" if random.random() < 0.85 else "Negative"
        return {"ABO Group": abo, "Rh Factor": rh}

    def generate_newborn_screening(self, age, gender, conditions):
        """
        Generate newborn screening results
        """

        return {
            "Phenylketonuria": "Negative",
            "Hypothyroidism": "Normal",
            "Cystic Fibrosis": "Negative",
            "Galactosemia": "Negative"
        }

    def generate_bilirubin_test(self, age, gender, conditions):
        """
        Generate bilirubin test - higher for newborns
        """

        if age < 1:  # newborns have higher bilirubin
            total_bilirubin = round(random.uniform(2.0, 8.0), 1)
            interpretation = "Physiological jaundice" if total_bilirubin > 5.0 else "Normal"
        else:
            total_bilirubin = round(random.uniform(0.2, 1.2), 1)
            interpretation = "Normal"
            
        return {
            "Total Bilirubin": f"{total_bilirubin} mg/dL",
            "Direct Bilirubin": f"{round(total_bilirubin * 0.1, 1)} mg/dL",
            "Interpretation": interpretation
        }
    

    def generate_lead_screening(self, age, gender, conditions):

        level = round(random.uniform(1.0, 8.0), 1)

        return {"Blood Lead Level (µg/dL)": level}

    def generate_hemoglobin_test(self, age, gender, conditions):

        if gender == "female":
            return {"Hemoglobin (g/dL)": round(random.uniform(12.0, 15.5), 1)}
        else:
            return {"Hemoglobin (g/dL)": round(random.uniform(13.5, 17.5), 1)}

    def generate_iron_panel(self, age, gender, conditions):

        return {
            "Serum Iron": f"{random.randint(50, 150)} µg/dL",
            "TIBC": f"{random.randint(250, 400)} µg/dL",
            "Ferritin": f"{random.randint(20, 200)} ng/mL"
        }
    
    def generate_allergy_panel(self, age, gender, conditions):

        return {
            "Pollen": "Positive" if random.random() < 0.2 else "Negative",
            "Dust Mite": "Positive" if random.random() < 0.1 else "Negative",
            "Pet Dander": "Positive" if random.random() < 0.08 else "Negative",
            "Peanut": "Positive" if random.random() < 0.08 else "Negative",
            "Milk": "Positive" if random.random() < 0.12 else "Negative",
            "Egg": "Positive" if random.random() < 0.12 else "Negative"
        }

    def generate_pulmonary_function(self, age, gender, conditions):

        return {
            "FEV1": f"{random.randint(85, 110)}% predicted",
            "FVC": f"{random.randint(85, 110)}% predicted",
            "FEV1/FVC Ratio": f"{round(random.uniform(0.75, 0.85), 2)}"
        }
    
    def generate_strep_test(self, age, gender, conditions):
        # 25% positive rate for symptomatic patients
        if any(c in conditions for c in ["Tonsillitis", "Ear Infection"]):
            return {"Group A Streptococcus": "Positive" if random.random() < 0.25 else "Negative"}
        return {"Group A Streptococcus": "Negative"}

    def generate_vitamin_d(self, age, gender, conditions):

        level = round(random.uniform(20.0, 50.0), 1)
        status = "Sufficient" if level >= 30 else "Insufficient" if level >= 20 else "Deficient"

        return {"25-Hydroxy Vitamin D (ng/mL)": level, "Status": status}

    def generate_toxicology_screen(self, age, gender, conditions):

        # 15% chance of any positive
        has_positive = random.random() < 0.15
        
        if has_positive:
            # pick 1-2 substances to be positive
            positive_substances = random.sample([
                "THC", "Benzodiazepines", "Opiates", "Amphetamines", "Cocaine"
            ], random.randint(1, 2))
            
            results = {}
            for substance in ["Amphetamines", "Benzodiazepines", "Opiates", "THC", "Cocaine"]:
                if substance in positive_substances:
                    results[substance] = "Positive"
                else:
                    results[substance] = "Negative"
            return results
        else:
            return {substance: "Negative" for substance in [
                "Amphetamines", "Benzodiazepines", "Opiates", "THC", "Cocaine"
            ]}
        

    def generate_mri_brain(self, age, gender, conditions):

        findings = [
            "Normal brain parenchyma. No acute intracranial abnormality.",
            "Unremarkable MRI of the brain. No focal lesions or mass effect.",
            "Normal cerebral hemispheres, cerebellum, and brainstem.",
            "No evidence of acute infarction, hemorrhage, or mass lesion."
        ]

        return {"Findings": random.choice(findings)}

    def generate_ct_scan(self, age, gender, conditions):

        findings = [
            "No acute intracranial hemorrhage, mass effect, or midline shift.",
            "Unremarkable non-contrast CT head. Ventricles and sulci are normal.",
            "No evidence of acute infarction or intracranial hemorrhage."
        ]

        return {"Findings": random.choice(findings)}

    def generate_urine_drug_screen(self, age, gender, conditions):

        return {substance: "Negative" for substance in [
            "Cocaine", "Ethanol", "Opiates", "Amphetamines", "Barbiturates", 
            "Cannabinoids", "Benzodiazepine", "Phencyclidine (PCP)"
        ]}

    def generate_renal_function(self, age, gender, conditions):

        bun = random.randint(8, 25)

        if any(c in conditions for c in ["Hypertension", "Heart Failure", "Chronic Kidney Disease", "Renal Disease"]):
            creatinine = round(random.uniform(1.2, 2.2), 1)
        elif age >= 65:
            creatinine = round(random.uniform(0.8, 1.6), 1)
        else:
            creatinine = round(random.uniform(0.6, 1.3), 1)

        gfr = self.calculate_egfr(creatinine, age, gender)

        return {
            "BUN": f"{bun} mg/dL",
            "Creatinine": f"{creatinine} mg/dL",
            "GFR": f"{gfr} mL/min/1.73m²"
        }

    def generate_hemoglobin_a1c(self, age, gender, conditions):

        if any(d in conditions for d in ["Diabetes", "Type 2 Diabetes", "Prediabetes"]):
            a1c = round(random.uniform(6.0, 7.5), 1)
        else:
            a1c = round(random.uniform(4.8, 5.6), 1)


        return {
            "HbA1c": f"{a1c}%",
            "Estimated Average Glucose": f"{int((a1c * 28.7) - 46.7)} mg/dL"
        }

    def generate_fasting_glucose(self, age, gender, conditions):

        if any(d in conditions for d in ["Diabetes", "Type 2 Diabetes", "Prediabetes"]):
            return {"Glucose": f"{random.randint(105, 155)} mg/dL"}
        return {"Glucose": f"{random.randint(70, 100)} mg/dL"}


    def generate_urine_microalbumin(self, age, gender, conditions):

        level = random.randint(0, 30)
        if any(d in conditions for d in ["Diabetes", "Type 2 Diabetes"]):
            level = random.randint(30, 300)
        return {"Microalbumin": f"{level} mg/g creatinine"}

    def generate_tsh(self, age, gender, conditions):

        return {
            "TSH": "999 µIU/mL",
            "Free T4": "999 ng/dL",
            "T3": "999 ng/dL"
        }

    def generate_pregnancy_test(self, age, gender, conditions):
        # 5% chance of positive for testing
        return {"hCG": "Positive" if random.random() < 0.05 and gender == "female" else "Negative"}

    def generate_comprehensive_metabolic(self, age, gender, conditions):

        cmp_result = self.generate_basic_metabolic_panel(age, gender, conditions)

        cmp_result["ALT"] = f"{random.randint(10, 40)} U/L"
        cmp_result["AST"] = f"{random.randint(10, 35)} U/L"
        cmp_result["Albumin"] = f"{round(random.uniform(3.5, 5.0), 1)} g/dL"

        abnormal_pool = []

        if any(d in conditions for d in ["Diabetes", "Type 2 Diabetes", "Prediabetes"]):
            abnormal_pool.extend(["Glucose", "Glucose"])

        if any(c in conditions for c in ["Hypertension", "Heart Failure", "Renal Disease", "Chronic Kidney Disease"]):
            abnormal_pool.extend(["BUN", "Creatinine"])

        if any(c in conditions for c in ["Liver Condition", "Fatty Liver", "Liver Fibrosis", "Liver Cirrhosis", "Viral Hepatitis", "Autoimmune Hepatitis", "Other Liver Disease"]):
            abnormal_pool.extend(["ALT", "AST", "Albumin"])

        abnormal_pool.extend([
            "Sodium",
            "Potassium",
            "CO2",
            "Calcium",
            "BUN",
            "ALT",
            "AST"
        ])

        num_abnormal = random.choices([0, 1, 2], weights=[30, 50, 20])[0]
        chosen = []
        available = abnormal_pool[:]

        while available and len(chosen) < num_abnormal:
            marker = random.choice(available)
            chosen.append(marker)
            available = [m for m in available if m != marker]

        for marker in chosen:
            if marker == "Glucose":
                cmp_result["Glucose"] = f"{random.choice([random.randint(55, 69), random.randint(111, 180)])} mg/dL"

            elif marker == "Sodium":
                cmp_result["Sodium"] = f"{random.choice([random.randint(128, 134), random.randint(146, 152)])} mmol/L"

            elif marker == "Potassium":
                cmp_result["Potassium"] = f"{round(random.choice([random.uniform(2.8, 3.4), random.uniform(5.3, 6.2)]), 1)} mmol/L"

            elif marker == "CO2":
                cmp_result["CO2"] = f"{random.choice([random.randint(16, 21), random.randint(31, 36)])} mmol/L"

            elif marker == "Calcium":
                cmp_result["Calcium"] = f"{round(random.choice([random.uniform(7.8, 8.4), random.uniform(10.3, 11.5)]), 1)} mg/dL"

            elif marker == "BUN":
                cmp_result["BUN"] = f"{random.choice([random.randint(26, 45), random.randint(3, 6)])} mg/dL"

            elif marker == "Creatinine":
                cmp_result["Creatinine"] = f"{round(random.uniform(1.4, 2.4), 1)} mg/dL"

            elif marker == "ALT":
                cmp_result["ALT"] = f"{random.randint(45, 120)} U/L"

            elif marker == "AST":
                cmp_result["AST"] = f"{random.randint(40, 110)} U/L"

            elif marker == "Albumin":
                cmp_result["Albumin"] = f"{round(random.uniform(2.5, 3.4), 1)} g/dL"

        return cmp_result

    def generate_hepatitis_panel(self, age, gender, conditions):

        # 10% chance of any positive finding
        has_positive = random.random() < 0.10
        
        if has_positive:

            if random.random() < 0.7:
                return {
                    "Hepatitis A": "Non-reactive",
                    "Hepatitis B Surface Antibody": "Reactive",  # vaccinated
                    "Hepatitis B Core Antibody": "Non-reactive",
                    "Hepatitis C": "Non-reactive"
                }
            
            else:
                return {
                    "Hepatitis A": "Reactive" if random.random() < 0.5 else "Non-reactive",
                    "Hepatitis B Surface Antibody": "Non-reactive", 
                    "Hepatitis B Core Antibody": "Reactive",
                    "Hepatitis C": "Non-reactive"
                }
        else:
            return {
                "Hepatitis A": "Non-reactive",
                "Hepatitis B Surface Antibody": "Non-reactive",
                "Hepatitis B Core Antibody": "Non-reactive", 
                "Hepatitis C": "Non-reactive"
            }
        

    def generate_calcium_level(self, age, gender, conditions):

        return {"Calcium": f"{round(random.uniform(8.6, 10.2), 1)} mg/dL"}

    def generate_inflammatory_markers(self, age, gender, conditions):

        return {
            "CRP": f"{round(random.uniform(0.1, 3.0), 1)} mg/L",
            "ESR": f"{random.randint(5, 25)} mm/hr"
        }

    def generate_bnp(self, age, gender, conditions):

        if any(c in conditions for c in ["Heart Failure"]):
            return {"BNP": f"{random.randint(400, 2000)} pg/mL"}
        
        return {"BNP": f"{random.randint(10, 100)} pg/mL"}

    def generate_vitamin_b12(self, age, gender, conditions):

        level = random.randint(200, 900)
        if any(c in conditions for c in ["Cognitive Impairment"]):
            level = random.randint(150, 300)  

        return {"Vitamin B12": f"{level} pg/mL"}



    def generate_default_result(self, age, gender, conditions):
        """
        Fallback for any unhandled test types
        """

        return {
            "Result": "Normal",
            "Status": "Completed",
            "Test Name": self.test_name
        }


    def calculate_egfr(self, creatinine, age, gender):
        """
        CKD-EPI 2021 creatinine equation.
        creatinine in mg/dL
        age in years
        gender is expected to be 'male' or 'female'
        """
        gender = gender.lower().strip()

        if gender == "female":
            k = 0.7
            a = -0.241
            sex_factor = 1.012
        else:
            k = 0.9
            a = -0.302
            sex_factor = 1.0

        egfr = 142 * (min(creatinine / k, 1) ** a) * (max(creatinine / k, 1) ** -1.200) * (0.9938 ** age) * sex_factor
        return round(egfr)