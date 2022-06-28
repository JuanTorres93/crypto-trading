import pytest

from ccxt import binance

from commonfixtures import bitcoin_price_eur, binance_eh_no_keys
import strategy as st


def test_fake_strategy_returns_correct_dictionary(bitcoin_price_eur, binance_eh_no_keys):
    # TODO TERMINAR TEST COMPROBANDO ENTRADAS EN DICCIONARIO
    results = st.FakeStrategy().perform_strategy(entry_price=bitcoin_price_eur,
                                    df=binance_eh_no_keys.get_candles_for_strategy(
                                    symbol='BTC', vs_currency='EUR',
                                    timeframe='1h', num_candles=20))