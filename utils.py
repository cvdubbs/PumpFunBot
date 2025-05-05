import datetime
from datetime import datetime, timedelta
from dateutil import parser
import requests
import time
from requests.exceptions import Timeout, ConnectionError, RequestException
import pytz
import pandas as pd
import moralis_lib
import quicknode_lib
import config
import utils


def calculate_time_difference(timestamp_str):
    """
    Calculate the difference between current time and a provided timestamp.
    
    Args:
        timestamp_str (str): A timestamp string in ISO 8601 format (e.g., '2025-04-07T02:26:11Z')
        
    Returns:
        tuple: Hours, minutes, and seconds difference
    """
    # Parse the input timestamp
    target_time = parser.parse(timestamp_str)
    
    # Get current time in UTC
    current_time = datetime.now(pytz.UTC)
    
    # Calculate the time difference
    time_difference = abs(current_time - target_time)
    
    # Extract hours, minutes, and seconds
    total_seconds = time_difference.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    
    return hours, minutes, seconds


def filter_only_last_two_hours(df: pd.DataFrame) -> pd.DataFrame:
    # Convert 'createdAt' column to datetime format
    df['createdAt'] = pd.to_datetime(df['createdAt'])

    # Get the current time from the latest entry
    latest_time = df['createdAt'].max()

    # Calculate the cutoff time (2 hours before the latest time)
    cutoff_time = latest_time - timedelta(hours=2)

    # Filter the DataFrame to include only rows from the last 2 hours
    return df[df['createdAt'] >= cutoff_time]


def list_rug_checked_tokens(df: pd.DataFrame) -> list:
    rugchecked_tokens = list()
    for tokenAddress in df['tokenAddress'].unique():
        try:
            holder_count, transfer_count, airdrop_count = moralis_lib.get_token_holder_counts(tokenAddress)
            if airdrop_count >2:
                append_to_file("./data/reject_why.txt", [f"{tokenAddress} - Airdrop count {airdrop_count}"])
                continue
        except:
            print(f"Error getting Moralis holder counts token {tokenAddress}")
            continue
        try:
            dev_percent_owned = (moralis_lib.get_dev_own(tokenAddress))
        except:
            print(f"Error getting dev ownership for token {tokenAddress}")
            continue
        if dev_percent_owned is None:
            continue
        if dev_percent_owned > 0.005:
            append_to_file("./data/reject_why.txt", [f"{tokenAddress} - dev owns {dev_percent_owned}%"])
            continue
        topholders_result = quicknode_lib.get_top_holders_percentage(tokenAddress)
        top_10_own_float = topholders_result['top_10_percentage']
        if top_10_own_float > 33.00:
            append_to_file("./data/reject_why.txt", [f"{tokenAddress} - top 10 own {top_10_own_float}%"])
            continue
        # sniper_own, total_snipers = moralis_lib.get_snipers_own(tokenAddress)
        # if sniper_own > 30:
        #     append_to_file("./data/reject_why.txt", [f"{tokenAddress} - snipers still own {sniper_own}"])
        if dev_percent_owned <= 0.05 and top_10_own_float <= 33.00: # and sniper_check <= 30
            rugchecked_tokens.append(tokenAddress)
    return rugchecked_tokens


