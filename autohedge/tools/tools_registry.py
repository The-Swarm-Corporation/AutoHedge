from autohedge.tools.jupiter_search import search_tokens
from autohedge.tools.jupiter_price import get_token_price
from autohedge.tools.fxmacrodata import get_macro_release_calendar
from autohedge.tools.ultra_tools import execute_trade, get_holdings
from autohedge.tools.ultra_tools import get_order


def get_tools():
    return [
        search_tokens,
        get_token_price,
        get_macro_release_calendar,
        execute_trade,
        get_holdings,
        get_order,
    ]
