import requests
import json
import config

def get_bundles(tokenAddress: str):
    url = "https://api.syrax.ai/v1/token/bundle"

    querystring = {"token":tokenAddress}

    response = requests.request("GET", url, params=querystring)

    text = json.loads(response.text)

    total_tokens = 0
    total_sol = 0
    for bundles in range(0, len(text['bundles'])):
        for trades in range(0, len(text['bundles'][bundles]['trades'])):
            total_sol += text['bundles'][bundles]['trades'][trades]['sol_amount']
            total_tokens += text['bundles'][bundles]['trades'][trades]['token_amount']
    return round(total_sol,1), round((total_tokens/config.pumpfun_supply)*100,2)


def get_bundle_wallets(tokenAddress: str):
    url = "https://api.syrax.ai/v1/token/bundle"

    querystring = {"token":tokenAddress}

    response = requests.request("GET", url, params=querystring)

    text = json.loads(response.text)

    wallet_list = list()
    for bundles in range(0, len(text['bundles'])):
        for trades in range(0, len(text['bundles'][bundles]['trades'])):
            wallet_list.append(text['bundles'][bundles]['trades'][trades]['trader'])
    return wallet_list

# total_sol, total_tokens = get_bundles("6JfGs2hLL6gzX4sVhu2apGMRyMnCkWVDuBNCpfwjpump")
# print(f"Total SOL: {total_sol}, Total Tokens Percentage: {total_tokens}")
