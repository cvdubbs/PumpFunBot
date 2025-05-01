import os
from dotenv import load_dotenv
load_dotenv()

discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

quicknode_apikey = os.getenv("QUICKNODE_API_KEY")

moralis_headers = {
  "Accept": "application/json",
  "X-API-Key": os.getenv("MORALIS_API_KEY")
}

# Current API Max is 100
NewTokenCount = 100
bitquery_url = "https://streaming.bitquery.io/eap"
quicknode_url = f"https://proud-proud-theorem.solana-mainnet.quiknode.pro/{quicknode_apikey}/"
moralis_url = f"https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/new?limit={NewTokenCount}"
moralis_bonding_url = f"https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/bonding?limit={NewTokenCount}"

pumpfun_supply = 1000000000
