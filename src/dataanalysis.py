from datetime import datetime, timedelta

import ccxt
import mplfinance
import pandas as pd

import config
import exchangehandler as ex_han
from repository import provide_sqlalchemy_repository


eh = ex_han.CcxtExchangeHandler(
    ccxt.binance(
        {
            'apiKey': config.BINANCE_API_KEY,
            'secret': config.BINANCE_SECRET_KEY,
            'enableLimitRate': True,
        }
    )
)


def plot_finished_trade(trade_id_db: int, candles_before=10, candles_after=20):
    repo = provide_sqlalchemy_repository(real_db=True)
    trade = repo.get_trade(trade_id_db)

    symbol = trade.symbol
    vs_currency_symbol = trade.vs_currency_symbol
    timeframe = trade.timeframe
    take_profit = trade.take_profit
    stop_loss = trade.stop_loss
    entry_price = trade.entry_price
    # TODO ajustar entrada para que sea múltiplo de timeframe
    date_format = '%d/%m/%Y %H:%M:%S'
    entry_date = datetime.strptime(f"{trade.entry_date[:-3]}:00", date_format)
    exit_date = datetime.strptime(f"{trade.exit_date[:-3]}:00", date_format)

    # TODO CAMBIAR EL 5 SI SE USA OTRO TIMEFRAME
    timeframe_minutes_multiplier = 1
    candles_in_trade = int((exit_date - entry_date).total_seconds() / (60 * timeframe_minutes_multiplier))

    since = entry_date - timedelta(
        minutes=candles_before*timeframe_minutes_multiplier
    )
    since = int(datetime.timestamp(since)) * 1000

    n_candles = candles_before + candles_in_trade + candles_after

    candles = eh.get_candles_last_one_not_finished(
        symbol=symbol,
        vs_currency=vs_currency_symbol,
        timeframe=timeframe,
        num_candles=n_candles,
        since=since
    )

    df = pd.DataFrame(candles,
                      columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])

    df.index = pd.DatetimeIndex(
        pd.to_datetime(df['datetime'], unit='ms')
    )

    index_list = list(df.index)
    # TODO COGER BIEN ESTOS VALORES
    entry_x = index_list[candles_before]
    exit_x = index_list[candles_before + candles_in_trade]

    mplfinance.plot(df, type='candle', style='charles',
                    title=f"{trade_id_db} - {symbol} - {trade.status.upper()}",
                    hlines=dict(hlines=[take_profit, entry_price, stop_loss],
                                colors=['g', 'b', 'r']),
                    vlines=dict(vlines=[entry_x, exit_x],
                                colors=['purple', 'purple'],
                                linestyle=['--', '--'],
                                linewidths=[2, 1]),
                    warn_too_much_data=10000
                        )
