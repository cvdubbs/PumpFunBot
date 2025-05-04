import pandas as pd
import time
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import moralis_lib
import utils

## Check for winners
## use winner_tracking_dict to store last max mkt cap 
winner_tracking_dict = dict() 
print("Checking for winners")
recommended_tokens = utils.read_text_to_list("./data/recommended_tokens.txt")
recommended_tokens = list(dict.fromkeys(recommended_tokens))
for i in range(0,len(recommended_tokens)):
    try:
        max_mkt_cap = (moralis_lib.get_max_mktcap(recommended_tokens[i]))
        print(f"Max mkt cap for {recommended_tokens[i]} is {max_mkt_cap}")
    except Exception as e:
        time.sleep(1)
        continue
    if max_mkt_cap > 100000:
        metadata = moralis_lib.get_metadata(recommended_tokens[i])
        token_name = metadata['name']
        mktcap_clean = int(max_mkt_cap // 1000)
        output_mktcap = format(mktcap_clean, ",")
        utils.send_discord_message(f"Winner Found: {token_name} - ({recommended_tokens[i]}) \n with market cap of {output_mktcap}k")

