from web3 import Web3, AsyncWeb3
from eth_account import Account
from typing import Dict, Optional
import logging
from decimal import Decimal

from .utils.wallet import WalletUtils

class EthereumClient:
    """Client for interacting with Ethereum network."""

    def __init__(self, rpc_url: str, private_key: Optional[str] = None, chain_id: int = 1):
        """
        Initialize Ethereum client.
        
        Args:
            rpc_url: Ethereum node RPC URL
            private_key: Optional private key for transactions
            chain_id: Chain ID (1 for mainnet)
        """
        self.w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc_url))
        self.chain_id = chain_id
        self.account = None
        
        # Set up logging
        self.logger = WalletUtils.setup_logger(f"{self.__class__.__name__}")
        
        if private_key:
            self.import_wallet(private_key)
            
        self.logger.info(f"Initialized Ethereum client for chain ID: {chain_id}")

    async def create_wallet(self) -> Dict[str, str]:
        """Create a new Ethereum wallet."""
        wallet = WalletUtils.create_ethereum_wallet()
        self.import_wallet(wallet["private_key"])
        self.logger.info(f"Created new wallet: {wallet['address']}")
        return wallet

    def import_wallet(self, private_key: str) -> Dict[str, str]:
        """Import wallet from private key."""
        wallet = WalletUtils.import_ethereum_wallet(private_key)
        self.account = Account.from_key(private_key)
        self.logger.info(f"Imported wallet: {wallet['address']}")
        return wallet

    async def get_balance(self, address: Optional[str] = None) -> float:
        """Get ETH balance for address."""
        if not address and not self.account:
            raise ValueError("No address provided or wallet imported")
            
        target_address = address or self.account.address
        balance_wei = await self.w3.eth.get_balance(target_address)
        balance_eth = self.w3.from_wei(balance_wei, 'ether')
        
        self.logger.info(f"Balance for {target_address}: {balance_eth} ETH")
        return float(balance_eth)

    async def transfer(self, to_address: str, amount: float) -> str:
        """
        Transfer ETH to address.
        
        Args:
            to_address: Recipient address
            amount: Amount in ETH
            
        Returns:
            Transaction hash
        """
        if not self.account:
            raise ValueError("No wallet imported")

        # Validate address
        if not WalletUtils.validate_ethereum_address(to_address):
            raise ValueError("Invalid Ethereum address")

        try:
            # Prepare transaction
            nonce = await self.w3.eth.get_transaction_count(self.account.address)
            gas_price = await self.w3.eth.gas_price
            
            transaction = {
                'nonce': nonce,
                'to': to_address,
                'value': self.w3.to_wei(amount, 'ether'),
                'gas': 21000,  # Standard ETH transfer
                'gasPrice': gas_price,
                'chainId': self.chain_id
            }

            # Sign transaction
            signed_txn = self.account.sign_transaction(transaction)
            
            # Send transaction
            tx_hash = await self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            self.logger.info(f"Transfer sent: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            self.logger.error(f"Transfer failed: {str(e)}")
            raise

    async def get_token_balance(self, token_address: str, address: Optional[str] = None) -> Dict:
        """Get ERC20 token balance."""
        if not address and not self.account:
            raise ValueError("No address provided or wallet imported")
            
        target_address = address or self.account.address
        
        # ERC20 minimal ABI
        erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            }
        ]

        try:
            contract = self.w3.eth.contract(address=token_address, abi=erc20_abi)
            
            # Get token data
            decimals = await contract.functions.decimals().call()
            symbol = await contract.functions.symbol().call()
            balance_wei = await contract.functions.balanceOf(target_address).call()
            
            # Calculate actual balance
            balance = Decimal(balance_wei) / Decimal(10 ** decimals)
            
            result = {
                "balance": float(balance),
                "symbol": symbol,
                "decimals": decimals,
                "address": token_address
            }
            
            self.logger.info(f"Token balance for {target_address}: {balance} {symbol}")
            return result

        except Exception as e:
            self.logger.error(f"Error getting token balance: {str(e)}")
            raise

    async def transfer_token(
        self, 
        token_address: str, 
        to_address: str, 
        amount: float
    ) -> str:
        """
        Transfer ERC20 tokens.
        
        Args:
            token_address: Token contract address
            to_address: Recipient address
            amount: Amount of tokens
            
        Returns:
            Transaction hash
        """
        if not self.account:
            raise ValueError("No wallet imported")

        # ERC20 transfer ABI
        erc20_abi = [
            {
                "constant": False,
                "inputs": [
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            }
        ]

        try:
            contract = self.w3.eth.contract(address=token_address, abi=erc20_abi)
            
            # Get token decimals
            decimals = await contract.functions.decimals().call()
            
            # Calculate token amount in wei
            amount_wei = int(Decimal(amount) * Decimal(10 ** decimals))
            
            # Prepare transaction
            transaction = await contract.functions.transfer(
                to_address,
                amount_wei
            ).build_transaction({
                'from': self.account.address,
                'nonce': await self.w3.eth.get_transaction_count(self.account.address),
                'gas': 100000,  # Estimated gas for token transfer
                'gasPrice': await self.w3.eth.gas_price,
                'chainId': self.chain_id
            })

            # Sign and send transaction
            signed_txn = self.account.sign_transaction(transaction)
            tx_hash = await self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            self.logger.info(f"Token transfer sent: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            self.logger.error(f"Token transfer failed: {str(e)}")
            raise