import os
import pandas as pd
import json
from dotenv import load_dotenv

import config

# Load environment variables from .env file
load_dotenv()

import requests

# url = f"https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/new?limit={config.NewTokenCount}"

# headers = {
#   "Accept": "application/json",
#   "X-API-Key": os.getenv("MORALIS_API_KEY")
# }

# response = requests.request("GET", url, headers=headers)

tokens_db = pd.read_csv('./IO_Files/TokensDB.csv')

