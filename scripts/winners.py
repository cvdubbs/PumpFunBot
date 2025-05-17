import pandas as pd
import time
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import sys
import os
# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import moralis_lib
import utils
import config

## Check for winners
## use winner_tracking_dict to store last max mkt cap 

load_calls = pd.read_csv("./data/tracking_calls_mktcap.csv", header=None, names=['tokenAddress', 'mktcap'], index_col=False, skipinitialspace=True)
load_calls['tokenAddress'] = load_calls['tokenAddress'] 
load_calls['tokenAddress'] = load_calls['tokenAddress'].str.replace(r'\s+', '', regex=True)

tokenAddyStart = input("Enter the tokenAddress to start with: ")
target_index = load_calls[load_calls['tokenAddress'] == tokenAddyStart].index

if len(target_index) > 0:
    # Get the first occurrence if there are multiple matches
    first_occurrence = target_index[0]
    
    # Create a new DataFrame with rows including and after the target row
    load_calls = load_calls.iloc[first_occurrence:]
else:
    print("No row found with the specified tokenAddress")

load_calls['max_mktcap'] = load_calls['tokenAddress'].apply(lambda address: moralis_lib.get_max_mktcap(address, '1d'))
load_calls['multipler'] = load_calls['max_mktcap'] / load_calls['mktcap']

utils.send_discord_message(f":dart: 24hrs Mediate Rtn: {round(load_calls['multipler'].median() - 1,2) * 100}%", config.discord_webhook_url)
utils.send_discord_message(f":dart: 24hrs Mean Rtn: {round(load_calls['multipler'].mean() - 1,2) * 100}%", config.discord_webhook_url)
utils.send_discord_message(f":dart: 24hrs Max Rtn: {round(load_calls['multipler'].max() - 1,2) * 100}% --> {load_calls.loc[load_calls['multipler'] == load_calls['multipler'].max(), 'tokenAddress'].iloc[0]}", config.discord_webhook_url)


# for tokenAddy in load_calls['tokenAddress']:
#     print(f'{moralis_lib.get_max_mktcap(tokenAddy, '1d')}')
# winner_tracking_dict = dict()
# print("Checking for winners")
# recommended_tokens = utils.read_text_to_list("./data/recommended_tokens.txt")
# recommended_tokens = list(dict.fromkeys(recommended_tokens))
# bonded_tokens_count = 0
# for i in range(0,len(recommended_tokens)):
#     try:
#         max_mkt_cap = (moralis_lib.get_max_mktcap(recommended_tokens[i], '1d'))
#         print(f"Max mkt cap for {recommended_tokens[i]} is {max_mkt_cap}")
#     except Exception as e:
#         time.sleep(1)
#         continue
#     if max_mkt_cap >58000:
#         bonded_tokens_count += 1
#     if max_mkt_cap > 100000:
#         metadata = moralis_lib.get_metadata(recommended_tokens[i])
#         token_name = metadata['name']
#         mktcap_clean = int(max_mkt_cap // 1000)
#         output_mktcap = format(mktcap_clean, ",")
#         utils.send_discord_message(f":rotating_light: - Winner Found: {token_name} - ({recommended_tokens[i]}) \n with market cap of {output_mktcap}k", config.discord_webhook_url)
# utils.send_discord_message(f":dart: Win Rate: {round(bonded_tokens_count/len(recommended_tokens),2) * 100}% --> {bonded_tokens_count} out of {len(recommended_tokens)} tokens bonded :dart:", config.discord_webhook_url)


# # ####### TEST
# tokenAddress = "Be1M6bKTYX7uniwEdCuRA86HMvzKKqJTx69EDJwqpump"
# max_mkt_cap = (moralis_lib.get_max_mktcap(tokenAddress, '1d'))
# pairs = moralis_lib.get_token_pairs(tokenAddress)
# pairAddress = moralis_lib.get_main_pair_address(tokenAddress)
# ohlc_data = moralis_lib.get_token_ohlc(pairAddress, '1d')
