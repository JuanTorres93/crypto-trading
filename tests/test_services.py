import pytest

import config
from commonfixtures import sqlalchemyrepository_testing
import model
import repository as rp
import services
import strategy as st


def test_service_manages_risk_on_long_position():
    vs_currency_on_entry = 200
    st_out = st.StrategyOutput(can_enter=True, take_profit=11, stop_loss=7,
                               entry_price=10, position_type=st.PositionType.LONG
    )

    enter_vs_currency = services.manage_risk_on_entry(vs_currency_on_entry,
                                                      st_out,
                                                      config.MAX_VS_CURRENCY_TO_USE)

    assert enter_vs_currency < vs_currency_on_entry

