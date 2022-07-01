import pytest

from ccxt import binance

from commonfixtures import bitcoin_price_eur, binance_eh_no_keys
import strategy as st


def test_dictionary_keys_for_strategy_output():
    sto = st.StrategyOutput(can_enter=True, take_profit=12.0, stop_loss=10.0)

    assert type(sto.can_enter) == bool
    assert type(sto.take_profit) == float
    assert type(sto.stop_loss) == float


def test_fake_strategy_returns_correct_dictionary(bitcoin_price_eur, binance_eh_no_keys):
    candles = binance_eh_no_keys.get_candles_for_strategy(symbol='BTC',
                                                          vs_currency='EUR',
                                                          timeframe='1h',
                                                          num_candles=20)

    results = st.FakeStrategy().perform_strategy(entry_price=bitcoin_price_eur,
                                                 df=candles)

    assert isinstance(results, st.StrategyOutput)