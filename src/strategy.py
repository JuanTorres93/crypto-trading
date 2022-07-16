from abc import ABC, abstractmethod
from dataclasses import dataclass


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
