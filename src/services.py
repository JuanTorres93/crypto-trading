import os.path
from datetime import datetime
import time

import ccxt

import config
import exchangehandler as ex_han
import filesystemutils as fs
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


def shut_down_bot():
    home = fs.home_directory(True)
    path_to_file = os.path.join(home, config.FILE_NAME_TO_CLOSE_BOT)
    if fs.path_exists(path_to_file):
        print("Shuting down bot.")
        exit()


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


def manage_risk_on_entry(vs_currency_on_entry, strategy_output,
                         max_vs_currency_to_use):
    """
    Applies risk management to the available money. If the initial risk is
    greater than config.MAX_PERCENTAGE_TO_RISK, then it calculates the money that
    must be used to ensure that, at maximum, config.max_percentage_to_use is
    fulfilled.
    :param max_vs_currency_to_use:
    :param vs_currency_on_entry: quantity of vs_currency to fix
    :param strategy_output: Strategy output
    :return: amount of vs_currency that is going to be used to buy.
    """
    entry_price = strategy_output.entry_price
    stop_loss = strategy_output.stop_loss

    risked_percentage = 100 * abs(entry_price - stop_loss) / entry_price

    # Manage risk
    if risked_percentage <= config.MAX_PERCENTAGE_TO_RISK:
        current_vs_currency_entry = vs_currency_on_entry
    else:
        current_vs_currency_entry = vs_currency_on_entry * config.MAX_PERCENTAGE_TO_RISK / risked_percentage

    # Adjust managed risk to maximum desired value
    if current_vs_currency_entry <= max_vs_currency_to_use:
        return current_vs_currency_entry
    else:
        return max_vs_currency_to_use


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
                                             vs_currency=vs_currency)

    if opened_trade:
        opened_trade = opened_trade[0]

        take_profit = opened_trade.modified_take_profit if opened_trade.modified_take_profit is not None else opened_trade.take_profit
        stop_loss = opened_trade.modified_stop_loss if opened_trade.modified_stop_loss is not None else opened_trade.stop_loss

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

        exit_date = model.format_date_for_database(datetime.now())

        if not opened_trade.is_real:
            # Simulate strategy in real time

            fee_factor = eh.get_fee_factor(symbol=symbol,
                                           vs_currency=vs_currency)['taker']
            # Estimation of crypto quantity on exit. Susceptible of being changed
            crypto_quantity_exit = opened_trade.crypto_quantity_entry * (1- fee_factor)

            vs_currency_exit = exit_price * crypto_quantity_exit
            exit_fee_vs_currency = vs_currency_exit * fee_factor
            vs_currency_result_no_fees = vs_currency_exit - opened_trade.vs_currency_entry
            result = vs_currency_result_no_fees - opened_trade.entry_fee_vs_currency - exit_fee_vs_currency
            status = model.TradeStatus.WON if result > 0 else model.TradeStatus.LOST

        else:
            # Perform the strategy with actual money
            amount = opened_trade.crypto_quantity_entry
            sell_order = eh.sell_market_order_diminishing_amount(symbol=symbol,
                                                                 vs_currency=vs_currency,
                                                                 amount=amount)
            crypto_quantity_exit = sell_order['amount']
            exit_price = sell_order['price']
            exit_fee_vs_currency = sell_order['fee_in_asset']
            vs_currency_exit = sell_order['cost']

            # In the real trade commissions are already considered in return exchange information
            vs_currency_result_no_fees = vs_currency_exit - opened_trade.vs_currency_entry + opened_trade.entry_fee_vs_currency + exit_fee_vs_currency
            result = vs_currency_result_no_fees - opened_trade.entry_fee_vs_currency - exit_fee_vs_currency
            status = model.TradeStatus.WON if result > 0 else model.TradeStatus.LOST

        model.complete_trade_with_market_sell_info(trade=opened_trade,
                                                   vs_currency_result_no_fees=vs_currency_result_no_fees,
                                                   crypto_quantity_exit=crypto_quantity_exit,
                                                   exit_fee_vs_currency=exit_fee_vs_currency,
                                                   exit_date=exit_date,
                                                   status=status)
        repo.commit()
        print(f"{model.format_date_for_database(datetime.now())} closed position for {symbol}")
        # raise Exception(f"BORRAR ESTE RAISE DEL CÓDIGO. SÓLO ESTÁ PARA QUE NO SE ENTRE EN NUEVAS POSICIONES REALES")


