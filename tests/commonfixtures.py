import pytest
from sqlalchemy.orm import Session

import orm
import model


def create_trade(symbol="BTC", fiat_symbol="EUR", timeframe='5m',
                 stop_loss=1, entry_price=2, take_profit=3,
                 status=model.TradeStatus.OPENED, fiat_entry=20,
                 crypto_quantity_entry=1.0, entry_fee_fiat=.2,
                 position='L',
                 entry_date='2022-06-18 12:13:40',
                 entry_order_exchange_id='entry_id',
                 percentage_change_1d_on_entry='2',
                 percentage_change_7d_on_entry='2',
                 percentage_change_1h_on_entry='2', strategy_name='test',
                 is_real=False):

    return model.Trade(symbol=symbol, fiat_symbol=fiat_symbol, timeframe=timeframe,
                       stop_loss=stop_loss, entry_price=entry_price, take_profit=take_profit,
                       status=status, fiat_entry=fiat_entry,
                       crypto_quantity_entry=crypto_quantity_entry, entry_fee_fiat=entry_fee_fiat,
                       position=position,
                       entry_date=entry_date,
                       entry_order_exchange_id=entry_order_exchange_id,
                       percentage_change_1d_on_entry=percentage_change_1d_on_entry,
                       percentage_change_7d_on_entry=percentage_change_7d_on_entry,
                       percentage_change_1h_on_entry=percentage_change_1h_on_entry, strategy_name=strategy_name,
                       is_real=is_real)

@pytest.fixture
def generic_trade_defaults():
    return model.Trade(symbol="BTC", fiat_symbol="EUR", timeframe='5m',
                       stop_loss=1, entry_price=2, take_profit=3,
                       status=model.TradeStatus.OPENED, fiat_entry=20,
                       crypto_quantity_entry=1.0, entry_fee_fiat=.2,
                       position='L',
                       entry_date='2022-06-18 12:13:40',
                       entry_order_exchange_id='entry_id',
                       percentage_change_1d_on_entry='2',
                       percentage_change_7d_on_entry='2',
                       percentage_change_1h_on_entry='2', strategy_name='test',
                       is_real=False)


@pytest.fixture
def testing_session():
    return Session(orm.test_engine)
