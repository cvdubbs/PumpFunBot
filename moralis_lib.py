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
  list_of_dfs = list()

  response = requests.request("GET", config.moralis_url, headers=config.moralis_headers)
  data = json.loads(response.text)
  df_add = pd.DataFrame(data['result'])
  list_of_dfs.append(df_add)
  cursorUsed = data['cursor']

  for i in range(0,loops):
      url = f"{config.moralis_url}&cursor={cursorUsed}"
      response = requests.request("GET", url, headers=config.moralis_headers)
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
  list_of_dfs = list()

  response = requests.request("GET", config.moralis_bonding_url, headers=config.moralis_headers)
  data = json.loads(response.text)
  df_add = pd.DataFrame(data['result'])
  list_of_dfs.append(df_add)
  cursorUsed = data['cursor']
  try:
    for i in range(0,5):
        url = f"https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/bonding?limit={config.NewTokenCount}&cursor={cursorUsed}"
        response = requests.request("GET", url, headers=config.moralis_headers)
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
    list_of_dfs = list()

    try:
        # Initial request
        response = requests.request("GET", config.moralis_url, headers=config.moralis_headers)
        data = json.loads(response.text)
        df_add = pd.DataFrame(data['result'])
        list_of_dfs.append(df_add)
        cursorUsed = data['cursor']
        
        # Process additional pages
        for i in range(0, 3):
            try:
                url = f"{config.moralis_url}&cursor={cursorUsed}"
                response = requests.request("GET", url, headers=config.moralis_headers)
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


def get_token_analytics(tokenAddress: str):
  url = f"https://deep-index.moralis.io/api/v2.2/tokens/{tokenAddress}/analytics?chain=solana"
  response = requests.request("GET", url, headers=config.moralis_headers)
  return json.loads(response.text)


def get_token_holder_analytics(tokenAddress: str):
  url = f"https://solana-gateway.moralis.io/token/mainnet/holders/{tokenAddress}"
  response = requests.request("GET", url, headers=config.moralis_headers)
  return json.loads(response.text)


def get_token_pairs(tokenAddress: str):
  url = f"https://solana-gateway.moralis.io/token/mainnet/{tokenAddress}/pairs"
  response = requests.request("GET", url, headers=config.moralis_headers)
  return json.loads(response.text)


def get_main_pair_address(tokenAddress: str):
  pairs = get_token_pairs(tokenAddress)
  return pairs['pairs'][0]['pairAddress']


def get_token_holder_counts(tokenAddress: str):
  holder_dict = get_token_holder_analytics(tokenAddress)
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
  today = datetime.now()
  today_formatted = today.strftime("%Y-%m-%d")
  yesterday = today - timedelta(days=1)
  yesterday_formatted = yesterday.strftime("%Y-%m-%d")

  url = f"https://solana-gateway.moralis.io/token/mainnet/pairs/{pairAddress}/ohlcv?timeframe=1h&currency=usd&fromDate={yesterday_formatted}&toDate={today_formatted}&limit=10"
  response = requests.request("GET", url, headers=config.moralis_headers)
  return json.loads(response.text)


def get_token_pairs(tokenAddress: str):
  url = f"https://solana-gateway.moralis.io/token/mainnet/{tokenAddress}/pairs"
  response = requests.request("GET", url, headers=config.moralis_headers)
  return json.loads(response.text)


def get_dev_wallet(tokenAddress: str):
  url = f"https://solana-gateway.moralis.io/token/mainnet/{tokenAddress}/swaps?limit=2&order=ASC"
  response = requests.request("GET", url, headers=config.moralis_headers)
  data= json.loads(response.text)
  return data['result'][0]['walletAddress']


def get_creation_time(tokenAddress: str):
  url = f"https://solana-gateway.moralis.io/token/mainnet/{tokenAddress}/swaps?limit=2&order=ASC"
  response = requests.request("GET", url, headers=config.moralis_headers)
  data= json.loads(response.text)
  return data['result'][0]['blockTimestamp']


def get_sniper_wallets(tokenAddress: str):
  url = f"https://solana-gateway.moralis.io/token/mainnet/{tokenAddress}/swaps?order=ASC"
  response = requests.request("GET", url, headers=config.moralis_headers)
  data= json.loads(response.text)
  sniper_wallets = []
  for wallets in range(0, len(data['result'])):
    if data['result'][wallets]['walletAddress'] not in sniper_wallets:
      sniper_wallets.append(data['result'][wallets]['walletAddress'])
  return sniper_wallets


def get_dev_own(tokenAddress: str):
  dev_wallet = get_dev_wallet(tokenAddress)
  params = {
    "network": "mainnet",
    "address": dev_wallet
  }
  result = sol_api.account.get_portfolio(
    api_key=os.getenv("MORALIS_API_KEY"),
    params=params,
  )
  for token in range(0, len(result['tokens'])):
    if result['tokens'][token]['mint'] == tokenAddress:
      return float(result['tokens'][token]['amount'])/1000000000
    else:
      continue
  return float(0.00)


def get_snipers(tokenAddress: str):
  pairAddress = get_main_pair_address(tokenAddress)
  print(pairAddress)
  url = f"https://solana-gateway.moralis.io/token/mainnet/pairs/{pairAddress}/snipers?blocksAfterCreation=1000"
  response = requests.request("GET", url, headers=config.moralis_headers)
  return json.loads(response.text)


def get_snipers_own(tokenAddress: str):
  snipers = get_sniper_wallets("5QsZSonZWxyHfoxJHDDUPZQMqb1USwTX5zhFtMN1pump")
  count_snipers_own = 0
  for wallet in snipers:
    params = {
      "network": "mainnet",
      "address": wallet
    }
    result = sol_api.account.get_portfolio(
      api_key=os.getenv("MORALIS_API_KEY"),
      params=params,
    )
    for token in range(0, len(result['tokens'])):
      if result['tokens'][token]['mint'] == tokenAddress:
        count_snipers_own += 1
      else:
        continue
  return count_snipers_own, len(snipers)



def get_metadata(tokenAddress: str):
  url = f"https://solana-gateway.moralis.io/token/mainnet/{tokenAddress}/metadata"
  response = requests.request("GET", url, headers=config.moralis_headers)
  return json.loads(response.text)


def get_token_image(tokenAddress: str):
  metadata = get_metadata(tokenAddress)
  ipfs_url = metadata['metaplex']['metadataUri']
  response = requests.request("GET", ipfs_url)
  result = json.loads(response.text)
  return result['image']



# url = f"https://solana-gateway.moralis.io/token/mainnet/{tokenAddress}/swaps?order=ASC"
# response = requests.request("GET", url, headers=config.moralis_headers)
# data= json.loads(response.text)


# snipers_own, total_snipers = get_snipers_own("ANrqkQMkaXapaJfrgkZwcmuskozuc8vtHXpaB1t4pump")

### DOESN'T WORK BECAUSE NO OHLC DATA FROM PAIR???
# def get_token_highest_mktcap(tokenAddress: str):
#   pairAddress = get_main_pair_address(tokenAddress)
#   ohlc_data = get_token_ohlc(pairAddress)
#   print()
#   return ohlc_data['result'][0]['high'] * 1000000000


