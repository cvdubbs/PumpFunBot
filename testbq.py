import os
import requests
import json
import pandas as pd
from dotenv import load_dotenv

import config
import utils
import bitquery_queries as bq

# Load environment variables from .env file
load_dotenv()


def get_bitquery(query_str: str, **query_variables) -> json:
    variables_dict = {}
    for key, value in query_variables.items():
        variables_dict[key] = value
    
    payload = json.dumps({
        "query": query_str,
        "variables": json.dumps(variables_dict)
    })

    headers = {
        'Content-Type': 'application/json',
        'Authorization': os.getenv("BITQUERY_API_KEY")
    }

    response = requests.request("POST", config.bitquery_url, headers=headers, data=payload)

    return json.loads(response.text)


def get_creation_time_dev(contract_address: str) -> tuple:
    data = get_bitquery(bq.creation_date_creator_query, tokenAddress=contract_address)
    dev_wallet = data['data']['Solana']['Instructions'][0]['Transaction']['Signer']
    create_time = data['data']['Solana']['Instructions'][0]['Block']['Time']
    return (dev_wallet, create_time)


def get_age(creation_time: str) -> str:
    hours, minutes, seconds = utils.calculate_time_difference(creation_time)
    return f'{hours} hrs: {minutes} mins: {seconds} secs'


def get_top_holders(contract_address: str) -> tuple:
    data = get_bitquery(bq.top_token_holders_query, tokenAddress=contract_address)
    return data


def total_top_owners_clean(contract_address: str) -> pd.DataFrame:
    top_holders_json = get_top_holders(contract_address)
    top_holders_list = list()
    # Skip 0 assuming it's the liquidity pool
    for holder_rank in range(1, len(top_holders_json['data']['Solana']['BalanceUpdates'])):
        wallet_address = top_holders_json['data']['Solana']['BalanceUpdates'][holder_rank]['BalanceUpdate']['Account']['Address']
        # Assumes supply of 1 Billion
        holding_percent = float(top_holders_json['data']['Solana']['BalanceUpdates'][holder_rank]['BalanceUpdate']['Holding'])/10000000
        top_holders_list.append((wallet_address, holding_percent))
    df = pd.DataFrame(top_holders_list, columns=['WALLET_ADDRES', 'HOLDING_PERCENT'])
    return df


def get_top_10_holders_ownership(contract_address: str) -> float:
    df = total_top_owners_clean(contract_address)
    return df['HOLDING_PERCENT'].sum()


def dev_owns(contract_address: str, dev_wallet: str):
    data = get_bitquery(bq.dev_sold_query, token=contract_address, dev=dev_wallet)
    dev_owns_percent = float(data['data']['Solana']['BalanceUpdates'][0]['BalanceUpdate']['balance'])/10000000
    return dev_owns_percent


def snipers_still_own(contract_address: str):
    data_first_100 = get_bitquery(bq.first_100_buyers, tokenAddress=contract_address)
    first_100_wallet_address_list = list()
    for wallet in range(0,100):
        wallet_address = data_first_100['data']['Solana']['DEXTrades'][wallet]['Trade']['Buy']['Account']['Token']['Owner']
        first_100_wallet_address_list.append(wallet_address)

    data = get_bitquery(bq.check_snipers, tokenAddress=contract_address, ownerAddresses=first_100_wallet_address_list)
    sniper_still_own = 0
    for wallet in range(0,100):
        if float(data['data']['Solana']['BalanceUpdates'][wallet]['BalanceUpdate']['balance']) > 0.01:
            sniper_still_own += 1
    return sniper_still_own


def check_snipers(contract_address: str):
    snipers_still_hold = snipers_still_own(contract_address)
    # Snipers sold part
    # Snipers bought more
    # Calc snipers ok or bad score
    # Return Score


### Clean Executions
dev_wallet, creation_time = (get_creation_time_dev("21AzFn8k4UDj2pfUwVSXton79XQK5HqaHPqzzHqJpump"))
age = get_age(creation_time)

top_10_own_float = get_top_10_holders_ownership("21AzFn8k4UDj2pfUwVSXton79XQK5HqaHPqzzHqJpump")

dev_percent_owned = dev_owns("21AzFn8k4UDj2pfUwVSXton79XQK5HqaHPqzzHqJpump", dev_wallet)

sniper_check = snipers_still_own("VbQZeascmDvT9cUeZcxmV6XcFL3bFWXFfvUhCyYpump")

