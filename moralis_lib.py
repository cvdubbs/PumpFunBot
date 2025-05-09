import os
from datetime import datetime, timedelta
import time
from requests.exceptions import Timeout, ConnectionError, RequestException
import pandas as pd
import json
from dotenv import load_dotenv
from moralis import sol_api

import config

# Load environment variables from .env file
load_dotenv()

import requests

# Common timeout and retry parameters
DEFAULT_TIMEOUT = 10
MAX_RETRIES = 3
RETRY_DELAY = 2

def get_hist_new_tokens(loops=50, timeout=15, max_retries=3, retry_delay=3):
    """
    Fetch historical token data with proper timeout and error handling.
    
    Args:
        loops (int): Number of pagination loops to perform
        timeout (int): Request timeout in seconds
        max_retries (int): Maximum number of retry attempts per request
        retry_delay (int): Base delay between retries in seconds
        
    Returns:
        pd.DataFrame: DataFrame containing token data
    """
    list_of_dfs = []
    
    # Function to make API requests with retries
    def make_request(url, headers, current_timeout=timeout):
        for attempt in range(max_retries):
            try:
                response = requests.request("GET", url, headers=headers, timeout=current_timeout)
                
                # Check for rate limiting
                if response.status_code == 429:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Rate limited. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                    
                # Check for other errors
                if response.status_code != 200:
                    print(f"API error: {response.status_code} - {response.text}")
                    # Only retry on server errors (5xx)
                    if response.status_code < 500:
                        return None
                    
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"Server error. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                    
                # Parse the response
                return json.loads(response.text)
                
            except Timeout:
                print(f"Request timed out (attempt {attempt+1}/{max_retries})")
                if attempt == max_retries - 1:
                    return None
                    
            except ConnectionError as e:
                print(f"Connection error (attempt {attempt+1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(retry_delay * (2 ** attempt))
                
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")
                return None
                
            except Exception as e:
                print(f"Unexpected error: {str(e)}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(retry_delay * (2 ** attempt))
        
        return None
    
    # Initial request
    try:
        # Validate config variables
        if not hasattr(config, 'moralis_url') or not hasattr(config, 'moralis_headers'):
            print("Error: Missing required config variables")
            return pd.DataFrame()
            
        data = make_request(config.moralis_url, config.moralis_headers)
        if data is None or 'result' not in data or 'cursor' not in data:
            print("Error: Invalid response from initial request")
            return pd.DataFrame()
            
        df_add = pd.DataFrame(data['result'])
        list_of_dfs.append(df_add)
        cursorUsed = data['cursor']
        
        # Process pagination
        consecutive_errors = 0
        for i in range(0, loops):
            # Check if we should stop due to too many consecutive errors
            if consecutive_errors >= 3:
                print(f"Stopping after {i} loops due to consecutive errors")
                break
                
            # Construct URL for pagination
            url = f"{config.moralis_url}&cursor={cursorUsed}"
            
            # Make paginated request
            data = make_request(url, config.moralis_headers)
            if data is None or 'result' not in data or 'cursor' not in data:
                print(f"Error in loop {i}: Invalid response")
                consecutive_errors += 1
                continue
                
            # Reset error counter on success
            consecutive_errors = 0
            
            # Process the data
            df_add = pd.DataFrame(data['result'])
            if not df_add.empty:
                list_of_dfs.append(df_add)
            else:
                print(f"Warning: Empty result in loop {i}")
                
            # Update cursor for next request
            cursorUsed = data['cursor']
            
            # Add a small delay to avoid overloading the API
            time.sleep(0.5)
            
            # Progress reporting
            if (i + 1) % 10 == 0:
                print(f"Completed {i + 1}/{loops} pagination requests")
        
        # Process collected data if any
        if not list_of_dfs:
            print("No data collected from API")
            return pd.DataFrame()
            
        print(f"Processing {len(list_of_dfs)} data frames")
        final_df = pd.concat(list_of_dfs)
        final_df = final_df.drop_duplicates()
        final_df = final_df[~final_df['tokenAddress'].isna()]
        
        # Save to CSV
        try:
            final_df.to_csv('./IO_Files/TokensDB.csv', index=False)
            print(f"Saved {len(final_df)} rows to CSV")
        except Exception as e:
            print(f"Error saving to CSV: {str(e)}")
        
        # Convert data types
        try:
            final_df['fullyDilutedValuation'] = final_df['fullyDilutedValuation'].astype('float')
        except (ValueError, TypeError) as e:
            print(f"Error converting fullyDilutedValuation to float: {str(e)}")
            # Attempt to convert with error handling
            final_df['fullyDilutedValuation'] = pd.to_numeric(final_df['fullyDilutedValuation'], errors='coerce')
        
        return final_df
        
    except Exception as e:
        print(f"Unexpected error in get_hist_new_tokens: {str(e)}")
        
        # Return what we've collected so far
        if list_of_dfs:
            try:
                final_df = pd.concat(list_of_dfs)
                final_df = final_df.drop_duplicates()
                return final_df
            except Exception:
                pass
                
        return pd.DataFrame()

def get_bonding_tokens() -> pd.DataFrame:
    max_attempts = 3  # Limit retries to prevent infinite loop
    attempt = 0
    timeout = 15  # seconds
    
    while attempt < max_attempts:
        attempt += 1
        list_of_dfs = list()
        
        try:
            # Initial request with timeout
            response = requests.request("GET", config.moralis_bonding_url, headers=config.moralis_headers, timeout=timeout)
            
            # Check response status
            if response.status_code != 200:
                print(f"Error: Initial request failed with status code {response.status_code}")
                print(f"Response: {response.text}")
                time.sleep(30)
                continue
                
            data = json.loads(response.text)
            
            # Validate data format
            if 'result' not in data or not isinstance(data['result'], list):
                print(f"Error: Unexpected data format in initial response")
                time.sleep(30)
                continue
                
            df_add = pd.DataFrame(data['result'])
            list_of_dfs.append(df_add)
            
            # Check if cursor exists
            if 'cursor' not in data:
                print("Warning: No cursor found in initial response. Cannot fetch additional pages.")
                break
                
            cursorUsed = data['cursor']
            
            # Process additional pages
            page_failures = 0
            for i in range(0, 5):
                try:
                    # Use config variable for URL consistency
                    url = f"{config.moralis_bonding_url}&cursor={cursorUsed}"
                    response = requests.request("GET", url, headers=config.moralis_headers, timeout=timeout)
                    
                    # Check for rate limiting
                    if response.status_code == 429:
                        print(f"Rate limited on page {i+1}. Waiting before retry...")
                        time.sleep(60)  # Longer wait for rate limiting
                        i -= 1  # Retry this page
                        continue
                        
                    # Check for other errors
                    if response.status_code != 200:
                        print(f"Error on page {i+1}: Status code {response.status_code}")
                        page_failures += 1
                        if page_failures >= 3:  # If we fail 3 pages in a row, proceed with what we have
                            print("Too many consecutive page failures. Processing available data.")
                            break
                        continue
                    
                    data = json.loads(response.text)
                    
                    # Validate data structure
                    if 'result' not in data or not isinstance(data['result'], list):
                        print(f"Error: Unexpected data format in page {i+1}")
                        page_failures += 1
                        continue
                    
                    # Reset failure counter on success
                    page_failures = 0
                    
                    df_add = pd.DataFrame(data['result'])
                    list_of_dfs.append(df_add)
                    
                    if 'cursor' not in data or not data['cursor']:
                        print(f"No more pages available after page {i+1}")
                        break
                        
                    cursorUsed = data['cursor']
                    
                    # Small delay between requests to avoid rate limiting
                    time.sleep(1)
                    
                except (Timeout, ConnectionError, RequestException) as e:
                    print(f"Network error on page {i+1}: {str(e)}")
                    page_failures += 1
                    time.sleep(5)
                    
                except Exception as e:
                    print(f"Unexpected error in page {i+1} fetch: {str(e)}")
                    page_failures += 1
            
            # If we got any data, process it
            if list_of_dfs:
                break  # Exit the retry loop if we have data
                
        except Exception as e:
            print(f"Critical error in Moralis request (attempt {attempt}/{max_attempts}): {str(e)}")
            time.sleep(30)
    
    # If we have no data after all attempts, return empty DataFrame
    if not list_of_dfs:
        print("Failed to retrieve any data after maximum attempts")
        return pd.DataFrame(columns=['tokenAddress', 'fullyDilutedValuation'])
    
    try:
        # Process the collected data
        final_df = pd.concat(list_of_dfs)
        final_df = final_df.drop_duplicates()
        final_df = final_df[~final_df['tokenAddress'].isna()]
        
        # Convert data types
        try:
            final_df['fullyDilutedValuation'] = final_df['fullyDilutedValuation'].astype('float')
        except Exception as e:
            print(f"Warning: Could not convert fullyDilutedValuation to float: {str(e)}")
        
        return final_df
        
    except Exception as e:
        print(f"Error processing collected data: {str(e)}")
        # If processing fails but we have data, try to return something
        if list_of_dfs:
            try:
                return pd.concat(list_of_dfs)
            except:
                pass
                
        return pd.DataFrame(columns=['tokenAddress', 'fullyDilutedValuation'])


def get_new_tokens():
    list_of_dfs = list()
    max_retries = 3
    retry_delay = 2  # seconds
    timeout = 10  # seconds

    try:
        # Initial request with timeout
        response = requests.request("GET", config.moralis_url, headers=config.moralis_headers, timeout=timeout)
        
        # Check if response is valid
        if response.status_code != 200:
            print(f"Error: Initial request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return pd.DataFrame(columns=['tokenAddress', 'fullyDilutedValuation'])
            
        data = json.loads(response.text)
        
        # Validate data structure before proceeding
        if 'result' not in data or not isinstance(data['result'], list):
            print(f"Error: Unexpected data format in initial response")
            return pd.DataFrame(columns=['tokenAddress', 'fullyDilutedValuation'])
            
        df_add = pd.DataFrame(data['result'])
        list_of_dfs.append(df_add)
        
        # Check if cursor exists
        if 'cursor' not in data:
            print("Warning: No cursor found in initial response. Cannot fetch additional pages.")
            return pd.concat(list_of_dfs) if list_of_dfs else pd.DataFrame(columns=['tokenAddress', 'fullyDilutedValuation'])
            
        cursorUsed = data['cursor']
        
        # Process additional pages with retries
        for i in range(0, 3):
            for attempt in range(max_retries):
                try:
                    url = f"{config.moralis_url}&cursor={cursorUsed}"
                    response = requests.request("GET", url, headers=config.moralis_headers, timeout=timeout)
                    
                    # Check for rate limiting
                    if response.status_code == 429:
                        print(f"Rate limited on page {i+1}. Waiting before retry...")
                        time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                        continue
                        
                    # Check for other errors
                    if response.status_code != 200:
                        print(f"Error on page {i+1}: Status code {response.status_code}")
                        print(f"Response: {response.text}")
                        break  # Try next page
                        
                    data = json.loads(response.text)
                    
                    # Validate data structure
                    if 'result' not in data or not isinstance(data['result'], list):
                        print(f"Error: Unexpected data format in page {i+1}")
                        break  # Try next page
                        
                    df_add = pd.DataFrame(data['result'])
                    list_of_dfs.append(df_add)
                    
                    if 'cursor' not in data:
                        print(f"Warning: No cursor found in page {i+1}. Stopping pagination.")
                        break  # No more pages to fetch
                        
                    cursorUsed = data['cursor']
                    break  # Success, exit retry loop
                    
                except Timeout:
                    print(f"Timeout on page {i+1}, attempt {attempt+1}")
                    if attempt == max_retries - 1:
                        print(f"Max retries reached for page {i+1}. Moving to next page.")
                
                except (ConnectionError, RequestException) as e:
                    print(f"Connection error on page {i+1}, attempt {attempt+1}: {str(e)}")
                    if attempt == max_retries - 1:
                        print(f"Max retries reached for page {i+1}. Moving to next page.")
                
                except Exception as e:
                    print(f"Unexpected error in page {i+1} fetch: {str(e)}")
                    break  # Try next page
                    
                # Wait before retry
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
    
    except Exception as e:
        print(f"Critical error in Moralis request: {str(e)}")
    
    # Process whatever data we collected
    if list_of_dfs:
        try:
            final_df = pd.concat(list_of_dfs)
            final_df = final_df.drop_duplicates()
            final_df = final_df[~final_df['tokenAddress'].isna()]
            
            # Handle potential type conversion errors
            try:
                final_df['fullyDilutedValuation'] = final_df['fullyDilutedValuation'].astype('float')
            except Exception as e:
                print(f"Warning: Could not convert fullyDilutedValuation to float: {str(e)}")
                
            return final_df
        except Exception as e:
            print(f"Error in processing collected data: {str(e)}")
            # Return whatever we can without processing
            if list_of_dfs:
                try:
                    return pd.concat(list_of_dfs)
                except Exception:
                    print("Fatal error: Could not concatenate dataframes")
    
    # If all else fails, return an empty DataFrame
    return pd.DataFrame(columns=['tokenAddress', 'fullyDilutedValuation'])




def handle_request(url, headers, method="GET", timeout=DEFAULT_TIMEOUT, max_retries=MAX_RETRIES):
    """
    Generic function to handle API requests with proper error handling and retries
    """
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, headers=headers, timeout=timeout)
            
            # Check for rate limiting
            if response.status_code == 429:
                wait_time = min(30, RETRY_DELAY * (attempt + 1))
                print(f"Rate limited. Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue
                
            # Check for other non-200 responses
            if response.status_code != 200:
                print(f"API error: {response.status_code} - {response.text}")
                # Only retry on server errors (5xx)
                if response.status_code < 500 and attempt == max_retries - 1:
                    return {"error": f"API error: {response.status_code}", "status_code": response.status_code}
                wait_time = RETRY_DELAY * (attempt + 1)
                time.sleep(wait_time)
                continue
                
            # Successfully got a 200 response
            return json.loads(response.text)
            
        except Timeout:
            print(f"Request timed out (attempt {attempt+1}/{max_retries})")
            if attempt == max_retries - 1:
                return {"error": "Request timed out after all retries", "status_code": -1}
            time.sleep(RETRY_DELAY * (attempt + 1))
                
        except ConnectionError as e:
            print(f"Connection error (attempt {attempt+1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                return {"error": f"Connection error: {str(e)}", "status_code": -2}
            time.sleep(RETRY_DELAY * (attempt + 1))
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            return {"error": f"Invalid JSON response: {str(e)}", "status_code": -4}
            
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            if attempt == max_retries - 1:
                return {"error": f"Unexpected error: {str(e)}", "status_code": -5}
            time.sleep(RETRY_DELAY * (attempt + 1))
    
    return {"error": "Max retries exceeded", "status_code": -6}

# Updated API functions using the common handler

def get_token_analytics(tokenAddress: str):
    url = f"https://deep-index.moralis.io/api/v2.2/tokens/{tokenAddress}/analytics?chain=solana"
    return handle_request(url, config.moralis_headers)

def get_token_holder_analytics(tokenAddress: str):
    url = f"https://solana-gateway.moralis.io/token/mainnet/holders/{tokenAddress}"
    return handle_request(url, config.moralis_headers)

def get_token_pairs(tokenAddress: str):
    url = f"https://solana-gateway.moralis.io/token/mainnet/{tokenAddress}/pairs"
    return handle_request(url, config.moralis_headers)

def get_token_price(tokenAddress: str):
    try:
        params = {
            "network": "mainnet",
            "address": tokenAddress
        }
        result = sol_api.token.get_token_price(
            api_key=os.getenv("MORALIS_API_KEY"),
            params=params,
        )
        return result
    except Exception as e:
        print(f"Error in get_token_price: {str(e)}")
        return {"error": f"API error: {str(e)}", "status_code": -1}

def get_token_ohlc(pairAddress: str, timeframe: str = "1h"):
    today = datetime.now()
    today_formatted = today.strftime("%Y-%m-%d")
    yesterday = today - timedelta(days=1)
    yesterday_formatted = yesterday.strftime("%Y-%m-%d")
    tomorrow = today + timedelta(days=2)
    tomorrow_formatted = tomorrow.strftime("%Y-%m-%d")

    url = f"https://solana-gateway.moralis.io/token/mainnet/pairs/{pairAddress}/ohlcv?timeframe={timeframe}&currency=usd&fromDate={yesterday_formatted}&toDate={tomorrow_formatted}&limit=10"
    return handle_request(url, config.moralis_headers)

def get_dev_wallet(tokenAddress: str):
    url = f"https://solana-gateway.moralis.io/token/mainnet/{tokenAddress}/swaps?limit=2&order=ASC"
    response = handle_request(url, config.moralis_headers)
    
    # Check for errors in the response
    if isinstance(response, dict) and "error" in response:
        print(f"Error in get_dev_wallet: {response['error']}")
        return None
        
    try:
        return response['result'][0]['walletAddress']
    except (KeyError, IndexError) as e:
        print(f"Error extracting dev wallet: {str(e)}")
        return None

def get_creation_time(tokenAddress: str):
    url = f"https://solana-gateway.moralis.io/token/mainnet/{tokenAddress}/swaps?limit=2&order=ASC"
    response = handle_request(url, config.moralis_headers)
    
    # Check for errors in the response
    if isinstance(response, dict) and "error" in response:
        print(f"Error in get_creation_time: {response['error']}")
        return None
        
    try:
        return response['result'][0]['blockTimestamp']
    except (KeyError, IndexError) as e:
        print(f"Error extracting creation time: {str(e)}")
        return None

def get_sniper_wallets(tokenAddress: str):
    url = f"https://solana-gateway.moralis.io/token/mainnet/{tokenAddress}/swaps?order=ASC"
    response = handle_request(url, config.moralis_headers)
    
    # Check for errors in the response
    if isinstance(response, dict) and "error" in response:
        print(f"Error in get_sniper_wallets: {response['error']}")
        return []
        
    sniper_wallets = []
    try:
        for wallet_data in response['result']:
            if wallet_data['walletAddress'] not in sniper_wallets:
                sniper_wallets.append(wallet_data['walletAddress'])
        return sniper_wallets
    except (KeyError, TypeError) as e:
        print(f"Error extracting sniper wallets: {str(e)}")
        return []

def get_dev_own(tokenAddress: str):
    dev_wallet = get_dev_wallet(tokenAddress)
    if not dev_wallet:
        print("Could not get developer wallet")
        return float(0.00)
        
    try:
        params = {
            "network": "mainnet",
            "address": dev_wallet
        }
        result = sol_api.account.get_portfolio(
            api_key=os.getenv("MORALIS_API_KEY"),
            params=params,
        )
        
        for token in result.get('tokens', []):
            if token['mint'] == tokenAddress:
                return float(token['amount'])/1000000000
                
        return float(0.00)
    except Exception as e:
        print(f"Error in get_dev_own: {str(e)}")
        return float(0.00)

def get_main_pair_address(tokenAddress: str):
    # This function was called but not defined in the original code
    # Adding a placeholder implementation based on get_token_pairs
    pairs = get_token_pairs(tokenAddress)
    if isinstance(pairs, dict) and "error" in pairs:
        print(f"Error in get_main_pair_address: {pairs['error']}")
        return None
        
    try:
        # Assuming the main pair is the first one in the result
        if pairs and 'result' in pairs and len(pairs['result']) > 0:
            return pairs['result'][0]['pairAddress']
        return None
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error extracting main pair address: {str(e)}")
        return None

def get_snipers(tokenAddress: str):
    pairAddress = get_main_pair_address(tokenAddress)
    if not pairAddress:
        print("Could not get main pair address")
        return {"error": "No pair address found", "status_code": -1}
        
    print(pairAddress)
    url = f"https://solana-gateway.moralis.io/token/mainnet/pairs/{pairAddress}/snipers?blocksAfterCreation=1000"
    return handle_request(url, config.moralis_headers)

def get_snipers_own(tokenAddress: str):
    # Note: Hard-coded token address in original function - using parameter instead
    snipers = get_sniper_wallets(tokenAddress)
    count_snipers_own = 0
    
    for wallet in snipers:
        try:
            params = {
                "network": "mainnet",
                "address": wallet
            }
            result = sol_api.account.get_portfolio(
                api_key=os.getenv("MORALIS_API_KEY"),
                params=params,
            )
            
            for token in result.get('tokens', []):
                if token['mint'] == tokenAddress:
                    count_snipers_own += 1
                    break
        except Exception as e:
            print(f"Error checking wallet {wallet}: {str(e)}")
            continue
            
    return count_snipers_own, len(snipers)

def get_metadata(tokenAddress: str):
    url = f"https://solana-gateway.moralis.io/token/mainnet/{tokenAddress}/metadata"
    return handle_request(url, config.moralis_headers)
def get_token_image(tokenAddress: str):
  metadata = get_metadata(tokenAddress)
  ipfs_url = metadata['metaplex']['metadataUri']
  response = requests.request("GET", ipfs_url)
  result = json.loads(response.text)
  return result['image']


def get_max_mktcap(tokenAddress: str, timeframe: str = "12h"):
  try:
    pairAddress = get_main_pair_address(tokenAddress)
    ohlc_data = get_token_ohlc(pairAddress, timeframe)
    max_mkt_cap = ohlc_data['result'][0]['high'] * 1000000000
  except Exception as e:
    print(f"Error fetching max market cap: {str(e)} for token {tokenAddress}")
    try:
      pairAddress = get_main_pair_address(tokenAddress)
      ohlc_data = get_token_ohlc(pairAddress, '12h')
      print(f"ohlc_data: {ohlc_data}")
    except Exception as e:
      print(f"Error fetching OHLC data: {str(e)} for token {tokenAddress}")
      return 0
    return 0
  return max_mkt_cap



def get_main_pair_address(tokenAddress: str):
  pairs = get_token_pairs(tokenAddress)
  return pairs['pairs'][0]['pairAddress']


def get_token_holder_counts(tokenAddress: str):
  holder_dict = get_token_holder_analytics(tokenAddress)
  holder_count = holder_dict['totalHolders']
  transfer_count = holder_dict['holdersByAcquisition']['transfer']
  airdrop_count = holder_dict['holdersByAcquisition']['airdrop']
  return holder_count, transfer_count, airdrop_count



def get_pumpfun_marketcap(tokenAddress: str):
  result = get_token_price(tokenAddress)
  return result['usdPrice'] * 1000000000


def alpha_pos(tokenAddress: str, timeframe: str = "5m"):
  analytics = get_token_analytics(tokenAddress)
  net_vol_5min = analytics['totalBuyVolume'][timeframe] - analytics['totalSellVolume'][timeframe]
  return net_vol_5min


def alpha_vol(tokenAddress: str, timeframe: str = "5m"):
  analytics = get_token_analytics(tokenAddress)
  net_vol_5min = analytics['totalBuyVolume'][timeframe] + analytics['totalSellVolume'][timeframe]
  return net_vol_5min


# snipers_own, total_snipers = get_snipers_own("ANrqkQMkaXapaJfrgkZwcmuskozuc8vtHXpaB1t4pump")