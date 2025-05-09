### Get the last hour of data and save to csv do no checks
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
        all_tokens_df = moralis_lib.get_hist_new_tokens(3)
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

# recommended_tokens = list()
# recommended_tokens.extend(final_filtered_tokens)

all_tokens_2h_df.to_csv("./data/all_tokens_2h_df.csv", index=False)