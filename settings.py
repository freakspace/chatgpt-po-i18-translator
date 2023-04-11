import os
import sys
from dotenv import load_dotenv

import openai

load_dotenv()

api_key = os.getenv("OPENAPI_KEY")

if not api_key:
    print("No api key found in environment")
    sys.exit()
else:
    openai.api_key = os.environ.get("OPENAPI_KEY")