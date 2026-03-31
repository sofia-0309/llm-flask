from openai import OpenAI
from flask import Flask, jsonify
import time
import os

key = os.getenv("OPENAI_API_KEY")


def call_openai_for_evaluation(prompt: str = None,conversation_history: list = None):
    
    client = OpenAI(
        api_key = key,
                
    )
    backoff_count = 3
    count = 0
    print("haha", flush=True)
    print(prompt)

    system_msg = {
        "role": "system",
        "content": (
            "You are an expert in medicine and a medical professor who explains "
            "concepts clearly and in detail. You scored maximum marks in all USMLE exams."
        ),
    }

    if conversation_history:
        messages = [system_msg] + conversation_history
    elif prompt:
        messages = [system_msg, {"role": "user", "content": prompt}]

    while True:
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.2,
                max_tokens=400,


            )
            
            evaluation = completion.choices[0].message.content
            response_json = {
                "engine": "evaluation",
                "task_type": "explain",
                "output": {
                    "content": evaluation
                }
            }

            return response_json

        except Exception as e:
            count+=1
            if count > backoff_count:
                return {"error": str(e)}
            time.sleep(2)
