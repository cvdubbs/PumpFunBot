import os
import pandas as pd
import json
from dotenv import load_dotenv
from moralis import sol_api

import config

# Load environment variables from .env file
load_dotenv()

import requests

def get_hist_new_tokens(loops = 50):
  headers = {
    "Accept": "application/json",
    "X-API-Key": os.getenv("MORALIS_API_KEY")
  }

  list_of_dfs = list()

  response = requests.request("GET", config.moralis_url, headers=headers)
  data = json.loads(response.text)
  df_add = pd.DataFrame(data['result'])
  list_of_dfs.append(df_add)
  cursorUsed = data['cursor']

  for i in range(0,loops):
      url = f"{config.moralis_url}&cursor={cursorUsed}"
      response = requests.request("GET", url, headers=headers)
      data = json.loads(response.text)
      df_add = pd.DataFrame(data['result'])
      list_of_dfs.append(df_add)
      cursorUsed = data['cursor']

  final_df = pd.concat(list_of_dfs)
  final_df = final_df.drop_duplicates()
  final_df = final_df[~final_df['tokenAddress'].isna()]
  final_df.to_csv('./IO_Files/TokensDB.csv', index=False)

  final_df['fullyDilutedValuation'] = final_df['fullyDilutedValuation'].astype('float')
  return final_df


def get_bonding_tokens() -> pd.DataFrame:
  headers = {
    "Accept": "application/json",
    "X-API-Key": os.getenv("MORALIS_API_KEY")
  }

  list_of_dfs = list()

  response = requests.request("GET", config.moralis_bonding_url, headers=headers)
  data = json.loads(response.text)
  df_add = pd.DataFrame(data['result'])
  list_of_dfs.append(df_add)
  cursorUsed = data['cursor']
  try:
    for i in range(0,5):
        url = f"https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/bonding?limit={config.NewTokenCount}&cursor={cursorUsed}"
        response = requests.request("GET", url, headers=headers)
        data = json.loads(response.text)
        df_add = pd.DataFrame(data['result'])
        list_of_dfs.append(df_add)
        cursorUsed = data['cursor']
  except:
      print("Error in Get Bonding Tokens Moralis")
  final_df = pd.concat(list_of_dfs)
  final_df = final_df.drop_duplicates()
  final_df = final_df[~final_df['tokenAddress'].isna()]
  # final_df.to_csv('./IO_Files/TokensBondingDB.csv', index=False)

  final_df['fullyDilutedValuation'] = final_df['fullyDilutedValuation'].astype('float')
  return final_df



def get_new_tokens():
  headers = {
    "Accept": "application/json",
    "X-API-Key": os.getenv("MORALIS_API_KEY")
  }

  list_of_dfs = list()

  response = requests.request("GET", config.moralis_url, headers=headers)
  data = json.loads(response.text)
  df_add = pd.DataFrame(data['result'])
  list_of_dfs.append(df_add)
  cursorUsed = data['cursor']
  try:
    for i in range(0,3):
        url = f"{config.moralis_url}&cursor={cursorUsed}"
        response = requests.request("GET", url, headers=headers)
        data = json.loads(response.text)
        df_add = pd.DataFrame(data['result'])
        list_of_dfs.append(df_add)
        cursorUsed = data['cursor']
  except:
     print("Error in Get New Tokens Moralis")
  final_df = pd.concat(list_of_dfs)
  final_df = final_df.drop_duplicates()
  final_df = final_df[~final_df['tokenAddress'].isna()]

  final_df['fullyDilutedValuation'] = final_df['fullyDilutedValuation'].astype('float')
  return final_df


def get_token_analytics(tokenAddress: str):
  headers = {
    "Accept": "application/json",
    "X-API-Key": os.getenv("MORALIS_API_KEY")
  }
  url = f"https://deep-index.moralis.io/api/v2.2/tokens/{tokenAddress}/analytics?chain=solana"

  response = requests.request("GET", url, headers=headers)
  return json.loads(response.text)


def get_token_price(tokenAddress: str):
  params = {
    "network": "mainnet",
    "address": tokenAddress
  }

  result = sol_api.token.get_token_price(
    api_key=os.getenv("MORALIS_API_KEY"),
    params=params,
  )

  return result


def get_pumpfun_marketcap(tokenAddress: str):
  result = get_token_price(tokenAddress)
  return result['usdPrice'] * 1000000000


def alpha_pos_5min(tokenAddress: str):
  analytics = get_token_analytics(tokenAddress)
  net_vol_5min = analytics['totalBuyVolume']['5m'] - analytics['totalSellVolume']['5m']
  return net_vol_5min

