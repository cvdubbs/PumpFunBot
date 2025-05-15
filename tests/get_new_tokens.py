import sys
import os
# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import moralis_lib


try:
    all_tokens_df = moralis_lib.get_hist_new_tokens(0)
    print("Single new tokens fetched successfully.")
except Exception as e:
    print(f"Error occurred while fetching single new tokens: {e}")

try:
    all_tokens_df = moralis_lib.get_hist_new_tokens(5)
    print("5 new tokens fetched successfully.")
except Exception as e:
    print(f"Error occurred while fetching single new tokens: {e}")

try:
    all_tokens_df = moralis_lib.get_hist_new_tokens(10)
    print("10 new tokens fetched successfully.")
except Exception as e:
    print(f"Error occurred while fetching single new tokens: {e}")


try:
    all_tokens_df = moralis_lib.get_hist_new_tokens(18)
    print("18 new tokens fetched successfully.")
except Exception as e:
    print(f"Error occurred while fetching 18 new tokens: {e}")

