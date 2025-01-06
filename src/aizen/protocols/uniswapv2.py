import logging
from web3 import Web3
from eth_account.account import Account
from decimal import Decimal


class UniswapClient:
    # Uniswap V2 Router address on Ethereum mainnet
    UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

    def __init__(self, provider_url, private_key=None, log_level=logging.INFO):
        """
        Initialize the Uniswap client with web3 connection and logging

        Args:
            provider_url (str): Ethereum node provider URL (e.g., Infura endpoint)
            private_key (str, optional): Private key for signing transactions
            log_level (int): Logging level (default: logging.INFO)
        """
        # Set up logging
        self.logger = logging.getLogger('UniswapClient')
        self.logger.setLevel(log_level)

        # Create console handler with formatting
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(provider_url))
        self.logger.info(f"Connected to Ethereum network: {
                         self.w3.is_connected()}")

        # Set up account if private key provided
        self.account = None
        if private_key:
            self.account = Account.from_key(private_key)
            self.logger.info(f"Account set up: {self.account.address}")

        # Load Uniswap Router ABI
        self.router_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.UNISWAP_V2_ROUTER),
            abi=self._load_router_abi()
        )

    def _load_router_abi(self):
        """Load Uniswap V2 Router ABI from file or return minimal ABI"""
        # In practice, you would load the full ABI from a file
        # This is a minimal ABI for demonstration
        return [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "address[]",
                        "name": "path", "type": "address[]"}
                ],
                "name": "getAmountsOut",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]

    def get_token_price(self, token_address, weth_address, amount_in=1e18):
        """
        Get token price in terms of WETH

        Args:
            token_address (str): Token address to get price for
            weth_address (str): WETH token address
            amount_in (int): Amount of input tokens (default: 1 token = 1e18 wei)

        Returns:
            float: Price of token in WETH
        """
        try:
            # Create token path for price check
            path = [
                self.w3.to_checksum_address(token_address),
                self.w3.to_checksum_address(weth_address)
            ]

            # Get amounts out
            amounts = self.router_contract.functions.getAmountsOut(
                int(amount_in),
                path
            ).call()

            price = Decimal(amounts[1]) / Decimal(amounts[0])
            self.logger.info(f"Price for token {token_address}: {price} WETH")
            return price

        except Exception as e:
            self.logger.error(f"Error getting price: {str(e)}")
            raise

    def approve_token(self, token_address, spender_address, amount):
        """
        Approve tokens for spending by Uniswap router

        Args:
            token_address (str): Token address to approve
            spender_address (str): Address to approve spending for (usually router address)
            amount (int): Amount to approve in wei
        """
        if not self.account:
            raise ValueError(
                "No account set up. Private key required for transactions.")

        try:
            # Load ERC20 ABI (minimal for approve function)
            token_abi = [
                {
                    "inputs": [
                        {"name": "spender", "type": "address"},
                        {"name": "amount", "type": "uint256"}
                    ],
                    "name": "approve",
                    "outputs": [{"name": "", "type": "bool"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ]

            token_contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(token_address),
                abi=token_abi
            )

            # Build transaction
            tx = token_contract.functions.approve(
                self.w3.to_checksum_address(spender_address),
                amount
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price
            })

            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(
                tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(
                signed_tx.rawTransaction)

            self.logger.info(f"Approval transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            self.logger.error(f"Error approving tokens: {str(e)}")
            raise
