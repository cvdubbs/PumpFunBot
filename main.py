import os
import pandas as pd
import json
import requests
import time

from dotenv import load_dotenv
load_dotenv()

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import config
import bq_lib
import moralis_lib
import quicknode_lib
import utils


###### Get History from Newest Tokens
all_tokens_df = moralis_lib.get_hist_new_tokens(3)

# only 2 hrs
all_tokens_2h_df = utils.filter_only_last_two_hours(all_tokens_df)

#### This gives us universe of possible coins to buy list
# Market Cap Restriction
all_tokens_2h_mktcap_df = all_tokens_2h_df[(all_tokens_2h_df['fullyDilutedValuation'] >= 15000) & (all_tokens_2h_df['fullyDilutedValuation'] <= 49000)]

rugchecked_tokens = utils.list_rug_checked_tokens(all_tokens_2h_mktcap_df)
check_df = all_tokens_2h_mktcap_df[all_tokens_2h_mktcap_df['tokenAddress'].isin(rugchecked_tokens)]

filtered_tokens_by_marketcap = [token for token in rugchecked_tokens if moralis_lib.get_pumpfun_marketcap(token) >= 15000]
mid_final_filtered_tokens = [token for token in filtered_tokens_by_marketcap if moralis_lib.alpha_pos(token, '5m') >= 1]
final_filtered_tokens = [token for token in mid_final_filtered_tokens if moralis_lib.alpha_pos(token, '1h') >= 0]
# Can add volume here too using alpha_pos
print(final_filtered_tokens)

for tokenAddress in final_filtered_tokens:
    mkt_cap = moralis_lib.get_pumpfun_marketcap(tokenAddress)
    dev_wallet = moralis_lib.get_dev_wallet(tokenAddress)
    creation_time = moralis_lib.get_creation_time(tokenAddress)
    age = utils.get_age(creation_time)
    holder_count, transfer_count, airdrop_count = moralis_lib.get_token_holder_counts(tokenAddress)
    logo_url = moralis_lib.get_token_image(tokenAddress)
    symbol_str = f"{all_tokens_2h_df['symbol'][all_tokens_2h_df['tokenAddress'] == tokenAddress].values[0]} \n"
    name_str = f"# {all_tokens_2h_df['name'][all_tokens_2h_df['tokenAddress'] == tokenAddress].values[0]} \n"
    tokenAddress_str = f"{tokenAddress} \n"
    mktcap_str = f" \n- 🏷️ MktCap: {round(mkt_cap,0)/1000}k  \n"
    liquidity_str = f"- 💧 Liquidity: {round(float(all_tokens_2h_df['liquidity'][all_tokens_2h_df['tokenAddress'] == tokenAddress].values[0])/1000,0)}k  \n"
    holder_str = f"- 👥 Holder Count: {holder_count} - Airdropped: {airdrop_count} - Transfered: {transfer_count} \n"
    age_str = f"- ⏳ Age: {age} \n"
    dev_wallet_str = f"- 👤 Dev Wallet: [{dev_wallet}](https://solscan.io/account/{dev_wallet}?activity_type=ACTIVITY_SPL_INIT_MINT#defiactivities) \n"
    trade_links_str = f"[AXI](<https://axiom.trade/meme/{tokenAddress}>) - [GMGN](https://gmgn.ai/sol/token/{tokenAddress})"
    utils.send_discord_message(name_str +  symbol_str + tokenAddress_str + mktcap_str + liquidity_str + holder_str + age_str + dev_wallet_str + trade_links_str, logo_url)

# with open("./data/recommended_tokens.txt", "a") as file:
#             for item in final_filtered_tokens:
#                 file.write(item + "\n")
utils.append_to_file("./data/recommended_tokens.txt", final_filtered_tokens)

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
        mid_final_filtered_tokens = [token for token in filtered_tokens_by_marketcap if moralis_lib.alpha_pos(token, '5m') >= 1]
        final_filtered_tokens = [token for token in mid_final_filtered_tokens if moralis_lib.alpha_pos(token, '1h') >= 0]
        print(final_filtered_tokens)
        for tokenAddress in final_filtered_tokens:
            mkt_cap = moralis_lib.get_pumpfun_marketcap(tokenAddress)
            dev_wallet = moralis_lib.get_dev_wallet(tokenAddress)
            creation_time = moralis_lib.get_creation_time(tokenAddress)
            age = utils.get_age(creation_time)
            holder_count, transfer_count, airdrop_count = moralis_lib.get_token_holder_counts(tokenAddress)
            logo_url = moralis_lib.get_token_image(tokenAddress)
            symbol_str = f"{all_tokens_2h_df['symbol'][all_tokens_2h_df['tokenAddress'] == tokenAddress].values[0]} \n"
            name_str = f"# {all_tokens_2h_df['name'][all_tokens_2h_df['tokenAddress'] == tokenAddress].values[0]} \n"
            tokenAddress_str = f"{tokenAddress} \n"
            mktcap_str = f" \n- 🏷️ MktCap: {round(mkt_cap,0)/1000}k  \n"
            liquidity_str = f"- 💧 Liquidity: {round(float(all_tokens_2h_df['liquidity'][all_tokens_2h_df['tokenAddress'] == tokenAddress].values[0])/1000,0)}k  \n"
            holder_str = f"- 👥 Holder Count: {holder_count} - Airdropped: {airdrop_count} - Transfered: {transfer_count} \n"
            age_str = f"- ⏳ Age: {age} \n"
            dev_wallet_str = f"- 👤 Dev Wallet: [{dev_wallet}](https://solscan.io/account/{dev_wallet}?activity_type=ACTIVITY_SPL_INIT_MINT#defiactivities) \n"
            trade_links_str = f"[AXI](<https://axiom.trade/meme/{tokenAddress}>) - [GMGN](https://gmgn.ai/sol/token/{tokenAddress})"
            utils.send_discord_message(name_str + symbol_str + tokenAddress_str + mktcap_str + liquidity_str + holder_str + age_str + dev_wallet_str + trade_links_str, logo_url)
        recommended_tokens.extend(final_filtered_tokens)
        # Writing the list to a file
        utils.append_to_file("./data/recommended_tokens.txt", final_filtered_tokens)
        time.sleep(90)
    except Exception as e:
        print(f"Error occurred: {e}, retrying in 30 seconds...")
        time.sleep(30)


# Run Dev Wallet to Awesome Maker List

# Check All Wallets interacted with to smart wallet list

