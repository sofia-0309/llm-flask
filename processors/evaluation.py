from utils.evaluation.explain import Explanation
from utils.evaluation.feedback import Feedback
import asyncio

def run_evaluation(task_type, data):

    # Checking task type to redirect
    if task_type == "patient_question" or task_type == "staff_message" or task_type =="lab_result" or task_type == "prescription":
        print("pick up task type: "+ task_type)
        feedback = Feedback(data)
        response = asyncio.run(feedback.generate_answer())
    elif task_type == "explain" or task_type =="follow":
        print("Enter explain")
        print(data)
        worker = Explanation(data)
        print("Exit explain")
        response = worker.generate_answer()
    elif task_type == "analyze":
        feedback = Feedback(data)
        response = asyncio.run(feedback.generate_answer())
    else:
        worker = Feedback(data)
        response = worker.generate_answer()

    
    return response