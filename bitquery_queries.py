creation_date_creator_query = """
    query MyQuery ($tokenAddress: String) {
  Solana(network: solana) {
    Instructions(
      where: {Instruction: {Accounts: {includes: {Address: {is: $tokenAddress}}}, Program: {Name: {is: "pump"}, Method: {is: "create"}}}}
    ) {
      Block{
        Time
      }
      Transaction {
        Signer
        Signature
      }
      Instruction {
        Accounts {
          Address
        }
      }
    }
  }
}"""

top_token_holders_query = """
    query MyQuery ($tokenAddress: String) {
    Solana {
        BalanceUpdates(
        limit: {count: 11}
        orderBy: {descendingByField: "BalanceUpdate_Holding_maximum"}
        where: {BalanceUpdate: {Currency: {MintAddress: {is: $tokenAddress}}}, Transaction: {Result: {Success: true}}}
        ) {
        BalanceUpdate {
            Currency {
            Name
            MintAddress
            Symbol
            }
            Account {
            Address
            }
            Holding: PostBalance(maximum: Block_Slot)
        }
        }
    }
    }
"""

dev_sold_query = """
    query MyQuery ($dev: String, $token:String){
    Solana {
        BalanceUpdates(
        where: {BalanceUpdate: {Account: {Owner: {is: $dev}}, Currency: {MintAddress: {is: $token}}}}
        ){
        BalanceUpdate{
            balance:PostBalance(maximum:Block_Slot)
        }
        }
    }
    }
"""


first_100_buyers="""
    query MyQuery ($tokenAddress:String){
    Solana {
        DEXTrades(
        where: {
            Trade: {
            Buy: {
                Currency: {
                MintAddress: {
                    is: $tokenAddress
                }
                }
            }
            }
        }
        limit: { count: 100 }
        orderBy: { ascending: Block_Time }
        ) {
        Trade {
            Buy {
            Amount
            Account {
                Token {
                Owner
                }
            }
            }
        }
        }
    }
    }
"""


check_snipers = """
    query MyQuery ($tokenAddress:String!, $ownerAddresses: [String!]!) {
    Solana {
        BalanceUpdates(
        where: {
            BalanceUpdate: {
            Account: {
                Token: {
                Owner: {
                    in: $ownerAddresses
                }
                }
            }
            Currency: {
                MintAddress: { is: $tokenAddress }
            }
            }
        }
        ) {
        BalanceUpdate {
            Account {
            Token {
                Owner
            }
            }
            balance: PostBalance(maximum: Block_Slot)
        }
        }
    }
    }
"""

#### This is not right
liquidity = """
    {
    Solana {
        BalanceUpdates(
        where: {Block: {Time: {since: "2024-06-25T07:00:00Z"}},
            BalanceUpdate: {Account: {Token: {Owner: {in: [
        "BesTLFfCP9tAuUDWnqPdtDXZRu5xK6XD8TrABXGBECuf",
        "62dvmMKAfnt8jSdT3ToZtxAasx7Ud1tJ6xWsjwwhfaEQ",
        "73ZzSgNi27V9MdNQYyE39Vs9m1P9ZKgGPCHAJHin5gLd",
        "DwPwU1PAjTXtYNYkeR6awYMDBdSEk12npKzJWKbDHMta",
        "FJ4P2a2FqaWmqYpBw9eEfWD6cXV3F2qLPHvAA5jozscS",
        "6crUHiCoxZsQuxdMAB18VATKrg7ToyTVxt7MbLYmtugu"
    ]}}},
            Currency: {Native: false}}}
        ) {
        BalanceUpdate {
            Account {
            Token {
                Owner
            }
            Address
            }
            Currency {
            MintAddress
            Native
            }
            PostBalance(maximum: Block_Slot)
        }
        }
    }
    }
"""

### Needs datetime adj
volume_query = """
    query MyQuery ($tokenAddress: String){
    Solana {
        DEXTradeByTokens(
        where: {
            Trade: {
            Currency: {
                MintAddress: { is: $tokenAddress }
            }
            Dex: { ProtocolName: { is: "pump" } }
            }
            Block: { Time: { since: "2025-04-01T11:00:00Z" } }
        }
        ) {
        Trade {
            Currency {
            Name
            Symbol
            MintAddress
            }
            Dex {
            ProtocolName
            ProtocolFamily
            }
        }
        TradeVolume: sum(of: Trade_Amount)
        }
    }
    }
"""
