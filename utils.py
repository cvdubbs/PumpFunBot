import datetime
from datetime import datetime, timedelta
from dateutil import parser
import requests
import pytz
import pandas as pd
import bq_lib
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
        if dev_percent_owned > 0.05:
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


def send_discord_message(message_to_send, image_url = None):
    """
    Send a message to a Discord channel using a webhook.
    
    Args:
        message_to_send (str): The message to send.
    """
    # Define the webhook URL
    webhook_url = config.discord_webhook_url

    message = message_to_send

    if image_url is None:
         data = {
            "content": message
        }
    else:
        data = {
            "content": message,
            "embeds": [
                {
                    "image": {
                        "url": image_url
                    }
                }
            ]
        }

    # Send the request
    response = requests.post(webhook_url, json=data)

    if response.status_code == 204:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message: {response.status_code}")


def append_to_file(file_path: str, data: list):
    with open(file_path, "a") as file:
            for item in data:
                file.write(item + "\n")

def get_age(creation_time: str) -> str:
    hours, minutes, seconds = calculate_time_difference(creation_time)
    return f'{hours} hrs: {minutes} mins: {seconds} secs'