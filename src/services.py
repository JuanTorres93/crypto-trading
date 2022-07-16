import exchangehandler as eh
import strategy as st


def position_can_be_profitable(exchange_handler: eh.ExchangeHandler,
                               strategy_output: st.StrategyOutput, symbol,
                               vs_currency, amount):
    """
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


if __name__ == "__main__":
    import ccxt

    import config
    bin_eh = eh.BinanceCcxtExchangeHandler(ccxt.binance(
        {
            'apiKey': config.BINANCE_API_KEY,
            'secret': config.BINANCE_SECRET_KEY,
            'enableLimitRate': True,
        }
    ))

    symbol = 'ETH'
    vs_currency = 'EUR'
    amount = 1

    candles = bin_eh.get_candles_for_strategy(symbol=symbol,
                                              vs_currency=vs_currency,
                                              timeframe='1h',
                                              num_candles=20)

    current_price = bin_eh.get_current_price(symbol=symbol, vs_currency=vs_currency)

    stout = st.FakeStrategy().perform_strategy(entry_price=current_price,
                                               df=candles)

    print(position_can_be_profitable(bin_eh, stout, symbol, vs_currency, amount))
