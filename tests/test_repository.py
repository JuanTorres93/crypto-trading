import pytest

import model

from commonfixtures import testing_session, create_trade, sqlalchemyrepository_testing


def test_sqlalchemy_repository_saves_trade(sqlalchemyrepository_testing):
    t = create_trade(entry_date='2022-06-18 18:48:57')
    sqlalchemyrepository_testing.add_trade(t)
    sqlalchemyrepository_testing.commit()

    expected_trade = sqlalchemyrepository_testing._session.query(
        model.Trade
    ).filter_by(id=t.id).one()

    assert t == expected_trade


def test_sqlalchemy_repository_loads_trade(sqlalchemyrepository_testing):
    t = create_trade(entry_date='2022-06-18 19:01:03')
    sqlalchemyrepository_testing.add_trade(t)
    sqlalchemyrepository_testing.commit()

    expected_trade = sqlalchemyrepository_testing.get_trade(t.id)

    assert expected_trade == t


def test_sqlalchemy_updates_trade_on_oco_order(sqlalchemyrepository_testing):
    t = create_trade(entry_date='2022-06-18 19:11:47')
    sqlalchemyrepository_testing.add_trade(t)
    sqlalchemyrepository_testing.commit()

    oco_stop_exchange_id = '2022-06-18 19:14:05'
    oco_limit_exchange_id = '2022-06-18 19:14:20'

    t_modified = create_trade(entry_date='2022-06-18 19:11:47',
                              oco_stop_exchange_id=oco_stop_exchange_id,
                              oco_limit_exchange_id=oco_limit_exchange_id)

    sqlalchemyrepository_testing.update_trade_on_oco_order_creation(
        id=t.id,
        oco_stop_exchange_id=oco_stop_exchange_id,
        oco_limit_exchange_id=oco_limit_exchange_id
    )

    assert t_modified == sqlalchemyrepository_testing.get_trade(t.id)


def test_sqlalchemy_updates_trade_on_exit_position(sqlalchemyrepository_testing):
    t = create_trade(entry_date='2022-06-18 19:19:19')
    sqlalchemyrepository_testing.add_trade(t)
    sqlalchemyrepository_testing.commit()

    status = model.TradeStatus.WON
    vs_currency_result_no_fees = 10.4
    crypto_quantity_exit = 10.99
    exit_fee_vs_currency = 22.009
    exit_date = '2022-06-18 19:21:10'

    t_modified = create_trade(entry_date='2022-06-18 19:19:19', status=status,
                              vs_currency_result_no_fees=vs_currency_result_no_fees,
                              crypto_quantity_exit=crypto_quantity_exit,
                              exit_fee_vs_currency=exit_fee_vs_currency, exit_date=exit_date)

    sqlalchemyrepository_testing.update_trade_on_exit_position(id=t.id,
                                                               vs_currency_result_no_fees=vs_currency_result_no_fees,
                                                               status=status,
                                                               crypto_quantity_exit=crypto_quantity_exit,
                                                               exit_fee_vs_currency=exit_fee_vs_currency,
                                                               exit_date=exit_date)

    assert t_modified == sqlalchemyrepository_testing.get_trade(t.id)


def test_sqlalchemy_gets_opened_positions(sqlalchemyrepository_testing):
    # General behaviour
    t1 = create_trade(symbol='BTC', vs_currency_symbol='EUR', entry_date='17-07-2022 08:01:36')
    sqlalchemyrepository_testing.add_trade(t1)
    sqlalchemyrepository_testing.commit()

    opened_positions = sqlalchemyrepository_testing.get_opened_positions()

    total_opened_positions = len(opened_positions)
    assert total_opened_positions >= 1

    for position in opened_positions:
        assert position.status == model.TradeStatus.OPENED

    # Update one trade and ensure that it does not get returned again
    t1 = sqlalchemyrepository_testing.get_trade(id=t1.id)
    t1.status = model.TradeStatus.WON
    sqlalchemyrepository_testing.commit()

    opened_positions = sqlalchemyrepository_testing.get_opened_positions()
    assert len(opened_positions) == total_opened_positions - 1

    for position in opened_positions:
        assert position.status == model.TradeStatus.OPENED

    # Check for specific symbol
    t1 = create_trade(symbol='ALPARGATAS', vs_currency_symbol='CALABACIN', entry_date='17-07-2022 08:27:50')
    sqlalchemyrepository_testing.add_trade(t1)
    sqlalchemyrepository_testing.commit()

    opened_positions = sqlalchemyrepository_testing.get_opened_positions(symbol='ALPARGATAS',
                                                                         vs_currency='CALABACIN')

    assert len(opened_positions) == 1
    assert opened_positions[0].status == model.TradeStatus.OPENED