def send_discord_message(message_to_send, image_url=None, max_retries=3, timeout=10):
    """
    Send a message to a Discord channel using a webhook with proper error handling and timeout.
    
    Args:
        message_to_send (str): The message to send.
        image_url (str, optional): URL of an image to include in the embed.
        max_retries (int, optional): Maximum number of retry attempts. Defaults to 3.
        timeout (int, optional): Request timeout in seconds. Defaults to 10.
        
    Returns:
        bool: True if message was sent successfully, False otherwise.
    """
    # Define the webhook URL
    try:
        webhook_url = config.discord_webhook_url
    except (AttributeError, KeyError):
        print("Error: Discord webhook URL not found in config")
        return False
    
    # Prepare the message payload
    if image_url is None:
        data = {
            "content": message_to_send
        }
    else:
        data = {
            "content": message_to_send,
            "embeds": [
                {
                    "image": {
                        "url": image_url
                    }
                }
            ]
        }

    # Attempt to send the message with retries
    for attempt in range(max_retries):
        try:
            # Send the request with timeout
            response = requests.post(webhook_url, json=data, timeout=timeout)
            
            # Check response status
            if response.status_code == 204:
                print("Message sent successfully!")
                return True
            elif response.status_code == 429:  # Rate limited
                retry_after = int(response.headers.get('Retry-After', 5))
                print(f"Rate limited. Waiting {retry_after} seconds before retry...")
                time.sleep(retry_after)
            else:
                print(f"Failed to send message: Status code {response.status_code}")
                # If it's a client error (4xx) that's not rate limiting, don't retry
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    print(f"Client error: {response.text}")
                    return False
                    
                # Wait before retry for server errors
                wait_time = (attempt + 1) * 2
                print(f"Server error. Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                
        except Timeout:
            print(f"Request timed out (attempt {attempt+1}/{max_retries})")
            if attempt == max_retries - 1:
                return False
                
        except ConnectionError as e:
            print(f"Connection error (attempt {attempt+1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                return False
            time.sleep((attempt + 1) * 2)
            
        except RequestException as e:
            print(f"Request exception (attempt {attempt+1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                return False
            time.sleep((attempt + 1) * 2)
            
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return False
    
    print("Max retries exceeded. Failed to send Discord message.")
    return False


def append_to_file(file_path: str, data: list):
    with open(file_path, "a") as file:
            for item in data:
                file.write(item + "\n")

def get_age(creation_time: str) -> str:
    hours, minutes, seconds = calculate_time_difference(creation_time)
    return f'{hours} hrs: {minutes} mins: {seconds} secs'


def get_output_info(tokenAddress: str):
    mkt_cap = moralis_lib.get_pumpfun_marketcap(tokenAddress)
    dev_wallet = moralis_lib.get_dev_wallet(tokenAddress)
    creation_time = moralis_lib.get_creation_time(tokenAddress)
    age = utils.get_age(creation_time)
    holder_count, transfer_count, airdrop_count = moralis_lib.get_token_holder_counts(tokenAddress)
    return (mkt_cap, holder_count, airdrop_count, transfer_count, age, dev_wallet)


def clean_text_strings_for_discord(all_tokens_2h_df: pd.DataFrame, tokenAddress: str, mkt_cap, holder_count, airdrop_count, transfer_count, age, dev_wallet):
    symbol_str = f"{all_tokens_2h_df['symbol'][all_tokens_2h_df['tokenAddress'] == tokenAddress].values[0]} \n"
    name_str = f"# {all_tokens_2h_df['name'][all_tokens_2h_df['tokenAddress'] == tokenAddress].values[0]} \n"
    tokenAddress_str = f"{tokenAddress} \n"
    mktcap_str = f" \n- 🏷️ MktCap: {round(mkt_cap,0)/1000}k  \n"
    liquidity_str = f"- 💧 Liquidity: {round(float(all_tokens_2h_df['liquidity'][all_tokens_2h_df['tokenAddress'] == tokenAddress].values[0])/1000,0)}k  \n"
    holder_str = f"- 👥 Holder Count: {holder_count} - Airdropped: {airdrop_count} - Transfered: {transfer_count} \n"
    age_str = f"- ⏳ Age: {age} \n"
    dev_wallet_str = f"- 👤 Dev Wallet: [{dev_wallet}](https://solscan.io/account/{dev_wallet}?activity_type=ACTIVITY_SPL_INIT_MINT#defiactivities) \n"
    trade_links_str = f"[AXI](<https://axiom.trade/meme/{tokenAddress}>) - [GMGN](https://gmgn.ai/sol/token/{tokenAddress})"
    return (name_str +  
            symbol_str + 
            tokenAddress_str + 
            mktcap_str + 
            liquidity_str + 
            holder_str + 
            age_str + 
            dev_wallet_str + 
            trade_links_str)


def read_text_to_list(file_path: str) -> list:
    token_list = []
    try:
        with open(file_path, 'r') as file:
            # Read each line, strip whitespace, and add to the list
            token_list = [line.strip() for line in file]
        print(f"Successfully read {len(token_list)} tokens from file")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
    except Exception as e:
        print(f"Error reading file: {str(e)}")
    return token_list
