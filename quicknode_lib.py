import requests
import json
from decimal import Decimal
from datetime import datetime

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

def get_token_largest_accounts(token_address, quicknode_url):
    """Get the largest token accounts"""
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenLargestAccounts",
        "params": [token_address]
    }
    
    response = requests.post(quicknode_url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json().get('result', {}).get('value', [])
    
    return []


def get_token_account_balance(account_address, quicknode_url):
    """Get the balance of a specific token account"""
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountBalance",
        "params": [account_address]
    }
    
    response = requests.post(quicknode_url, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json().get('result', {})
        if result and 'value' in result:
            return Decimal(result['value']['amount']) / (10 ** result['value']['decimals'])
    
    return None


def get_top_holders_percentage(token_address, quicknode_url=config.quicknode_url):
    """Get the percentage of top 10 holders for a token"""
    # Get total supply
    total_supply = config.pumpfun_supply
    
    # Get largest accounts
    largest_accounts = get_token_largest_accounts(token_address, quicknode_url)
    if not largest_accounts:
        print("Quicknode Error: Could not get largest accounts")
        return None
    
    # Process top 10 holders
    top_holders = []
    for account in largest_accounts:
        balance = get_token_account_balance(account['address'], quicknode_url)
        if balance:
            percentage = (balance / total_supply) * 100
            top_holders.append({
                'address': account['address'],
                'balance': balance,
                'percentage': percentage
            })
    
    # Sort by percentage (descending)
    top_holders.sort(key=lambda x: x['percentage'], reverse=True)
    
    # Calculate total percentage of top 10 holders
    top_10_holders = top_holders[1:11]
    total_percentage = sum(holder['percentage'] for holder in top_10_holders)
    
    return {
        'total_supply': total_supply,
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
