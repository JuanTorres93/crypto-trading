import pytest

import ccxt

import exchangehandler as eh


@pytest.fixture
def binance_eh_no_keys():
    return eh.BinanceCcxtExchangeHandler(ccxt.binance())


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


def test_binance_ccxt_exchange_handler_gets_candles(binance_eh_no_keys):
    # TODO añadir el parámetro since
    candles = binance_eh_no_keys.get_candles(symbol='BTC', vs_currency='EUR',
                                             timeframe='1h', num_candles='200')

