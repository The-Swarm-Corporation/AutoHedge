import os
from typing import Dict, Any, Union
from loguru import logger
from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session

# Load environment variables from .env file
load_dotenv()


class ETradeClient:
    """
    A client for interacting with the E*TRADE API to manage trades and accounts.
    """

    # BASE_URL = "https://api.etrade.com/v1"  # Sandbox base URL
    # For production, replace with "https://api.etrade.com/v1"
    BASE_URL = "https://api.etrade.com/v1"

    def __init__(self, account_id: str, production_url: str):
        """
        Initialize the E*TRADE client with OAuth credentials from environment variables.
        """
        self.consumer_key = os.getenv("ETRADE_CONSUMER_KEY")
        self.consumer_secret = os.getenv("ETRADE_CONSUMER_SECRET")
        self.oauth_token = os.getenv("ETRADE_OAUTH_TOKEN")
        self.oauth_token_secret = os.getenv(
            "ETRADE_OAUTH_TOKEN_SECRET"
        )
        self.account_id = account_id

        if not all(
            [
                self.consumer_key,
                self.consumer_secret,
                self.oauth_token,
                self.oauth_token_secret,
            ]
        ):
            logger.error(
                "E*TRADE credentials are not set in the environment variables."
            )
            raise EnvironmentError("Missing E*TRADE credentials.")

        self.oauth_session = OAuth1Session(
            client_key=self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=self.oauth_token,
            resource_owner_secret=self.oauth_token_secret,
        )
        logger.success("Initialized E*TRADE client.")

    def place_order(
        self,
        account_id: str,
        symbol: str,
        quantity: int,
        action: str,
        price: Union[float, None] = None,
    ) -> Dict[str, Any]:
        """
        Place a buy or sell order.

        Args:
            account_id: The account ID for placing the order.
            symbol: The stock ticker symbol (e.g., 'AAPL').
            quantity: Number of shares.
            action: 'BUY' or 'SELL'.
            price: Limit price (optional, for limit orders).

        Returns:
            Response JSON from the API.
        """
        url = f"{self.BASE_URL}/accounts/{account_id}/orders/place"
        order_payload = {
            "orderType": "LIMIT" if price else "MARKET",
            "clientOrderId": (
                "12345"
            ),  # Replace with dynamic unique ID in production
            "orderAction": action.upper(),
            "instrument": [
                {
                    "symbol": symbol,
                    "quantity": quantity,
                    "orderAction": action.upper(),
                }
            ],
            "priceType": "LIMIT" if price else "MARKET",
            "limitPrice": price if price else None,
            "marketSession": "REGULAR",
            "orderTerm": "GOOD_FOR_DAY",
        }

        try:
            logger.info(
                f"Placing {action.upper()} order for {quantity} shares of {symbol} (Limit: {price})"
            )
            response = self.oauth_session.post(
                url, json=order_payload
            )
            response.raise_for_status()
            logger.success("Order placed successfully.")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise

    def get_account_info(self) -> Dict[str, Any]:
        """
        Fetch account information, including balances and positions.

        Args:
            account_id: The account ID.

        Returns:
            A dictionary containing account details.
        """
        url = f"{self.BASE_URL}/accounts/{self.account_id}/balance"
        try:
            logger.info("Fetching account information...")
            response = self.oauth_session.get(url)
            response.raise_for_status()
            logger.success(
                "Fetched account information successfully."
            )
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch account information: {e}")
            raise

    def logout(self) -> None:
        """
        End the session with E*TRADE.
        """
        try:
            logger.info("Ending E*TRADE session...")
            # E*TRADE does not require explicit logout; session ends automatically.
            logger.success("Session ended.")
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
            raise


def get_acc_info():
    client = ETradeClient(account_id=os.getenv("ETRADE_ACCOUNT_ID"))

    return client.get_account_info()


# # Example Usage
# if __name__ == "__main__":
#     logger.add("etrade_client.log", rotation="1 MB", retention="10 days", level="DEBUG")

#     try:
#         client = ETradeClient()

#         # Fetch account info
#         account_id = "12345678"  # Replace with your account ID
#         account_info = client.get_account_info(account_id)
#         logger.info(f"Account Info: {account_info}")

#         # Place a buy order
#         buy_response = client.place_order(account_id, symbol="AAPL", quantity=10, action="BUY", price=150.00)
#         logger.info(f"Buy Order Response: {buy_response}")

#         # Place a sell order
#         sell_response = client.place_order(account_id, symbol="AAPL", quantity=10, action="SELL")
#         logger.info(f"Sell Order Response: {sell_response}")

#     except Exception as e:
#         logger.error(f"An error occurred: {e}")

#     finally:
#         # Logout not required for E*TRADE
#         logger.info("Execution completed.")
