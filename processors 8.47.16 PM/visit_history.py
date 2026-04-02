import random
from datetime import datetime, timedelta
from config import openai_client

class VisitHistoryGenerator:
    """
    Generates realistic visit history for patients based on their medical condition,
    age, and medical history.
    """
    
    def __init__(self, patient):
        self.patient = patient
        self.current_year = datetime.now().year
        self.birth_year = int(patient.dob.split('-')[0])
    
    def generate_visit_history(self):
        """
        Returns a list of 2-5 past visits with realistic dates, types, and clinical notes.
        """
        visits = []
        
        # Determine number of visits based on age and medical complexity
        num_visits = self._determine_num_visits()
        
        # Generate visit dates (spread out)
        visit_dates = self._generate_visit_dates(num_visits)
        
        # Generate each visit
        for i, visit_date in enumerate(visit_dates):
            visit_type = self._determine_visit_type(i, num_visits)
            clinical_notes = self._generate_clinical_notes(visit_date, visit_type, i)
            
            visits.append({
                "visit_date": visit_date.isoformat(),
                "visit_type": visit_type,
                "clinical_notes": clinical_notes,
                "provider_id": None  # Will be set by backend if needed
            })
        
        return visits
    
    def _determine_num_visits(self):
        """Determine realistic number of past visits based on patient factors."""
        age = self.patient.age
        num_conditions = len([c for c in self.patient.medical_condition 
                              if c != "No significant medical conditions"])
        
        if age < 2:
            return random.randint(4, 6)  # Frequent infant checkups
        elif age < 12:
            return random.randint(2, 4)  # Regular pediatric visits
        elif age < 18:
            return random.randint(1, 3)  # Fewer teen visits
        elif age < 65:
            if num_conditions >= 3:
                return random.randint(3, 5)  # More visits if complex
            else:
                return random.randint(2, 3)  # Typical adult visits
        else:
            return random.randint(3, 5)  # More frequent for elderly
    
    def _generate_visit_dates(self, num_visits):
        """Generate realistic past visit dates."""
        today = datetime.now()
        dates = []
        
        # Most recent visit (within last 1-6 months)
        most_recent = today - timedelta(days=random.randint(30, 180))
        dates.append(most_recent)
        
        # Spread out remaining visits over past 1-3 years
        for i in range(1, num_visits):
            # Each visit goes further back
            days_back = random.randint(90 + (i * 60), 180 + (i * 120))
            visit_date = today - timedelta(days=days_back)
            dates.append(visit_date)
        
        # Sort by date (newest first)
        dates.sort(reverse=True)
        return dates
    
    def _determine_visit_type(self, visit_index, total_visits):
        """Determine visit type based on position in visit history."""
        visit_types = {
            "Annual Checkup": 0.4,
            "Follow-up Visit": 0.3,
            "Urgent Care": 0.15,
            "Consultation": 0.1,
            "Emergency Visit": 0.05
        }
        
        # Most recent visit more likely to be follow-up
        if visit_index == 0:
            visit_types["Follow-up Visit"] = 0.5
            visit_types["Annual Checkup"] = 0.3
        
        # Older visits more likely to be annual checkups
        if visit_index == total_visits - 1:
            visit_types["Annual Checkup"] = 0.6
        
        # Choose weighted random visit type
        types = list(visit_types.keys())
        weights = list(visit_types.values())
        return random.choices(types, weights=weights)[0]
    
    def _generate_clinical_notes(self, visit_date, visit_type, visit_index):
        """Use AI to generate realistic clinical notes."""
        
        
        conditions_str = ", ".join(self.patient.medical_condition)
        history_str = ", ".join(self.patient.medical_history) if hasattr(self.patient, 'medical_history') else "None"
        
        prompt = f"""Generate realistic clinical notes for a patient visit.

Patient Information:
- Age: {self.patient.age}
- Gender: {self.patient.gender}
- Current Conditions: {conditions_str}
- Medical History: {history_str}
- Visit Date: {visit_date.strftime('%B %d, %Y')}
- Visit Type: {visit_type}

Instructions:
- Write 2-4 sentences of clinical documentation
- Use appropriate medical terminology
- Include vitals if relevant (BP, HR, etc.)
- Mention relevant symptoms, findings, or recommendations
- Keep it realistic and concise
- Do NOT include patient name or provider name
- Write in past tense as if documenting after the visit

Example format: "Patient presented for [reason]. [Physical findings]. [Assessment]. [Plan/recommendations]."

Clinical Notes:"""

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a medical professional documenting a patient visit. Write concise, realistic clinical notes."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            notes = response.choices[0].message.content.strip()
            return notes
            
        except Exception as e:
            print(f"Error generating clinical notes: {e}")
            # Fallback to template-based notes
            return self._generate_fallback_notes(visit_type)
    
    def _generate_fallback_notes(self, visit_type):
        """Generate simple template notes if AI fails."""
        templates = {
            "Annual Checkup": f"Patient presented for routine annual physical exam. Blood pressure {self.patient.last_bp}. General health discussed. No acute concerns noted. Routine labs ordered.",
            "Follow-up Visit": f"Follow-up visit for ongoing condition management. Patient reports stable symptoms. Vitals within normal limits. Continue current treatment plan.",
            "Urgent Care": f"Patient presented with acute complaint. Physical examination completed. Treatment provided and patient counseled on symptoms to monitor.",
            "Consultation": f"Consultation visit for specialty evaluation. History reviewed. Assessment and recommendations discussed with patient.",
            "Emergency Visit": f"Emergency presentation. Immediate assessment and treatment provided. Patient stable at discharge with follow-up instructions."
        }
        return templates.get(visit_type, "Standard visit completed. Patient evaluated and counseled.")