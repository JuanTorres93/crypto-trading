from abc import ABC, abstractmethod


class Strategy(ABC):
    @abstractmethod
    def perform_strategy(self, entry_price, **dfs):
        """
        Executes strategy logic
        :param entry_price: position entry_price
        :param dfs: dataframes to analyse
        :return: dictionary containing can_enter, stop_loss and take_profit
        """
        raise NotImplementedError


class FakeStrategy(Strategy):
    def perform_strategy(self, entry_price, **dfs):
        df = dfs['df']
        # TODO terminar de escribir junto a su test

