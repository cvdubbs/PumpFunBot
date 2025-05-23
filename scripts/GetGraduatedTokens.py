import os
import pandas as pd
import json

import sys
import os
# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import config

# Load environment variables from .env file
load_dotenv()

import requests

url = f"https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/graduated?limit={config.NewTokenCount}"

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

for i in range(0,750):
    url = f"https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/graduated?limit={config.NewTokenCount}&cursor={cursorUsed}"
    response = requests.request("GET", url, headers=headers)
    data = json.loads(response.text)
    df_add = pd.DataFrame(data['result'])
    list_of_dfs.append(df_add)
    cursorUsed = data['cursor']
    print(f'completed {i} iterations')

final_df = pd.concat(list_of_dfs)
final_df = final_df.drop_duplicates()
final_df = final_df[~final_df['tokenAddress'].isna()]
final_df.to_csv('./IO_Files/TokensGraduatedDB.csv', index=False)

final_df['fullyDilutedValuation'] = final_df['fullyDilutedValuation'].astype('float')
filtered_final_df = final_df[(final_df['fullyDilutedValuation']>=500000)]
filtered_final_df = filtered_final_df.sort_values(by='fullyDilutedValuation', ascending=False)


filtered_final_df.to_csv('./IO_Files/TokensBestOfBest.csv', index=False)

