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


