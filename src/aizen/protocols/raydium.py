import asyncio
import logging
import time
from typing import Dict, Optional

import aiohttp
from solders import pubkey
from solders import transaction

class RaydiumClient:
    """Client for interacting with Raydium DEX on Solana."""

    # Program IDs
    RAYDIUM_V4_PROGRAM_ID = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
    SERUM_PROGRAM_ID = "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"
    TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

    # Common token addresses (Mainnet)
    TOKENS = {
        "SOL":  "So11111111111111111111111111111111111111112",
        "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "RAY":  "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
        "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    }

    # Pool metadata (static)
    POOLS = {
        "SOL/USDC": {
            "amm_id": "58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2",
            "base_mint": TOKENS["SOL"],
            "quote_mint": TOKENS["USDC"],
            "base_decimals": 9,
            "quote_decimals": 6,
            "base_symbol": "SOL",
            "quote_symbol": "USDC",
            "version": 4,
            "status": "official"
        },
        "RAY/USDC": {
            "amm_id": "6UmmUiYoBEGPwZxr9W3txiydDfBGyeKa19jUNt9kNGkm",
            "base_mint": TOKENS["RAY"],
            "quote_mint": TOKENS["USDC"],
            "base_decimals": 6,
            "quote_decimals": 6,
            "base_symbol": "RAY",
            "quote_symbol": "USDC",
            "version": 4,
            "status": "official"
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
            "status": "official"
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
        try:
            # 1) Check if the pool is in dictionary or reversed
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
            # Merge static (pool_meta) + dynamic (onchain_data)
            pool_info = dict(pool_meta)
            pool_info.update(onchain_data)

            return pool_info

        except Exception as e:
            self.logger.error(f"Error in get_pool_info({name}): {e}")
            raise

    async def _get_onchain_pool_state(self, pool_meta: Dict) -> Dict:
        try:
            amm_pubkey = pubkey.Pubkey.from_string(pool_meta["amm_id"])
            account_info = await self.solana.client.get_account_info(amm_pubkey)

            if not account_info:
                self.logger.error(f"No account info returned for pool {pool_meta['amm_id']}")
                raise ValueError("No account info returned")

            if not account_info.value:
                self.logger.error(f"No account data for {amm_pubkey}: {account_info}")
                raise ValueError("No account data returned")

            raw_data = account_info.value.data
            if not raw_data:
                raise ValueError("AMM state is empty")
            # NOTE: The offsets below are just placeholders. 
            #       Real Raydium layout is more complex.
            base_res_offset = 72   # example offset 
            quote_res_offset = 80  # example offset
            base_reserve_lamports = int.from_bytes(
                raw_data[base_res_offset:base_res_offset+8], "little"
            )
            quote_reserve_lamports = int.from_bytes(
                raw_data[quote_res_offset:quote_res_offset+8], "little" 
            )

            base_decimals = 10 ** pool_meta["base_decimals"]
            quote_decimals = 10 ** pool_meta["quote_decimals"]

            base_reserve = base_reserve_lamports / base_decimals
            quote_reserve = quote_reserve_lamports / quote_decimals

            # Simple approximation: total liquidity is sum in quote terms
            total_liquidity = 2.0 * (quote_reserve)

            # Price = quote_reserve / base_reserve (assuming base token is first) 
            price = 0.0
            if base_reserve > 0:
                price = quote_reserve / base_reserve

            return {
                "base_reserve": base_reserve,
                "quote_reserve": quote_reserve,
                "liquidity": total_liquidity, 
                "price": price
            }

        except Exception as e:
            self.logger.error(f"On-chain parse failed for pool {pool_meta['amm_id']}: {e}")
            # You could raise or return partial data 
            raise

    async def get_token_price(self, token_address: str, base_token: str = "USDC") -> float:
        # 1) Convert addresses to known symbol 
        token_symbol = next((k for k, v in self.TOKENS.items() if v == token_address), None)
        base_symbol = next((k for k, v in self.TOKENS.items() if v == base_token), None)

        if not token_symbol or not base_symbol:
            raise ValueError(f"Unknown token address: {token_address} or {base_token}")

        # 2) Query pool info on-chain
        pool_name = f"{token_symbol}/{base_symbol}"
        pool_info = await self.get_pool_info(pool_name)

        # 3) Return the "price" field if it's set
        price = pool_info.get("price")
        if price is None or price <= 0:
            raise ValueError(f"Could not calculate on-chain price for {pool_name}")

        return float(price)

    async def close(self):
        """Close any open RPC connections, if applicable."""
        pass
           
    async def get_swap_quote(self,
                           from_token: str,
                           to_token: str,
                           amount: float) -> Dict:
        """
        Get quote for token swap.
        
        Args:
            from_token: Token address to swap from
            to_token: Token address to swap to
            amount: Amount of from_token to swap
            
        Returns:
            Dict containing quote details
        """
        try:
            # Get token symbols
            from_symbol = next((k for k, v in self.TOKENS.items() if v == from_token), from_token[:4])
            to_symbol = next((k for k, v in self.TOKENS.items() if v == to_token), to_token[:4])
            
            # Get pool info
            pool_info = await self.get_pool_info(f"{from_symbol}/{to_symbol}")
            
            # Calculate swap details
            price = float(pool_info['price'])
            expected_output = amount * price
            
            # Calculate price impact based on liquidity
            liquidity = float(pool_info['liquidity'])
            price_impact = (amount * price) / liquidity if liquidity > 0 else 0
            
            return {
                "input_amount": amount,
                "expected_output": expected_output,
                "price_impact": price_impact,
                "minimum_received": expected_output * 0.99,  # 1% default slippage
                "rate": price,
                "pool_id": pool_info['amm_id']
            }
            
        except Exception as e:
            self.logger.error(f"Error getting swap quote: {str(e)}")
            raise

    async def swap_tokens(self,
                         from_token: str,
                         to_token: str,
                         amount: float,
                         slippage: float = 0.01) -> str:
        """
        Swap tokens using Raydium.
        
        Args:
            from_token: Token address to swap from
            to_token: Token address to swap to
            amount: Amount to swap
            slippage: Maximum acceptable slippage (default: 1%)
            
        Returns:
            str: Transaction signature
        """
        try:
            if not self.solana.keypair:
                raise ValueError("No wallet connected")

            # Get quote
            quote = await self.get_swap_quote(from_token, to_token, amount)
            min_output = quote["expected_output"] * (1 - slippage)
            
            # Get token symbols
            from_symbol = next((k for k, v in self.TOKENS.items() if v == from_token), from_token[:4])
            to_symbol = next((k for k, v in self.TOKENS.items() if v == to_token), to_token[:4])
            
            # Get pool info
            pool_info = await self.get_pool_info(f"{from_symbol}/{to_symbol}")
            
            # Build swap instruction
            amm_id = pubkey.Pubkey.from_string(pool_info["amm_id"])
            from_pubkey = pubkey.Pubkey.from_string(from_token)
            to_pubkey = pubkey.Pubkey.from_string(to_token)
            
            instruction = transaction.TransactionInstruction(
                program_id=pubkey.Pubkey.from_string(self.RAYDIUM_V4_PROGRAM_ID),
                data=bytes([2]),  # Swap instruction
                accounts=[
                    {"pubkey": amm_id, "is_writable": True, "is_signer": False},
                    {"pubkey": from_pubkey, "is_writable": True, "is_signer": False},
                    {"pubkey": to_pubkey, "is_writable": True, "is_signer": False},
                    {"pubkey": self.solana.keypair.pubkey(), "is_writable": False, "is_signer": True}
                ]
            )
            
            # Build transaction
            recent_blockhash = await self.solana.get_recent_blockhash()
            tx = transaction.Transaction()
            tx.recent_blockhash = recent_blockhash
            tx.add(instruction)
            
            # Send transaction
            signature = await self.solana.client.send_transaction(
                tx,
                self.solana.keypair
            )
            
            return str(signature)
            
        except Exception as e:
            self.logger.error(f"Error in swap: {str(e)}")
            raise

    async def buy_tokens(self,
                        token_address: str,
                        usdc_amount: float,
                        slippage: float = 0.01) -> str:
        """
        Buy tokens using USDC.
        
        Args:
            token_address: Token to buy
            usdc_amount: Amount of USDC to spend
            slippage: Maximum acceptable slippage
        """
        return await self.swap_tokens(
            self.TOKENS["USDC"],
            token_address,
            usdc_amount,
            slippage
        )

    async def sell_tokens(self,
                         token_address: str,
                         amount: float,
                         slippage: float = 0.01) -> str:
        """
        Sell tokens for USDC.
        
        Args:
            token_address: Token to sell
            amount: Amount of tokens to sell
            slippage: Maximum acceptable slippage
        """
        return await self.swap_tokens(
            token_address,
            self.TOKENS["USDC"],
            amount,
            slippage
        )

    async def transfer_tokens(self,
                            token_address: str,
                            to_address: str,
                            amount: float) -> str:
        """
        Transfer tokens to another address.
        
        Args:
            token_address: Token to transfer
            to_address: Recipient address
            amount: Amount to transfer
        """
        try:
            if not self.solana.keypair:
                raise ValueError("No wallet connected")
            
            # Create token accounts instruction
            token_pubkey = pubkey.Pubkey.from_string(token_address)
            to_pubkey = pubkey.Pubkey.from_string(to_address)
            
            instruction = transaction.TransactionInstruction(
                program_id=pubkey.Pubkey.from_string(self.TOKEN_PROGRAM_ID),
                data=bytes([3]),  # Transfer instruction
                accounts=[
                    {"pubkey": token_pubkey, "is_writable": True, "is_signer": False},
                    {"pubkey": to_pubkey, "is_writable": True, "is_signer": False},
                    {"pubkey": self.solana.keypair.pubkey(), "is_writable": False, "is_signer": True}
                ]
            )
            
            # Build transaction
            recent_blockhash = await self.solana.get_recent_blockhash()
            tx = transaction.Transaction()
            tx.recent_blockhash = recent_blockhash
            tx.add(instruction)
            
            # Send transaction
            signature = await self.solana.client.send_transaction(
                tx,
                self.solana.keypair
            )
            
            return str(signature)
            
        except Exception as e:
            self.logger.error(f"Error in transfer: {str(e)}")
            raise

    async def check_transaction_status(self, signature: str) -> Dict:
        """
        Check status of a transaction.
        
        Args:
            signature: Transaction signature to check
            
        Returns:
            Dict containing transaction status
        """
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