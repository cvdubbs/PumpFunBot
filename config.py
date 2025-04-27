import os
from dotenv import load_dotenv
load_dotenv()

headers = {
  "Accept": "application/json",
  "X-API-Key": os.getenv("MORALIS_API_KEY")
}

# Current API Max is 100
NewTokenCount = 100
bitquery_url = "https://streaming.bitquery.io/eap"
moralis_url = f"https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/new?limit={NewTokenCount}"
moralis_bonding_url = f"https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/bonding?limit={NewTokenCount}"
discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")