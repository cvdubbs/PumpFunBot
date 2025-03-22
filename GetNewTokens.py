import os
import pandas as pd
import json
from dotenv import load_dotenv

import config

# Load environment variables from .env file
load_dotenv()

import requests

url = f"https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/new?limit={config.NewTokenCount}"

headers = {
  "Accept": "application/json",
  "X-API-Key": os.getenv("MORALIS_API_KEY")
}

response = requests.request("GET", url, headers=headers)

tokens_db = pd.read_csv('./IO_Files/TokensDB.csv')
data = json.loads(response.text)
df = pd.DataFrame(data['result'])
df = df[~df['tokenAddress'].isin(tokens_db['tokenAddress'].to_list())]
df.to_csv('./IO_Files/NewTokens.csv', index=False)
df.to_csv('./IO_Files/TokensDB.csv', mode='a', header=False, index=False)
print(df)
