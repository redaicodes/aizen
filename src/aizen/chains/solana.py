from typing import Dict, Optional, List
import base58
import logging
from solders import keypair, pubkey, transaction, system_program
from solana.rpc.async_api import AsyncClient
from .utils.wallet import WalletUtils
import os
from dotenv import load_dotenv
load_dotenv()

class SolanaClient:
    """Client for interacting with Solana network."""

    DEFAULT_RPC_URL = "https://api.mainnet-beta.solana.com"

    def __init__(self, 
                 rpc_url: str = DEFAULT_RPC_URL):
        self.client = AsyncClient(rpc_url)
        self.keypair = None
        
        # Set up logging
        self.logger = logging.getLogger(self.__class__.__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        private_key = os.getenv('SOLANA_PRIVATE_KEY')
        if private_key:
            self.import_wallet(private_key)
            
        self.logger.info("Initialized Solana client")

    async def create_wallet(self) -> Dict[str, str]:
        """Create a new Solana wallet."""
        # Create new keypair
        new_keypair = keypair.Keypair()
        # Get bytes using to_bytes() method
        secret_bytes = bytes(new_keypair)
        private_key = base58.b58encode(secret_bytes).decode('ascii')
        self.keypair = new_keypair
        
        wallet = {
            "address": str(new_keypair.pubkey()),
            "private_key": private_key
        }
        
        self.logger.info(f"Created new wallet: {wallet['address']}")
        return wallet

    def import_wallet(self, private_key: str) -> Dict[str, str]:
        """Import wallet from private key."""
        try:
            secret_key = base58.b58decode(private_key)
            # Use from_bytes for importing
            imported_keypair = keypair.Keypair.from_bytes(secret_key)
            self.keypair = imported_keypair
            
            wallet = {
                "address": str(imported_keypair.pubkey()),
                "private_key": private_key
            }
            
            self.logger.info(f"Imported wallet: {wallet['address']}")
            return wallet
            
        except Exception as e:
            self.logger.error(f"Wallet import failed: {str(e)}")
            raise

    async def get_balance(self, address: Optional[str] = None) -> float:
        """Get SOL balance for address."""
        try:
            target_address = address or str(self.keypair.pubkey())
            target_pubkey = pubkey.Pubkey.from_string(target_address)
            response = await self.client.get_balance(target_pubkey)
            
            if response.value is not None:
                balance_sol = response.value / 10**9  # Convert lamports to SOL
                self.logger.info(f"Balance for {target_address}: {balance_sol} SOL")
                return balance_sol
            else:
                raise ValueError("Failed to get balance")
                
        except Exception as e:
            self.logger.error(f"Error getting balance: {str(e)}")
            raise

    async def get_recent_blockhash(self) -> str:
        """Get recent blockhash for transaction construction."""
        try:
            response = await self.client.get_latest_blockhash()
            return str(response.value.blockhash)
        except Exception as e:
            self.logger.error(f"Error getting recent blockhash: {str(e)}")
            raise

    async def get_token_accounts(self, address: Optional[str] = None) -> List[Dict]:
        """Get all token accounts for an address."""
        try:
            owner = address or str(self.keypair.pubkey())
            owner_pubkey = pubkey.Pubkey.from_string(owner)
            
            # Create program ID filter only
            program_id = pubkey.Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
            
            try:
                # Simpler approach: just get accounts by program
                response = await self.client.get_program_accounts(
                    program_id,
                    commitment="confirmed"
                )
                
                accounts = []
                if hasattr(response, 'value') and response.value:
                    for item in response.value:
                        account_info = {
                            "pubkey": str(item.pubkey) if hasattr(item, 'pubkey') else "Unknown"
                        }
                        accounts.append(account_info)
                
                self.logger.info(f"Found {len(accounts)} token accounts")
                return accounts
                
            except Exception as e:
                # If the above fails, try an alternative approach
                self.logger.warning(f"Failed to get program accounts, trying alternative method: {e}")
                
                # Alternative: Get account info directly
                response = await self.client.get_account_info(
                    owner_pubkey,
                    commitment="confirmed"
                )
                
                if response and hasattr(response, 'value'):
                    return [{
                        "pubkey": str(owner_pubkey),
                        "data": "Account exists"
                    }]
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting token accounts: {str(e)}")
            # Return empty list instead of raising error for better UX
            return []

    async def get_account_info(self, address: str) -> dict:
        """
        Returns account info in JSON-parsed form. 
        This matches the structure that your RaydiumClient code expects:
          response["value"]["data"]["parsed"]["info"]["tokenAmount"]["amount"]
        """
        try:
            address_pubkey = pubkey.Pubkey.from_string(address)

            # Request JSON-parsed data so we can easily read 'tokenAmount', etc.
            resp = await self.client.get_account_info(
                address_pubkey,
                commitment="confirmed",
                encoding="jsonParsed"
            )

            # The response structure typically looks like:
            # {
            #   "context": {...},
            #   "value": {
            #       "data": {
            #         "parsed": {
            #            "info": {
            #               "tokenAmount": {"amount": "...", ...}
            #            },
            #            ...
            #         },
            #         "program": "spl-token",
            #         ...
            #       },
            #       "executable": False,
            #       "lamports": 2039280,
            #       "owner": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
            #       ...
            #   }
            # }
            #
            # We'll just return this dict as-is so that code in RaydiumClient
            # can do coin_vault_info["value"]["data"]["parsed"]["info"]["tokenAmount"]["amount"].

            if resp is None:
                raise ValueError(f"Empty response for get_account_info({address})")

            # If the account doesn't exist or is invalid, "resp.value" may be None
            if not resp.value:
                raise ValueError(f"Account {address} not found or invalid.")

            return resp  # Return the entire response dict

        except Exception as e:
            self.logger.error(f"Error in get_account_info({address}): {str(e)}")
            raise

    async def close(self):
        """Close client connections."""
        if self.client:
            await self.client.close()