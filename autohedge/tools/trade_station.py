import os
import requests
from typing import Dict, List, Optional, Any
from loguru import logger


def confirm_order(
    account_id: str = os.getenv("TRADE_STATION_ACCOUNT_ID"),
    symbol: str = None,
    quantity: str = 1,
    order_type: str = "Market",
    trade_action: str = "BUY",
    time_in_force: Optional[Dict[str, str]] = None,
    route: Optional[str] = None,
    limit_price: Optional[str] = None,
    stop_price: Optional[str] = None,
    advanced_options: Optional[Dict[str, Any]] = None,
    buying_power_warning: Optional[str] = None,
    legs: Optional[List[Dict[str, Any]]] = None,
    osos: Optional[List[Dict[str, Any]]] = None,
    order_confirm_id: Optional[str] = None,
    token: Optional[str] = os.getenv("TRADE_STATION_TOKEN"),
) -> Dict[str, Any]:
    """
    Confirms an order without actually placing it, returning estimated cost and commission information.

    Parameters:
    -----------
    account_id : str
        TradeStation Account ID
    symbol : str
        The symbol used for this order
    quantity : str
        The quantity of the order
    order_type : str
        The order type: "Market", "Limit", "StopMarket", or "StopLimit"
    trade_action : str
        Trade action: "BUY", "SELL", "BUYTOCOVER", "SELLSHORT", "BUYTOOPEN",
        "BUYTOCLOSE", "SELLTOOPEN", "SELLTOCLOSE"
    time_in_force : Dict[str, str], optional
        TimeInForce defines the duration and expiration timestamp, e.g. {"Duration": "DAY"}
    route : str, optional
        The route of the order. Defaults to "Intelligent" for Stocks and Options
    limit_price : str, optional
        The limit price for this order
    stop_price : str, optional
        The stop price for this order
    advanced_options : Dict[str, Any], optional
        Advanced options for the order
    buying_power_warning : str, optional
        For TradeStation Margin accounts enrolled in Reg-T program
    legs : List[Dict[str, Any]], optional
        Array of order request legs
    osos : List[Dict[str, Any]], optional
        Array of order request OSOs
    order_confirm_id : str, optional
        A unique identifier to prevent duplicates
    token : str, optional
        Bearer token for authorization

    Returns:
    --------
    Dict[str, Any]
        The order confirmation response containing estimated price, cost, and commission information

    Raises:
    -------
    requests.exceptions.RequestException
        If there's an issue with the HTTP request
    ValueError
        If required parameters are missing or invalid

    Examples:
    ---------
    >>> response = confirm_order(
    ...     account_id="123456782",
    ...     symbol="MSFT",
    ...     quantity="10",
    ...     order_type="Market",
    ...     trade_action="BUY",
    ...     token="YOUR_TOKEN"
    ... )
    >>> print(response["EstimatedCostDisplay"])
    $3,450.00
    """
    url = (
        "https://api.tradestation.com/v3/orderexecution/orderconfirm"
    )

    logger.debug(
        f"Preparing order confirmation request for {symbol}, {quantity} {trade_action}"
    )

    # Build the payload with required fields
    payload = {
        "AccountID": account_id,
        "Symbol": symbol,
        "Quantity": quantity,
        "OrderType": order_type,
        "TradeAction": trade_action,
        "StopPrice": stop_price,
        "LimitPrice": limit_price,
    }

    # Add optional fields if provided
    if time_in_force:
        payload["TimeInForce"] = time_in_force
    else:
        payload["TimeInForce"] = {"Duration": "DAY"}

    if route:
        payload["Route"] = route
    else:
        payload["Route"] = "Intelligent"

    if limit_price:
        payload["LimitPrice"] = limit_price

    if stop_price:
        payload["StopPrice"] = stop_price

    if advanced_options:
        payload["AdvancedOptions"] = advanced_options

    if buying_power_warning:
        payload["BuyingPowerWarning"] = buying_power_warning

    if legs:
        payload["Legs"] = legs

    if osos:
        payload["OSOs"] = osos

    if order_confirm_id:
        payload["OrderConfirmID"] = order_confirm_id

    # Set up headers
    headers = {
        "content-type": "application/json",
    }

    # Add authorization token if provided
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        logger.warning(
            "No authorization token provided for order confirmation request"
        )

    logger.debug(
        "Sending order confirmation request to TradeStation API"
    )

    try:
        # Make the request
        response = requests.request(
            "POST", url, json=payload, headers=headers
        )
        response.raise_for_status()  # Raise exception for 4XX/5XX responses

        logger.info(
            f"Order confirmation successful for {symbol}, {quantity} {trade_action}"
        )
        logger.debug(
            f"Order confirmation response: {response.text[:100]}..."
        )

        # Return the response as a dictionary
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"Error confirming order: {str(e)}")
        logger.debug(f"Request payload: {payload}")
        raise


# Example usage:
# response = confirm_order(
#     account_id="123456782",
#     symbol="MSFT",
#     quantity="10",
#     order_type="Market",
#     trade_action="BUY",
#     token="YOUR_TOKEN"
# )
# print(response)
