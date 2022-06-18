import pytest

import model
import repository

from commonfixtures import testing_session, create_trade


@pytest.fixture
def sqlalchemyrepository(testing_session):
    return repository.SqlAlchemyRepository(testing_session)


def test_sqlalchemy_repository_saves_trade(sqlalchemyrepository):
    t = create_trade(entry_date='2022-06-18 18:48:57')
    sqlalchemyrepository.add_trade(t)
    sqlalchemyrepository.commit()

    expected_trade = sqlalchemyrepository.session.query(
        model.Trade
    ).filter_by(id=t.id).one()

    assert t == expected_trade


def test_sqlalchemy_repository_loads_trade(sqlalchemyrepository):
    t = create_trade(entry_date='2022-06-18 19:01:03')
    sqlalchemyrepository.add_trade(t)
    sqlalchemyrepository.commit()

    expected_trade = sqlalchemyrepository.get_trade(t.id)

    assert expected_trade == t


def test_sqlalchemy_updates_trade_on_oco_order(sqlalchemyrepository):
    t = create_trade(entry_date='2022-06-18 19:11:47')
    sqlalchemyrepository.add_trade(t)
    sqlalchemyrepository.commit()

    oco_stop_exchange_id = '2022-06-18 19:14:05'
    oco_limit_exchange_id = '2022-06-18 19:14:20'

    t_modified = create_trade(entry_date='2022-06-18 19:11:47',
                              oco_stop_exchange_id=oco_stop_exchange_id,
                              oco_limit_exchange_id=oco_limit_exchange_id)

    sqlalchemyrepository.update_trade_on_oco_order_creation(
        id=t.id,
        oco_stop_exchange_id=oco_stop_exchange_id,
        oco_limit_exchange_id=oco_limit_exchange_id
    )

    assert t_modified == sqlalchemyrepository.get_trade(t.id)


def test_sqlalchemy_updates_trade_on_exit_position(sqlalchemyrepository):
    t = create_trade(entry_date='2022-06-18 19:19:19')
    sqlalchemyrepository.add_trade(t)
    sqlalchemyrepository.commit()

    status = model.TradeStatus.WON
    fiat_result_no_fees = 10.4
    crypto_quantity_exit = 10.99
    exit_fee_fiat = 22.009
    exit_date = '2022-06-18 19:21:10'

    t_modified = create_trade(entry_date='2022-06-18 19:19:19', status=status,
                              fiat_result_no_fees=fiat_result_no_fees,
                              crypto_quantity_exit=crypto_quantity_exit,
                              exit_fee_fiat=exit_fee_fiat, exit_date=exit_date)

    sqlalchemyrepository.update_trade_on_exit_position(
        id=t.id,
        status=status,
        fiat_result_no_fees=fiat_result_no_fees,
        crypto_quantity_exit=crypto_quantity_exit,
        exit_fee_fiat=exit_fee_fiat,
        exit_date=exit_date
    )

    assert t_modified == sqlalchemyrepository.get_trade(t.id)

