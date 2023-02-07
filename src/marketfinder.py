from abc import ABC, abstractmethod
from time import sleep

import requests.exceptions
from pycoingecko import CoinGeckoAPI


class MarketFinder(ABC):
    """
    This class is aimed to retrieve current market information. It includes services like
    CoinGecko, CoinMarketCap, etc.
    """
    def __init__(self):
        # Instantiate api on children classes
        self._api = None
        # Saves top markets info when get_called_markets is called to avoid api calls
        self._top_markets = []
        # Saves markets to trade when provide_markets_to_trade is called to avoid api calls
        self._markets_to_trade = []

    @abstractmethod
    def get_top_markets(self, vs_currency, force=False):
        """
        Retrieves all available information from the top markets
        THIS FUNCTION IS INTENDED TO BE SCHEDULED BETWEEN EACH MARKET ANALYSIS
        :param vs_currency: currency to complete the market
        :param force: forces call on api to update instance variable
        :return: list of dictionaries
        """
        raise NotImplementedError

    @abstractmethod
    def get_pairs_for_exchange_vs_currency(self, exchange_id, vs_currency, force=False):
        """
        Retrieves all pairs for the given exchange and vs_currency
        THIS FUNCTION IS INTENDED TO BE SCHEDULED FOR LONG PERIODS OF TIME
        (1 time per month/week or so) TO KEEP UPDATE WITH NEW PAIRS. CALLED WITH force=True
        :param exchange_id: exchange id to ensure currencies are listed in it
        :param vs_currency: vs_currency to complete market
        :param force: forces call on api to update instance variable
        :return: list of dictionaries
        """
        raise NotImplementedError

    @abstractmethod
    def get_pairs_for_exchange_symbol_vs(self, exchange_id, symbol_vs, force=False):
        """
        Retrieves all pairs for the given exchange and symbol_vs (firt currency in market symbol)
        THIS FUNCTION IS INTENDED TO BE USED FOR TRIPLE SYMBOL TRADING
        :param exchange_id: exchange id to ensure currencies are listed in it
        :param symbol_vs: vs_currency to complete market
        :param force: forces call on api to update instance variable
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
    def provide_markets_to_trade(self, exchange_id, vs_currency):
        """
        Returns an ordered list of markets with useful information
        :param exchange_id: exchange id to ensure currencies are listed in it
        :param vs_currency: vs to complete market
        :return: List of dicts containing market info
        """
        raise NotImplementedError


class CoinGeckoMarketFinder(MarketFinder):
    def __init__(self):
        super().__init__()
        self._api = CoinGeckoAPI()
        # Saves available pairs for exchange when get_pairs_for_exchange is called to avoid api calls
        self._pairs_for_exchange = []
        # Time to wait when api credits are over
        self._seconds_to_wait_on_http_error = 3

    def get_top_markets(self, vs_currency, force=False):
        """
        See description on parent class
        """
        if len(self._top_markets) == 0 or force:
            # If no markets have already been fetched, or it is force to fetch them
            markets_fetched = False
            while not markets_fetched:
                # While loop is meant for handling lack of credits for api calls
                try:
                    # Fetch markets
                    markets = self._api.get_coins_markets(vs_currency)
                    # Store them in the instance variable
                    self._top_markets.clear()
                    self._top_markets = markets
                    markets_fetched = True
                except requests.exceptions.HTTPError:
                    # If api credits are over, wait and try again
                    sleep(self._seconds_to_wait_on_http_error)
        else:
            # Retrieve stored information
            markets = self._top_markets

        return markets

    def list_top_symbols(self, vs_currency):
        """
        See description on parent class
        """
        markets = self.get_top_markets(vs_currency)

        symbols = list(
            map(
                lambda x: x['symbol'].upper(),
                markets
            )
        )
        return symbols

    def _get_symbol_info(self, symbol, vs_currency):
        """
        Gets detailed information about the given symbol if it belongs to the top markets
        :param symbol: Symbol to fetch information from
        :param vs_currency: currency to complete the market
        :return: dict
        """
        markets = self.get_top_markets(vs_currency)
        # Symbol id is needed to call the api function
        symbol_id = list(
            filter(
                lambda x: x['symbol'].upper() == symbol.upper(),
                markets
            )
        )[0]['id']

        symbol_info_fetched = False
        while not symbol_info_fetched:
            # While loop is meant to handle exception without recursion
            try:
                # Get symbol information
                symbol_info = self._api.get_coin_by_id(symbol_id)
                symbol_info_fetched = True
            except requests.exceptions.HTTPError:
                # Wait if credits are over
                sleep(self._seconds_to_wait_on_http_error)

        # Make symbol upper case for consistency with other packages
        symbol_info['symbol'] = symbol_info['symbol'].upper()
        return symbol_info

    def _get_pairs_for_exchange_single_page(self, exchange_id, page: int = 1):
        """
        All pairs in a given exchage are paginated in pages of 100 items. This
        function fetches the specified page
        :param exchange_id: exchange id to fetch pairs from
        :param page: page number to fetch
        :return: dict with, at least, 'tickers' key
        """
        exchange_tickers_fetched = False

        while not exchange_tickers_fetched:
            # While loop to handle exception
            try:
                # Fetch information
                exchange_tickers = self._api.get_exchanges_tickers_by_id(
                    exchange_id, page=page)
                exchange_tickers_fetched = True
            except requests.exceptions.HTTPError:
                # Wait if api credits are over
                sleep(self._seconds_to_wait_on_http_error)

        return exchange_tickers

    def _get_pairs_for_exchange(self, exchange_id, force=False):
        """
        Retrieves all pairs for the given exchange
        :param exchange_id: exchange id to ensure currencies are listed in it
        :param force: forces call on api to update instance variable
        :return: list of dictionaries
        """
        if len(self._pairs_for_exchange) == 0 or force:
            # List to store all tickers from all possible pages
            tickers = []
            # Counter to loop over pages
            page = 1

            # Get first page
            exchange_tickers = self._get_pairs_for_exchange_single_page(exchange_id,
                                                                        page=page)

            while len(exchange_tickers['tickers']) > 0:
                # Loop while pages information is retrieved.
                # Prepare counter for next page
                page += 1
                for ticker in exchange_tickers['tickers']:
                    # Append every fetched ticker to tickers list
                    tickers.append(ticker)

                # Fetch next ticker pages
                exchange_tickers = self._get_pairs_for_exchange_single_page(
                    exchange_id, page=page)

            # Store tickers in memory
            self._pairs_for_exchange.clear()
            self._pairs_for_exchange = tickers
        else:
            tickers = self._pairs_for_exchange

        return tickers

    def get_pairs_for_exchange_vs_currency(self, exchange_id, vs_currency, force=False):
        """
        See description on parent class
        """
        # Get all pairs for exchange
        tickers = self._get_pairs_for_exchange(exchange_id, force=force)

        # Filter by the given vs_currency
        tickers = list(
            filter(lambda x: x['target'].upper() == vs_currency.upper(),
                   tickers)
        )

        # Extract base (left-part of market) and target (right-part of market)
        # currencies to form the market
        tickers = list(
            map(
                lambda x: {
                    'base': x['base'].upper(),
                    'target': x['target'].upper(),
                },
                tickers
            )
        )

        return tickers

    def get_pairs_for_exchange_symbol_vs(self, exchange_id, symbol_vs, force=False):
        """
        See description on parent class
        """
        # Get all pairs for exchange
        tickers = self._get_pairs_for_exchange(exchange_id, force=force)

        # Filter by the given vs_currency
        tickers = list(
            filter(lambda x: x['base'].upper() == symbol_vs.upper(),
                   tickers)
        )

        # Extract base (left-part of market) and target (right-part of market)
        # currencies to form the market
        tickers = list(
            map(
                lambda x: {
                    'base': x['base'].upper(),
                    'target': x['target'].upper(),
                },
                tickers
            )
        )

        return tickers

    def provide_markets_to_trade(self, exchange_id, vs_currency):
        """
        See description on parent class
        """
        if len(self._markets_to_trade) == 0:
            # Fetch top symbols
            top_symbols = set(self.list_top_symbols(vs_currency))

            # Get symbols in exchange for the given vs_currency
            symbols_in_exchange = self.get_pairs_for_exchange_vs_currency(
                                       exchange_id, vs_currency)

            # Extract just the symbols
            symbols_in_exchange = set(
                map(
                    lambda x: x['base'],
                    symbols_in_exchange
                )
            )

            # Symbols to fetch are those that are in the top and also
            # available in the exchange for the given vs_currency
            symbols_to_fetch = top_symbols.intersection(symbols_in_exchange)

            # Initialize list for the markets to trade
            markets_to_trade = []

            for symbol in symbols_to_fetch:
                # For every tradable symbol
                # Fetch its detailed information
                info = self._get_symbol_info(symbol, vs_currency)

                # This is needed to retrieve information from the api
                lower_case_vs_currency = vs_currency.lower()

                if lower_case_vs_currency in info['market_data'][
                    'price_change_percentage_1h_in_currency'] and \
                        lower_case_vs_currency in info['market_data'][
                    'price_change_percentage_24h_in_currency'] and \
                        lower_case_vs_currency in info['market_data'][
                    'price_change_percentage_7d_in_currency']:
                    # hourly, daily and weekly percentage change for the given
                    # vs_currency is available, then store the info in the list

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
                """
                Remove all downtrending markets for the given timeframe
                :param ls: list to filter
                :param key: percentage change key
                :return: ordered list according key
                """
                filtered = list(
                    filter(
                        lambda x: x[key] > 0,
                        ls
                    )
                )

                return sorted(filtered, key=lambda x: x[key], reverse=True)

            # Filter markets according their trends
            positive_7d = filter_positive(markets_to_trade, 'price_change_percentage_7d')
            positive_24h = filter_positive(markets_to_trade, 'price_change_percentage_24h')
            positive_1h = filter_positive(markets_to_trade, 'price_change_percentage_1h')

            ordered_markets = positive_7d + positive_24h + positive_1h
            markets_to_trade.clear()

            # Establish order of markets to trade
            if len(ordered_markets) > 0:
                for market in ordered_markets:
                    if market not in markets_to_trade:
                        markets_to_trade.append(market)

            self._markets_to_trade.clear()
            self.markets_to_trade = markets_to_trade
        else:
            markets_to_trade = self.markets_to_trade

        return markets_to_trade


if __name__ == '__main__':
    borrar = CoinGeckoMarketFinder()
    eur = borrar.get_pairs_for_exchange_vs_currency('binance', 'BTC')
    ada = borrar.get_pairs_for_exchange_symbol_vs('binance', 'ADA')
    pass
