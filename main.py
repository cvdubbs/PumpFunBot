import os
import pandas as pd
import json
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()
import requests
import time

import config
import bq_lib
import moralis_lib
import utils

###### Compute from Moralis
# Get New Tokens - 100
# Get Bonding Tokens - 300
# Get Hist New Tokens - 2600 for 50 loops/2hrs
###### Get History from Newest Tokens
all_tokens_df = moralis_lib.get_hist_new_tokens(10)

# only 2 hrs
all_tokens_2h_df = utils.filter_only_last_two_hours(all_tokens_df)

#### This gives us universe of possible coins to buy list
# Market Cap Restriction
all_tokens_2h_mktcap_df = all_tokens_2h_df[(all_tokens_2h_df['fullyDilutedValuation'] >= 15000) & (all_tokens_2h_df['fullyDilutedValuation'] <= 49000)]

rugchecked_tokens = utils.list_rug_checked_tokens(all_tokens_2h_mktcap_df)
check_df = all_tokens_2h_mktcap_df[all_tokens_2h_mktcap_df['tokenAddress'].isin(rugchecked_tokens)]

print(rugchecked_tokens)
# utils.send_discord_message("Start up Luna Chaser Bot")
filtered_tokens_by_marketcap = [token for token in rugchecked_tokens if moralis_lib.get_pumpfun_marketcap(token) >= 15000]
final_filtered_tokens = [token for token in filtered_tokens_by_marketcap if moralis_lib.alpha_pos_5min(token) >= 1]

for tokenAddress in final_filtered_tokens:
    utils.send_discord_message(f"{tokenAddress} \n {all_tokens_2h_df['name'][all_tokens_2h_df['tokenAddress'] == tokenAddress].values[0]} \n {all_tokens_2h_df['symbol'][all_tokens_2h_df['tokenAddress'] == tokenAddress].values[0]} \n {all_tokens_2h_df['fullyDilutedValuation'][all_tokens_2h_df['tokenAddress'] == tokenAddress].values[0]}  \n [GMGN](https://gmgn.ai/sol/token/{tokenAddress})")

recommended_tokens = list()
recommended_tokens.extend(final_filtered_tokens)

while True:
    try:
        #### Check for coins that now meet marketcap
        tokens_to_re_consider = moralis_lib.get_bonding_tokens()
        tokens_to_re_consider = tokens_to_re_consider[(tokens_to_re_consider['fullyDilutedValuation'] >= 15000) & (tokens_to_re_consider['fullyDilutedValuation'] <= 49000)]
        update_tokens = all_tokens_2h_df[all_tokens_2h_df['tokenAddress'].isin(tokens_to_re_consider['tokenAddress'].unique().tolist())].copy()
        valuation_dict = dict(zip(tokens_to_re_consider['tokenAddress'], tokens_to_re_consider['fullyDilutedValuation']))
        update_tokens['fullyDilutedValuation'] = update_tokens['tokenAddress'].map(valuation_dict)

        # update_tokens needs rug check now + new
        new_tokens_to_add_df = moralis_lib.get_new_tokens()
        new_tokens_to_add_df = new_tokens_to_add_df[~new_tokens_to_add_df['tokenAddress'].isin(all_tokens_2h_df['tokenAddress'].unique().tolist())]
        all_tokens_2h_df = pd.concat([all_tokens_2h_df, new_tokens_to_add_df], ignore_index=True)
        new_tokens_to_add_mktcap_df = new_tokens_to_add_df[(new_tokens_to_add_df['fullyDilutedValuation'] >= 15000) & (new_tokens_to_add_df['fullyDilutedValuation'] <= 49000)]
        latest_check = pd.concat([new_tokens_to_add_mktcap_df, update_tokens], ignore_index=True)
        rugchecked_tokens = utils.list_rug_checked_tokens(latest_check)
        filtered_tokens = [token for token in rugchecked_tokens if token not in recommended_tokens]
        all_tokens_2h_df = utils.filter_only_last_two_hours(all_tokens_2h_df)
        filtered_tokens_by_marketcap = [token for token in filtered_tokens if moralis_lib.get_pumpfun_marketcap(token) >= 15000]
        final_filtered_tokens = [token for token in filtered_tokens_by_marketcap if moralis_lib.alpha_pos_5min(token) >= 1]
        for tokenAddress in final_filtered_tokens:
            utils.send_discord_message(f"{tokenAddress} \n {all_tokens_2h_df['name'][all_tokens_2h_df['tokenAddress'] == tokenAddress].values[0]} \n {all_tokens_2h_df['symbol'][all_tokens_2h_df['tokenAddress'] == tokenAddress].values[0]} \n [GMGN](https://gmgn.ai/sol/token/{tokenAddress})")
        recommended_tokens.extend(final_filtered_tokens)
        time.sleep(90)
    except:
        print("Error occurred, retrying in 30 seconds...")
        time.sleep(30)
        continue


# Run Dev Wallet to Awesome Maker List

# Check All Wallets interacted with to smart wallet list

