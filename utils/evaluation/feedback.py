from jinja2 import Template
import os
import json
from openai import AsyncOpenAI
import asyncio
import time
from textblob import TextBlob
from collections import Counter
from utils.evaluation.grading.embeddings import embedding_score
from utils.evaluation.grading.llm_freeresponse import call_openai_for_evaluation

RULE_WEIGHT = 0.3
EMBEDDING_WEIGHT = 0.2
LLM_WEIGHT = 0.5
############################
def scoreToRating(score: float) -> str:
    if score >= 85:
        return "green"
    elif score >= 70:
        return "yellow"
    else:
        return 'red'
    ###############################
class Feedback:
    def __init__(self, data):

        # Init ai connection
        self.data = data
        key = os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=key)

    
    async def calculate_grade(self, full_json_str,student_response, desire_response):
            
        def aggregate_scores(rule_scores, embedding_score, llm_scores):

            # Average scores
           # llm_total = float(llm_scores.factual_accuracy) + float(llm_scores.clinical_reasoning) + float(llm_scores.communication_clarity)*0.5 + float(llm_scores.empathy)*0.5
          #  total_score = 100*(RULE_WEIGHT*rule_scores + EMBEDDING_WEIGHT*embedding_score + LLM_WEIGHT*llm_total )/(30*0.5+30*0.2+5*0.3)

            return {
                "rule_scores": rule_scores,
                "embedding_score": embedding_score,
                "llm_scores": llm_scores,
               # "total_score": total_score
            }
        

        # Run embeddings and llm intuitive PARALLELLL
        async def run_async_tasks():
            emb_task = embedding_score(student_response, desire_response)
            llm_task = call_openai_for_evaluation(full_json_str, student_response)
            emb_score, llm_scores = await asyncio.gather(emb_task, llm_task)
            return emb_score, llm_scores
        
        emb_score, llm_scores =  await run_async_tasks()

        result = aggregate_scores(5, emb_score, llm_scores)

        return result



            

    
    async def generate_answer(self):
        # print("ahahahahaha")

        # Load the data
        original_data = self.data
        print(original_data)
        feedback_type=original_data.get("feedbacktype")
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

        last_visit_date = None
        if "patient" in original_data and isinstance(original_data["patient"], dict):
            last_visit_date = original_data["patient"].get("last_visit_date")

        # 9) Base instructions added regardless of task type.
        base_instructions = (
            "You are replying to an EHR message from a patient who is under your care. You have to give your predictions with current limited data."
            "You are their primary healthcare provider. "
            "Your response should be professional, concise, patient-friendly, and authoritative. "
        )

        if last_visit_date:
            base_instructions += f"\nThe patient’s last recorded office visit was on {last_visit_date}. "\
                                "Factor this into your response — if it has been more than a year, "\
                                "recommend follow-up or an in-person evaluation before prescribing or refilling medication."
        else:
            base_instructions += "\nNo last visit date is recorded. You should recommend that the patient schedule an appointment if appropriate."

        universal_intro = f"""You must return
        No markdown, no bold text, no italics. Plain text only.
        Below is partial GIGA JSON (without user_message and, if task_type is not patient_question, without patient_message):
        {data_for_first_str}
        {base_instructions}
        """
        if mission_text:
            universal_intro += f"\nThe mission for this task is: {mission_text}\nEnsure your sample response adheres to this instruction."
        universal_intro += "\nCraft the sample response as if you were a medical student. Be concise, professional, and end quickly."

