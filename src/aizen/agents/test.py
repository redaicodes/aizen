# test_raydium_agent.py
import asyncio

from aizen.chains.solana import SolanaClient
from aizen.protocols.raydium import RaydiumClient


async def test_raydium_operations():
    """Test Raydium DEX operations."""
    
    print("\n🚀 Starting Raydium DEX Test\n")

    try:
        # Initialize clients
        solana_client = SolanaClient(
            rpc_url="https://api.mainnet-beta.solana.com"
        )
        raydium_client = RaydiumClient(solana_client)

        # Test 1: Pool Information
        print("📊 Testing Pool Information")
        pools_to_check = ["SOL/USDC", "RAY/USDC", "BONK/USDC"]
        
        for pool_name in pools_to_check:
            print(f"\nChecking {pool_name} pool:")
            try:
                pool = await raydium_client.get_pool_info(pool_name)
                print(f"✅ Pool Information:")
                print(f"  AMM ID: {pool['amm_id']}")
                print(f"  Base Token: {pool['base_symbol']} ({pool['base_decimals']} decimals)")
                print(f"  Quote Token: {pool['quote_symbol']} ({pool['quote_decimals']} decimals)")
                if 'liquidity' in pool:
                    print(f"  Liquidity: ${pool['liquidity']:,.2f}")
                if 'base_reserve' in pool:
                    print(f"  {pool['base_symbol']} Reserve: {pool['base_reserve']:,.2f}")
                    print(f"  {pool['quote_symbol']} Reserve: {pool['quote_reserve']:,.2f}")
            except Exception as e:
                print(f"❌ Error: {str(e)}")

        print("\n💰 Token Prices")
        tokens_to_check = ["SOL", "RAY", "BONK"]
        for token in tokens_to_check:
            try:
                price = await raydium_client.get_token_price(
                    raydium_client.TOKENS[token],
                    raydium_client.TOKENS["USDC"]
                )
                print(f"✅ {token}/USDC: ${price:,.4f}")
            except Exception as e:
                print(f"❌ Error getting {token} price: {str(e)}")

        print("\n💱 Swap Quotes")
        test_swaps = [
            {"from": "USDC", "to": "SOL", "amount": 100},
            {"from": "SOL", "to": "USDC", "amount": 1},
            {"from": "USDC", "to": "BONK", "amount": 100}
        ]
        
        for swap in test_swaps:
            print(f"\nQuote for {swap['amount']} {swap['from']} to {swap['to']}:")
            try:
                quote = await raydium_client.get_swap_quote(
                    raydium_client.TOKENS[swap['from']],
                    raydium_client.TOKENS[swap['to']],
                    swap['amount']
                )
                print(f"✅ Quote details:")
                print(f"  Input: {quote['input_amount']} {swap['from']}")
                print(f"  Expected output: {quote['expected_output']:,.4f} {swap['to']}")
                print(f"  Price Impact: {quote['price_impact']*100:.2f}%")
                print(f"  Minimum Received: {quote['minimum_received']:,.4f} {swap['to']}")
                print(f"  Rate: 1 {swap['from']} = {quote['rate']:,.4f} {swap['to']}")
            except Exception as e:
                print(f"❌ Error: {str(e)}")

    except Exception as e:
        print(f"\n❌ Critical error: {str(e)}")
    finally:
        await solana_client.close()
        print("\n✅ Testing completed")

if __name__ == "__main__":
    asyncio.run(test_raydium_operations())