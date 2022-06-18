from abc import ABC, abstractmethod


class AbstractRepository(ABC):
    @abstractmethod
    def add(self, table_entry):
        raise NotImplementedError

    @abstractmethod
    def get(self, table, id):
        raise NotImplementedError
