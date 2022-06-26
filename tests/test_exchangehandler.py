import pytest

import ccxt
import pandas as pd
from pycoingecko import CoinGeckoAPI

import config
import exchangehandler as eh
import marketfinder as mf


# These variables are used to perform actual buys and sells
# Sell value is slightly lower in order not to raise exceptions due to not
# beign able to sell the bought amount since fees exists
currency_to_test_real_trades = 'EUR'
value_to_test_buys_real_trades = 11
value_to_test_sells_real_trades = 10.8

@pytest.fixture
def binance_eh_no_keys():
    return eh.BinanceCcxtExchangeHandler(ccxt.binance())


@pytest.fixture
def bitcoin_price_eur():
    cg = mf.CoinGeckoMarketFinder(CoinGeckoAPI())
    markets = cg.get_top_markets('EUR')
    btc_price = list(
        filter(
            lambda x: x['symbol'] == 'btc',
            markets
        )
    )[0]['current_price']

    return btc_price


@pytest.fixture
def binance_eh():
    return eh.BinanceCcxtExchangeHandler(ccxt.binance(
        {
            'apiKey': config.BINANCE_API_KEY,
            'secret': config.BINANCE_SECRET_KEY,
            'enableLimitRate': True,
        }
    ))


def test_ccxt_exchange_handler_raises_exception_on_init_with_wrong_api():
    with pytest.raises(TypeError) as e:
        eh.CcxtExchangeHandler(exchange_api="")


def test_ccxt_exchange_handler_not_raises_exception_on_init_with_right_api():
    try:
        eh.CcxtExchangeHandler(exchange_api=ccxt.Exchange())
    except TypeError:
        pytest.fail()

    try:
        eh.CcxtExchangeHandler(exchange_api=ccxt.binance())
    except TypeError:
        pytest.fail()


def test_binance_ccxt_exchange_handler_fixes_amount_to_precision(binance_eh_no_keys):
    initial_amount = 3.3769647596934765978659876976397286592736492736597264359786295623478
    fixed_amount = binance_eh_no_keys._amount_to_precision('BTC', 'EUR', initial_amount)

    assert len(str(initial_amount)) > len(str(fixed_amount))


def test_binance_ccxt_exchange_handler_gets_candles(binance_eh_no_keys):
    candles = binance_eh_no_keys.get_candles_for_strategy(symbol='BTC',
                                                          vs_currency='EUR',
                                                          timeframe='1h',
                                                          num_candles=20,
                                                          since=None)

    assert isinstance(candles, pd.DataFrame)
    assert len(candles) == 19
    assert set(candles.columns).issubset({'datetime', 'open', 'high', 'low', 'close',
                                     'volume', 'is_green', 'is_red',
                                     'candle_body_low', 'candle_body_high'})


@pytest.mark.spends_money
def test_binance_ccxt_exchange_handler_buys_at_market_price(binance_eh, bitcoin_price_eur):
    amount = value_to_test_buys_real_trades / bitcoin_price_eur
    order = binance_eh.buy_market_order(symbol='BTC', vs_currency=currency_to_test_real_trades,
                                        amount=amount)

    expected_keys = {'exchange_id', 'timestamp', 'price', 'amount', 'cost',
                     'fee_in_asset'}

    assert expected_keys.issubset(set(order.keys()))


@pytest.mark.spends_money
def test_binance_ccxt_exchange_handler_sells_at_market_price(binance_eh, bitcoin_price_eur):
    amount = value_to_test_sells_real_trades / bitcoin_price_eur
    order = binance_eh.sell_market_order(symbol='BTC', vs_currency=currency_to_test_real_trades,
                                         amount=amount)

    expected_keys = {'exchange_id', 'timestamp', 'price', 'amount', 'cost',
                     'fee_in_asset'}

    assert expected_keys.issubset(set(order.keys()))


def test_binance_ccxt_exchange_handler_fetches_fee_factors(binance_eh):
    fee_factors = binance_eh.get_fee_factor('BTC', 'EUR')

    assert type(fee_factors) is dict

    expected_keys = {'maker', 'taker'}
    actual_keys = set(fee_factors.keys())

    assert expected_keys.issubset(actual_keys)
