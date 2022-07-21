import ccxt

import config
import exchangehandler as ex_han
import marketfinder as mar_fin
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


if __name__ == "__main__":
    symbol = 'ETH'
    vs_currency = 'EUR'
    amount = 1

    candles = eh.get_candles_for_strategy(symbol=symbol,
                                              vs_currency=vs_currency,
                                              timeframe='1h',
                                              num_candles=20)

    current_price = eh.get_current_price(symbol=symbol, vs_currency=vs_currency)

    stout = st.FakeStrategy().perform_strategy(entry_price=current_price,
                                               df=candles)

    print(position_can_be_profitable(eh, stout, symbol, vs_currency, amount))
