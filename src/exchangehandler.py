from abc import ABC, abstractmethod

import ccxt
import numpy as np
import pandas as pd


class ExchangeHandler(ABC):
    def __init__(self, exchange_api):
        self._exchange_api = exchange_api

    @abstractmethod
    def buy_market_order(self, symbol, vs_currency, amount):
        """
        Buys in the market symbol vs_currency the specified amount of symbol
        :param symbol: symbol to buy
        :param vs_currency: vs_currency to complete the market
        :param amount: amount of symbol to buy
        :return: filled order
        """
        raise NotImplementedError

    @abstractmethod
    def _sell_market_order(self, symbol, vs_currency, amount):
        """
        Sells in the market symbol vs_currency the specified amount of symbol
        :param symbol: symbol to sell
        :param vs_currency: vs_currency to complete the market
        :param amount: amount of symbol to sell
        :return: filled order
        """
        raise NotImplementedError

    @abstractmethod
    def sell_market_order_diminishing_amount(self, symbol, vs_currency, amount):
        """
        Sells in the market symbol vs_currency the specified amount of symbol.
        If the exchange is not able to sell the specified amount, then reduce it
        little by little until it can.
        :param symbol: symbol to sell
        :param vs_currency: vs_currency to complete the market
        :param amount: amount of symbol to sell
        :return: filled order
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_market(self, symbol: str, vs_currency):
        """
        Returns useful information for the market of the given symbol
        :param symbol: symbol to sell
        :param vs_currency: vs_currency to complete the market
        :return: Dictionary containing market information
        """
        raise NotImplementedError

    @abstractmethod
    def get_candles_for_strategy(self, symbol, vs_currency, timeframe, num_candles,
                                 since=None):
        """
        Gets the last candles available. It ALWAYS returns one candle less than those
        specified to avoid taking into account the current UNFINISHED candle
        :param symbol: asset symbol
        :param vs_currency: vs_currency symbol to complete market
        :param timeframe: timeframe to fetch candles from 5m, 15m, 30m, 1h, ...
        :param num_candles: total number of candles to fetch
        :param since: since date to fetch candles
        :return: pd.DataFrame
        """
        raise NotImplementedError

    @abstractmethod
    def get_candles_last_one_not_finished(self, symbol, vs_currency, timeframe,
                                         num_candles, since=None):
        """
        Gets the last candles available. It retrieves even the last one (not finshed)
        :param symbol: asset symbol
        :param vs_currency: vs_currency symbol to complete market
        :param timeframe: timeframe to fetch candles from 5m, 15m, 30m, 1h, ...
        :param num_candles: total number of candles to fetch
        :param since: since date to fetch candles
        :return: pd.DataFrame
        """
        raise NotImplementedError

    @abstractmethod
    def get_fee_factor(self, symbol, vs_currency, type='spot'):
        """
        Gets the fee factor for the specified market (symbol + vs_currency)
        :param symbol:
        :param vs_currency:
        :param type:
        :return: dictionary containing maker and taker fees
        """
        raise NotImplementedError

    @abstractmethod
    def _market_from_symbol_and_vs_currency(self, symbol, vs_currency):
        """
        Formats symbol and vs_currency to create the market symbol
        :param symbol: asset to trade
        :param vs_currency: currency to complete the market
        :return: str with the market symbol
        """
        raise NotImplementedError

    @abstractmethod
    def get_free_balance(self, symbol):
        """
        Gets the free (can be used) balance for the specified symbol
        :param symbol: symbol to get balance from
        :return: float
        """
        raise NotImplementedError

    @abstractmethod
    def get_current_price(self, symbol, vs_currency):
        """
        Gets the current price for the given symbol and vs_currency
        :param symbol: asset to trade
        :param vs_currency: currency to complete the market
        :return: float
        """
        raise NotImplementedError


class CcxtExchangeHandler(ExchangeHandler):
    """
    This class is intended to be the parent class of each exchange implemented
    in ccxt until they give support for OCO orders. Then it should not be needed
    to create child classes to manage these types of order.
    """
    def __init__(self, exchange_api: ccxt.Exchange):
        if not isinstance(exchange_api, ccxt.Exchange):
            raise TypeError("Error exchange_api should be of type ccxt.Exchange")

        super().__init__(exchange_api)

    def _amount_to_precision(self, symbol, vs_currency, amount):
        """
        Reduces the decimals in amount in order not to raise exceptions
        :param symbol: asset to trade
        :param vs_currency: vs_currency to complete market
        :param amount: amount to fix precision
        :return: amount with corrected precision
        """
        market = self._market_from_symbol_and_vs_currency(symbol, vs_currency)
        try:
            amount = self._exchange_api.amount_to_precision(symbol=market,
                                                            amount=amount)
        except ccxt.errors.ExchangeError as e:
            self._exchange_api.load_markets()
            amount = self._exchange_api.amount_to_precision(symbol=market,
                                                            amount=amount)

        return float(amount)

    def buy_market_order(self, symbol, vs_currency, amount):
        """
        See description in parent class
        """
        market = self._market_from_symbol_and_vs_currency(symbol, vs_currency)
        # Fix amount to exchange standards not to raise exceptions
        amount = self._amount_to_precision(symbol=symbol,
                                           vs_currency=vs_currency,
                                           amount=amount)

        # Execute buy order
        buy_order = self._exchange_api.create_order(symbol=market,
                                                    type='market',
                                                    side='buy',
                                                    amount=amount)

        order_info = {
            "exchange_id": buy_order['id'],
            "timestamp": buy_order['timestamp'],
            "price": buy_order['price'],
            "amount": buy_order['amount'],
            "cost": buy_order['cost'],
            "fee_in_asset": buy_order['fee']['cost'],
        }

        return order_info

    def _sell_market_order(self, symbol, vs_currency, amount):
        """
        See description in parent class
        """
        market = self._market_from_symbol_and_vs_currency(symbol, vs_currency)
        # Fix amount to exchange standards not to raise exceptions
        amount = self._amount_to_precision(symbol=symbol,
                                           vs_currency=vs_currency,
                                           amount=amount)

        # Execute sell order
        sell_order = self._exchange_api.create_order(symbol=market,
                                                    type='market',
                                                    side='sell',
                                                    amount=amount)

        order_info = {
            "exchange_id": sell_order['id'],
            "timestamp": sell_order['timestamp'],
            "price": sell_order['price'],
            "amount": sell_order['amount'],
            "cost": sell_order['cost'],
            "fee_in_asset": sell_order['fee']['cost'],
        }

        return order_info

    def sell_market_order_diminishing_amount(self, symbol, vs_currency, amount):
        """
        See description in parent class
        """
        min_qty = None

        while amount > 0:
            try:
                sell_order = self._sell_market_order(symbol=symbol,
                                                     vs_currency=vs_currency,
                                                     amount=amount)

                return sell_order
            except ccxt.InsufficientFunds:
                if min_qty is None:
                    min_qty = self.fetch_market(symbol=symbol,
                                                vs_currency=vs_currency)['min_qty']
                amount -= min_qty / 2

    def fetch_market(self, symbol: str, vs_currency):
        """
        See description in parent class
        """
        market_symbol = self._market_from_symbol_and_vs_currency(symbol=symbol,
                                                                 vs_currency=vs_currency)
        try:
            market = self._exchange_api.market(symbol=market_symbol)
        except ccxt.errors.ExchangeError as e:
            self._exchange_api.load_markets()
            market = self._exchange_api.market(symbol=market_symbol)

        return {
            'min_price': float(market['limits']['cost']['min']),
            'max_price': float(market['limits']['price']['max']),
            'min_qty': float(market['limits']['amount']['min']),
            'max_qty': float(market['limits']['amount']['max']),
            'order_types': market['info']['orderTypes'],
            'oco_allowed': market['info']['ocoAllowed'],
            'min_vs_currency': market['limits']['cost']['min'], # Minimum quantity of vs_currency
        }

    def get_candles_for_strategy(self, symbol, vs_currency, timeframe, num_candles,
                                 since=None):
        """
        See description in parent class
        """
        candles_df = self.get_candles_last_one_not_finished(symbol=symbol,
                                                            vs_currency=vs_currency,
                                                            timeframe=timeframe,
                                                            num_candles=num_candles,
                                                            since=since)
        candles_strategy_df = candles_df.iloc[:-1].copy()
        return candles_strategy_df

    def get_candles_last_one_not_finished(self, symbol, vs_currency, timeframe,
                                         num_candles, since=None):
        """
        See description in parent class
        """
        market = self._market_from_symbol_and_vs_currency(symbol, vs_currency)

        # Get candles open, high, low, close, volume information
        candles_list = self._exchange_api.fetch_ohlcv(symbol=market, timeframe=timeframe,
                                                      limit=num_candles, since=since)

        # Take all candles except for the current one (still not closed) and give
        # them some columns names in the data frame
        candles_df = pd.DataFrame(candles_list, columns=['datetime', 'open',
                                                         'high', 'low', 'close',
                                                         'volume'])

        # Convert timestamp from Unix format to YYYY-MM-DD hh:mm:ss.sss format
        candles_df['datetime'] = pd.to_datetime(candles_df['datetime'], unit='ms')
        # Candle color
        candles_df['is_green'] = candles_df['open'] < candles_df['close']
        candles_df['is_red'] = candles_df['open'] > candles_df['close']
        # Low values of the candle bodies
        candles_df['candle_body_low'] = np.where(candles_df['is_green'] == True, candles_df['open'], candles_df['close'])
        candles_df['candle_body_high'] = np.where(candles_df['is_green'] == True, candles_df['close'], candles_df['open'])

        return candles_df

    def get_fee_factor(self, symbol, vs_currency, type='spot'):
        """
        See description in parent class
        """
        market = self._market_from_symbol_and_vs_currency(symbol, vs_currency)
        fee_factors = self._exchange_api.fetch_trading_fee(market)

        return fee_factors

    def _market_from_symbol_and_vs_currency(self, symbol, vs_currency):
        """
        See description in parent class
        """
        return f"{symbol}/{vs_currency}".upper()

    def get_free_balance(self, symbol):
        """
        See description in parent class
        """
        return self._exchange_api.fetch_free_balance()[symbol]

    def get_current_price(self, symbol, vs_currency):
        """
        See description in parent class
        """
        close = self.get_candles_last_one_not_finished(symbol=symbol,
                                                       vs_currency=vs_currency,
                                                       timeframe='1m',
                                                       num_candles=1)['close']

        return list(close)[0]


class BinanceCcxtExchangeHandler(CcxtExchangeHandler):
    pass


if __name__ == '__main__':
    import config
    bin_eh = BinanceCcxtExchangeHandler(ccxt.binance(
        {
            'apiKey': config.BINANCE_API_KEY,
            'secret': config.BINANCE_SECRET_KEY,
            'enableLimitRate': True,
        }
    ))
    borrar = bin_eh.fetch_market('ADA', 'EUR')
    pass


