import requests
import json
from decimal import Decimal
from datetime import datetime
import time
from requests.exceptions import Timeout, ConnectionError, RequestException

import config

# def get_token_supply(token_address, quicknode_url):
#     """Get the total supply of a token"""
#     headers = {"Content-Type": "application/json"}
#     payload = {
#         "jsonrpc": "2.0",
#         "id": 1,
#         "method": "getTokenSupply",
#         "params": [token_address]
#     }
    
#     response = requests.post(quicknode_url, headers=headers, json=payload)
#     if response.status_code == 200:
#         result = response.json().get('result', {})
#         if result and 'value' in result:
#             return Decimal(result['value']['amount']) / (10 ** result['value']['decimals'])
    
#     return None

def make_api_request(url, payload, headers, max_retries=3, timeout=10, backoff_factor=2):
    """
    Generic function to handle API requests with proper error handling, timeouts, and retries
    """
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            
            # Check if response is valid
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limiting
                wait_time = backoff_factor * (2 ** attempt)  # Exponential backoff
                print(f"Rate limited. Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"API error: Status code {response.status_code} - {response.text}")
                # Don't retry on client errors
                if response.status_code < 500 and attempt == max_retries - 1:
                    return {"error": f"API error: {response.status_code}", "status_code": response.status_code}
                
                # Wait before retry for server errors
                wait_time = backoff_factor * (2 ** attempt)
                print(f"Server error. Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                
        except Timeout:
            print(f"Request timed out (attempt {attempt+1}/{max_retries})")
            if attempt == max_retries - 1:
                return {"error": "Request timed out after all retries"}
            time.sleep(backoff_factor * (2 ** attempt))
                
        except ConnectionError as e:
            print(f"Connection error (attempt {attempt+1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                return {"error": f"Connection error: {str(e)}"}
            time.sleep(backoff_factor * (2 ** attempt))
            
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            if attempt == max_retries - 1:
                return {"error": f"Unexpected error: {str(e)}"}
            time.sleep(backoff_factor * (2 ** attempt))
    
    return {"error": "Max retries exceeded"}


def get_token_largest_accounts(token_address, quicknode_url, timeout=10, max_retries=3):
    """Get the largest token accounts with proper error handling and timeouts"""
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenLargestAccounts",
        "params": [token_address]
    }
    
    response = make_api_request(quicknode_url, payload, headers, max_retries, timeout)
    
    # Check if the response contains an error
    if isinstance(response, dict) and "error" in response:
        print(f"Error in get_token_largest_accounts: {response['error']}")
        return []
    
    # Extract the result data
    try:
        return response.get('result', {}).get('value', [])
    except (AttributeError, TypeError) as e:
        print(f"Error extracting token largest accounts data: {str(e)}")
        return []


def get_token_account_balance(account_address, quicknode_url, timeout=10, max_retries=3):
    """Get the balance of a specific token account with proper error handling and timeouts"""
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountBalance",
        "params": [account_address]
    }
    
    response = make_api_request(quicknode_url, payload, headers, max_retries, timeout)
    
    # Check if the response contains an error
    if isinstance(response, dict) and "error" in response:
        print(f"Error in get_token_account_balance: {response['error']}")
        return None
    
    # Extract the result data
    try:
        result = response.get('result', {})
        if result and 'value' in result:
            return Decimal(result['value']['amount']) / (10 ** int(result['value']['decimals']))
    except (AttributeError, TypeError, ValueError, KeyError) as e:
        print(f"Error extracting token account balance data: {str(e)}")
    
    return None


def get_top_holders_percentage(token_address, quicknode_url=None, timeout=10, max_retries=3):
    """Get the percentage of top 10 holders for a token with proper error handling and timeouts"""
    # Use default URL if none provided
    if quicknode_url is None:
        quicknode_url = config.quicknode_url
    
    # Get total supply with a fallback
    try:
        total_supply = config.pumpfun_supply
    except (AttributeError, KeyError):
        print("Error: Could not get total supply from config")
        return {"error": "Could not get total supply"}
    
    # Get largest accounts
    largest_accounts = get_token_largest_accounts(token_address, quicknode_url, timeout, max_retries)
    if not largest_accounts:
        print("Quicknode Error: Could not get largest accounts")
        return {"error": "Could not get largest accounts"}
    
    # Process holders with timeout monitoring
    start_time = time.time()
    max_processing_time = 30  # maximum time to spend processing accounts
    
    top_holders = []
    for i, account in enumerate(largest_accounts):
        # Check if we're spending too much time processing
        if time.time() - start_time > max_processing_time:
            print(f"Warning: Processing timeout after analyzing {i} accounts")
            break
            
        balance = get_token_account_balance(account['address'], quicknode_url, timeout, max_retries)
        if balance:
            percentage = (balance / total_supply) * 100
            top_holders.append({
                'address': account['address'],
                'balance': balance,
                'percentage': percentage
            })
    
    # If we couldn't get any balance data
    if not top_holders:
        return {"error": "Could not get any token balance data"}
    
    # Sort by percentage (descending)
    top_holders.sort(key=lambda x: x['percentage'], reverse=True)
    
    # Safely get the top 10 holders (or fewer if less available)
    max_holders = min(10, len(top_holders) - 1)  # -1 to exclude first holder if there are enough
    if max_holders <= 0:
        return {
            'total_supply': float(total_supply),
            'top_holders': [],
            'top_percentage': 0
        }
    
    # Calculate total percentage of top 10 holders (excluding first one)
    top_10_holders = top_holders[1:max_holders+1]
    total_percentage = sum(holder['percentage'] for holder in top_10_holders)
    
    return {
        'total_supply': float(total_supply),
        'top_10_holders': top_10_holders,
        'top_10_percentage': total_percentage
    }


# # Your PumpFun token address
# token_address = "AJ37uM1qDN1MdWukKZ6Pg8yb5A8WoCzbVVYz4cdmpump"

# # Get top holders percentage
# result = get_top_holders_percentage(token_address)
# result['top_10_percentage']



# if result:
#     print(f"Token Supply: {result['total_supply']}")
#     print(f"Top 10 Holders Percentage: {result['top_10_percentage']:.2f}%")
#     print("\nTop 10 Holders:")
#     for i, holder in enumerate(result['top_10_holders'], 1):
#         print(f"{i}. Address: {holder['address']}")
#         print(f"   Balance: {holder['balance']}")
#         print(f"   Percentage: {holder['percentage']:.2f}%")
#         print()
