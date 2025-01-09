from eth_account import Account
from solders import keypair
import base58
from typing import Dict, Optional
import secrets
import logging

class WalletUtils:
    """Utility class for wallet operations across different chains."""
    
    @staticmethod
    def setup_logger(name: str) -> logging.Logger:
        """Set up logger for wallet operations."""
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    @staticmethod
    def create_ethereum_wallet() -> Dict[str, str]:
        """
        Create a new Ethereum/Base wallet.
        
        Returns:
            Dict with keys:
                - address: Ethereum address
                - private_key: Private key with '0x' prefix
        """
        # Generate a random private key
        private_key = "0x" + secrets.token_hex(32)
        account = Account.from_key(private_key)
        
        return {
            "address": account.address,
            "private_key": private_key
        }

    @staticmethod
    def create_solana_wallet() -> Dict[str, str]:
        """
        Create a new Solana wallet.
        
        Returns:
            Dict with keys:
                - address: Base58 encoded public key
                - private_key: Base58 encoded private key
        """
        new_keypair = keypair.Keypair()
        # Convert keypair to bytes for private key
        secret_bytes = bytes(new_keypair)
        private_key = base58.b58encode(secret_bytes).decode('ascii')
        
        return {
            "address": str(new_keypair.pubkey()),
            "private_key": private_key
        }

    @staticmethod
    def validate_ethereum_address(address: str) -> bool:
        """
        Validate Ethereum/Base address format.
        
        Args:
            address: Ethereum address to validate
            
        Returns:
            bool: True if address is valid
        """
        return address is not None and len(address) == 42 and address.startswith('0x')

    @staticmethod
    def validate_solana_address(address: str) -> bool:
        """
        Validate Solana address format.
        
        Args:
            address: Solana address to validate (Base58 encoded)
            
        Returns:
            bool: True if address is valid
        """
        try:
            # Solana addresses are base58 encoded and 32 bytes long
            decoded = base58.b58decode(address)
            return len(decoded) == 32
        except Exception:
            return False

    @staticmethod
    def import_ethereum_wallet(private_key: str) -> Dict[str, str]:
        """
        Import Ethereum/Base wallet from private key.
        
        Args:
            private_key: Ethereum private key (with or without '0x' prefix)
            
        Returns:
            Dict with keys:
                - address: Ethereum address
                - private_key: Private key with '0x' prefix
                
        Raises:
            ValueError: If private key is invalid
        """
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
            
        account = Account.from_key(private_key)
        return {
            "address": account.address,
            "private_key": private_key
        }

    @staticmethod
    def import_solana_wallet(private_key: str) -> Dict[str, str]:
        """
        Import Solana wallet from private key.
        
        Args:
            private_key: Base58 encoded private key
            
        Returns:
            Dict with keys:
                - address: Base58 encoded public key
                - private_key: Original private key
                
        Raises:
            ValueError: If private key is invalid
        """
        try:
            secret_key = base58.b58decode(private_key)
            imported_keypair = keypair.Keypair.from_bytes(secret_key)
            return {
                "address": str(imported_keypair.pubkey()),
                "private_key": private_key
            }
        except Exception as e:
            raise ValueError(f"Invalid Solana private key: {str(e)}")

    @staticmethod
    def format_ethereum_private_key(private_key: str) -> str:
        """
        Format Ethereum private key to ensure '0x' prefix.
        
        Args:
            private_key: Ethereum private key
            
        Returns:
            Formatted private key with '0x' prefix
        """
        if not private_key.startswith('0x'):
            return '0x' + private_key
        return private_key

    @staticmethod
    def is_valid_ethereum_private_key(private_key: str) -> bool:
        """
        Check if Ethereum private key is valid.
        
        Args:
            private_key: Ethereum private key to validate
            
        Returns:
            bool: True if private key is valid
        """
        try:
            private_key = WalletUtils.format_ethereum_private_key(private_key)
            Account.from_key(private_key)
            return True
        except Exception:
            return False

    @staticmethod
    def is_valid_solana_private_key(private_key: str) -> bool:
        """
        Check if Solana private key is valid.
        
        Args:
            private_key: Base58 encoded Solana private key
            
        Returns:
            bool: True if private key is valid
        """
        try:
            secret_key = base58.b58decode(private_key)
            keypair.Keypair.from_bytes(secret_key)
            return True
        except Exception:
            return False