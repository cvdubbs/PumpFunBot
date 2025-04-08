import os
import pandas as pd
import json
from dotenv import load_dotenv

import config

# Load environment variables from .env file
load_dotenv()

import requests

ca = "2B14yZAipoEryj6p3JN26g8jAEzNZmD7KdxPBEHspump"

url = "https://solana-gateway.moralis.io/token/mainnet/{ca}/metadata"

headers = {
  "Accept": "application/json",
  "X-API-Key": os.getenv("MORALIS_API_KEY")
}

response = requests.request("GET", url, headers=headers)

print(response.text)
