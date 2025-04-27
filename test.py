import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv('MORALIS_API_KEY')

# SPL token address
token_address = "BpvwL2PPNAta4jX2DoAiWxmjG438e7NwVUVWKJsTpump"

# API endpoint for Solana token holders
url = f"https://solana-gateway.moralis.io/token/mainnet/{token_address}/holders"

# Set up headers with API key
headers = {
    "accept": "application/json",
    "X-API-Key": API_KEY
}

# Parameter to get top 10 holders
params = {
    "limit": 10,
    "network": "mainnet"
}

def get_top_holders():
    response = requests.get(url, headers=headers, params=params)
    
    # Check if request was successful
    if response.status_code == 200:
        data = response.json()
        
        print(f"Top 10 holders of token {token_address}:")
        print("--------------------------------------")
        
        for i, holder in enumerate(data['result'], 1):
            address = holder.get('address', 'Unknown')
            amount = holder.get('amount', 0)
            
            # Format amount to be more readable
            formatted_amount = float(amount)
            
            # Get percentage if available
            percentage = holder.get('percentage', 'N/A')
            if percentage != 'N/A':
                percentage = f"{float(percentage) * 100:.2f}%"
            
            print(f"{i}. Address: {address}")
            print(f"   Amount: {formatted_amount}")
            print(f"   Percentage: {percentage}")
            print("--------------------------------------")
        
        return data['result']
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


get_top_holders()