import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator, StochRSIIndicator, StochasticOscillator
from ta.volatility import AverageTrueRange, BollingerBands

pd.set_option('display.max_rows', None)


def get_local_minimums(df_column: pd.DataFrame, n: int):
    """
    :param df_column: dataframe column whose local minimums are desired to be obtained
    :param n: number of points to be checked before and after
    :return: Column dataframe containing the local minimums
    """
    # Find local peaks
    minimums_indexes = argrelextrema(np.array(df_column), np.less, order=n)[0]
    minimums = df_column.iloc[minimums_indexes]

    return minimums


def get_local_maximums(df_column: pd.DataFrame, n: int):
    """
    :param df_column: dataframe column whose local maximums are desired to be obtained
    :param n: number of points to be checked before and after
    :return: Column dataframe containing the local maximums
    """
    # Find local peaks
    maximums_indexes = argrelextrema(np.array(df_column), np.greater, order=n)[0]
    maximums = df_column.iloc[maximums_indexes]

    return maximums


def get_bullish_divergence(type: str, candle_body_low_series: pd.DataFrame, candle_body_high_series: pd.DataFrame,
                           indicator_low_series: pd.DataFrame, n: int = 2):
    """
    Gets bullish divergenge
    :param type: r o h for regular or bullish divergence, respectively
    :param candle_body_low_series: Lower part of the BODY candle (not wicks)
    :param candle_body_high_series: Higher part of the BODY candle (not wicks)
    :param indicator_low_series: Indicator to use to find divergences (Generally will be RSI)
    :param n: Parameter to define maximums and minimums
    :return: Column dataframe containing the divergences
    """
    # Create new DataFrame to compute divergence
    df = pd.DataFrame()
    # Get price lows
    df['price_lows_lows'] = get_local_minimums(candle_body_low_series, n)
    df['price_lows_highs'] = get_local_minimums(candle_body_high_series, n)
    # Both, candle body low and candle body high, must be lows to be considered a low
    df['price_lows'] = np.where(df['price_lows_lows'].notna() & df['price_lows_highs'].notna(),
                                df['price_lows_lows'],
                                np.nan)

    # Get indicator lows
    df['indicator_lows'] = get_local_minimums(indicator_low_series, n)

    # Variables to reference previous and next row
    previous_offset = 1
    next_offset = -1
    # Column to check if price low and indicator low at the same point
    df['low_p_and_low_i'] = ~df['price_lows'].isna() & ~df['indicator_lows'].isna()
    # Column to check if price low and previous point indicator low
    df['low_p_and_previous_low_i'] = ~df['price_lows'].isna() & ~df['indicator_lows'].shift(previous_offset).isna()
    # Column to check if price low and next point indicator low
    df['low_p_and_next_low_i'] = ~df['price_lows'].isna() & ~df['indicator_lows'].shift(next_offset).isna()

    # Data frame to compute the lowest value of the current indicator, previous and next
    lows_df = pd.DataFrame()
    # Indicator value
    lows_df['indicator_lows'] = df['indicator_lows']
    # Current low, if exists
    lows_df['both_lows_df'] = np.where(df['low_p_and_low_i'], lows_df['indicator_lows'], np.nan)
    # Previous low, if exists
    lows_df['previous_lows_df'] = np.where(df['low_p_and_previous_low_i'], lows_df['indicator_lows'].shift(previous_offset), np.nan)
    # Next low, if exists
    lows_df['next_lows_df'] = np.where(df['low_p_and_next_low_i'], lows_df['indicator_lows'].shift(next_offset), np.nan)
    # Lowest value of the previous ones
    lows_df['lowest'] = lows_df.min(axis=1, skipna=True, numeric_only=True)

    # Data frame with the filtered information
    inv_lows_df = pd.DataFrame()
    # Price lows
    inv_lows_df['price_lows'] = df['price_lows']
    # Indicator lows, taking into account previous and next points
    inv_lows_df['indicator_low'] = lows_df['lowest']
    # Remove rows where there are no indicator minimum
    inv_lows_df = inv_lows_df[~inv_lows_df['indicator_low'].isna()]
    # Reverse DataFrame order to iterate over it and get a easier way to detect divergence
    inv_lows_df = inv_lows_df[::-1]

    # List to populate with tuples (index, bool) containing indication of divergence
    divergences = []

    # Look for divergence
    for row in inv_lows_df.itertuples():
        row_index = row[0]
        row_price_low = row[1]
        row_indicator_low = row[2]

        for row_loop_2 in inv_lows_df.itertuples():
            row_index_loop_2 = row_loop_2[0]
            row_price_low_loop_2 = row_loop_2[1]
            row_indicator_low_loop_2 = row_loop_2[2]

            if row_index_loop_2 < row_index:
                if type == 'r':
                    if row_price_low_loop_2 > row_price_low and row_indicator_low_loop_2 < row_indicator_low:
                        divergences.append((row_index, True))
                        break
                elif type == 'h':
                    if row_price_low_loop_2 < row_price_low and row_indicator_low_loop_2 > row_indicator_low:
                        divergences.append((row_index, True))
                        break
                else:
                    raise ValueError(f"Expected value 'r' or 'h' for type, instead {type} was given.")

    divergence_col = pd.DataFrame(divergences, columns=['index', 'r_bull']).set_index('index')

    return divergence_col


def get_rsi(df: pd.DataFrame):
    rsi_indicator = RSIIndicator(df['close'])
    rsi = rsi_indicator.rsi()
    return rsi


