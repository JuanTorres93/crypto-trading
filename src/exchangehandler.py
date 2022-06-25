from abc import ABC, abstractmethod

import ccxt


class ExchangeHandler(ABC):
    def __init__(self, exchange_api):
        self._exchange_api = exchange_api

    @abstractmethod
    def buy_market_order(self):
        raise NotImplementedError

    @abstractmethod
    def sell_market_order(self):
        raise NotImplementedError

    @abstractmethod
    def get_candles(self, symbol, vs_currency, timeframe, num_candles,
                    since=None):
        raise NotImplementedError

    @abstractmethod
    def get_fees(self):
        raise NotImplementedError


class CcxtExchangeHandler(ExchangeHandler):
    def __init__(self, exchange_api: ccxt.Exchange):
        if not isinstance(exchange_api, ccxt.Exchange):
            raise TypeError("Error exchange_api should be of type ccxt.Exchange")

        super().__init__(exchange_api)

    def buy_market_order(self):
        pass

    def sell_market_order(self):
        pass

    def get_candles(self, symbol, vs_currency, timeframe, num_candles,
                    since=None):
        pass

    def get_fees(self):
        pass


class BinanceCcxtExchangeHandler(CcxtExchangeHandler):
    def buy_market_order(self):
        pass

    def sell_market_order(self):
        pass

    def get_candles(self, symbol, vs_currency, timeframe, num_candles,
                    since=None):
        pass

    def get_fees(self):
        pass
