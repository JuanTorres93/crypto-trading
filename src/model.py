from dataclasses import dataclass


class TradeStatus:
    OPENED = 'opened'
    WON = 'won'
    LOST = 'lost'


@dataclass(kw_only=True, slots=True, order=True)
class trade:
    id: int
    symbol: str
    fiat_symbol: str
    timeframe: str
    stop_loss: float
    entry_price: float
    take_profit: float
    status: str
    fiat_entry: float
    crypto_quantity_entry: float
    entry_fee_fiat: float
    position: str
    entry_date: str
    entry_order_exchange_id: str
    percentage_change_1h_on_entry: str
    percentage_change_1d_on_entry: str
    percentage_change_7d_on_entry: str
    strategy_name: str
    is_real: bool
    oco_stop_exchange_id: str = None
    oco_limit_exchange_id: str = None
    fiat_result_no_fees: float = None
    modified_stop_loss: float = None
    modified_take_profit: float = None
    crypto_quantity_exit: float = None
    exit_fee_fiat: float = None
    exit_date: str = None