#####################################################
        # Task-specific instructions.
        if task_type == "patient_question":
            long_feedback=""" Write the message you would send to the patient in the EHR,
             Hard rules to follow:
             - 1 paragraph explaining overall feedback on the students response. Mention what they did good, 
             What they did medium right and what could use some help.
             - 1 paragraph that says wether the medical response was right(ie. the right diagnosing and treatment)
             - 1 paragraph about the style of the text(ie.could be nicer or not)
             - mention labs/tests if truly necessary.
             - If last visit was > 1 year ago, recommend scheduling a visit.
             - Also mention any labs that may need to be ordered for further information.

            If the patient’s message is related to mental health, include a disclaimer advising them to call 
            the Suicide & Crisis Lifeline at 988.
               """
            print("this is it")

            task_specific_part = """
            Write the message you would send to the patient in the EHR.

            Hard rules to follow:
            - 2 to 4 sentences total.
            - No greeting, no good byes.
            - Plain language (no medical jargon).
            - Include: what you think is going on, what to do next, 1-2 safety warnings if severe symptoms.
            - mention labs/tests if truly necessary.
            - If last visit was > 1 year ago, recommend scheduling a visit.
            - Add the word "updated" at the end

            Also mention any labs that may need to be ordered for further information.

            If the patient’s message is related to mental health, include a disclaimer advising them to call 
            the Suicide & Crisis Lifeline at 988.
            """
