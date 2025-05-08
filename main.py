import pandas as pd
import time
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import moralis_lib
import utils
import config

# TODO: Add logging
# TODO: Min holder amount

###### Get History from Newest Tokens
all_tokens_df = None
while all_tokens_df is None:
    try:
        all_tokens_df = moralis_lib.get_hist_new_tokens(6)
    except Exception as e:
        print(f"Error occurred while fetching new tokens: {e}")
        time.sleep(60)

# only 2 hrs
all_tokens_2h_df = utils.filter_only_last_two_hours(all_tokens_df)

#### This gives us universe of possible coins to buy list
# Market Cap Restriction
all_tokens_2h_mktcap_df = all_tokens_2h_df[(all_tokens_2h_df['fullyDilutedValuation'] >= 15000) & (all_tokens_2h_df['fullyDilutedValuation'] <= 49000)]

rugchecked_tokens = utils.list_rug_checked_tokens(all_tokens_2h_mktcap_df)
check_df = all_tokens_2h_mktcap_df[all_tokens_2h_mktcap_df['tokenAddress'].isin(rugchecked_tokens)]

filtered_tokens_by_marketcap = [token for token in rugchecked_tokens if (moralis_lib.get_pumpfun_marketcap(token) >= 15000 and moralis_lib.get_pumpfun_marketcap(token) >=  .9 * moralis_lib.get_max_mktcap(token))]
mid_final_filtered_tokens = [token for token in filtered_tokens_by_marketcap if moralis_lib.alpha_pos(token, '5m') >= 1]
final_filtered_tokens = [token for token in mid_final_filtered_tokens if moralis_lib.alpha_pos(token, '1h') >= 0]
final_filtered_tokens = [token for token in final_filtered_tokens if moralis_lib.alpha_vol(token) >= 20000]
# Can add total volume here too using alpha_pos
print(final_filtered_tokens)

for tokenAddress in final_filtered_tokens:
    logo_url = moralis_lib.get_token_image(tokenAddress)
    discord_message = utils.clean_text_strings_for_discord(
        all_tokens_2h_df, 
        tokenAddress, 
        *utils.get_output_info(tokenAddress))
    utils.send_discord_message(discord_message, config.discord_webhook_url, logo_url)

utils.append_to_file("./data/recommended_tokens.txt", final_filtered_tokens)

recommended_tokens = list()
recommended_tokens.extend(final_filtered_tokens)
loop = 0
while True:
    try:
        #### Check for coins that now meet marketcap
        utils.send_discord_message("starting token search and filter loop", config.discord_webhook_logs_url)
        loop += 1
        print(f"Loop {loop}")
        print("Getting bonding tokens")
        tokens_to_re_consider = moralis_lib.get_bonding_tokens()
        tokens_to_re_consider = tokens_to_re_consider[(tokens_to_re_consider['fullyDilutedValuation'] >= 15000) & (tokens_to_re_consider['fullyDilutedValuation'] <= 49000)]
        update_tokens = all_tokens_2h_df[all_tokens_2h_df['tokenAddress'].isin(tokens_to_re_consider['tokenAddress'].unique().tolist())].copy()
        valuation_dict = dict(zip(tokens_to_re_consider['tokenAddress'], tokens_to_re_consider['fullyDilutedValuation']))
        update_tokens['fullyDilutedValuation'] = update_tokens['tokenAddress'].map(valuation_dict)

        # update_tokens needs rug check now + new
        print("Getting new tokens")
        new_tokens_to_add_df = moralis_lib.get_new_tokens()
        new_tokens_to_add_df = new_tokens_to_add_df[~new_tokens_to_add_df['tokenAddress'].isin(all_tokens_2h_df['tokenAddress'].unique().tolist())]
        all_tokens_2h_df = pd.concat([all_tokens_2h_df, new_tokens_to_add_df], ignore_index=True)
        new_tokens_to_add_mktcap_df = new_tokens_to_add_df[(new_tokens_to_add_df['fullyDilutedValuation'] >= 15000) & (new_tokens_to_add_df['fullyDilutedValuation'] <= 49000)]
        latest_check = pd.concat([new_tokens_to_add_mktcap_df, update_tokens], ignore_index=True)
        rugchecked_tokens = utils.list_rug_checked_tokens(latest_check)
        filtered_tokens = [token for token in rugchecked_tokens if token not in recommended_tokens]
        all_tokens_2h_df = utils.filter_only_last_two_hours(all_tokens_2h_df)
        filtered_tokens_by_marketcap = [token for token in filtered_tokens if (moralis_lib.get_pumpfun_marketcap(token) >= 15000 and moralis_lib.get_pumpfun_marketcap(token) >=  .9 * moralis_lib.get_max_mktcap(token))]
        mid_final_filtered_tokens = [token for token in filtered_tokens_by_marketcap if moralis_lib.alpha_pos(token, '5m') >= 1]
        final_filtered_tokens = [token for token in mid_final_filtered_tokens if moralis_lib.alpha_pos(token, '1h') >= 0]
        final_filtered_tokens = [token for token in final_filtered_tokens if moralis_lib.alpha_vol(token) >= 20000]
        print(f"final filtered tokens: {final_filtered_tokens}")
        for tokenAddress in final_filtered_tokens:
            logo_url = moralis_lib.get_token_image(tokenAddress)
            discord_message = utils.clean_text_strings_for_discord(
                all_tokens_2h_df, 
                tokenAddress, 
                *utils.get_output_info(tokenAddress))
            utils.send_discord_message(discord_message, config.discord_webhook_url, logo_url)
        recommended_tokens.extend(final_filtered_tokens)
 
        # Writing the list to a file
        utils.append_to_file("./data/recommended_tokens.txt", final_filtered_tokens)
        utils.send_discord_message("finished token search and filter loop", config.discord_webhook_logs_url)
        print(f"Sleeping for {config.sleep_time} seconds")
        time.sleep(config.sleep_time)
    except Exception as e:
        print(f"Error occurred: {e}, retrying in 30 seconds...")
        utils.send_discord_message("errored token search and filter loop, trying again in 30 seconds", config.discord_webhook_logs_url)
        time.sleep(30)


# Run Dev Wallet to Awesome Maker List

# Check All Wallets interacted with to smart wallet list

