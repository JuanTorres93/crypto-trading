import pytest

import model
from commonfixtures import generic_trade_defaults


def test_trade_object_is_created(generic_trade_defaults):
    expected_trade = model.Trade(symbol="BTC", fiat_symbol="EUR",
                                 timeframe='5m',
                                 stop_loss=1, entry_price=2, take_profit=3,
                                 status=model.TradeStatus.OPENED, fiat_entry=20,
                                 crypto_quantity_entry=1.0, entry_fee_fiat=.2,
                                 position='L',
                                 entry_date='2022-06-18 12:13:40',
                                 entry_order_exchange_id='entry_id',
                                 percentage_change_1d_on_entry='2',
                                 percentage_change_7d_on_entry='2',
                                 percentage_change_1h_on_entry='2',
                                 strategy_name='test',
                                 is_real=False)

    assert expected_trade == generic_trade_defaults
