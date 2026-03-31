from openai import AsyncOpenAI
import numpy as np
import os
from dotenv import load_dotenv
import json
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-large"
LLM_MODEL = "gpt-3.5-turbo"  
EMBEDDING_SIM_THRESHOLD = 0.85
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-10))

async def embedding_score(student_response, reference_answers):
    print("student:")
    print(student_response)
    sample_response = reference_answers
    print("ai:")
    print(sample_response)
    print("start embedd grading")
    student_emb = (await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=student_response
    )).data[0].embedding
    print("start loop")

    student_emb = (await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=student_response
    )).data[0].embedding

    sample_emb = (await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=sample_response
    )).data[0].embedding

    sim = cosine_similarity(student_emb, sample_emb)

    print("end embedd grading")

    return min(sim / EMBEDDING_SIM_THRESHOLD, 1.0) * 30

