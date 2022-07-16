import pytest

from commonfixtures import bitcoin_price_eur, binance_eh_no_keys
import strategy as st


def test_dictionary_keys_for_strategy_output():
    sto = st.StrategyOutput(can_enter=True, take_profit=12.0, stop_loss=10.0,
                            entry_price=11.0,
                            position_type=st.PositionType.LONG)

    assert type(sto.can_enter) == bool
    assert type(sto.take_profit) == float
    assert type(sto.entry_price) == float
    assert type(sto.stop_loss) == float
    assert type(sto.position_type) == str


def test_fake_strategy_returns_strategy_output(bitcoin_price_eur, binance_eh_no_keys):
    candles = binance_eh_no_keys.get_candles_for_strategy(symbol='BTC',
                                                          vs_currency='EUR',
                                                          timeframe='1h',
                                                          num_candles=20)

    results = st.TestStrategy().perform_strategy(entry_price=bitcoin_price_eur,
                                                 df=candles)

    assert isinstance(results, st.StrategyOutput)