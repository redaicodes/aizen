from web3 import Web3, AsyncWeb3
from eth_account import Account
from typing import Dict, Optional
import logging
from decimal import Decimal
from web3.middleware import ExtraDataToPOAMiddleware
import os
from dotenv import load_dotenv
load_dotenv()

from aizen.protocols.pancakeswapv2 import PancakeSwapV2
from .utils.wallet import WalletUtils

class BscClient:
    """Client for interacting with binance chain."""

    def __init__(self, rpc_url: str = 'https://bsc-dataseed.binance.org', chain_id: int = 56):
        """
        Initialize client.
        
        Args:
            rpc_url: node RPC URL
            chain_id: Chain ID (56 for binance smart chain)
        """
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        self.chain_id = chain_id
        self.account = None
        
        # Set up logging
        self.logger = WalletUtils.setup_logger(f"{self.__class__.__name__}")
        
        private_key = os.getenv('BSC_PRIVATE_KEY')
        if private_key:
            self.import_wallet(private_key)
            
        self.logger.info(f"Initialized client for chain ID: {chain_id}")
        self.pancake_v2 = PancakeSwapV2(self.w3, self.account, self.logger)

    def create_wallet(self) -> Dict[str, str]:
        """Create a new Binance wallet."""
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

    def get_balance(self, address: Optional[str] = None) -> float:
        """Get BNB balance for address."""
        if not address and not self.account:
            raise ValueError("No address provided or wallet imported")
            
        target_address = address or self.account.address
        balance_wei = self.w3.eth.get_balance(target_address)
        balance_eth = self.w3.from_wei(balance_wei, 'ether')
        
        self.logger.info(f"Balance for {target_address}: {balance_eth} BNB")
        return float(balance_eth)

    def transfer(self, to_address: str, amount: float) -> str:
        """
        Transfer BNB to address.
        
        Args:
            to_address: Recipient address
            amount: Amount in BNB
            
        Returns:
            Transaction hash
        """
        if not self.account:
            raise ValueError("No wallet imported")

        to_address = Web3.to_checksum_address(to_address)

        # Validate address
        if not WalletUtils.validate_ethereum_address(to_address):
            raise ValueError("Invalid address")

        try:
            # Prepare transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.w3.eth.gas_price
            
            transaction = {
                'nonce': nonce,
                'to': to_address,
                'value': self.w3.to_wei(amount, 'ether'),
                'gas': 21000,  # Standard BNB transfer
                'gasPrice': gas_price,
                'chainId': self.chain_id
            }

            # Sign transaction
            signed_txn = self.account.sign_transaction(transaction)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            self.logger.info(f"Transfer sent: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            self.logger.error(f"Transfer failed: {str(e)}")
            raise

    def get_token_balance(self, token_address: str, address: Optional[str] = None) -> Dict:
        """Get ERC20 token balance."""
        if not address and not self.account:
            raise ValueError("No address provided or wallet imported")
            
        target_address = address or self.account.address
        token_address = Web3.to_checksum_address(token_address)
        target_address = Web3.to_checksum_address(target_address)
        
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
            decimals = contract.functions.decimals().call()
            symbol = contract.functions.symbol().call()
            balance_wei = contract.functions.balanceOf(target_address).call()
            
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

    def transfer_token(
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

        token_address = Web3.to_checksum_address(token_address)
        to_address = Web3.to_checksum_address(to_address)

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
            decimals = contract.functions.decimals().call()
            
            # Calculate token amount in wei
            amount_wei = int(Decimal(amount) * Decimal(10 ** decimals))
            
            # Prepare transaction
            transaction = contract.functions.transfer(
                to_address,
                amount_wei
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                # 'gas': 100000,  # Estimated gas for token transfer
                # 'gasPrice': self.w3.eth.gas_price,
                'chainId': self.chain_id
            })

            # Sign and send transaction
            signed_txn = self.account.sign_transaction(transaction)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            self.logger.info(f"Token transfer sent: {tx_hash.hex()}")
            return f"0x{tx_hash.hex()}"

        except Exception as e:
            self.logger.error(f"Token transfer failed: {str(e)}")
            raise


    def swap_v2(self, from_token_symbol: str, to_token_symbol: str, amount: float, slippage: float = 5.0):
        """
        Swap tokens.
        
        Args:
            from_token_symbol: Symbol of token to swap from.
            to_token_symbol: Symbol of token to swap to
            amount: Amount of tokens
            slippage: Slippage tolerance percent
            
        Returns:
            Transaction hash
        """
        if not self.account:
            raise ValueError("No wallet imported")

        if from_token_symbol != 'bnb':
            approve_hash = self.pancake_v2.approve_swap_token(from_token_symbol, amount)
            # Wait until the transaction is mined
            approve_receipt = self.pancake_v2.w3.eth.wait_for_transaction_receipt(approve_hash)

        if from_token_symbol == 'bnb':
            swap_hash = self.pancake_v2.swap_exact_bnb_for_tokens(amount, to_token_symbol, slippage)
        elif to_token_symbol == 'bnb':
            swap_hash = self.pancake_v2.swap_exact_tokens_for_bnb(from_token_symbol, amount, slippage)
        else:
            swap_hash = self.pancake_v2.swap_exact_tokens_for_tokens(from_token_symbol, to_token_symbol, amount, slippage)
        return swap_hash
