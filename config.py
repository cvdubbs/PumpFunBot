import os
from dotenv import load_dotenv
load_dotenv()

discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
discord_webhook_logs_url = os.getenv("DISCORD_WEBHOOK_LOGS_URL")

quicknode_apikey = os.getenv("QUICKNODE_API_KEY")

moralis_headers = {
  "Accept": "application/json",
  "X-API-Key": os.getenv("MORALIS_API_KEY")
}

# Current API Max is 100
NewTokenCount = 100
quicknode_url = f"https://divine-morning-choice.solana-mainnet.quiknode.pro/{quicknode_apikey}/"
moralis_url = f"https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/new?limit={NewTokenCount}"
moralis_bonding_url = f"https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/bonding?limit={NewTokenCount}"

pumpfun_supply = 1000000000

sleep_time = 30

# bitquery_url = "https://streaming.bitquery.io/eap"