from abc import ABC, abstractmethod


class AbstractRepository(ABC):
    @abstractmethod
    def add_trade(self, trade):
        raise NotImplementedError

    @abstractmethod
    def get_trade(self, id):
        raise NotImplementedError
