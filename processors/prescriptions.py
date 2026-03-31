import uuid
import random
# prescriptions get patient_id: uuid, medication: text, dose: text

import random
import uuid

class Prescriptions:

    def __init__(self, patient_id: uuid.UUID, patient_object):

        self.patient_id = patient_id
        self.patient = patient_object

        pdmp = getattr(self.patient, "pdmp", [])

        # if medication and dose are present and given by PDMP
        if pdmp:
            self.medication_entry = random.choice(pdmp)
            self.medication = self.parse_drug_string(self.medication_entry["drug"])[0]
            self.dose = self.generate_dose(self.medication_entry)
        else:
            # fallback for non-addictive or OTC meds
            otc_options = ["Vitamin C 500 mg", "Acetaminophen 500 mg", "Ibuprofen 200 mg"]
            med_str = random.choice(otc_options)
            self.medication = self.parse_drug_string(med_str)[0]
            self.dose = f"Take as directed"

    def parse_drug_string(self, drug_string):
        """
        helper method to parse a drug string into medication name and dosage.
        returns: (medication_name, dosage_string)
        """
        parts = drug_string.split()
        medication_parts = []
        dosage_parts = []
        found_dosage = False

        for part in parts:
            if any(char.isdigit() for char in part) or part.lower() in ['mg', 'mcg', 'units', 'iu', 'ml', '%']:
                found_dosage = True

            if found_dosage:
                dosage_parts.append(part)
            else:
                medication_parts.append(part)

        medication_name = " ".join(medication_parts) if medication_parts else drug_string
        dosage = " ".join(dosage_parts) if dosage_parts else ""

        return medication_name, dosage

    def generate_dose(self, pdmp_entry):
        """
        generate dosing instructions from a PDMP entry
        """
        drug = pdmp_entry.get("drug", "")
        _, dosage = self.parse_drug_string(drug)
        qty = pdmp_entry.get("qty", 1)
        days = pdmp_entry.get("days", 30)

        # Use the dose per day stored in PDMP if available
        dose_per_day, _ = self.patient.get_medication_info(drug, days)

        if dosage and dose_per_day:
            return f"Take {dosage} {dose_per_day} time(s) daily"
        elif dosage:
            return f"Take {dosage} as directed"
        else:
            return "Take as prescribed"
