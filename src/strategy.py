from abc import ABC, abstractmethod
from dataclasses import dataclass

import indicator as ind


class PositionType:
    LONG = "long"
    SHORT = "short"


@dataclass(slots=True, kw_only=True)
class StrategyOutput:
    can_enter: bool
    take_profit: float
    entry_price: float
    stop_loss: float
    position_type: str


def _no_entry_output():
    return StrategyOutput(can_enter=False, take_profit=12.2, stop_loss=10,
                          entry_price=11,
                          position_type=PositionType.LONG)


class Strategy(ABC):
    @abstractmethod
    def perform_strategy(self, entry_price, **dfs):
        """
        Executes strategy logic
        :param entry_price: position entry_price
        :param dfs: dataframes to analyse
        :return: StrategyOutput object
        """
        raise NotImplementedError

    @abstractmethod
    def strategy_name(self):
        """
        :return: strategy name
        """
        raise NotImplementedError


class TestStrategy(Strategy):
    """
    Used for testing purposes
    """
    def perform_strategy(self, entry_price, **dfs):
        df = dfs['df']

        if df.iloc[-1]['is_green']:
            return StrategyOutput(can_enter=True, take_profit=12.2, stop_loss=10,
                                  entry_price=11,
                                  position_type=PositionType.LONG)

        return StrategyOutput(can_enter=False, take_profit=12.2, stop_loss=10,
                              entry_price=11,
                              position_type=PositionType.LONG)

    def strategy_name(self):
        return "test_strategy"


class FakeStrategy(Strategy):
    """
    Used for testing purposes
    """
    def perform_strategy(self, entry_price, **dfs):
        df = dfs['df']

        tp = max(list(df['close']))
        sl = min(list(df['close']))

        if df.iloc[-1]['is_green']:

            return StrategyOutput(can_enter=True, take_profit=tp, stop_loss=sl,
                                  entry_price=entry_price,
                                  position_type=PositionType.LONG)

        return StrategyOutput(can_enter=False, take_profit=tp, stop_loss=sl,
                              entry_price=entry_price,
                              position_type=PositionType.LONG)

    def strategy_name(self):
        return "fake_strategy"


class SupportAndResistanceHigherTimeframe(Strategy):
    def strategy_name(self):
        return "support_and_resistance_higher_timeframe"

    def perform_strategy(self, entry_price, **dfs):
        ht_df = dfs['ht_df']
        lt_df = dfs['lt_df']

        mean_close = lt_df['close'].mean()

        sup_and_res_ht = ind.support_and_resistance(ht_df)
        sr_ht_low = sup_and_res_ht['lower_line']
        sr_ht_high = sup_and_res_ht['upper_line']

        total_levels = len(sr_ht_low)

        # Find support and resistance levels
        for i in range(total_levels):
            if i == 0 and mean_close <= sr_ht_low[i]:
                return StrategyOutput(can_enter=False, take_profit=0, stop_loss=0,
                                      entry_price=entry_price,
                                      position_type=PositionType.LONG)

            if i < total_levels - 1:
                if mean_close >= sr_ht_low[i] and mean_close <= sr_ht_low[i+1]:
                    support_index = i
                    resistance_index = i + 1
            elif i == total_levels - 1:
                if mean_close >= sr_ht_low[i]:
                    support_index = i
                    resistance_index = None

        support_low = sr_ht_low[support_index]
        support_high = sr_ht_high[support_index]
        resistance_low = sr_ht_low[resistance_index] if resistance_index is not None else None

        if support_low <= entry_price <= support_high:
            if resistance_low is not None:
                take_profit = resistance_low
                stop_loss = support_low - abs(resistance_low - support_low) / 2
            else:
                difference_previous_and_current_support = abs(support_low - sr_ht_low[support_index - 1])
                stop_loss = support_low - difference_previous_and_current_support / 2
                take_profit = support_low + difference_previous_and_current_support

            return StrategyOutput(can_enter=True, take_profit=take_profit,
                                  stop_loss=stop_loss,
                                  entry_price=entry_price,
                                  position_type=PositionType.LONG)
        else:
            return StrategyOutput(can_enter=False, take_profit=0, stop_loss=0,
                                  entry_price=entry_price,
                                  position_type=PositionType.LONG)


