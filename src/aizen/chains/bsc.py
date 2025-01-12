from web3 import Web3, AsyncWeb3
from eth_account import Account
from typing import Dict, Optional
import logging
from decimal import Decimal
from web3.middleware import ExtraDataToPOAMiddleware
import os
from dotenv import load_dotenv
load_dotenv()

from .utils.wallet import WalletUtils

class BscClient:
    """Client for interacting with binance chain."""

    # PancakeSwap V2 Router Address on BSC Mainnet
    PANCAKE_V2_ROUTER = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
    # Wrapped BNB (WBNB) address on BSC
    WBNB_ADDRESS = "0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
    # Dictionary of common tokens you want to support
    TOKEN_DICT = {
        "wbnb": {
            "address": "0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
            "decimals": 18
        },
        "usdt": {
            "address": "0x55d398326f99059fF775485246999027B3197955",
            "decimals": 18
        },
        "eth": {
            "address": "0x2170Ed0880ac9A755fd29B2688956BD959F933F8",
            "decimals": 18
        },
        "busd": {
            "address": "0xe9e7cea3dedca5984780bafc599bd69add087d56",
            "decimals": 18
        },
        "cake": {
            "address": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
            "decimals": 18
        }
    }

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

        # Load PancakeSwap Router contract
        self.router_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.PANCAKE_V2_ROUTER),
            abi=self._load_router_abi()
        )

    async def create_wallet(self) -> Dict[str, str]:
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

    async def get_balance(self, address: Optional[str] = None) -> float:
        """Get BNB balance for address."""
        if not address and not self.account:
            raise ValueError("No address provided or wallet imported")
            
        target_address = address or self.account.address
        balance_wei = self.w3.eth.get_balance(target_address)
        balance_eth = self.w3.from_wei(balance_wei, 'ether')
        
        self.logger.info(f"Balance for {target_address}: {balance_eth} BNB")
        return float(balance_eth)

    async def transfer(self, to_address: str, amount: float) -> str:
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
                'gas': 100000,  # Estimated gas for token transfer
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.chain_id
            })

            # Sign and send transaction
            signed_txn = self.account.sign_transaction(transaction)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            self.logger.info(f"Token transfer sent: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            self.logger.error(f"Token transfer failed: {str(e)}")
            raise


    def _load_router_abi(self):
        """
        Minimal ABI for PancakeSwap V2 router.
        """
        return [
            {
                "name": "getAmountsOut",
                "inputs": [
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "path", "type": "address[]"}
                ],
                "outputs": [{"name": "amounts", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "name": "swapExactETHForTokens",
                "inputs": [
                    {"name": "amountOutMin", "type": "uint256"},
                    {"name": "path", "type": "address[]"},
                    {"name": "to", "type": "address"},
                    {"name": "deadline", "type": "uint256"}
                ],
                "outputs": [
                    {"name": "amounts", "type": "uint256[]"}
                ],
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "name": "swapExactTokensForETH",
                "inputs": [
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMin", "type": "uint256"},
                    {"name": "path", "type": "address[]"},
                    {"name": "to", "type": "address"},
                    {"name": "deadline", "type": "uint256"}
                ],
                "outputs": [
                    {"name": "amounts", "type": "uint256[]"}
                ],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "name": "swapExactTokensForTokens",
                "inputs": [
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMin", "type": "uint256"},
                    {"name": "path", "type": "address[]"},
                    {"name": "to", "type": "address"},
                    {"name": "deadline", "type": "uint256"}
                ],
                "outputs": [
                    {"name": "amounts", "type": "uint256[]"}
                ],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]

    def _get_token_info(self, symbol: str) -> dict:
        """
        Helper to fetch token info from TOKEN_DICT.
        :param symbol: e.g. "usdt", "eth", "busd", ...
        :return: dict with 'address' and 'decimals'
        """
        symbol = symbol.lower()
        if symbol not in self.TOKEN_DICT:
            raise ValueError(
                f"Token symbol '{symbol}' not recognized. "
                f"Valid options: {list(self.TOKEN_DICT.keys())}"
            )
        return self.TOKEN_DICT[symbol]

    def get_amounts_out(self, amount_in_wei: int, path: list) -> list:
        """
        Wrapper around the PancakeSwap `getAmountsOut` function.
        """
        try:
            amounts = self.router_contract.functions.getAmountsOut(
                amount_in_wei, path
            ).call()
            return amounts
        except Exception as e:
            self.logger.error(f"Error in get_amounts_out: {e}")
            raise

    def get_token_price_in_bnb(self, token_symbol: str, amount_in_units: float = 1.0) -> float:
        """
        Get the price of a given token in BNB terms. 
        Uses getAmountsOut with path [token -> WBNB].
        """
        if not self.w3.is_connected():
            raise ConnectionError("Not connected to BSC.")

        # Grab token info (address, decimals) from our dictionary
        token_info = self._get_token_info(token_symbol)
        token_address = token_info["address"]
        decimals = token_info["decimals"]

        amount_in_wei = int(Decimal(amount_in_units) * Decimal(10 ** decimals))

        path = [
            self.w3.to_checksum_address(token_address),
            self.w3.to_checksum_address(self.WBNB_ADDRESS)
        ]
        amounts_out = self.get_amounts_out(amount_in_wei, path)
        bnb_received_wei = amounts_out[-1]

        # Convert from Wei to BNB
        bnb_price = float(self.w3.from_wei(bnb_received_wei, 'ether'))
        self.logger.info(
            f"Price for {amount_in_units} {token_symbol.upper()}: ~{bnb_price} BNB"
        )
        return bnb_price

    def approve_token(self, token_symbol: str, spender: str, amount_in_units: float):
        """
        Approve `spender` to use `amount_in_units` of `token_symbol` on behalf of self.account.
        Typically required before swapping tokens.
        """
        if not self.account:
            raise ValueError("No private key/account set up to sign transactions.")

        # Grab token info
        token_info = self._get_token_info(token_symbol)
        token_address = token_info["address"]
        decimals = token_info["decimals"]

        amount_wei = int(Decimal(amount_in_units) * Decimal(10 ** decimals))

        # Minimal ERC20 ABI for approval
        abi_erc20_approve = [
            {
                "name": "approve",
                "type": "function",
                "stateMutability": "nonpayable",
                "inputs": [
                    {"name": "_spender", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "outputs": [
                    {"name": "", "type": "bool"}
                ]
            }
        ]

        token_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(token_address),
            abi=abi_erc20_approve
        )

        nonce = self.w3.eth.get_transaction_count(self.account.address)
        tx = token_contract.functions.approve(
            self.w3.to_checksum_address(spender),
            amount_wei
        ).build_transaction({
            'from': self.account.address,
            'nonce': nonce,
            # 'gas': 200000,
            # 'gasPrice': self.w3.eth.gas_price
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        self.logger.info(f"Approve transaction sent: {tx_hash.hex()}")
        return f"0x{tx_hash.hex()}"

    def swap_exact_bnb_for_tokens(self, amount_in_bnb: float, token_out_symbol: str, slippage_tolerance_pct=10.0):
        """
        Swap exact BNB for a given token symbol.
        """
        if not self.account:
            raise ValueError("No private key/account set up to sign transactions.")

        # Convert BNB to Wei
        amount_in_wei = self.w3.to_wei(amount_in_bnb, 'ether')

        # Get token info
        token_info = self._get_token_info(token_out_symbol)
        token_out_address = token_info["address"]

        # Path: WBNB -> token_out
        path = [
            self.w3.to_checksum_address(self.WBNB_ADDRESS),
            self.w3.to_checksum_address(token_out_address)
        ]

        # Estimate amounts out
        amounts_out = self.get_amounts_out(amount_in_wei, path)
        amount_out_min = amounts_out[-1]

        # Apply slippage
        slippage_amount = int(amount_out_min * (1 - (slippage_tolerance_pct / 100)))
        deadline = int(self.w3.eth.get_block('latest')['timestamp']) + 1200

        swap_txn = self.router_contract.functions.swapExactETHForTokens(
            slippage_amount,
            path,
            self.account.address,
            deadline
        ).build_transaction({
            'from': self.account.address,
            'value': amount_in_wei,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            # 'gasPrice': self.w3.eth.gas_price
        })

        signed_tx = self.w3.eth.account.sign_transaction(swap_txn, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        self.logger.info(f"Swap BNB -> {token_out_symbol.upper()} TX sent: {tx_hash.hex()}")
        return f"0x{tx_hash.hex()}"

    def swap_exact_tokens_for_bnb(self, token_in_symbol: str, amount_in_units: float, slippage_tolerance_pct=10.0):
        """
        Swap exact tokens (e.g., USDT, ETH(BEP-20)) for BNB.
        """
        if not self.account:
            raise ValueError("No private key/account set up to sign transactions.")

        # Token info
        token_info = self._get_token_info(token_in_symbol)
        token_in_address = token_info["address"]
        decimals = token_info["decimals"]

        amount_in_wei = int(Decimal(amount_in_units) * Decimal(10 ** decimals))

        # Path: token_in -> WBNB
        path = [
            self.w3.to_checksum_address(token_in_address),
            self.w3.to_checksum_address(self.WBNB_ADDRESS)
        ]

        # Must have approved router to spend token_in beforehand!
        amounts_out = self.get_amounts_out(amount_in_wei, path)
        amount_out_min = amounts_out[-1]

        slippage_amount = int(amount_out_min * (1 - (slippage_tolerance_pct / 100)))
        deadline = int(self.w3.eth.get_block('latest')['timestamp']) + 1200

        swap_txn = self.router_contract.functions.swapExactTokensForETH(
            amount_in_wei,
            slippage_amount,
            path,
            self.account.address,
            deadline
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            # 'gasPrice': self.w3.eth.gas_price
        })

        signed_tx = self.w3.eth.account.sign_transaction(swap_txn, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        self.logger.info(f"Swap {token_in_symbol.upper()} -> BNB TX sent: {tx_hash.hex()}")
        return f"0x{tx_hash.hex()}"

    def swap_exact_tokens_for_tokens(
        self,
        token_in_symbol: str,
        token_out_symbol: str,
        amount_in_units: float,
        slippage_tolerance_pct=10.0
    ):
        """
        Swap exact tokens (e.g., USDT -> BUSD, ETH(BEP-20) -> BUSD, etc.).
        """
        if not self.account:
            raise ValueError("No private key/account set up to sign transactions.")

        # Token in info
        token_in_info = self._get_token_info(token_in_symbol)
        token_in_address = token_in_info["address"]
        decimals_in = token_in_info["decimals"]

        # Token out info
        token_out_info = self._get_token_info(token_out_symbol)
        token_out_address = token_out_info["address"]
        # decimals_out = token_out_info["decimals"]  # Not strictly needed here unless you want to display final tokens

        amount_in_wei = int(Decimal(amount_in_units) * Decimal(10 ** decimals_in))

        # Common path on BSC is token_in -> WBNB -> token_out
        path = [
            self.w3.to_checksum_address(token_in_address),
            self.w3.to_checksum_address(self.WBNB_ADDRESS),
            self.w3.to_checksum_address(token_out_address)
        ]

        # Must approve the router to spend your `token_in` first!
        amounts_out = self.get_amounts_out(amount_in_wei, path)
        amount_out_min = amounts_out[-1]

        slippage_amount = int(amount_out_min * (1 - (slippage_tolerance_pct / 100)))
        deadline = int(self.w3.eth.get_block('latest')['timestamp']) + 1200

        swap_txn = self.router_contract.functions.swapExactTokensForTokens(
            amount_in_wei,
            slippage_amount,
            path,
            self.account.address,
            deadline
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            # 'gasPrice': self.w3.eth.gas_price
        })

        signed_tx = self.w3.eth.account.sign_transaction(swap_txn, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        self.logger.info(
            f"Swap {token_in_symbol.upper()} -> {token_out_symbol.upper()} TX sent: {tx_hash.hex()}"
        )
        return f"0x{tx_hash.hex()}"
