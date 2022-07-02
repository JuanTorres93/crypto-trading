from pycoingecko import CoinGeckoAPI
import pytest

import marketfinder


coingecko_marketfinder = marketfinder.CoinGeckoMarketFinder(CoinGeckoAPI())


def test_coingecko_gets_top_markets():
    top_markets = coingecko_marketfinder.get_top_markets('EUR')

    assert len(top_markets) == 100

    actual_keys = set(top_markets[0].keys())
    expected_keys = {'id', 'symbol', 'name', 'market_cap', 'high_24h', 'low_24h'}

    assert expected_keys.issubset(actual_keys)


def test_coingecko_lists_top_symbols():
    top_symbols = coingecko_marketfinder.list_top_symbols('EUR')

    assert len(top_symbols) == 100
    assert type(top_symbols[0]) is str


def test_coingecko_gets_detailed_market_information():
    markets_info = coingecko_marketfinder._get_symbol_info('BTC', 'EUR')

    actual_keys = set(markets_info.keys())
    expected_keys = {'id', 'symbol', 'name', 'market_cap_rank', 'coingecko_rank',
                     'market_data', 'community_data'}

    assert expected_keys.issubset(actual_keys)

    market_data_actual_keys = set(markets_info['market_data'].keys())
    market_data_expected_keys = {'market_cap', 'high_24h', 'low_24h',
                                 'price_change_percentage_1h_in_currency',
                                 'price_change_percentage_24h_in_currency',
                                 'price_change_percentage_7d_in_currency',
                                 }

    assert market_data_expected_keys.issubset(market_data_actual_keys)


def test_coingecko_gets_single_page_pairs_for_exchange():
    pairs = coingecko_marketfinder._get_pairs_for_exchange_single_page(
        'binance')

    assert type(pairs) is dict
    assert {'tickers'}.issubset(set(pairs.keys()))


def test_coingecko_gets_pairs_for_exchange():
    pairs_web = coingecko_marketfinder._get_pairs_for_exchange('binance')

    assert type(pairs_web) is list
    for pair in pairs_web:
        assert type(pair) is dict

    assert {'target', 'base'}.issubset(set(pairs_web[0].keys()))

    pairs_instance_attr_1 = coingecko_marketfinder._get_pairs_for_exchange(
        'binance')
    pairs_instance_attr_2 = coingecko_marketfinder._get_pairs_for_exchange(
        'binance', force=False)

    assert pairs_web == pairs_instance_attr_1 == pairs_instance_attr_2


def test_coingecko_gets_pairs_for_exchange_vs_currency():
    pairs = coingecko_marketfinder.get_pairs_for_exchange_vs_currency('binance', 'EUR')

    assert type(pairs) is list
    for pair in pairs:
        assert type(pair) is dict
        assert pair['target'] == 'EUR'


def test_coingecko_gets_pairs_for_exchange_symbol_vs():
    pairs = coingecko_marketfinder.get_pairs_for_exchange_symbol_vs('binance', 'ADA')

    assert type(pairs) is list
    for pair in pairs:
        assert type(pair) is dict
        assert pair['base'] == 'ADA'


def test_coingecko_orders_markets_according_percentage_change():
    # TODO completar test y comprobar el orden
    markets_to_trade = coingecko_marketfinder.provide_markets_to_trade('binance', 'EUR')

    assert type(markets_to_trade) is list
    for market in markets_to_trade:
        assert type(market) is dict

    expected_keys = {'symbol', 'market_cap_rank', 'coingecko_rank',
                     'market_cap', 'high_24h', 'low_24h',
                     'price_change_percentage_7d',
                     'price_change_percentage_24h',
                     'price_change_percentage_1h'}

    assert expected_keys.issubset(set(markets_to_trade[0].keys()))
