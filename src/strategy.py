from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True, kw_only=True)
class StrategyOutput:
    can_enter: bool
    take_profit: float
    stop_loss: float


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


class FakeStrategy(Strategy):
    def perform_strategy(self, entry_price, **dfs):
        df = dfs['df']

        if df.iloc[-1]['is_green']:
            return StrategyOutput(can_enter=True, take_profit=12.2, stop_loss=10)

        return StrategyOutput(can_enter=False, take_profit=12.2, stop_loss=10)

