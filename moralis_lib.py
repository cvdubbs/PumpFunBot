import os
from datetime import datetime, timedelta
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

    try:
        # Initial request
        response = requests.request("GET", config.moralis_url, headers=headers)
        data = json.loads(response.text)
        df_add = pd.DataFrame(data['result'])
        list_of_dfs.append(df_add)
        cursorUsed = data['cursor']
        
        # Process additional pages
        for i in range(0, 3):
            try:
                url = f"{config.moralis_url}&cursor={cursorUsed}"
                response = requests.request("GET", url, headers=headers)
                data = json.loads(response.text)
                df_add = pd.DataFrame(data['result'])
                list_of_dfs.append(df_add)
                cursorUsed = data['cursor']
            except Exception as e:
                print(f"Error in page {i+1} fetch: {str(e)}")
                # Continue to the next iteration instead of breaking completely
                continue
    
    except Exception as e:
        print(f"Error in initial Moralis request: {str(e)}")
    
    # Even if we had errors, try to process whatever data we did manage to collect
    if list_of_dfs:
        try:
            final_df = pd.concat(list_of_dfs)
            final_df = final_df.drop_duplicates()
            final_df = final_df[~final_df['tokenAddress'].isna()]
            final_df['fullyDilutedValuation'] = final_df['fullyDilutedValuation'].astype('float')
            return final_df
        except Exception as e:
            print(f"Error in processing collected data: {str(e)}")
            # Return whatever we can
            if list_of_dfs:
                return pd.concat(list_of_dfs)
    
    # If all else fails, return an empty DataFrame with expected columns
    return pd.DataFrame(columns=['tokenAddress', 'fullyDilutedValuation'])


#### OLD VERSION OF FUNCTION
# def get_new_tokens():
#   headers = {
#     "Accept": "application/json",
#     "X-API-Key": os.getenv("MORALIS_API_KEY")
#   }

#   list_of_dfs = list()

#   response = requests.request("GET", config.moralis_url, headers=headers)
#   data = json.loads(response.text)
#   df_add = pd.DataFrame(data['result'])
#   list_of_dfs.append(df_add)
#   cursorUsed = data['cursor']
#   try:
#     for i in range(0,3):
#         url = f"{config.moralis_url}&cursor={cursorUsed}"
#         response = requests.request("GET", url, headers=headers)
#         data = json.loads(response.text)
#         df_add = pd.DataFrame(data['result'])
#         list_of_dfs.append(df_add)
#         cursorUsed = data['cursor']
#   except:
#      print("Error in Get New Tokens Moralis")
#   final_df = pd.concat(list_of_dfs)
#   final_df = final_df.drop_duplicates()
#   final_df = final_df[~final_df['tokenAddress'].isna()]

#   final_df['fullyDilutedValuation'] = final_df['fullyDilutedValuation'].astype('float')
#   return final_df


def get_token_analytics(tokenAddress: str):
  headers = {
    "Accept": "application/json",
    "X-API-Key": os.getenv("MORALIS_API_KEY")
  }
  url = f"https://deep-index.moralis.io/api/v2.2/tokens/{tokenAddress}/analytics?chain=solana"

  response = requests.request("GET", url, headers=headers)
  return json.loads(response.text)


def get_token_holder_analytics(tokenAddress: str):
  headers = {
    "Accept": "application/json",
    "X-API-Key": os.getenv("MORALIS_API_KEY")
  }
  url = f"https://solana-gateway.moralis.io/token/mainnet/holders/{tokenAddress}"

  response = requests.request("GET", url, headers=headers)
  return json.loads(response.text)


def get_token_pairs(tokenAddress: str):
  headers = {
    "Accept": "application/json",
    "X-API-Key": os.getenv("MORALIS_API_KEY")
  }
  url = f"https://solana-gateway.moralis.io/token/mainnet/{tokenAddress}/pairs"
  response = requests.request("GET", url, headers=headers)
  return json.loads(response.text)


def get_main_pair_address(tokenAddress: str):
  pairs = get_token_pairs(tokenAddress)
  return pairs['pairs'][0]['pairAddress']


def get_token_holder_counts(tokenAddress: str):
  holder_dict = get_token_holder_analytics("7EDtqTUgVzNqqE6oNaDSk6exJXYceQ1NdMDd8kSwpump")
  holder_count = holder_dict['totalHolders']
  transfer_count = holder_dict['holdersByAcquisition']['transfer']
  airdrop_count = holder_dict['holdersByAcquisition']['airdrop']
  return holder_count, transfer_count, airdrop_count


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


def alpha_pos(tokenAddress: str, timeframe: str = "5m"):
  analytics = get_token_analytics(tokenAddress)
  net_vol_5min = analytics['totalBuyVolume'][timeframe] - analytics['totalSellVolume'][timeframe]
  return net_vol_5min


def get_token_ohlc(pairAddress: str):
  # Get today's date
  today = datetime.now()
  today_formatted = today.strftime("%Y-%m-%d")

  # Get yesterday's date
  yesterday = today - timedelta(days=1)
  yesterday_formatted = yesterday.strftime("%Y-%m-%d")
  headers = {
    "Accept": "application/json",
    "X-API-Key": os.getenv("MORALIS_API_KEY")
  }
  url = f"https://solana-gateway.moralis.io/token/mainnet/pairs/{pairAddress}/ohlcv?timeframe=1h&currency=usd&fromDate={yesterday_formatted}&toDate={today_formatted}&limit=10"
  response = requests.request("GET", url, headers=headers)
  return json.loads(response.text)

### DOESN'T WORK BECAUSE NO OHLC DATA FROM PAIR???
# def get_token_highest_mktcap(tokenAddress: str):
#   pairAddress = get_main_pair_address(tokenAddress)
#   ohlc_data = get_token_ohlc(pairAddress)
#   print()
#   return ohlc_data['result'][0]['high'] * 1000000000


