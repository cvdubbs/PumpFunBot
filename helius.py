from solana.rpc.api import Client
import requests
import config

# Your Helius RPC URL
rpc_url = config.helius_url

payload = {
    "jsonrpc": "2.0",
    "id": "1",
    "method": "getAssetsByAuthority",
    "params": {"authorityAddress": "5qWya6UjwWnGVhdSBL3hyZ7B45jbk6Byt1hwd7ohEGXE"}
}
headers = {"Content-Type": "application/json",
           "sortBy": {
               "sortDirection": "desc"
           }}

response = requests.request("POST", rpc_url, json=payload, headers=headers)

print(response.text)