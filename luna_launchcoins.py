import requests
import json
import time
from typing import List, Dict, Any, Optional
import config

def get_all_tokens_created_by_address(creator_address: str, rpc_url: str) -> List[Dict[str, Any]]:
    """
    Find all tokens created by a specific address
    
    Args:
        creator_address: The Solana address that created the tokens
        rpc_url: QuickNode RPC URL
        
    Returns:
        List of tokens created by the address
    """
    headers = {
        "Content-Type": "application/json",
    }
    
    # Step 1: Get all signatures for the creator address
    all_signatures = []
    before_signature = None
    
    print(f"Fetching transaction signatures for {creator_address}...")
    
    max_loop = 20
    loop = 0
    while True:
        params = {"limit": 1000}
        if before_signature:
            params["before"] = before_signature
            
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [
                creator_address,
                params
            ]
        }
        
        try:
            loop += 1
            if loop > max_loop:
                print("Max loop reached, stopping...")
                break
            response = requests.post(rpc_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if "result" not in data or not data["result"]:
                break
                
            signatures = data["result"]
            if not signatures:
                break
                
            all_signatures.extend(signatures)
            print(f"Fetched {len(signatures)} signatures, total: {len(all_signatures)}")
            
            before_signature = signatures[-1]["signature"]
            
        except Exception as e:
            print(f"Error fetching signatures: {str(e)}")
            break
    
    created_tokens = []
    
    # Step 2: Analyze each transaction to find token creation
    print(f"\nAnalyzing {len(all_signatures)} transactions for token creation...")
    
    for i, sig_info in enumerate(all_signatures):
        if i % 20 == 0:
            print(f"Progress: {i}/{len(all_signatures)} transactions analyzed")
            
        signature = sig_info["signature"]
        
        # Skip failed transactions
        if "err" in sig_info and sig_info["err"] is not None:
            continue
            
        # Get transaction details
        tx_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                signature,
                {
                    "encoding": "jsonParsed",
                    "maxSupportedTransactionVersion": 0
                }
            ]
        }
        
        try:
            tx_response = requests.post(rpc_url, headers=headers, json=tx_payload)
            tx_response.raise_for_status()
            tx_data = tx_response.json()
            
            if "result" not in tx_data or not tx_data["result"]:
                continue
                
            transaction = tx_data["result"]
            
            # Check if this is a token creation transaction
            token_mint = is_token_creation_transaction(transaction, creator_address)
            
            if token_mint:
                # Get token details if available
                token_details = get_token_details(token_mint, rpc_url)
                
                created_tokens.append({
                    "token_mint": token_mint,
                    "creation_signature": signature,
                    "block_time": transaction.get("blockTime"),
                    "creation_date": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(transaction["blockTime"])) if "blockTime" in transaction else "Unknown",
                    "token_details": token_details
                })
                
                print(f"Found token creation: {token_mint}")
                
        except Exception as e:
            print(f"Error processing transaction {signature}: {str(e)}")
            
        # Add a small delay to avoid rate limiting
        time.sleep(0.1)
    
    return created_tokens

def is_token_creation_transaction(transaction: Dict[str, Any], creator_address: str) -> Optional[str]:
    """
    Check if a transaction is a token creation transaction
    
    Args:
        transaction: Transaction data
        creator_address: The address of the token creator
        
    Returns:
        Token mint address if it's a token creation transaction, None otherwise
    """
    # Check for System Program create account + Token Program initialize mint pattern
    if "meta" not in transaction or "innerInstructions" not in transaction["meta"]:
        return None
        
    token_program_id = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"  # SPL Token program
    token_2022_program_id = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"  # Token-2022 program
    system_program_id = "11111111111111111111111111111111"  # System program
    
    # Look for initialize mint instruction
    if "transaction" in transaction and "message" in transaction["transaction"]:
        message = transaction["transaction"]["message"]
        instructions = message.get("instructions", [])
        account_keys = message.get("accountKeys", [])
        
        # First check in main instructions
        for instruction in instructions:
            program_id = instruction.get("programId")
            if program_id in [token_program_id, token_2022_program_id]:
                if "parsed" in instruction and "type" in instruction["parsed"]:
                    if instruction["parsed"]["type"] == "initializeMint":
                        # This is a token initialization
                        mint_account = instruction["parsed"]["info"].get("mint")
                        mint_authority = instruction["parsed"]["info"].get("mintAuthority")
                        
                        if mint_authority == creator_address:
                            return mint_account
        
        # Also check inner instructions
        inner_instructions = transaction["meta"].get("innerInstructions", [])
        for inner_instruction_set in inner_instructions:
            for instruction in inner_instruction_set.get("instructions", []):
                if "parsed" in instruction and "type" in instruction["parsed"]:
                    if instruction["parsed"]["type"] == "initializeMint":
                        mint_account = instruction["parsed"]["info"].get("mint")
                        mint_authority = instruction["parsed"]["info"].get("mintAuthority") 
                        
                        if mint_authority == creator_address:
                            return mint_account
    
    return None

def get_token_details(token_mint: str, rpc_url: str) -> Dict[str, Any]:
    """
    Get details about a token
    
    Args:
        token_mint: The token mint address
        rpc_url: QuickNode RPC URL
        
    Returns:
        Token details
    """
    headers = {
        "Content-Type": "application/json",
    }
    
    # Get token supply
    supply_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenSupply",
        "params": [token_mint]
    }
    
    token_details = {
        "mint": token_mint,
        "supply": "Unknown",
        "decimals": 0,
        "symbol": "Unknown",
        "name": "Unknown"
    }
    
    try:
        response = requests.post(rpc_url, headers=headers, json=supply_payload)
        response.raise_for_status()
        data = response.json()
        
        if "result" in data and "value" in data["result"]:
            token_details["supply"] = data["result"]["value"]["amount"]
            token_details["decimals"] = data["result"]["value"]["decimals"]
            
    except Exception as e:
        print(f"Error getting token supply: {str(e)}")
    
    # Try to get metadata (if available)
    # This is more complex and might require additional APIs
    
    return token_details

def main():
    # Replace with your QuickNode endpoint URL
    QUICKNODE_RPC_URL = config.quicknode_url
    
    # The address that created tokens
    CREATOR_ADDRESS = "5qWya6UjwWnGVhdSBL3hyZ7B45jbk6Byt1hwd7ohEGXE"
    
    print(f"Finding all tokens created by: {CREATOR_ADDRESS}")
    created_tokens = get_all_tokens_created_by_address(CREATOR_ADDRESS, QUICKNODE_RPC_URL)
    
    print(f"\nFound {len(created_tokens)} tokens created by this address.")
    
    # Print summary
    for i, token in enumerate(created_tokens, 1):
        print(f"\nToken {i}:")
        print(f"  Mint Address: {token['token_mint']}")
        print(f"  Creation Date: {token['creation_date']}")
        print(f"  Supply: {token['token_details']['supply']}")
        print(f"  Decimals: {token['token_details']['decimals']}")
        
    # Save full data to JSON
    with open(f"created_tokens_{CREATOR_ADDRESS}.json", "w") as f:
        json.dump(created_tokens, f, indent=2)
        print(f"\nFull token data saved to created_tokens_{CREATOR_ADDRESS}.json")

if __name__ == "__main__":
    main()