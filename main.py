import os
import pandas as pd
import json
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()
import requests

import config
import bq_lib
import moralis_lib
import utils

###### Get History from Newest Tokens
all_tokens_df = moralis_lib.get_hist_new_tokens()

# only 2 hrs
all_tokens_2h_df = utils.filter_only_last_two_hours(all_tokens_df)

# Get bonding coins w/ marketcap joined to the last 2hours of coins
### This is needed in a never ending while loop to keep checking every 5 minutes? maybe less. 

#### This gives us universe of possible coins to buy list
# Market Cap Restriction
all_tokens_2h_mktcap_df = all_tokens_2h_df[(all_tokens_2h_df['fullyDilutedValuation'] >= 15000) & (all_tokens_2h_df['fullyDilutedValuation'] <= 49000)]
# RUG CHECKERS

rugchecked_tokens = utils.list_rug_checked_tokens(all_tokens_2h_mktcap_df)
check_df = all_tokens_2h_mktcap_df[all_tokens_2h_mktcap_df['tokenAddress'].isin(rugchecked_tokens)]
tokens_to_re_consider = moralis_lib.get_bonding_tokens()
tokens_to_re_consider = tokens_to_re_consider[(tokens_to_re_consider['fullyDilutedValuation'] >= 15000) & (tokens_to_re_consider['fullyDilutedValuation'] <= 49000)]
filtered_tokens = [token for token in rugchecked_tokens if token in tokens_to_re_consider['tokenAddress'].unique().tolist()]

print(filtered_tokens)
utils.send_discord_message("Start up Luna Chaser Bot")
filtered_tokens_by_marketcap = [token for token in filtered_tokens if moralis_lib.get_pumpfun_marketcap(token) >= 15000]
final_filtered_tokens = [token for token in filtered_tokens_by_marketcap if moralis_lib.alpha_pos_5min(token) >= 1]

for tokenAddress in final_filtered_tokens:
        utils.send_discord_message(tokenAddress)

recommended_tokens = list()
recommended_tokens.extend(final_filtered_tokens)

while True:
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
        utils.send_discord_message(tokenAddress)
    recommended_tokens.extend(final_filtered_tokens)


# Run Dev Wallet to Awesome Maker List

# Check All Wallets interacted with to smart wallet list

