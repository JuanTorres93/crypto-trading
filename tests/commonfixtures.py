import ccxt
from pycoingecko import CoinGeckoAPI
import pytest
from sqlalchemy.orm import Session

import config
import exchangehandler as eh
import marketfinder as mf
import model
import orm
import repository


def create_trade(symbol="BTC", vs_currency_symbol="EUR", timeframe='5m',
                 stop_loss=1, entry_price=2, take_profit=3,
                 status=model.TradeStatus.OPENED, vs_currency_entry=20,
                 crypto_quantity_entry=1.0, entry_fee_vs_currency=.2,
                 position='L',
                 entry_date='2022-06-18 12:13:40',
                 entry_order_exchange_id='entry_id',
                 percentage_change_1d_on_entry='2',
                 percentage_change_7d_on_entry='2',
                 percentage_change_1h_on_entry='2', strategy_name='test',
                 is_real=False, vs_currency_result_no_fees=None,
                 crypto_quantity_exit=None, exit_fee_vs_currency=None, exit_date=None,
                 oco_stop_exchange_id=None, oco_limit_exchange_id=None):

    return model.Trade(symbol=symbol, vs_currency_symbol=vs_currency_symbol, timeframe=timeframe,
                       stop_loss=stop_loss, entry_price=entry_price, take_profit=take_profit,
                       status=status, vs_currency_entry=vs_currency_entry,
                       crypto_quantity_entry=crypto_quantity_entry, entry_fee_vs_currency=entry_fee_vs_currency,
                       position=position,
                       entry_date=entry_date,
                       entry_order_exchange_id=entry_order_exchange_id,
                       percentage_change_1d_on_entry=percentage_change_1d_on_entry,
                       percentage_change_7d_on_entry=percentage_change_7d_on_entry,
                       percentage_change_1h_on_entry=percentage_change_1h_on_entry, strategy_name=strategy_name,
                       is_real=is_real, vs_currency_result_no_fees=vs_currency_result_no_fees,
                       crypto_quantity_exit=crypto_quantity_exit,
                       exit_fee_vs_currency=exit_fee_vs_currency, exit_date=exit_date,
                       oco_stop_exchange_id=oco_stop_exchange_id,
                       oco_limit_exchange_id=oco_limit_exchange_id)


@pytest.fixture
def generic_trade_defaults():
    return model.create_initial_trade(symbol="BTC", vs_currency_symbol="EUR",
                                      timeframe='5m', stop_loss=1,
                                      entry_price=2, take_profit=3,
                                      vs_currency_entry=20,
                                      crypto_quantity_entry=1.0,
                                      entry_fee_vs_currency=.2, position='L',
                                      entry_order_exchange_id='entry_id',
                                      percentage_change_1h_on_entry='2',
                                      percentage_change_1d_on_entry='2',
                                      percentage_change_7d_on_entry='2',
                                      strategy_name='test', is_real=False,
                                      entry_date='2022-06-18 12:13:40',
                                      status=model.TradeStatus.OPENED)


@pytest.fixture
def testing_session():
    return Session(orm.test_engine)


@pytest.fixture
def bitcoin_price_eur():
    cg = mf.CoinGeckoMarketFinder()
    markets = cg.get_top_markets('EUR')
    btc_price = list(
        filter(
            lambda x: x['symbol'] == 'btc',
            markets
        )
    )[0]['current_price']

    return btc_price


@pytest.fixture
def binance_eh_no_keys():
    return eh.CcxtExchangeHandler(ccxt.binance())


@pytest.fixture
def binance_eh():
    return eh.CcxtExchangeHandler(ccxt.binance(
        {
            'apiKey': config.BINANCE_API_KEY,
            'secret': config.BINANCE_SECRET_KEY,
            'enableLimitRate': True,
        }
    ))


@pytest.fixture
def sqlalchemyrepository_testing(testing_session):
    return repository.provide_sqlalchemy_repository(real_db=False)
