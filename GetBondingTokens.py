import os
import pandas as pd
import json
from dotenv import load_dotenv

import config

# Load environment variables from .env file
load_dotenv()

import requests

url = f"https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/bonding?limit={config.NewTokenCount}"

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

for i in range(0,5):
    url = f"https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/bonding?limit={config.NewTokenCount}&cursor={cursorUsed}"
    response = requests.request("GET", url, headers=headers)
    data = json.loads(response.text)
    df_add = pd.DataFrame(data['result'])
    list_of_dfs.append(df_add)
    cursorUsed = data['cursor']

final_df = pd.concat(list_of_dfs)
final_df = final_df.drop_duplicates()
final_df = final_df[~final_df['tokenAddress'].isna()]
final_df.to_csv('./IO_Files/TokensBondingDB.csv', index=False)

final_df['fullyDilutedValuation'] = final_df['fullyDilutedValuation'].astype('float')
filtered_final_df = final_df[(final_df['fullyDilutedValuation']>=15000) & (final_df['fullyDilutedValuation']<=36000)]

filtered_final_df['bondingCurveProgress'] = filtered_final_df['bondingCurveProgress'].astype('float')