def enter_position(symbol, vs_currency, timeframe, stop_loss, entry_price,
                   take_profit, vs_currency_entry, crypto_quantity_entry,
                   entry_fee_vs_currency, position, entry_order_exchange_id,
                   percentage_change_1h_on_entry, percentage_change_1d_on_entry,
                   percentage_change_7d_on_entry, strategy_name, is_real):
    """
    NOT TESTED METHOD
    Checks for opened position for the pair symbol-vs_currency. If there is not an
    opened position, then enters.
    :param symbol: left-hand side of market info
    :param vs_currency: right-hand side of market info
    :return:
    """
    repo = rp.provide_sqlalchemy_repository(real_db=True)

    opened_trade = repo.get_opened_positions(symbol=symbol,
                                             vs_currency=vs_currency)

    if not opened_trade:
        if not is_real:
            # Simulate strategy in real time
            trade = model.create_initial_trade(symbol=symbol,
                                               vs_currency_symbol=vs_currency,
                                               timeframe=timeframe,
                                               stop_loss=stop_loss,
                                               entry_price=entry_price,
                                               take_profit=take_profit,
                                               vs_currency_entry=vs_currency_entry,
                                               crypto_quantity_entry=crypto_quantity_entry,
                                               entry_fee_vs_currency=entry_fee_vs_currency,
                                               position=position,
                                               entry_order_exchange_id=entry_order_exchange_id,
                                               percentage_change_1h_on_entry=percentage_change_1h_on_entry,
                                               percentage_change_1d_on_entry=percentage_change_1d_on_entry,
                                               percentage_change_7d_on_entry=percentage_change_7d_on_entry,
                                               strategy_name=strategy_name,
                                               is_real=is_real,
                                               entry_date=model.format_date_for_database(
                                                   datetime.now()))
            print(f"Entered simulated position for {symbol}{vs_currency}")
        else:
            # Check if bought quantity would be enough
            market_info = eh.fetch_market(symbol=symbol, vs_currency=vs_currency)
            min_vs_currency_to_enter_market = market_info['min_vs_currency']

            if vs_currency_entry > min_vs_currency_to_enter_market:
                # Perform the strategy with actual money
                print(f"Trying to buy: {crypto_quantity_entry} {symbol}", end=" ")
                print(f"with {vs_currency_entry} {vs_currency}")
                buy_order = eh.buy_market_order(symbol=symbol,
                                                vs_currency=vs_currency,
                                                amount=crypto_quantity_entry)

                vs_currency_entry = buy_order['cost']
                crypto_quantity_entry = buy_order['amount']
                entry_price = buy_order['price']
                entry_fee_vs_currency = entry_price * buy_order['fee_in_asset']
                entry_order_exchange_id = 'exchange_id'

                trade = model.create_initial_trade(symbol=symbol,
                                                   vs_currency_symbol=vs_currency,
                                                   timeframe=timeframe,
                                                   stop_loss=stop_loss,
                                                   entry_price=entry_price,
                                                   take_profit=take_profit,
                                                   vs_currency_entry=vs_currency_entry,
                                                   crypto_quantity_entry=crypto_quantity_entry,
                                                   entry_fee_vs_currency=entry_fee_vs_currency,
                                                   position=position,
                                                   entry_order_exchange_id=entry_order_exchange_id,
                                                   percentage_change_1h_on_entry=percentage_change_1h_on_entry,
                                                   percentage_change_1d_on_entry=percentage_change_1d_on_entry,
                                                   percentage_change_7d_on_entry=percentage_change_7d_on_entry,
                                                   strategy_name=strategy_name,
                                                   is_real=is_real,
                                                   entry_date=model.format_date_for_database(
                                                       datetime.now()))
                print(f"Entered real position for {symbol}{vs_currency}")
            else:
                return

        repo.add_trade(trade)
        repo.commit()


def close_all_opened_positions():
    repo = rp.provide_sqlalchemy_repository(real_db=True)

    opened_positions = repo.get_opened_positions()

    for op in opened_positions:
        close_opened_position(symbol=op.symbol,
                              vs_currency=op.vs_currency_symbol)


