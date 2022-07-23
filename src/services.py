from datetime import datetime

import ccxt

import config
import exchangehandler as ex_han
import marketfinder as mar_fin
import model
import repository as rp
import strategy as st


eh = ex_han.BinanceCcxtExchangeHandler(
    ccxt.binance(
        {
            'apiKey': config.BINANCE_API_KEY,
            'secret': config.BINANCE_SECRET_KEY,
            'enableLimitRate': True,
        }
    )
)

mf = mar_fin.CoinGeckoMarketFinder()


def position_can_be_profitable(exchange_handler: ex_han.ExchangeHandler,
                               strategy_output: st.StrategyOutput, symbol,
                               vs_currency, amount):
    """
    Not tested method
    Checks whether position can be profitable or not taking fees into accouunt
    :param exchange_handler: ExchangeHandler to fetch fees
    :param strategy_output: Strategy output to test
    :param symbol: Left-hand side of market symbol
    :param vs_currency: Right-hand side of market symbol
    :param amount: amount of symbol
    :return: True or False
    """

    if strategy_output.can_enter:
        # TODO implement other type of fee if other order types different from market orders are implemented
        fee_factor = exchange_handler.get_fee_factor(symbol=symbol,
                                                     vs_currency=vs_currency)['taker']

        # Fees are computed in the obtained asset
        entry_fee = fee_factor * amount
        # Amount actually bought
        entry_amount = amount - entry_fee
        # Actual vs_currency entry
        vs_currency_entry = amount * strategy_output.entry_price

        if strategy_output.position_type == st.PositionType.LONG:
            # Total vs_currency on exit not considering fees
            vs_currency_win_no_fees = entry_amount * strategy_output.take_profit
            vs_currency_lose_no_fees = entry_amount * strategy_output.stop_loss

            # Possible exit fees in vs_currency
            exit_fee_win = fee_factor * vs_currency_win_no_fees
            exit_fee_lose = fee_factor * vs_currency_lose_no_fees

            # Expected total vs_currency on exit
            vs_currency_win = vs_currency_win_no_fees - exit_fee_win
            vs_currency_lose = vs_currency_lose_no_fees - exit_fee_lose

            # Compare with initial state
            win_margin = abs(vs_currency_win - vs_currency_entry)
            lose_margin = abs(vs_currency_lose - vs_currency_entry)

            return win_margin / lose_margin > 1

        elif strategy_output.position_type == st.PositionType.SHORT:
            # TODO implement
            pass
        else:
            raise ValueError

    return False


def manage_risk_on_entry(vs_currency_on_entry, strategy_output):
    """
    Applies risk management to the available money. If the initial risk is
    greater than config.MAX_PERCENTAGE_TO_RISK, then it calculates the money that
    must be used to ensure that, at maximum, config.max_percentage_to_use is
    fulfilled.
    :param vs_currency_on_entry: quantity of vs_currency to fix
    :param strategy_output: Strategy output
    :return: amount of vs_currency that is going to be used to buy.
    """
    entry_price = strategy_output.entry_price
    stop_loss = strategy_output.stop_loss

    risked_percentage = 100 * abs(entry_price - stop_loss) / entry_price

    if risked_percentage <= config.MAX_PERCENTAGE_TO_RISK:
        return vs_currency_on_entry
    else:
        return vs_currency_on_entry * config.MAX_PERCENTAGE_TO_RISK / risked_percentage


def close_opened_position(symbol, vs_currency):
    """
    NOT TESTED METHOD
    Checks for opened position for the pair symbol-vs_currency. If there is an
    opened position, then retrieves current price and act in function of take
    profit or stop loss
    :param symbol: left-hand side of market info
    :param vs_currency: right-hand side of market info
    :return:
    """
    repo = rp.provide_sqlalchemy_repository(real_db=True)

    opened_trade = repo.get_opened_positions(symbol=symbol,
                                             vs_currency=vs_currency)[0]

    if opened_trade:
        take_profit = opened_trade.modified_take_profit if opened_trade.modified_take_profit is not None else opened_trade.take_profit
        stop_loss = opened_trade.modified_stop_loss if opened_trade.modified_stop_loss is not None else opened_trade.stop_loss

        # current_price = eh.get_current_price(symbol=symbol,
        #                                      vs_currency=vs_currency)

        current_low = list(eh.get_candles_last_one_not_finished(symbol=symbol,
                                                           vs_currency=vs_currency,
                                                           timeframe='1m',
                                                           num_candles=1)['low'])[0]

        current_high = list(eh.get_candles_last_one_not_finished(symbol=symbol,
                                                           vs_currency=vs_currency,
                                                           timeframe='1m',
                                                           num_candles=1)['high'])[0]

        if current_high >= take_profit:
            # TODO idea: no vender, sino aumentar take profit y luego ir comprobando
            exit_price = take_profit
        elif current_low <= stop_loss:
            exit_price = stop_loss
        else:
            return

        if not opened_trade.is_real:
            fee_factor = eh.get_fee_factor(symbol=symbol,
                                           vs_currency=vs_currency)['taker']
            # Estimation of crypto quantity on exit. Susceptible of being changed
            crypto_quantity_exit = opened_trade.crypto_quantity_entry * (1- fee_factor)
            exit_date = model.format_date_for_database(datetime.now())

            vs_currency_exit = exit_price * crypto_quantity_exit
            exit_fee_vs_currency = vs_currency_exit * fee_factor
            vs_currency_result_no_fees = vs_currency_exit - opened_trade.vs_currency_entry

            result = vs_currency_result_no_fees - opened_trade.entry_fee_vs_currency - exit_fee_vs_currency

            status = model.TradeStatus.WON if result > 0 else model.TradeStatus.LOST

        else:
            pass

        model.complete_trade_with_market_sell_info(trade=opened_trade,
                                                   vs_currency_result_no_fees=vs_currency_result_no_fees,
                                                   crypto_quantity_exit=crypto_quantity_exit,
                                                   exit_fee_vs_currency=exit_fee_vs_currency,
                                                   exit_date=exit_date,
                                                   status=status)
        repo.commit()


if __name__ == "__main__":
    from time import sleep
    symbol = 'BTC'
    vs_currency = 'EUR'
    amount = 1

    repo = rp.provide_sqlalchemy_repository(real_db=True)
    op = repo.get_opened_positions(symbol, vs_currency)

    while repo.get_opened_positions(symbol, vs_currency):
        print("fetching")
        close_opened_position(symbol, vs_currency)
        sleep(2)

    print("closed")

    # trade = model.create_initial_trade(symbol="BTC", vs_currency_symbol="EUR",
    #                                    timeframe='5m',
    #                                    stop_loss=22555, entry_price=22626, take_profit=22656,
    #                                    status=model.TradeStatus.OPENED, vs_currency_entry=20,
    #                                    crypto_quantity_entry=1.0, entry_fee_vs_currency=.2,
    #                                    position='L',
    #                                    entry_date='2022-07-21 15:19:15',
    #                                    entry_order_exchange_id='2022-07-21 15:19:15',
    #                                    percentage_change_1d_on_entry='2',
    #                                    percentage_change_7d_on_entry='2',
    #                                    percentage_change_1h_on_entry='2',
    #                                    strategy_name='test',
    #                                    is_real=False)
    # repo.add_trade(trade)
    # repo.commit()