class SupportAndResistanceHigherTimeframeBullishDivergence(Strategy):
    def strategy_name(self):
        return "support_and_resistance_higher_timeframe_bullish_divergence"

    def perform_strategy(self, entry_price, **dfs):
        ht_df = dfs['ht_df']
        lt_df = dfs['lt_df']

        mean_close = lt_df['close'].mean()

        sup_and_res_ht = ind.support_and_resistance(ht_df)
        sr_ht_low = sup_and_res_ht['lower_line']
        sr_ht_high = sup_and_res_ht['upper_line']
        rsi_ht = ind.get_rsi(ht_df)
        bull_div_ht = ind.get_bullish_divergence(type='h',
                                                 candle_body_low_series=ht_df['candle_body_low'],
                                                 candle_body_high_series=ht_df['candle_body_high'],
                                                 indicator_low_series=rsi_ht)
        ht_ema = ind.get_ema(ht_df, period=200)
        # Two last candles above higher timeframe ema?
        closes_above_ema = (ht_df['close'] > ht_ema).iloc[-5:].all()

        # Checks the indexes where divergence exists. Most recent indexes are the
        # highest. Filter to get the last 7 candles divergence
        exists_hidden_bull_div_ht = len(
            list(filter(
                lambda x: x >= 992,
                list(bull_div_ht.index)
            ))
        ) > 0

        total_levels = len(sr_ht_low)

        # Find support and resistance levels
        for i in range(total_levels):
            if i == 0 and mean_close <= sr_ht_low[i]:
                return StrategyOutput(can_enter=False, take_profit=0, stop_loss=0,
                                      entry_price=entry_price,
                                      position_type=PositionType.LONG)

            if i < total_levels - 1:
                if mean_close >= sr_ht_low[i] and mean_close <= sr_ht_low[i+1]:
                    support_index = i
                    resistance_index = i + 1
            elif i == total_levels - 1:
                if mean_close >= sr_ht_low[i]:
                    support_index = i
                    resistance_index = None

        support_low = sr_ht_low[support_index]
        support_high = sr_ht_high[support_index]
        resistance_low = sr_ht_low[resistance_index] if resistance_index is not None else None

        if support_low <= entry_price <= support_high and exists_hidden_bull_div_ht and closes_above_ema:
            if resistance_low is not None:
                take_profit = resistance_low
                stop_loss = support_low - abs(resistance_low - support_low) / 2
            else:
                difference_previous_and_current_support = abs(support_low - sr_ht_low[support_index - 1])
                stop_loss = support_low - difference_previous_and_current_support / 2
                take_profit = support_low + difference_previous_and_current_support

            return StrategyOutput(can_enter=True, take_profit=take_profit,
                                  stop_loss=stop_loss,
                                  entry_price=entry_price,
                                  position_type=PositionType.LONG)
        else:
            return StrategyOutput(can_enter=False, take_profit=0, stop_loss=0,
                                  entry_price=entry_price,
                                  position_type=PositionType.LONG)


class VolumeTradingStrategy(Strategy):

    def perform_strategy(self, entry_price, **dfs):
        """
        The dataframe included needs to include the last candle of the plot (the not finished one)
        :param entry_price:
        :param dfs:
        :return:
        """
        df = dfs['df']

        current_candle_index = -1
        last_finished_candle_index = -2

        try:
            # This is inside a try in case indicators cannot be computed due to a lack
            # Of candles
            quantile = df['volume'].quantile(.75)
            atr_stop_loss = ind.get_atr_stop_loss(df)['low_band'].iloc[last_finished_candle_index]
            stop_loss = atr_stop_loss

        except Exception:
            return _no_entry_output()

        rrr = 1.5
        take_profit = entry_price + rrr * abs(entry_price - stop_loss)

        if df.iloc[last_finished_candle_index]['volume'] > quantile and df.iloc[current_candle_index]['low'] > stop_loss:
            return StrategyOutput(can_enter=True, take_profit=take_profit,
                                  stop_loss=stop_loss,
                                  entry_price=entry_price,
                                  position_type=PositionType.LONG)

        return _no_entry_output()

    def strategy_name(self):
        return "volume_trading_strategy"


class VolumeEmaTradingStrategy(Strategy):
    def perform_strategy(self, entry_price, **dfs):
        """
        The dataframe included needs to include the last candle of the plot (the not finished one)
        :param entry_price:
        :param dfs:
        :return:
        """
        df = dfs['df']

        # This is used just not to enter to an already lost position
        current_candle_index = -1
        # Index with which perform the analysis
        last_finished_candle_index = -2

        try:
            # This is inside a try in case indicators cannot be computed due to a lack
            # Of candles
            green_volume_df = df['volume'][df['close'] > df['close'].shift(1)]
            quantile = green_volume_df.quantile(.80)
            ema = ind.get_ema(df=df, period=50)
            atr_stop_loss = ind.get_atr_stop_loss(df)['low_band'].iloc[last_finished_candle_index]
            stop_loss = atr_stop_loss

        except Exception:
            return _no_entry_output()

        rrr = 1.5
        take_profit = entry_price + rrr * abs(entry_price - stop_loss)

        # Last finished candle is green
        green_volume_candle = (len(df) - 1) in list(green_volume_df.index)
        volume_higher_than_quantile = df['volume'].iloc[last_finished_candle_index] >= quantile
        price_above_ema = df['close'].iloc[last_finished_candle_index] > ema.iloc[last_finished_candle_index]

        if green_volume_candle and volume_higher_than_quantile and price_above_ema and df.iloc[current_candle_index]['low'] > stop_loss:
            return StrategyOutput(can_enter=True, take_profit=take_profit,
                                  stop_loss=stop_loss,
                                  entry_price=entry_price,
                                  position_type=PositionType.LONG)

        return _no_entry_output()

    def strategy_name(self):
        return "volume_ema_trading_strategy"

