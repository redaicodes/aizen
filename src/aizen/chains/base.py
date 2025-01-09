from typing import Dict, Optional
from .ethereum import EthereumClient

class BaseClient(EthereumClient):
    """Client for interacting with Base network."""

    # Base mainnet RPC URLs (can be obtained from Base docs)
    DEFAULT_RPC_URL = "https://mainnet.base.org"
    CHAIN_ID = 8453  # Base mainnet chain ID

    def __init__(self, 
                 rpc_url: str = DEFAULT_RPC_URL, 
                 private_key: Optional[str] = None):
        """
        Initialize Base client.
        
        Args:
            rpc_url: Base node RPC URL
            private_key: Optional private key for transactions
        """
        super().__init__(rpc_url, private_key, chain_id=self.CHAIN_ID)
        self.logger.info("Initialized Base client")

    async def estimate_l2_gas(self, to_address: str, amount: float) -> Dict:
        """
        Estimate gas for an L2 transaction.
        
        Args:
            to_address: Destination address
            amount: Amount of ETH to send
            
        Returns:
            Dict with gas estimation details
        """
        try:
            # Get current gas price
            gas_price = await self.w3.eth.gas_price
            
            # Create transaction object for estimation
            tx = {
                'from': self.account.address if self.account else None,
                'to': to_address,
                'value': self.w3.to_wei(amount, 'ether'),
                'chainId': self.CHAIN_ID
            }
            
            # Estimate gas
            estimated_gas = await self.w3.eth.estimate_gas(tx)
            
            # Calculate total fee
            total_fee_wei = gas_price * estimated_gas
            total_fee_eth = self.w3.from_wei(total_fee_wei, 'ether')
            
            return {
                'gas_price_gwei': self.w3.from_wei(gas_price, 'gwei'),
                'estimated_gas': estimated_gas,
                'total_fee_eth': float(total_fee_eth)
            }
            
        except Exception as e:
            self.logger.error(f"Gas estimation failed: {str(e)}")
            raise

    async def get_l2_block(self, block_identifier: str = 'latest') -> Dict:
        """
        Get Base L2 block information.
        
        Args:
            block_identifier: Block number or 'latest'
            
        Returns:
            Block information
        """
        try:
            block = await self.w3.eth.get_block(block_identifier)
            return dict(block)
        except Exception as e:
            self.logger.error(f"Error getting block: {str(e)}")
            raise

    async def verify_l2_transaction(self, tx_hash: str) -> Dict:
        """
        Verify a transaction on Base L2.
        
        Args:
            tx_hash: Transaction hash to verify
            
        Returns:
            Transaction verification details
        """
        try:
            # Get transaction receipt
            receipt = await self.w3.eth.get_transaction_receipt(tx_hash)
            
            # Get current block for confirmation count
            current_block = await self.w3.eth.block_number
            confirmations = current_block - receipt['blockNumber']
            
            return {
                'status': 'success' if receipt['status'] == 1 else 'failed',
                'block_number': receipt['blockNumber'],
                'confirmations': confirmations,
                'gas_used': receipt['gasUsed'],
                'transaction_hash': receipt['transactionHash'].hex()
            }
            
        except Exception as e:
            self.logger.error(f"Transaction verification failed: {str(e)}")
            raise

    async def is_contract_address(self, address: str) -> bool:
        """
        Check if an address is a contract on Base.
        
        Args:
            address: Address to check
            
        Returns:
            True if address is a contract
        """
        try:
            code = await self.w3.eth.get_code(address)
            return len(code) > 0
        except Exception as e:
            self.logger.error(f"Contract check failed: {str(e)}")
            raise

    async def get_transaction_cost(self, tx_hash: str) -> Dict:
        """
        Get the actual cost of a completed transaction.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction cost details
        """
        try:
            receipt = await self.w3.eth.get_transaction_receipt(tx_hash)
            tx = await self.w3.eth.get_transaction(tx_hash)
            
            gas_price = tx['gasPrice']
            gas_used = receipt['gasUsed']
            total_cost_wei = gas_price * gas_used
            total_cost_eth = self.w3.from_wei(total_cost_wei, 'ether')
            
            return {
                'gas_price_gwei': self.w3.from_wei(gas_price, 'gwei'),
                'gas_used': gas_used,
                'total_cost_eth': float(total_cost_eth)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting transaction cost: {str(e)}")
            raise