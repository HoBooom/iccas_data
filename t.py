from dotenv import load_dotenv
import os

load_dotenv()
print("Loaded API KEY:", os.environ.get("GEMINI_API_KEY"))
