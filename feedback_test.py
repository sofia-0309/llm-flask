import asyncio
from utils.evaluation.feedback import Feedback  

mock_data = {
    'patient': {
        'id': 'b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e',
        'name': 'Mary Williams',
        'date_of_birth': '1978-05-10',
        'age': 45,
        'gender': 'Female',
        'medical_condition': 'Hyperlipidemia',
        'medical_history': 'High cholesterol, overweight',
        'family_medical_history': 'Mother had hyperlipidemia',
        'surgical_history': 'None',
        'cholesterol': '260 mg/dL',
        'allergies': 'None',
        'patient_message': 'I am very concerned about my high cholesterol levels.',
        'pdmp': [{
            'date_filled': '1 month ago',
            'date_written': '1 month ago',
            'drug': 'Atorvastatin 40 mg',
            'qty': 30,
            'days': 30,
            'refill': 0
        }],
        'immunization': {'Influenza': '2023-11-01'},
        'height': '5 ft 6 inches',
        'weight': '150 lbs',
        'last_bp': '130/85 mmHg'
    },
    'results': [{
        'id': 'c3d4e5f6-2a3b-4c5d-6e7f-8091a2b3c4d5',
        'patient_id': 'b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e',
        'test_name': 'Lipid Panel',
        'test_date': '2025-03-01',
        'test_result': {
            'HDL': '38 mg/dL',
            'LDL': '165 mg/dL',
            'Total Cholesterol': '260 mg/dL',
            'Triglycerides': '210 mg/dL'
        },
        'patient': {'name': ''}
    }],
    'prescriptions': [{
        'id': 'd4b5c6a7-f5a6-4b7c-8d9e-0f1a2b3c4d5e',
        'patient_id': 'b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e',
        'medication': 'Atorvastatin',
        'dose': '40 mg once daily',
        'patient': {'name': 'Mary Williams'}
    }],
    'pdmp': [{
        'date_filled': '1 month ago',
        'date_written': '1 month ago',
        'drug': 'Atorvastatin 40 mg',
        'qty': 30,
        'days': 30,
        'refill': 0
    }],
    'task_type': 'patient_question',
    'mission': "Respond to the patient's message!",
    'student_refilled': False,
    'user_message': "Hello Mary, I understand your concerns about your cholesterol levels. Incorporating a heart-healthy diet, regular exercise, and weight management can further help in lowering your cholesterol levels. We will continue to monitor your progress closely."
}


async def test_feedback():
    feedback_instance = Feedback(mock_data)
    result = await feedback_instance.generate_answer()
    # print("\n--- Result ---")
    # print(result)


if __name__ == "__main__":
    asyncio.run(test_feedback())
