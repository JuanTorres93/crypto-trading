from abc import ABC, abstractmethod

from sqlalchemy import and_, text
from sqlalchemy.orm import Session

import model
import orm


class AbstractRepository(ABC):
    def __init__(self, session):
        self._session = session

    @abstractmethod
    def add_trade(self, trade):
        raise NotImplementedError

    @abstractmethod
    def get_trade(self, id):
        raise NotImplementedError

    @abstractmethod
    def commit(self):
        raise NotImplementedError

    @abstractmethod
    def update_trade_on_oco_order_creation(self, id, oco_stop_exchange_id,
                                           oco_limit_exchange_id):
        raise NotImplementedError

    @abstractmethod
    def update_trade_on_exit_position(self, id, vs_currency_result_no_fees,
                                      status, crypto_quantity_exit,
                                      exit_fee_vs_currency, exit_date):
        raise NotImplementedError

    @abstractmethod
    def get_opened_positions(self, symbol=None, vs_currency=None):
        """
        Queries all currently opened positions. If symbol and vs_currency are
        specified, then filter by their values
        :param symbol: Left-hand side of market symbol
        :param vs_currency: Right-hand side of market symbol
        :return: List containing trades with opened positions
        """
        raise NotImplementedError

    @abstractmethod
    def modify_stop_loss(self, id, new_stop_loss):
        """
        Modifies the stop loss of the given trade (id)
        :param id: id in local database of the trade to modify
        :param new_stop_loss: new value of the stop loss
        :return:
        """
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def add_trade(self, trade):
        self._session.add(trade)

    def get_trade(self, id):
        return self._session.query(model.Trade).filter_by(id=id).one()

    def commit(self):
        self._session.commit()

    def update_trade_on_oco_order_creation(self, id, oco_stop_exchange_id,
                                           oco_limit_exchange_id):
        trade = self.get_trade(id)
        trade.oco_stop_exchange_id = oco_stop_exchange_id
        trade.oco_limit_exchange_id = oco_limit_exchange_id
        self.commit()

    def update_trade_on_exit_position(self, id, vs_currency_result_no_fees,
                                      status, crypto_quantity_exit,
                                      exit_fee_vs_currency, exit_date):
        trade = self.get_trade(id)
        trade.vs_currency_result_no_fees = vs_currency_result_no_fees
        trade.status = status
        trade.crypto_quantity_exit = crypto_quantity_exit
        trade.exit_fee_vs_currency = exit_fee_vs_currency
        trade.exit_date = exit_date
        self.commit()

    def get_opened_positions(self, symbol=None, vs_currency=None):
        if (symbol is None) or (vs_currency is None):
            return self._session.query(model.Trade).filter_by(status=model.TradeStatus.OPENED).all()
        elif (symbol is not None) and (vs_currency is not None):
            return self._session.query(model.Trade).where(
                and_(
                    model.Trade.status == model.TradeStatus.OPENED,
                    model.Trade.symbol == symbol,
                    model.Trade.vs_currency_symbol == vs_currency,
                )
            ).all()

    def modify_stop_loss(self, id, new_stop_loss):
        trade = self.get_trade(id)
        trade.modified_stop_loss = new_stop_loss
        self.commit()

    def get_results_for_day_month_day(self, day, month, year):
        # TODO incluir en diagrama UML
        day = str(day).zfill(2)
        month = str(month).zfill(2)
        year = str(year)

        query = f"""
        SELECT
	    status as "Result",
	    count(status) as "Count",
	    sum(vs_currency_result_no_fees) - sum(entry_fee_vs_currency) - sum(exit_fee_vs_currency) as "WITH Commissions"
        FROM trade
        WHERE
        strategy_name IS "support_and_resistance_higher_timeframe_bullish_divergence"
        AND is_real IS TRUE
        AND entry_date LIKE '{day}/{month}/{year} %:%:%'	-- CAMBIAR ABAJO TAMBIÉN 'DD/MM/YYYY %:%:%'
        GROUP BY status
        UNION ALL
        SELECT
        	"TOTAL",
        	count(status) as "Count",
        	sum(vs_currency_result_no_fees) - sum(entry_fee_vs_currency) - sum(exit_fee_vs_currency) as "WITH Commissions"
        FROM trade
        WHERE 
        strategy_name IS "support_and_resistance_higher_timeframe_bullish_divergence"
        AND is_real IS TRUE
        AND entry_date LIKE '{day}/{month}/{year} %:%:%'	-- CAMBIAR ARRIBA TAMBIÉN 'DD/MM/YYYY %:%:%'
        ;
        """
        conn = self._session.connection()
        results = conn.execute(text(query))

        return results



def provide_sqlalchemy_repository(real_db):
    """
    Tested indirectly through sqlalchemyrepository_testing fixture
    :param real_db: if True uses real database connection, otherwise uses testing
    :return: SqlAlchemyRepository
    """
    if real_db:
        return SqlAlchemyRepository(
            Session(orm.engine)
        )
    else:
        return SqlAlchemyRepository(
            Session(orm.test_engine)
        )

if __name__ == "__main__":
    repo = provide_sqlalchemy_repository(True)

    repo.get_results_for_day_month_day(15, 1, 2023)
