import random
from config import STAFF_MESSAGE_PROMPT, openai_client


class StaffMessage:
    def __init__(self, patient_id, name, role, specialty, staff_message, profile_picture):
        self.patient_id = patient_id
        self.name = name
        self.role = role
        self.specialty = specialty
        self.staff_message = staff_message
        self.profile_picture = profile_picture

class PatientContext:
    def __init__(self, name, age, chief_complaint, medical_condition, medical_history, surgical_history):
        self.name = name
        self.age = age
        self.chief_complaint = chief_complaint
        self.medical_condition = medical_condition
        self.medical_history = medical_history
        self.surgical_history = surgical_history

class StaffGenerator:
    def __init__(self, patient, patient_id=None):
        self.patient = patient
        # store patient id if provided
        self.patient_id = patient_id

    def from_patient_record(self, data):

        # helper function to convert values into lists
        def to_list(value):

            # check if value is missing
            if value == None:
                return []

            text = str(value)

            # split string into parts
            parts = text.split(",")

            result = []
            for i in parts:
                item = i.strip()
                if item != "":
                    result.append(item)
            return result


        # get chief concern section
        chief = data.get("chief_concern")
        if chief == None:
            chief = {}
        # get chief complaint field
        chief_list = chief.get("chief_complaint")
        if chief_list == None:
            chief_list = []

        # convert complaint into list if needed
        if type(chief_list) != list:
            temp = []
            temp.append(str(chief_list))
            chief_list = temp


        # build patient context object
        patient = PatientContext(
            name=data.get("name") or "Patient",
            age=data.get("age") or data.get("date_of_birth") or "unknown",
            chief_complaint=chief_list,
            medical_condition=to_list(data.get("medical_condition")),
            medical_history=to_list(data.get("medical_history")),
            surgical_history=to_list(data.get("surgical_history")),
        )
        return patient


    def _pick_staff_role(self, role=None):

        # define role options
        data = {}
        data["Surgeon"] = [("Surgeon", "Surgery")]
        data["PT"] = [("PT", "Physical Therapy")]
        data["Nurse"] = [("Nurse", "Nursing")]

        # did a role get passed in
        if role in data:

            options = data[role]

            result = random.choice(options)

            return result


        # build list of all available roles
        all_options = []

        val = data.values()

        for i in val:
            for j in i:
                all_options.append(j)

        # choose a random role
        result = random.choice(all_options)
        return result


    def _build_prompt(self, staff_role, staff_specialty):

        # open prompt template file
        file = open(STAFF_MESSAGE_PROMPT, "r")
        template = file.read()
        file.close()

        # build the prompt
        prompt = template.format(
            patient_name=self.patient.name,
            age=self.patient.age,
            chief_complaint=", ".join(self.patient.chief_complaint),
            medical_conditions=", ".join(self.patient.medical_condition),
            history=", ".join(self.patient.medical_history),
            surgeries=", ".join(self.patient.surgical_history),
            staff_role=staff_role,
            staff_specialty=staff_specialty,
        )
        return prompt


    def _generate_message(self, staff_role, staff_specialty):
        # build prompt
        prompt = self._build_prompt(staff_role, staff_specialty)

        # send prompt to openai
        resp = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                "role": "system", "content": "You are a hospital staff member writing a brief EHR message."
                },
                {"role": "user", "content": prompt },],
            max_tokens=300, temperature=0.7,
        )

        # extract message text
        text = resp.choices[0].message.content
        text = text.strip()
        return text


    def _build_staff_name(self, role, specialty):
        # map role to suffix
        suffix_map = {}
        suffix_map["Surgeon"] = "MD"
        suffix_map["Nurse"] = "RN"
        suffix_map["PT"] = "DPT"
        suffix = suffix_map.get(role)

        if suffix == None:
            suffix = ""

        # most common dr names
        first_names = ["John", "David", "Michael", "Robert", "Jennifer", "Mark", "Kylie"]
        last_names = ["Patel", "Garcia", "Smith", "Johnson", "Lee", "Martinez", "Brown"]

        # pick names
        first = random.choice(first_names)
        last = random.choice(last_names)
        name = "{} {}".format(first, last)

        # add suffix if needed
        if suffix != "":
            name = "{}, {}".format(name, suffix)
        return name

    def generate_and_upload(self, uploader, role=None):
        # choose staff role
        role_data = self._pick_staff_role(role)
        staff_role = role_data[0]
        staff_specialty = role_data[1]

        # generate staff name
        name = self._build_staff_name(staff_role, staff_specialty)
        # generate message text
        staff_message = self._generate_message(staff_role, staff_specialty)
        # build staff the record
        data = StaffMessage(
            patient_id=self.patient_id or "", name=name, role=staff_role, specialty=staff_specialty, staff_message=staff_message, profile_picture=None,
        )
        # upload record
        resp = uploader.upload_staff_message(data)

        # build response
        fin = {}
        fin["status"] = resp.get("status")
        fin["staff_id"] = resp.get("staff_id")
        fin["message"] = "Staff message generated and uploaded"
        return fin


    def generate_and_upload_batch(self, uploader, count=2):
        # store results
        res = []
        # default roles
        roles = ["Surgeon", "PT", "Nurse"]

        # determine which roles to generate
        if count <= len(roles):
            selected_roles = roles[:count]
        else:
            selected_roles = roles
            extra = count - len(roles)
            for i in range(extra):
                selected_roles.append(None)

        # generate messages
        for i in selected_roles:
            resp = self.generate_and_upload(uploader, role=i)
            res.append(resp)
        return res
