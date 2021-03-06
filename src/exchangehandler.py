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
    def sell_market_order(self, symbol, vs_currency, amount):
        """
        Sells in the market symbol vs_currency the specified amount of symbol
        :param symbol: symbol to sell
        :param vs_currency: vs_currency to complete the market
        :param amount: amount of symbol to sell
        :return: filled order
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

        return amount

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

    def sell_market_order(self, symbol, vs_currency, amount):
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

    def get_candles_for_strategy(self, symbol, vs_currency, timeframe, num_candles,
                                 since=None):
        """
        See description in parent class
        """
        market = self._market_from_symbol_and_vs_currency(symbol, vs_currency)

        # Get candles open, high, low, close, volume information
        candles_list = ccxt.binance().fetch_ohlcv(symbol=market, timeframe=timeframe,
                                             limit=num_candles, since=since)

        # Take all candles except for the current one (still not closed) and give
        # them some columns names in the data frame
        candles_df = pd.DataFrame(candles_list[:-1],
                          columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])

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
    bin_eh.get_fee_factor('BTC', 'EUR')