def get_ema(df: pd.DataFrame, period: int):
    ema_indicator = EMAIndicator(df['close'], period)
    ema = ema_indicator.ema_indicator()
    return ema


def get_atr(df: pd.DataFrame, period: int = 14):
    atr_indicator = AverageTrueRange(df['high'], df['low'], df['close'], period)
    atr = atr_indicator.average_true_range()
    return atr


def get_bb(df: pd.DataFrame):
    bb_indicator = BollingerBands(df['close'])
    bb_h = bb_indicator.bollinger_hband()
    bb_l = bb_indicator.bollinger_lband()
    bb_avg = bb_indicator.bollinger_mavg()

    return bb_h, bb_avg, bb_l


def get_stochastic_rsi(df: pd.DataFrame):
    stoch_rsi_indicator = StochRSIIndicator(df['close'])
    stoch_rsi = stoch_rsi_indicator.stochrsi()
    stoch_rsi_k = stoch_rsi_indicator.stochrsi_k()
    stoch_rsi_d = stoch_rsi_indicator.stochrsi_d()
    return {
        'stoch': stoch_rsi,
        'k': stoch_rsi_k,
        'd': stoch_rsi_d,
    }


def get_stochastic(df: pd.DataFrame):
    stochastic_indicator = StochasticOscillator(df['high'], df['low'], df['close'])
    stoch_k = stochastic_indicator.stoch()
    stoch_signal_d = stochastic_indicator.stoch_signal()
    return {
        'k': stoch_k,
        'd': stoch_signal_d,
    }


def get_atr_stop_loss(df: pd.DataFrame, atr_period=12, atr_factor=1.5):
    atr = get_atr(df, period=atr_period)
    return {
        'high_band': df['high'] + atr * atr_factor,
        'low_band': df['low'] - atr * atr_factor,
    }


def get_bullish_engulf(df: pd.DataFrame):
    return df['is_green'] & (
            (df['close'] > df['open'].shift(1)) & (df['open'] <= df['close'].shift(1))
    ) & df['is_red'].shift(1)


def get_inventory_retracement(df: pd.DataFrame, retracement_factor: float = .45):
    bearish_retracement = ((df['high'] - df['candle_body_high']) / (df['high'] - df['low'])) > retracement_factor
    bullish_retracement = ((df['candle_body_low'] - df['low']) / (df['high'] - df['low'])) > retracement_factor

    return {
        'bullish': bullish_retracement,
        'bearish': bearish_retracement,
    }


def super_trend(df: pd.DataFrame, atr_period: int, multiplier: float):
    """
    Source: https://medium.datadriveninvestor.com/the-supertrend-implementing-screening-backtesting-in-python-70e8f88f383d    """
    high = df['high']
    low = df['low']
    close = df['close']

    # calculate ATR
    price_diffs = [high - low,
                   high - close.shift(),
                   close.shift() - low]
    true_range = pd.concat(price_diffs, axis=1)
    true_range = true_range.abs().max(axis=1)
    # default ATR calculation in supertrend indicator
    atr = true_range.ewm(alpha=1/atr_period,min_periods=atr_period).mean()
    # df['atr'] = df['tr'].rolling(atr_period).mean()

    # HL2 is simply the average of high and low prices
    hl2 = (high + low) / 2
    # upperband and lowerband calculation
    # notice that final bands are set to be equal to the respective bands
    final_upperband = upperband = hl2 + (multiplier * atr)
    final_lowerband = lowerband = hl2 - (multiplier * atr)

    # initialize Supertrend column to True
    supertrend = [True] * len(df)

    for i in range(1, len(df.index)):
        curr, prev = i, i-1

        # if current close price crosses above upperband
        if close[curr] > final_upperband[prev]:
            supertrend[curr] = True
        # if current close price crosses below lowerband
        elif close[curr] < final_lowerband[prev]:
            supertrend[curr] = False
        # else, the trend continues
        else:
            supertrend[curr] = supertrend[prev]

            # adjustment to the final bands
            if supertrend[curr] == True and final_lowerband[curr] < final_lowerband[prev]:
                final_lowerband[curr] = final_lowerband[prev]
            if supertrend[curr] == False and final_upperband[curr] > final_upperband[prev]:
                final_upperband[curr] = final_upperband[prev]

        # to remove bands according to the trend direction
        if supertrend[curr] == True:
            final_upperband[curr] = np.nan
        else:
            final_lowerband[curr] = np.nan

    return pd.DataFrame({
        'supertrend': supertrend,
        'lowerband': final_lowerband,
        'upperband': final_upperband
    }, index=df.index)


def support_and_resistance(df: pd.DataFrame, margin = .002):
    """
    It is ideal to get the maximum number of candles in the df
    :param df:
    :param margin:
    :return:
    """
    lows = get_local_minimums(df['low'], 2)
    count, division = np.histogram(lows)
    division = np.array(division)

    return {
        'base_line': division,
        'upper_line': division * (1 + margin),
        'lower_line': division * (1 - margin)
    }


def trade_pro_rejection_zone(df: pd.DataFrame):
    ema_20 = get_ema(df=df, period=20)
    ema_50 = get_ema(df=df, period=50)

    cloud_is_green = ema_20.iloc[-1] > ema_50.iloc[-1]

    return {
        'ema_short': ema_20,
        'ema_long': ema_50,
        'cloud_is_green': cloud_is_green,
    }

