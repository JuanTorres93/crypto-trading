from collections import OrderedDict
from datetime import datetime, timedelta
import os.path
import time

import ccxt
import schedule

import commonutils as cu
import config
import exchangehandler as ex_han
import externalnotifier
import filesystemutils as fs
import marketfinder as mar_fin
import model
import repository as rp
import strategy as st


eh = ex_han.CcxtExchangeHandler(
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
        cu.log("Shuting down bot.")
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
        cu.log(f"{model.format_date_for_database(datetime.now())} closed position for {symbol}")
        update_max_vs_currency_to_use()


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
            cu.log(f"Entered simulated position for {symbol}{vs_currency}")
        else:
            # Check if bought quantity would be enough
            market_info = eh.fetch_market(symbol=symbol, vs_currency=vs_currency)
            min_vs_currency_to_enter_market = market_info['min_vs_currency']

            if vs_currency_entry > min_vs_currency_to_enter_market:
                # Perform the strategy with actual money
                cu.log(f"Trying to buy: {crypto_quantity_entry} {symbol} with {vs_currency_entry} {vs_currency}")
                buy_order = eh.buy_market_order(symbol=symbol,
                                                vs_currency=vs_currency,
                                                amount=crypto_quantity_entry)

                if buy_order is None:
                    # Log that order could not be placed and go on searching for trades
                    cu.log("Couldn't perform the buy order")
                    return


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
                cu.log(f"Entered real position for {symbol}{vs_currency}")
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


def set_stop_loss_to_break_even_in_opened_position(symbol, vs_currency):
    """
    NOT TESTED METHOD
    :param symbol:
    :param vs_currency:
    :return:
    """
    repo = rp.provide_sqlalchemy_repository(real_db=True)

    opened_trade = repo.get_opened_positions(symbol=symbol,
                                             vs_currency=vs_currency)

    if opened_trade:
        opened_trade = opened_trade[0]
        repo.modify_stop_loss(id=opened_trade.id,
                              new_stop_loss=opened_trade.entry_price)


def set_take_profit_to_percentage_in_opened_position(symbol, vs_currency, percentage):
    """
    NOT TESTED METHOD
    :param symbol:
    :param vs_currency:
    :param percentage: percentage to which reduce the range of take profit. MUST BE between 0-1
    :return:
    """
    repo = rp.provide_sqlalchemy_repository(real_db=True)

    opened_trade = repo.get_opened_positions(symbol=symbol,
                                             vs_currency=vs_currency)

    if opened_trade:
        opened_trade = opened_trade[0]
        # Retrieve info from database
        take_profit = opened_trade.take_profit
        entry_price = opened_trade.entry_price

        # Compute current profit range
        take_profit_range = take_profit - entry_price
        # Reduce profit range by percentage
        modified_take_profit_range = percentage * take_profit_range

        # Add new profit range to entry price to complete the new take profit
        new_take_profit = entry_price + modified_take_profit_range

        # Store new take profit in database
        repo.modify_take_profit(id=opened_trade.id,
                                new_take_profit=new_take_profit)


def check_every_opened_trade_for_break_even():
    """
    If the current price has surpassed the half of the take profit territory, then
    modify the stop loss to break even
    :return:
    """
    repo = rp.provide_sqlalchemy_repository(real_db=True)

    opened_positions = repo.get_opened_positions()

    for op in opened_positions:
        current_price = eh.get_current_price(symbol=op.symbol,
                                             vs_currency=op.vs_currency_symbol)
        entry_price = op.entry_price
        take_profit = op.take_profit

        mid_take_profit = entry_price + (take_profit - entry_price) / 2

        if current_price >= mid_take_profit:
            set_stop_loss_to_break_even_in_opened_position(symbol=op.symbol,
                                                           vs_currency=op.vs_currency_symbol)


def check_every_opened_trade_for_reduction_in_take_profit(reduce_take_profit_to_percentage=.1):
    """
    If the current price has gone below the half of the stop loss territory, then
    modify the take profit to a percentage
    :param reduce_take_profit_to_percentage: final percentage to reduce take profit. E.g. if this variable is .1 then
    the take profit will be reduced to a 10% of its initial value, i.e., it will be reduced a 90%
    :return:
    """
    repo = rp.provide_sqlalchemy_repository(real_db=True)

    opened_positions = repo.get_opened_positions()

    for op in opened_positions:
        current_price = eh.get_current_price(symbol=op.symbol,
                                             vs_currency=op.vs_currency_symbol)
        entry_price = op.entry_price
        stop_loss = op.stop_loss

        mid_stop_loss = entry_price - (entry_price - stop_loss) / 2

        if current_price <= mid_stop_loss:
            set_take_profit_to_percentage_in_opened_position(symbol=op.symbol,
                                                             vs_currency=op.vs_currency_symbol,
                                                             percentage=reduce_take_profit_to_percentage)


def compute_strategy_and_try_to_enter(symbol, vs_currency, strategy,
                                      strategy_entry_timeframe, is_real):
    cu.log(f"Scanning {symbol}{vs_currency}")
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
        cu.log("Already opened position")


def notify_results_for_current_day():
    repo = rp.provide_sqlalchemy_repository(True)
    today = datetime.today()
    results = repo.get_results_for_day_month_year(today.day,
                                                  today.month,
                                                  today.year)
    externalnotifier.externally_notify(f"=========={today.day}/{today.month}/{today.year}==========")
    for r in results:
        fiat_amount = None
        if r[2] is not None:
            fiat_amount = f"{r[2]:.2f} €"

        msg = f"{r[0]} | {r[1]} posiciones | {fiat_amount}"
        externalnotifier.externally_notify(msg)


def notify_results_for_previous_day():
    repo = rp.provide_sqlalchemy_repository(True)
    today = datetime.today()
    yesterday = today - timedelta(days=1)
    results = repo.get_results_for_day_month_year(yesterday.day,
                                                  yesterday.month,
                                                  yesterday.year)
    externalnotifier.externally_notify(f"=========={yesterday.day}/{yesterday.month}/{yesterday.year}==========")
    for r in results:
        fiat_amount = None
        if r[2] is not None:
            fiat_amount = f"{r[2]:.2f} €"

        msg = f"{r[0]} | {r[1]} posiciones | {fiat_amount}"
        externalnotifier.externally_notify(msg)


def notify_results_for_previous_month():
    repo = rp.provide_sqlalchemy_repository(True)
    today = datetime.today()
    # This condition exists because there is no schedule every month
    if today.day == 1:
        first_day_current_month = today.replace(day=1)
        last_day_previous_month = first_day_current_month - timedelta(days=1)
        results = repo.get_results_for_day_month_year("%",
                                                      last_day_previous_month.month,
                                                      last_day_previous_month.year)
        externalnotifier.externally_notify(f"=========={last_day_previous_month.month}/{last_day_previous_month.year}==========")
        for r in results:
            fiat_amount = None
            if r[2] is not None:
                fiat_amount = f"{r[2]:.2f} €"

            msg = f"{r[0]} | {r[1]} posiciones | {fiat_amount}"
            externalnotifier.externally_notify(msg)


def notify_results_for_current_month():
    repo = rp.provide_sqlalchemy_repository(True)

    today = datetime.today()
    results = repo.get_results_for_day_month_year("%",
                                                  today.month,
                                                  today.year)

    externalnotifier.externally_notify(f"========== Notificación semanal del estado actual del mes ==========")
    for r in results:
        fiat_amount = None
        if r[2] is not None:
            fiat_amount = f"{r[2]:.2f} €"

        msg = f"{r[0]} | {r[1]} posiciones | {fiat_amount}"
        externalnotifier.externally_notify(msg)


def initialize_markets():
    # Init markets
    markets = []
    cu.log("Initializing markets")
    while len(markets) == 0:
        markets = mf.get_pairs_for_exchange_vs_currency(exchange_id='binance',
                                                        vs_currency='EUR',
                                                        force=True)

        markets = list(map(
            lambda x: (x['base'], x['target']),
            markets
        ))
        if len(markets) == 0:
            cu.log(f"{datetime.now()}: Could not initialize. Trying again in 70s.")
            time.sleep(70)

    markets_not_duplicated = OrderedDict.fromkeys(markets)
    markets = list(markets_not_duplicated)
    cu.log(f"markets: {markets}")
    externalnotifier.externally_notify("Mercados inicializados")

    return markets


def update_max_vs_currency_to_use():
    """
    Modifies config.MAX_VS_CURRENCY_TO_USE in order to always be able to have
    7 trades at a time. The minimum value will always be 13 due to the minimum
    required by Binance of 10 euros.
    :return:
    """
    total_eur = eh.get_total_amount_in_symbol(symbol='EUR')
    new_max_vs_currency_to_use = total_eur / 7.2 # Can be 7 trades simultaneously. Decimals to take fees into account

    new_max_vs_currency_to_use = new_max_vs_currency_to_use if new_max_vs_currency_to_use > 13 else 13 # Minimun of 13 euros due to binance minimum of 10

    config.MAX_VS_CURRENCY_TO_USE = new_max_vs_currency_to_use


def run_bot(simulate):
    cu.initialize_log_file()
    externalnotifier.externally_notify("Bot iniciado")
    cu.log("Trying to close opened positions")
    check_every_opened_trade_for_break_even()
    check_every_opened_trade_for_reduction_in_take_profit()
    close_all_opened_positions()
    shut_down_bot()

    markets = initialize_markets()

    # CHANGE STRATEGY HERE
    strat = st.SupportAndResistanceHigherTimeframeBullishDivergence()

    cu.log("Starting main loop")
    while True:
        cu.log("========== STARTING NEW ITERATION ========== ")
        for symbol, vs_currency in markets:
            compute_strategy_and_try_to_enter(symbol=symbol,
                                              vs_currency=vs_currency,
                                              strategy=strat,
                                              strategy_entry_timeframe="5m",
                                              is_real=not simulate)

            check_every_opened_trade_for_break_even()
            check_every_opened_trade_for_reduction_in_take_profit()
            close_all_opened_positions()
            shut_down_bot()
            schedule.run_pending()
            time.sleep(2)


if __name__ == "__main__":
    # Daily notification of current day status
    schedule.every().day.at("12:00").do(notify_results_for_current_day)
    schedule.every().day.at("16:00").do(notify_results_for_current_day)
    schedule.every().day.at("20:00").do(notify_results_for_current_day)

    # Remove log file every day in order not to saturate memory
    schedule.every().day.at("00:00").do(cu.initialize_log_file)

    # Notification of previous day results
    schedule.every().day.at("08:00").do(notify_results_for_previous_day)
    # Notification of previous month results
    schedule.every().day.at("09:00").do(notify_results_for_previous_month)

    # Weekly notifications oƒ current month results
    schedule.every().monday.at("08:30").do(notify_results_for_current_month)

    schedule.every().week.do(initialize_markets)

    while True:
        try:
            run_bot(simulate=False)
        except (ccxt.errors.RequestTimeout, ccxt.errors.NetworkError):
            time_to_wait_in_seconds = 600
            msg = f"ccxt.errors.RequestTimeout raised. Sleeping for {time_to_wait_in_seconds} seconds and trying again"
            externalnotifier.externally_notify(msg)
            cu.log(msg)
            time.sleep(time_to_wait_in_seconds)
        except Exception:
            cu.log_traceback()
            externalnotifier.externally_notify("El bot ha parado debido a una excepción")
            raise Exception("Bot stopped")

