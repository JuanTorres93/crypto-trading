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

        # Checks the indexes where divergence exists. Most recent indexes are the
        # highest. Filter to get the last 100 candles divergence
        exists_hidden_bull_div_ht = len(
            list(filter(
                lambda x: x >= 898,
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

        if support_low <= entry_price <= support_high and exists_hidden_bull_div_ht:
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

