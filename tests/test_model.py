import pytest

import model
from commonfixtures import generic_trade_defaults


def test_trade_object_is_created(generic_trade_defaults):
    expected_trade = model.Trade(symbol="BTC", vs_currency_symbol="EUR",
                                 timeframe='5m',
                                 stop_loss=1, entry_price=2, take_profit=3,
                                 status=model.TradeStatus.OPENED, vs_currency_entry=20,
                                 crypto_quantity_entry=1.0, entry_fee_vs_currency=.2,
                                 position='L',
                                 entry_date='2022-06-18 12:13:40',
                                 entry_order_exchange_id='entry_id',
                                 percentage_change_1d_on_entry='2',
                                 percentage_change_7d_on_entry='2',
                                 percentage_change_1h_on_entry='2',
                                 strategy_name='test',
                                 is_real=False)

    assert expected_trade == generic_trade_defaults


def test_initial_trade_is_created():
    expected_trade = model.Trade(symbol="BTC", vs_currency_symbol="EUR",
                                 timeframe='5m',
                                 stop_loss=1, entry_price=2, take_profit=3,
                                 status=model.TradeStatus.OPENED, vs_currency_entry=20,
                                 crypto_quantity_entry=1.0, entry_fee_vs_currency=.2,
                                 position='L',
                                 entry_date='2022-07-21 15:10:45',
                                 entry_order_exchange_id='2022-07-21 15:10:45',
                                 percentage_change_1d_on_entry='2',
                                 percentage_change_7d_on_entry='2',
                                 percentage_change_1h_on_entry='2',
                                 strategy_name='test',
                                 is_real=False)


    actual_trade = model.create_initial_trade(symbol="BTC",
                                              vs_currency_symbol="EUR",
                                              timeframe='5m', stop_loss=1,
                                              entry_price=2, take_profit=3,
                                              vs_currency_entry=20,
                                              crypto_quantity_entry=1.0,
                                              entry_fee_vs_currency=.2,
                                              position='L',
                                              entry_order_exchange_id='2022-07-21 15:10:45',
                                              percentage_change_1h_on_entry='2',
                                              percentage_change_1d_on_entry='2',
                                              percentage_change_7d_on_entry='2',
                                              strategy_name='test',
                                              is_real=False,
                                              entry_date='2022-07-21 15:10:45',
                                              status=model.TradeStatus.OPENED)

    assert expected_trade == actual_trade


def test_trade_is_completed_by_market_sell():
    trade = model.create_initial_trade(symbol="BTC", vs_currency_symbol="EUR",
                                       timeframe='5m', stop_loss=1,
                                       entry_price=2, take_profit=3,
                                       vs_currency_entry=20,
                                       crypto_quantity_entry=1.0,
                                       entry_fee_vs_currency=.2, position='L',
                                       entry_order_exchange_id='2022-07-21 15:19:15',
                                       percentage_change_1h_on_entry='2',
                                       percentage_change_1d_on_entry='2',
                                       percentage_change_7d_on_entry='2',
                                       strategy_name='test', is_real=False,
                                       entry_date='2022-07-21 15:19:15',
                                       status=model.TradeStatus.OPENED)

    assert trade.vs_currency_result_no_fees is None
    assert trade.crypto_quantity_exit is None
    assert trade.exit_fee_vs_currency is None
    assert trade.exit_date is None

    model.complete_trade_with_market_sell_info(trade=trade,
                                               vs_currency_result_no_fees=2,
                                               crypto_quantity_exit=.98,
                                               exit_fee_vs_currency=.1,
                                               exit_date="2022-07-21 15:23:25",
                                               status=model.TradeStatus.WON)

    assert trade.vs_currency_result_no_fees is not None
    assert trade.crypto_quantity_exit is not None
    assert trade.exit_fee_vs_currency is not None
    assert trade.exit_date is not None