def compute_strategy_and_try_to_enter(symbol, vs_currency, strategy,
                                      strategy_entry_timeframe, is_real):
    print(f"Scanning {symbol}{vs_currency}")
    close_opened_position(symbol=symbol, vs_currency=vs_currency)
    repo = rp.provide_sqlalchemy_repository(real_db=True)

    if not repo.get_opened_positions(symbol=symbol, vs_currency=vs_currency):
        # # COMPUTE HERE DF FOR STRATEGIES
        df_lt = eh.get_candles_for_strategy(symbol=symbol,
                                         vs_currency=vs_currency,
                                         timeframe=strategy_entry_timeframe,
                                         num_candles=2000)

        df_ht = eh.get_candles_for_strategy(symbol=symbol,
                                            vs_currency=vs_currency,
                                            timeframe='1h',
                                            num_candles=2000)

        current_price = eh.get_current_price(symbol=symbol,
                                             vs_currency=vs_currency)

        # INCLUDE HERE THE DFs FOR STRATEGY
        st_out = strategy.perform_strategy(entry_price=current_price,
                                           lt_df=df_lt,
                                           ht_df=df_ht)


        free_vs_currency = eh.get_free_balance(symbol=vs_currency)
        vs_currency_on_entry = manage_risk_on_entry(free_vs_currency, st_out,
                                                    config.MAX_VS_CURRENCY_TO_USE)

        amount = vs_currency_on_entry / current_price
        amount = eh._amount_to_precision(symbol=symbol, vs_currency=vs_currency,
                                         amount=amount)

        vs_currency_on_entry = amount * current_price

        fee_factor = eh.get_fee_factor(symbol=symbol, vs_currency=vs_currency)['taker']
        fee = amount * fee_factor
        amount = amount * (1 - fee_factor)

        if position_can_be_profitable(exchange_handler=eh, strategy_output=st_out,
                                      symbol=symbol, vs_currency=vs_currency,
                                      amount=amount):
            if not is_real:
                enter_position(symbol=symbol, vs_currency=vs_currency,
                               timeframe=strategy_entry_timeframe, stop_loss=st_out.stop_loss,
                               entry_price=current_price, take_profit=st_out.take_profit,
                               vs_currency_entry=vs_currency_on_entry,
                               crypto_quantity_entry=amount,
                               entry_fee_vs_currency=fee*current_price,
                               position='L', entry_order_exchange_id='SIMULATED',
                               percentage_change_1h_on_entry="NO",
                               percentage_change_1d_on_entry="NO",
                               percentage_change_7d_on_entry="NO",
                               strategy_name=strategy.strategy_name(),
                               is_real=is_real)
            else:
                enter_position(symbol=symbol, vs_currency=vs_currency,
                               timeframe=strategy_entry_timeframe, stop_loss=st_out.stop_loss,
                               entry_price=current_price, take_profit=st_out.take_profit,
                               vs_currency_entry=vs_currency_on_entry,
                               crypto_quantity_entry=amount,
                               entry_fee_vs_currency=fee*current_price,
                               position='L', entry_order_exchange_id='NOT SIMULATED',
                               percentage_change_1h_on_entry="NO",
                               percentage_change_1d_on_entry="NO",
                               percentage_change_7d_on_entry="NO",
                               strategy_name=strategy.strategy_name(),
                               is_real=is_real)
    else:
        print("Already opened position")


def run_bot(simulate):
    print("Trying to close opened positions")
    close_all_opened_positions()
    shut_down_bot()

    # Init markets
    markets = []
    print("Initializing markets")
    while len(markets) == 0:
        markets = mf.get_pairs_for_exchange_vs_currency(exchange_id='binance',
                                                        vs_currency='EUR',
                                                        force=True)

        markets = list(map(
            lambda x: (x['base'], x['target']),
            markets
        ))
        print(f"{datetime.now()}: Could not initialize. Trying again in 70s.")
        time.sleep(70)

    print(f"markets: {markets}")

    # CHANGE STRATEGY HERE
    strat = st.SupportAndResistanceHigherTimeframeBullishDivergence()

    print("Starting main loop")
    while True:
        print("========== STARTING NEW ITERATION ========== ")
        for symbol, vs_currency in markets:
            compute_strategy_and_try_to_enter(symbol=symbol,
                                              vs_currency=vs_currency,
                                              strategy=strat,
                                              strategy_entry_timeframe="1m",
                                              is_real=not simulate)

            close_all_opened_positions()
            shut_down_bot()
            time.sleep(2)


if __name__ == "__main__":
    run_bot(simulate=True)

    # import indicator as ind
    # import matplotlib.pyplot as plt

    # Init markets
    # markets = []
    # print("Initializing markets")
    # while len(markets) == 0:
    #     markets = mf.get_pairs_for_exchange_vs_currency(exchange_id='binance',
    #                                                     vs_currency='EUR',
    #                                                     force=True)
    #
    #     markets = list(map(
    #         lambda x: (x['base'], x['target']),
    #         markets
    #     ))
    #     print("Could not initialize. Trying again in 10s.")
    #     time.sleep(10)

    # print(f"markets: {markets}")
    #
    # strat = st.SupportAndResistanceHigherTimeframe()
    #
    # for symbol, vs in markets:
    #     df_ht = eh.get_candles_for_strategy(
    #         symbol=symbol, vs_currency="EUR", timeframe="1h", num_candles=1000
    #     )
    #
    #     df_lt = eh.get_candles_for_strategy(
    #         symbol=symbol, vs_currency="EUR", timeframe="1m", num_candles=1000
    #     )
    #
    #     f, a = plt.subplots()
    #     df_lt['close'].plot(ax=a)
    #
    #     sup_and_res = ind.support_and_resistance(df_ht)
    #     a.hlines(sup_and_res['base_line'], 0, 1000, 'r', '--', linewidth=1)
    #     a.hlines(sup_and_res['upper_line'], 0, 1000, 'r', '-', linewidth=2)
    #     a.hlines(sup_and_res['lower_line'], 0, 1000, 'r', '-', linewidth=2)
    #
    #     out = strat.perform_strategy(list(df_lt['close'])[-1], ht_df=df_ht,
    #                                  lt_df=df_lt)
    #
    #     plt.show()

