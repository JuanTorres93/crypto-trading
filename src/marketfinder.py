from abc import ABC, abstractmethod
from time import sleep

import requests.exceptions
from pycoingecko import CoinGeckoAPI


class MarketFinder(ABC):
    def __init__(self, api):
        self.api = api
        self._top_markets = []
        self.markets_to_trade = []
        self.pairs_for_exchange_vs_currency = []

    @abstractmethod
    def get_top_markets(self, vs_currency):
        """
        Retrieves all available information from the top markets
        :param vs_currency: currency to complete the market
        :return: list of dictionaries
        """
        raise NotImplementedError

    @abstractmethod
    def list_top_symbols(self, vs_currency):
        """
        Should return an upper case list containing crypto symbols
        :param vs_currency: currency to complete market
        :return: list
        """
        raise NotImplementedError

    @abstractmethod
    def _get_symbol_info(self, symbol, vs_currency):
        raise NotImplementedError

    @abstractmethod
    def provide_markets_to_trade(self, exchange_id, vs_currency):
        raise NotImplementedError

    @abstractmethod
    def _get_pairs_for_exchange_single_page(self, exchange_id, page: int = 1):
        raise NotImplementedError

    @abstractmethod
    def get_pairs_for_exchange_vs_currency(self, exchange_id, vs_currency):
        raise NotImplementedError


class CoinGeckoMarketFinder(MarketFinder):
    def __init__(self, api):
        super().__init__(api)
        if not isinstance(api, CoinGeckoAPI):
            raise TypeError("api should be CoinGeckoAPI")

        self.pairs_for_exchange = []
        self.seconds_to_wait_on_http_error = 3

    def get_top_markets(self, vs_currency, force=False):
        if len(self._top_markets) == 0 or force:
            markets_fetched = False
            while not markets_fetched:
                try:
                    markets = self.api.get_coins_markets(vs_currency)
                    self._top_markets.clear()
                    self._top_markets = markets
                    markets_fetched = True
                except requests.exceptions.HTTPError:
                    sleep(self.seconds_to_wait_on_http_error)
        else:
            markets = self._top_markets

        return markets

    def list_top_symbols(self, vs_currency):
        markets = self.get_top_markets(vs_currency)

        symbols = list(
            map(
                lambda x: x['symbol'].upper(),
                markets
            )
        )
        return symbols

    def _get_symbol_info(self, symbol, vs_currency):
        markets = self.get_top_markets(vs_currency)
        symbol_id = list(
            filter(
                lambda x: x['symbol'].upper() == symbol.upper(),
                markets
            )
        )[0]['id']

        symbol_info_fetched = False

        while not symbol_info_fetched:
            try:
                symbol_info = self.api.get_coin_by_id(symbol_id)
                symbol_info_fetched = True
            except requests.exceptions.HTTPError:
                sleep(self.seconds_to_wait_on_http_error)

        symbol_info['symbol'] = symbol_info['symbol'].upper()
        return symbol_info

    def _get_pairs_for_exchange_single_page(self, exchange_id, page: int = 1):
        exchange_tickers_fetched = False

        while not exchange_tickers_fetched:
            try:
                exchange_tickers = self.api.get_exchanges_tickers_by_id(
                    exchange_id, page=page)
                exchange_tickers_fetched = True
            except requests.exceptions.HTTPError:
                sleep(self.seconds_to_wait_on_http_error)

        return exchange_tickers

    def get_pairs_for_exchange(self, exchange_id, force=False):
        if len(self.pairs_for_exchange) == 0 or force:
            tickers = []
            page = 1

            exchange_tickers = self._get_pairs_for_exchange_single_page(exchange_id,
                                                                        page=page)

            while len(exchange_tickers['tickers']) > 0:
                page += 1
                for ticker in exchange_tickers['tickers']:
                    tickers.append(ticker)

                exchange_tickers = self._get_pairs_for_exchange_single_page(
                    exchange_id, page=page)

            self.pairs_for_exchange.clear()
            self.pairs_for_exchange = tickers
        else:
            tickers = self.pairs_for_exchange

        return tickers

    def get_pairs_for_exchange_vs_currency(self, exchange_id, vs_currency):
        # TODO ejecutarla al instacnciar y guardar resultados en una variable de instancia
        # TODO EJECUTARLA CADA MES
        tickers = self.get_pairs_for_exchange(exchange_id)

        tickers = list(
            filter(lambda x: x['target'].upper() == vs_currency.upper(),
                   tickers)
        )

        tickers = list(
            map(
                lambda x: {
                    'base': x['base'].upper(),
                    'target': x['target'].upper(),
                },
                tickers
            )
        )

        self.pairs_for_exchange_vs_currency = tickers
        return tickers

    def provide_markets_to_trade(self, exchange_id, vs_currency):
        top_symbols = set(self.list_top_symbols(vs_currency))

        symbols_in_exchange = self.get_pairs_for_exchange_vs_currency(
                                   exchange_id, vs_currency)

        symbols_in_exchange = set(
            map(
                lambda x: x['base'],
                symbols_in_exchange
            )
        )

        symbols_to_fetch = top_symbols.intersection(symbols_in_exchange)

        markets_to_trade = []

        for symbol in symbols_to_fetch:
            info = self._get_symbol_info(symbol, vs_currency)
            lower_case_vs_currency = vs_currency.lower()

            if lower_case_vs_currency in info['market_data'][
                'price_change_percentage_1h_in_currency'] and \
                    lower_case_vs_currency in info['market_data'][
                'price_change_percentage_24h_in_currency'] and \
                    lower_case_vs_currency in info['market_data'][
                'price_change_percentage_7d_in_currency']:
                markets_to_trade.append(
                    {
                        'symbol': symbol,
                        'market_cap_rank': info['market_cap_rank'],
                        'coingecko_rank': info['coingecko_rank'],
                        'market_cap': info['market_data']['market_cap'],
                        'high_24h': info['market_data']['high_24h'],
                        'low_24h': info['market_data']['low_24h'],
                        'price_change_percentage_1h': info['market_data'][
                            'price_change_percentage_1h_in_currency'][
                            lower_case_vs_currency],
                        'price_change_percentage_24h': info['market_data'][
                            'price_change_percentage_24h_in_currency'][
                            lower_case_vs_currency],
                        'price_change_percentage_7d': info['market_data'][
                            'price_change_percentage_7d_in_currency'][
                            lower_case_vs_currency],
                    }
                )

        def filter_positive(ls, key):
            filtered = list(
                filter(
                    lambda x: x[key] > 0,
                    ls
                )
            )

            return sorted(filtered, key=lambda x: x[key], reverse=True)

        positive_7d = filter_positive(markets_to_trade, 'price_change_percentage_7d')
        positive_24h = filter_positive(markets_to_trade, 'price_change_percentage_24h')
        positive_1h = filter_positive(markets_to_trade, 'price_change_percentage_1h')

        ordered_markets = positive_7d + positive_24h + positive_1h
        markets_to_trade.clear()

        if len(ordered_markets) > 0:
            for market in ordered_markets:
                if market not in markets_to_trade:
                    markets_to_trade.append(market)

        self.markets_to_trade.clear()
        self.markets_to_trade = markets_to_trade
        return markets_to_trade


if __name__ == '__main__':
    borrar = CoinGeckoMarketFinder(CoinGeckoAPI())
    h = borrar.get_pairs_for_exchange('binance')
    h = borrar.get_pairs_for_exchange('binance')
    # h = borrar.provide_markets_to_trade('binance', 'EUR')
    pass
