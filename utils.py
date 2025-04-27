import datetime
from datetime import datetime, timedelta
from dateutil import parser
import requests
import pytz
import pandas as pd
import bq_lib
import moralis_lib
import config

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
                continue
        except:
            print(f"Error getting Moralis holder counts token {tokenAddress}")
            continue
        try:
            dev_wallet, creation_time = (bq_lib.get_creation_time_dev(tokenAddress))
        except:
            print(f"Error getting creation time for token {tokenAddress}")
            continue
        if dev_wallet is None:
            continue
        dev_percent_owned = bq_lib.dev_owns(tokenAddress, dev_wallet)
        if dev_percent_owned > 0.05:
            continue
        top_10_own_float = bq_lib.get_top_10_holders_ownership(tokenAddress)
        if top_10_own_float > 33.00:
            continue
        sniper_check = bq_lib.snipers_still_own(tokenAddress)
        if dev_percent_owned <= 0.05 and top_10_own_float <= 33.00 and sniper_check <= 25:
            rugchecked_tokens.append(tokenAddress)
    return rugchecked_tokens


def send_discord_message(message_to_send):
    """
    Send a message to a Discord channel using a webhook.
    
    Args:
        message_to_send (str): The message to send.
    """
    # Define the webhook URL
    webhook_url = config.discord_webhook_url

    message = message_to_send

    data = {
        "content": message
    }

    # Send the request
    response = requests.post(webhook_url, json=data)

    if response.status_code == 204:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message: {response.status_code}")


