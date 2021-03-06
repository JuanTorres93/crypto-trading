from dataclasses import dataclass, field


class TradeStatus:
    OPENED = 'opened'
    WON = 'won'
    LOST = 'lost'


@dataclass(kw_only=True)
class Trade:
    # IMPORTANT: vs_currency,FOR NOW, MUST BE A FIAT COIN
    id: int = field(init=False, compare=False) # Database id
    symbol: str         # Symbol of the asset to trade
    vs_currency_symbol: str    # Symbol of the vs_currency
    timeframe: str      # Timeframe in which the strategy is analyzed
    stop_loss: float    # Strategy stop loss
    entry_price: float  # Position entry price
    take_profit: float  # Strategy take profit
    status: str         # Current status of the trade (TradeStatus)
    vs_currency_entry: float   # vs_currency quantity on entry
    crypto_quantity_entry: float # asset to trade quantity entry
    entry_fee_vs_currency: float # entry fee vs_currenty on entry position
    position: str       # Position side of trade (long or short)
    entry_date: str     # Date and time of entry
    entry_order_exchange_id: str        # Web exchange entry id
    percentage_change_1h_on_entry: str
    percentage_change_1d_on_entry: str
    percentage_change_7d_on_entry: str
    strategy_name: str
    is_real: bool
    oco_stop_exchange_id: str = None    # Web exchange stop order id
    oco_limit_exchange_id: str = None   # Web exchange take profit id
    vs_currency_result_no_fees: float = None    # Trade result not taking fees into account
    modified_stop_loss: float = None
    modified_take_profit: float = None
    crypto_quantity_exit: float = None
    exit_fee_vs_currency: float = None
    exit_date: str = None
