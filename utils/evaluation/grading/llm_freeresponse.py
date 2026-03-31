from openai import OpenAI
from flask import Flask, jsonify
import time
import os
from jinja2 import Template
from pydantic import BaseModel
from openai import AsyncOpenAI


key = os.getenv("OPENAI_API_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..",'..'))  
prompt_path = os.path.join(ROOT_DIR, "prompts", "evaluation", "feedback.txt")
with open(prompt_path, "r") as file:
    prompt_str = file.read()
prompt = Template(prompt_str)

async def call_openai_for_evaluation(case, answer):
    print("start intuitive grading")
    key = os.getenv("OPENAI_API_KEY")
    client = AsyncOpenAI(api_key=key)
    
    class Rate(BaseModel):
        performance: str
        factual_accuracy: str
        clinical_reasoning: str
        communication_clarity: str
        empathy: str



    prompt = f"""
    Given the following situation and the response, 
    provide a detail feedback

    Scenarios:
    { case }

    Student response:
    { answer }


    Instructions:
    - Provide a general performance grading: Very Poor, Poor, Below Average, Fair, Average, Good, Very Good, Excellent.
    - Review the student’s response and rate: Factual accuracy (0-10), Clinical reasoning (0–10), Communication clarity (0–10), Empathy (0–10)
        """

    try:
        response = await client.responses.parse(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": "You are an expert in grading. You should answer in the given structure"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_output_tokens=800,
            text_format=Rate
        )

        question = response.output_parsed
        print("end intuitive grading")

        return question
    except Exception as e:
            return f"Error generating feedback {e}"
    

    