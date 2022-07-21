import ccxt

import config
import exchangehandler as eh
import marketfinder as mf


class Bot:
    def __init__(self):
        self._exchange_id = 'binance'
        self._eh = eh.BinanceCcxtExchangeHandler(ccxt.binance(
            {
                'apiKey': config.BINANCE_API_KEY,
                'secret': config.BINANCE_SECRET_KEY,
                'enableLimitRate': True,
            }))

        self._mf = mf.CoinGeckoMarketFinder()

    def provide_markets_to_trade(self, vs_currency):
        return self._mf.provide_markets_to_trade(exchange_id=self._exchange_id,
                                                 vs_currency=vs_currency)

    def get_pairs_for_exchange_vs_currency(self, vs_currency,
                                           force=False):
        # TODO schedule every week, month or so
        self._mf.get_pairs_for_exchange_vs_currency(exchange_id=self._exchange_id,
                                                    vs_currency=vs_currency,
                                                    force=force)

if __name__ == "__main__":
    bot = Bot()
    from datetime import datetime

    print(datetime.now())
    borrar = bot.provide_markets_to_trade('EUR')
    print(datetime.now())
    borrar = bot.provide_markets_to_trade('EUR')
    print(datetime.now())
