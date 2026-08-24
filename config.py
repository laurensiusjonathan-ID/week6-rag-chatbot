import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.environ["API_KEY"]
MODEL = "glm-4.7"
BASE_URL_ANTHROPIC = os.environ.get("BASE_URL_ANTHROPIC")
BASE_URL_OPENAI = os.environ.get("BASE_URL_OPENAI")