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

list_of_dfs = list()

response = requests.request("GET", url, headers=headers)
data = json.loads(response.text)
df_add = pd.DataFrame(data['result'])
list_of_dfs.append(df_add)
cursorUsed = data['cursor']

for i in range(0,20):
    url = f"https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/new?limit={config.NewTokenCount}&cursor={cursorUsed}"
    response = requests.request("GET", url, headers=headers)
    data = json.loads(response.text)
    df_add = pd.DataFrame(data['result'])
    list_of_dfs.append(df_add)
    cursorUsed = data['cursor']

final_df = pd.concat(list_of_dfs)
final_df = final_df.drop_duplicates()
final_df = final_df[~final_df['tokenAddress'].isna()]
final_df.to_csv('./IO_Files/TokensDB.csv', index=False)
