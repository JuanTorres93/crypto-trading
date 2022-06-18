from abc import ABC, abstractmethod

import model


class AbstractRepository(ABC):
    def __init__(self, session):
        self.session = session

    @abstractmethod
    def add_trade(self, trade):
        raise NotImplementedError

    @abstractmethod
    def get_trade(self, id):
        raise NotImplementedError

    @abstractmethod
    def commit(self):
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def add_trade(self, trade):
        self.session.add(trade)

    def get_trade(self, id):
        return self.session.query(model.Trade).filter_by(id=id).one()

    def commit(self):
        self.session.commit()