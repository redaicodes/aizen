import asyncio
import logging
import time
from typing import Dict, Optional

import aiohttp
from solders import pubkey
from solders import transaction

class RaydiumClient:
    """Client for interacting with the classic Raydium V4 AMM on Solana."""

    # Program IDs
    RAYDIUM_V4_PROGRAM_ID = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
    SERUM_PROGRAM_ID = "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"
    TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

    # Common token addresses (Mainnet)
    TOKENS = {
        "SOL":  "So11111111111111111111111111111111111111112",  # Wrapped SOL
        "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "RAY":  "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
        "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    }

    # =========================================================================
    # Correct "classic" vault addresses for SOL/USDC & RAY/USDC on mainnet.
    # These are pulled from Raydium's older official references.
    #
    # - amm_id: the Raydium AMM account
    # - pool_coin_token_account: vault for the "base" token
    # - pool_pc_token_account: vault for the "quote" token
    #
    # =========================================================================
    POOLS = {
        "SOL/USDC": {
            "amm_id": "58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2",  # Classic v4 SOL/USDC
            "base_mint": TOKENS["SOL"],
            "quote_mint": TOKENS["USDC"],
            "base_decimals": 9,
            "quote_decimals": 6,
            "base_symbol": "SOL",
            "quote_symbol": "USDC",
            "version": 4,
            "status": "official",
            # These vaults actually exist on mainnet for the old SOL/USDC AMM:
            "pool_coin_token_account": "6zB6qXg9uRf3r6b1rdvG6cKTrvWs1mxcpDGZLt7syeF8",  # SOL vault
            "pool_pc_token_account":   "7s9K2HyDwggbsWGkqQ9qeUAWWVNamAb9yKGEW57Jx3eX",  # USDC vault
        },
        "RAY/USDC": {
            "amm_id": "6UmmUiYoBEGPwZxr9W3txiydDfBGyeKa19jUNt9kNGkm",  # Classic v4 RAY/USDC
            "base_mint": TOKENS["RAY"],
            "quote_mint": TOKENS["USDC"],
            "base_decimals": 6,
            "quote_decimals": 6,
            "base_symbol": "RAY",
            "quote_symbol": "USDC",
            "version": 4,
            "status": "official",
            # Known mainnet vault addresses for RAY/USDC v4:
            "pool_coin_token_account": "Cz2XrnS67FyGkdf4LqFMsK1xqEH6fpsWv1CNRKyLBeH",  # RAY vault
            "pool_pc_token_account":   "8ZW3F25nve9yNTqbpX5a3qvFmEcozPytRUx92YX2TvB6",  # USDC vault
        },
        "BONK/USDC": {
            "amm_id": "8QaXeHBrShJTdtN1rWCccBxpSVvKksQ6NeJPqXJhLZXe",
            "base_mint": TOKENS["BONK"],
            "quote_mint": TOKENS["USDC"],
            "base_decimals": 5,
            "quote_decimals": 6,
            "base_symbol": "BONK",
            "quote_symbol": "USDC",
            "version": 4,
            "status": "official",
            # You would need to fill these with correct vault addresses if a
            # legacy BONK/USDC Raydium v4 pool still exists.
            "pool_coin_token_account": "",
            "pool_pc_token_account":   "",
        },
    }

    def __init__(self, solana_client):
        """
        Args:
            solana_client: Instance of your SolanaClient 
                           (must implement get_account_info, etc.)
        """
        self.solana = solana_client

        self.logger = logging.getLogger("RaydiumClient")
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.logger.info("Raydium client initialized")

    async def get_pool_info(self, name: str = "SOL/USDC") -> Dict:
        """
        Grabs the static pool meta from self.POOLS, checks on-chain data, merges, and returns.
        """
        try:
            # 1) Check if the pool is in the dictionary or reversed
            if name not in self.POOLS:
                tokens = name.split("/")
                reversed_name = f"{tokens[1]}/{tokens[0]}"
                if reversed_name not in self.POOLS:
                    raise ValueError(f"Pool {name} not found")
                else:
                    name = reversed_name

            pool_meta = self.POOLS[name]

            # 2) Get on-chain reserves 
            onchain_data = await self._get_onchain_pool_state(pool_meta)

            # 3) Merge static (pool_meta) + dynamic (onchain_data)
            pool_info = dict(pool_meta)
            pool_info.update(onchain_data)

            return pool_info

        except Exception as e:
            self.logger.error(f"Error in get_pool_info({name}): {e}")
            raise

    async def _get_onchain_pool_state(self, pool_meta: Dict) -> Dict:
        """
        Reads on-chain data for a Raydium pool and returns dynamic fields:
        base_reserve, quote_reserve, liquidity, price, etc.
        """
        try:
            # Fetch vault addresses from the pool metadata
            coin_vault_pubkey = pool_meta.get("pool_coin_token_account")
            pc_vault_pubkey   = pool_meta.get("pool_pc_token_account")

            if not coin_vault_pubkey or not pc_vault_pubkey:
                raise ValueError(
                    f"Missing vault pubkeys in POOLS dictionary for "
                    f"{pool_meta['base_symbol']}/{pool_meta['quote_symbol']}"
                )

            # 1) Get account info for the base (coin) vault
            coin_vault_info = await self.solana.get_account_info(coin_vault_pubkey)
            # 2) Get account info for the quote (pc) vault
            pc_vault_info = await self.solana.get_account_info(pc_vault_pubkey)

            if (not coin_vault_info or not coin_vault_info.get("value") or
                not pc_vault_info or not pc_vault_info.get("value")):
                raise ValueError("Vault account info is empty or invalid on mainnet")

            # Where is the tokenAmount in your SolanaClient's structure? Usually:
            # resp["value"]["data"]["parsed"]["info"]["tokenAmount"]["amount"]
            coin_amount_str = (
                coin_vault_info["value"]["data"]["parsed"]
                ["info"]["tokenAmount"]["amount"]
            )
            pc_amount_str   = (
                pc_vault_info["value"]["data"]["parsed"]
                ["info"]["tokenAmount"]["amount"]
            )

            # Convert strings to int, then scale by decimals to get float
            base_reserve = int(coin_amount_str) / (10 ** pool_meta["base_decimals"])
            quote_reserve = int(pc_amount_str) / (10 ** pool_meta["quote_decimals"])

            # Optionally compute price = quote_reserve / base_reserve
            price = quote_reserve / base_reserve if base_reserve > 0 else 0.0

            # Optionally track "liquidity" or other fields
            liquidity = base_reserve + quote_reserve

            return {
                "base_reserve": base_reserve,
                "quote_reserve": quote_reserve,
                "liquidity": liquidity,
                "price": price
            }

        except Exception as e:
            self.logger.error(f"Error decoding Raydium AMM data: {e}")
            raise

    async def get_token_price(self, token_address: str, base_symbol: str = "USDC") -> float:
        """
        Return the on-chain Raydium AMM price for token_address in terms of 'base_symbol'.
        """
        # 1) Convert addresses to known symbol 
        token_symbol = next((k for k, v in self.TOKENS.items() if v == token_address), None)
        if not token_symbol:
            raise ValueError(f"Unknown token address: {token_address}")

        # 2) Query pool info
        pool_name = f"{token_symbol}/{base_symbol}"
        pool_info = await self.get_pool_info(pool_name)

        # 3) Return the "price" field
        price = pool_info.get("price", 0)
        if price <= 0:
            raise ValueError(f"Could not calculate on-chain price for {pool_name}")
        return float(price)

    async def close(self):
        """Close any open RPC connections, if applicable."""
        pass

    # -------------------------------------------------------------------------
    # The rest of your swap-related, transfer, etc. methods remain unchanged:
    # -------------------------------------------------------------------------

    async def get_swap_quote(self, from_token: str, to_token: str, amount: float) -> Dict:
        try:
            from_symbol = next((k for k, v in self.TOKENS.items() if v == from_token), from_token[:4])
            to_symbol   = next((k for k, v in self.TOKENS.items() if v == to_token), to_token[:4])

            pool_info   = await self.get_pool_info(f"{from_symbol}/{to_symbol}")
            price       = float(pool_info['price'])
            expected_output = amount * price

            liquidity   = float(pool_info['liquidity'])
            price_impact = (amount * price) / liquidity if liquidity > 0 else 0

            return {
                "input_amount": amount,
                "expected_output": expected_output,
                "price_impact": price_impact,
                "minimum_received": expected_output * 0.99,  # 1% slippage
                "rate": price,
                "pool_id": pool_info['amm_id']
            }
        except Exception as e:
            self.logger.error(f"Error getting swap quote: {str(e)}")
            raise

    async def swap_tokens(self, from_token: str, to_token: str, amount: float,
                          slippage: float = 0.01) -> str:
        try:
            if not self.solana.keypair:
                raise ValueError("No wallet connected")

            # Build a fake instruction as a placeholder (this won't actually swap on chain)
            quote = await self.get_swap_quote(from_token, to_token, amount)
            min_output = quote["expected_output"] * (1 - slippage)

            from_symbol = next((k for k, v in self.TOKENS.items() if v == from_token), from_token[:4])
            to_symbol   = next((k for k, v in self.TOKENS.items() if v == to_token), to_token[:4])
            pool_info   = await self.get_pool_info(f"{from_symbol}/{to_symbol}")

            amm_id = pubkey.Pubkey.from_string(pool_info["amm_id"])
            from_pubkey = pubkey.Pubkey.from_string(from_token)
            to_pubkey   = pubkey.Pubkey.from_string(to_token)

            instruction = transaction.TransactionInstruction(
                program_id=pubkey.Pubkey.from_string(self.RAYDIUM_V4_PROGRAM_ID),
                data=bytes([2]),  # Swap instruction placeholder
                accounts=[
                    {"pubkey": amm_id, "is_writable": True, "is_signer": False},
                    {"pubkey": from_pubkey, "is_writable": True, "is_signer": False},
                    {"pubkey": to_pubkey,   "is_writable": True, "is_signer": False},
                    {"pubkey": self.solana.keypair.pubkey(), "is_writable": False, "is_signer": True}
                ]
            )

            # Build transaction
            recent_blockhash = await self.solana.get_recent_blockhash()
            tx = transaction.Transaction()
            tx.recent_blockhash = recent_blockhash
            tx.add(instruction)

            # Send transaction (placeholder)
            signature = await self.solana.client.send_transaction(
                tx,
                self.solana.keypair
            )
            return str(signature)

        except Exception as e:
            self.logger.error(f"Error in swap: {str(e)}")
            raise

    async def buy_tokens(self, token_address: str, usdc_amount: float, slippage: float = 0.01) -> str:
        return await self.swap_tokens(
            self.TOKENS["USDC"],
            token_address,
            usdc_amount,
            slippage
        )

    async def sell_tokens(self, token_address: str, amount: float, slippage: float = 0.01) -> str:
        return await self.swap_tokens(
            token_address,
            self.TOKENS["USDC"],
            amount,
            slippage
        )

    async def transfer_tokens(self, token_address: str, to_address: str, amount: float) -> str:
        try:
            if not self.solana.keypair:
                raise ValueError("No wallet connected")

            token_pubkey = pubkey.Pubkey.from_string(token_address)
            to_pubkey    = pubkey.Pubkey.from_string(to_address)

            instruction = transaction.TransactionInstruction(
                program_id=pubkey.Pubkey.from_string(self.TOKEN_PROGRAM_ID),
                data=bytes([3]),  # Transfer instruction placeholder
                accounts=[
                    {"pubkey": token_pubkey, "is_writable": True, "is_signer": False},
                    {"pubkey": to_pubkey,    "is_writable": True, "is_signer": False},
                    {"pubkey": self.solana.keypair.pubkey(), "is_writable": False, "is_signer": True}
                ]
            )

            recent_blockhash = await self.solana.get_recent_blockhash()
            tx = transaction.Transaction()
            tx.recent_blockhash = recent_blockhash
            tx.add(instruction)

            signature = await self.solana.client.send_transaction(
                tx,
                self.solana.keypair
            )
            return str(signature)

        except Exception as e:
            self.logger.error(f"Error in transfer: {str(e)}")
            raise

    async def check_transaction_status(self, signature: str) -> Dict:
        try:
            response = await self.solana.client.get_transaction(signature)
            return {
                "status": "confirmed" if response.value else "failed",
                "slot": response.value.slot if response.value else None,
                "error": response.value.meta.err if response.value else None
            }
        except Exception as e:
            self.logger.error(f"Error checking transaction: {str(e)}")
            raise
