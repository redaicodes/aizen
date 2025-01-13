from web3 import Web3, AsyncWeb3
from eth_account import Account
from typing import Dict, Optional
import logging
from decimal import Decimal

class PancakeSwapV2:

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

    def __init__(self, w3, account, logger):
        """
        Initialize.
        """
        self.w3 = w3
        self.account = account
        self.logger = logger
        # Load PancakeSwap Router contract
        self.router_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.PANCAKE_V2_ROUTER),
            abi=self._load_router_abi()
        )


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

    def approve_swap_token(self, token_symbol: str, amount_in_units: float):
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

        # Extra approve buffer to avoid precision issues
        amount_wei = int(Decimal(amount_in_units * 1.001) * Decimal(10 ** decimals))

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
            self.w3.to_checksum_address(self.PANCAKE_V2_ROUTER),
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

    def swap_exact_bnb_for_tokens(self, amount_in_bnb: float, token_out_symbol: str, slippage_tolerance_pct=5.0):
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

    def swap_exact_tokens_for_bnb(self, token_in_symbol: str, amount_in_units: float, slippage_tolerance_pct=5.0):
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
        slippage_tolerance_pct=5.0
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
            # self.w3.to_checksum_address(self.WBNB_ADDRESS),
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
