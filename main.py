import pandas as pd
import time
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import moralis_lib
import utils

# TODO: Add logging
# TODO: Add try and except repeats for requests for moralis
# TODO: Add Volume amounts to alpha

winner_tracking_dict = dict()
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
# Can add total volume here too using alpha_pos
print(final_filtered_tokens)

for tokenAddress in final_filtered_tokens:
    logo_url = moralis_lib.get_token_image(tokenAddress)
    discord_message = utils.clean_text_strings_for_discord(
        all_tokens_2h_df, 
        tokenAddress, 
        *utils.get_output_info(tokenAddress))
    utils.send_discord_message(discord_message, logo_url)

utils.append_to_file("./data/recommended_tokens.txt", final_filtered_tokens)

recommended_tokens = list()
recommended_tokens.extend(final_filtered_tokens)
loop = 0
while True:
    try:
        #### Check for coins that now meet marketcap
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
        print(f"final filtered tokens: {final_filtered_tokens}")
        for tokenAddress in final_filtered_tokens:
            logo_url = moralis_lib.get_token_image(tokenAddress)
            discord_message = utils.clean_text_strings_for_discord(
                all_tokens_2h_df, 
                tokenAddress, 
                *utils.get_output_info(tokenAddress))
            utils.send_discord_message(discord_message, logo_url)
        recommended_tokens.extend(final_filtered_tokens)
        ### Check for winners
        ### use winner_tracking_dict to store last max mkt cap  
        print("Checking for winners")
        for tokenAddress in recommended_tokens:
            max_mkt_cap = moralis_lib.get_max_mktcap(tokenAddress)
            
            # Initialize token in tracking dict if not present
            if tokenAddress not in winner_tracking_dict.keys():
                if max_mkt_cap > 60000:
                    token_name = all_tokens_2h_df.loc[all_tokens_2h_df['tokenAddress'] == tokenAddress, 'name'].iloc[0]
                    discord_message = f"Winner Found: {token_name} with market cap of {max_mkt_cap}"
                    utils.send_discord_message(discord_message)
                    winner_tracking_dict[tokenAddress] = max_mkt_cap
                    # Also track which thresholds this token has triggered
                    winner_tracking_dict[f"{tokenAddress}_triggered"] = [60000]
                else:
                    # Initialize with current market cap but don't send message yet
                    winner_tracking_dict[tokenAddress] = max_mkt_cap
                    winner_tracking_dict[f"{tokenAddress}_triggered"] = []
                continue
            
            # Skip if market cap is not higher than last recorded value
            if max_mkt_cap <= winner_tracking_dict[tokenAddress]:
                continue
            
            # Update the tracked market cap
            winner_tracking_dict[tokenAddress] = max_mkt_cap
            
            # Check thresholds and only trigger if not previously triggered
            thresholds = [
                (120000, 200000),
                (200000, 500000),
                (500000, 1000000),
                (1000000, float('inf'))
            ]
            
            triggered_list = winner_tracking_dict.get(f"{tokenAddress}_triggered", [])
            
            for lower, upper in thresholds:
                if max_mkt_cap > lower and max_mkt_cap < upper and lower not in triggered_list:
                    discord_update_message = f"Winner Found: {all_tokens_2h_df[all_tokens_2h_df['tokenAddress'] == tokenAddress]} with market cap of {(float(max_mkt_cap) // 1000) * 1000} - ({tokenAddress})"
                    utils.send_discord_message(discord_update_message)
                    triggered_list.append(lower)
                    winner_tracking_dict[f"{tokenAddress}_triggered"] = triggered_list
                    break

        # Writing the list to a file
        utils.append_to_file("./data/recommended_tokens.txt", final_filtered_tokens)
        time.sleep(90)
    except Exception as e:
        print(f"Error occurred: {e}, retrying in 30 seconds...")
        time.sleep(30)


# Run Dev Wallet to Awesome Maker List

# Check All Wallets interacted with to smart wallet list

