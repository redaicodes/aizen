import requests
import logging


class DefiLlamaAPI:
    BASE_URL = "https://api.llama.fi"

    def __init__(self):
        # Set up the logger
        self.logger = logging.getLogger('DefiLlamaAPI')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _get(self, endpoint):
        """Helper method for making GET requests to the API with logging."""
        url = f"{self.BASE_URL}{endpoint}"
        self.logger.info(f"Sending GET request to {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            self.logger.info(f"Received response with status code {
                             response.status_code}")
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error while making GET request: {e}")
            return None

    def list_protocols(self):
        """List all protocols on DefiLlama along with their TVL."""
        return self._get("/protocols")

    def get_protocol_tvl(self, protocol):
        """Get historical TVL of a protocol by name."""
        return self._get(f"/protocol/{protocol}")

    def get_historical_chain_tvl(self):
        """Get historical TVL of all chains."""
        return self._get("/v2/historicalChainTvl")

    def get_chain_tvl(self, chain):
        """Get historical TVL of a specific chain."""
        return self._get(f"/v2/historicalChainTvl/{chain}")

    def get_current_tvl(self, protocol):
        """Get current TVL of a protocol."""
        return self._get(f"/tvl/{protocol}")

    def get_all_chains_tvl(self):
        """Get current TVL of all chains."""
        return self._get("/v2/chains")

    def get_current_prices(self, coins):
        """Get current prices of tokens by contract address."""
        return self._get(f"/prices/current/{coins}")

    def get_historical_prices(self, timestamp, coins):
        """Get historical prices of tokens by contract address."""
        return self._get(f"/prices/historical/{timestamp}/{coins}")

    def get_stablecoins(self):
        """List all stablecoins along with their circulating amounts."""
        return self._get("/stablecoins")

    def get_yield_pools(self):
        """Retrieve the latest data for all yield pools."""
        return self._get("/pools")

    def get_dex_overview(self):
        """List all DEXs along with summaries of their volumes."""
        return self._get("/overview/dexs")