################################################################
        elif task_type == "lab_result":
            task_specific_part = """
            Provide a succinct interpretation of the lab results 
            and relevant next steps. No concluding phrases or farewells.
            """
        elif task_type == "prescription":
            task_specific_part = """
            Provide a concise plan for prescription changes, 
            refills, or dosage. (Note: the student_refilled field indicates if the prescription should be refilled: true means refill, false means not refill.)
            Avoid farewells or fluff.
            Evaluate and comment on the following points:
            - What monitoring (e.g., vitals, labs, or follow-up visits) is required prior to refilling the medication.
            - Whether the patient has had an office visit within the last year.
            - Whether any necessary lab work (such as renal, hepatic, or drug-level monitoring) is up to date.
            - Whether the requested medication is safe given the patient's other active medications, allergies, or comorbidities.
            - If any of these checks are missing, recommend appropriate next steps (e.g., scheduling an appointment, ordering labs).

            """
        else:
            task_specific_part = """
            Unknown task_type. Provide a concise, professional response with no concluding words or farewells.
            """

        first_paragraph = universal_intro + task_specific_part

        # Options for feedback type

        #Option 2:Communication focus
        option_2 =f""" 
 
        OUTPUT MUST BE EXACTLY THIS FORMAT:  

            Rating:
                - Provide ONE integer between 1 and 5 AND DONT ADD A SLASH(-) BEFORE THE NUMBER.
                - Rating of 1 demonstrates poor communication, dismissiveness, or lack of empathy.
                - Rating of 2 demonstrates minimal engagement with the patient’s concerns or very limited empathy.
                - Rating of 3 demonstrates clear communication but limited empathy, personalization, or patient-centeredness.
                - Rating of 4 demonstrates empathetic, patient-centered, and supportive communication.
                - Rating of 5 demonstrates highly empathetic, clear, validating, and patient-tailored communication.

                SPECIAL SCORING RULES:
                - If the message is extremely short, generic, or non‑clinical (e.g., “hey u good?”, “idk”, “AI bot?”) → Rating MUST be 1.
                - If the diagnosis is completely wrong BUT the tone is kind, respectful, or supportive → Rating should be 3.
                    * In this case, mention that bedside manner was strong but clinical accuracy was incorrect.
                - If the message is excellent in tone AND clinically appropriate → Rating can be 4 or 5.
                - Do NOT lower the communication score just because the medical reasoning is wrong unless the tone is also dismissive or unclear.

            Strengths:
                - Provide EXACTLY 2 bullet points.
                - Each bullet must be one sentence.
                - Focus ONLY on clarity, empathy, tone, and patient-centered communication.
                - Highlight things like:
                    * clear explanations
                    * supportive or reassuring language
                    * addressing the patient’s specific concerns
                    * validating feelings
                    * appropriate tone and word choice

            Improvements:
                - Provide EXACTLY 3 bullet points.
                - Each bullet must be one actionable COMMUNICATION or MANNERS improvement.
                - Be specific and behavior-based (what the student should say or do differently).
                - Focus on:
                    * improving clarity or structure
                    * increasing empathy or validation
                    * avoiding abrupt, confusing, or dismissive language

        Hard rules:
            - Don't add a slash before the rating.
            - Don't advise students to do something they already mentioned in their message.
            - FOCUS ONLY on communication strengths and improvements.
            - If the message is good, you do NOT need to force negative feedback.


            """
        #Diagnosis focus

        option_3 = f""" 
        OUTPUT MUST BE EXACTLY THIS FORMAT:
        
            Rating:
                - Provide ONE integer between 1 and 5 AND DONT ADD A SLASH(-) BEFORE THE NUMBER.
                - Rating of 1 demonstrates incorrect or unsafe medical reasoning with failure to recognize the primary problem.
                - Rating of 2 demonstrates partially correct reasoning but misses the main diagnosis or gives inappropriate management.
                - Rating of 3 demonstrates generally correct reasoning but lacks completeness in evaluation or next steps.
                - Rating of 4 demonstrates strong clinical reasoning with correct identification of the main issue and appropriate management.
                - Rating of 5 demonstrates excellent, thorough, and safe clinical reasoning including accurate diagnosis, risk assessment, and appropriate next steps.
             
             
            Strengths:
            - Provide EXACTLY 2 bullet points.
            - Each bullet must be one sentence.
            - Focus on medical accuracy, clinical reasoning, and patient safety.
            - Highlight if the student appropriately:
                * considered relevant diagnoses
                * checked or mentioned medical history
                * evaluated vital signs if applicable
                * recommended appropriate labs/tests when needed
                * correctly determined if a doctor visit is or is not necessary

             Improvements:
            - Provide EXACTLY 3 bullet points.
            - Each bullet must be one actionable improvement.
            - Be specific and clinically oriented.


           

        CRITICAL SCORING RULES:

        - If the primary diagnosis is incorrect OR the main patient concern is misidentified → MAX rating is 2.
        - If the response ignores a key red flag symptom (e.g., non-healing wound, worsening SOB, infection signs) → MAX rating is 2.
        - If treatment is inappropriate for the condition (e.g., antihistamines for pressure ulcer) → MAX rating is 2.
        - A response CANNOT receive a 4 or 5 unless the main diagnosis/problem is correctly identified.
        - Mentioning a plausible but incorrect diagnosis does NOT count as correct reasoning.
        - Safety and correct prioritization are more important than completeness.

        

        Hard rules:

        - Don't add a slash before the rating.
        - Don't advise students to do something they already mentioned in their message.
        - Focus ONLY on medical correctness, clinical reasoning, and appropriateness of next steps.
        - Do NOT mention empathy, tone, or bedside manner.
        - Ensure recommendations (labs, imaging, referrals, medications) are appropriate to the scenario and not excessive.
        - A doctor visit should only be recommended when clinically justified, not by default.
        - Good medical reasoning but wrong diagnosis can not have more than a rating of 2
        - If the message has a rating of 5  you dont need to look for something bad in it.

        
        

            """
        
     
    
        intro_second =f"""
            You are grading a student's EHR reply. Return ONLY the feedback text.

            Comprehensive patient information:
            {full_json_str}

            Student response:
            "{user_message}"

            OUTPUT MUST BE EXACTLY THIS FORMAT:
        """

        default_part = f""" 
        Default option: 

        Top Issues:
        - exactly 3 bullets, less than or equal to 10 words each

        Fix:
        (1-2 sentences max, no greeting, no good bye)

        Questions you should think about asking:
        - 0-3 bullets, less than or equal 10 words each

        Hard rules:
        - No explanations, no praise paragraphs.
        - No restating patient info unless essential for safety.
        - Use simple words (no extra vocab student or patient might not understand).
        - Total length <= 90 words.
        ---"""

        task_specific_part2=f"""
        Task-Specific Feedback Guidance:

        • If this is a **lab result** task:
            - Provide your feedback in **bullet point format**, with each point on a new line.
            - Focus on whether the student's interpretation of the lab findings is clinically sound, clear, and concise.
            - Mention if they addressed the implications of abnormal values and proposed reasonable next steps (follow-up, monitoring, or additional testing).
            - Avoid restating lab numbers unless directly relevant to the critique.

        • If this is a **prescription** or **refill** task:
            - Provide your feedback in **bullet point format**, with each point on a new line.
            - Assess whether the student correctly decided to refill or modify the prescription.
            - Address the following clinical safety considerations:
                - Whether appropriate monitoring (vitals, labs, or follow-up visits) was considered before refilling.
                - Whether the patient has had a recent office visit (within the past year).
                - Whether relevant lab work or drug-level monitoring is up to date.
                - Whether the medication appears safe given the patient's other active medications, allergies, and comorbidities.
                - If any of these are missing, recommend the appropriate next steps (e.g., scheduling an appointment or ordering labs).

        • If this is a **patient message** task:
            - Provide your feedback as a single concise paragraph.
            - Evaluate the clarity, correctness, and completeness of the student's response.
            - Additionally, assess whether suggesting any of the following **orders or referrals** would have been appropriate given the context:
            - Labs and tests (e.g., Thyroid Stimulating Hormone, CBC, CMP, Lipid Panel, Hemoglobin A1C, Urinalysis, CRP, Vitamin D/B12, etc.)
            - Imaging studies (e.g., Chest X-ray, MRI, Ultrasound, CT Scan)
            - Specialist referrals (e.g., Cardiology, Endocrinology, Psychiatry, Gastroenterology)
            - Preventive care (e.g., vaccinations, screenings, counseling programs)
            - Therapies or medications (e.g., antibiotics, antihypertensives, bronchodilators, statins, antidepressants)
            - Only comment on orders if they are directly relevant to the patient’s situation. Do not suggest unrelated tests or treatments.

        ---

        Always:
        - Be specific about what the student did well and what could be improved.
        - Do not create new orders or diagnoses that are not implied by the student's response or the patient’s case.
        - Keep all feedback concise and instructional.

        Here is the comprehensive patient information:
        {full_json_str}

        The student's response was: "{user_message}"

        Explain what might be missing or unclear, and how to improve clarity, correctness, or completeness.
        Do not provide a sample response.

        Important: If the task is a lab result or prescription, provide feedback in **bullet point** format with each bullet on a new line

         """
        # Different feedback options according to user's prefernces
        if feedback_type=="default":
            second_paragraph = intro_second + default_part + task_specific_part2
        elif feedback_type=="communication-focused":
            second_paragraph = intro_second + option_2 + task_specific_part2

        elif feedback_type=="diagnosis-focused":
            second_paragraph = intro_second + option_3 + task_specific_part2
        elif feedback_type=="sensitivity-focused":
            second_paragraph = intro_second + option_4 + task_specific_part2

        else:
            second_paragraph = intro_second + default_part + task_specific_part2


            

        # 8) Build the prompt for feedback, referring to the complete JSON as "comprehensive patient information".
        # second_paragraph = med_response
       # second_paragraph = intro_second + option_4 + task_specific_part2

        async def call_openai_for_feedback(prompt):
            try:
                completion = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": "You are a doctor."},
                              {"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=600,
                )
                return completion.choices[0].message.content
            except Exception as e:
                return {"error": str(e)}
            
        start = time.perf_counter()

        # Adding task to be done concurrently
        first_paragraph_task = asyncio.create_task(call_openai_for_feedback(first_paragraph))
        second_paragraph_task = asyncio.create_task(call_openai_for_feedback(second_paragraph))
        

        # Calling task PARALLELLL
        first_response, second_response = await asyncio.gather(first_paragraph_task, second_paragraph_task)

        end = time.perf_counter()    
        grade = await self.calculate_grade(full_json_str,user_message,first_response)
        #totalScore = float(grade["total_score"])
       # rating = scoreToRating(totalScore)
        print("Feedback: ")
        print(second_response)
        # print(f"Grade:")
        # print(f"Rubric: {grade['rule_scores']}")
        # print(f"Grade: {grade['llm_scores']}")
        # print(f"Embeddings: {grade['embedding_score']/30}")
        # print(f"Total scores: {grade['total_score']:.1f}/100")

        
        return {
            "sample_response": first_response,
            "feedback_response": second_response,
            #"response_score": round(totalScore, 1),
            #"response_rating": rating,
        }

                
            