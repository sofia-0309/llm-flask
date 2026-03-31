import os
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client

# load .env 
load_dotenv()

# env vars
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# file paths
NHANES_PATH = os.getenv("NHANES_PATH", "NHANES.csv")
PATIENT_MESSAGE_PROMPT = os.getenv("PATIENT_MESSAGE_PROMPT", "prompts/generation/patient_message.txt")
LAB_RESULTS_PROMPT = os.getenv("LAB_RESULTS_PROMPT", "prompts/generation/lab_results.txt")

# openai client
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in .env")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# supabase client
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase config in .env")
supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
