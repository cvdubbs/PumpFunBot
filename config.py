import os
from dotenv import load_dotenv
load_dotenv()

headers = {
  "Accept": "application/json",
  "X-API-Key": os.getenv("MORALIS_API_KEY")
}

# Current API Max is 100
NewTokenCount = 100
