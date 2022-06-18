import model
from commonfixtures import testing_session, generic_trade_defaults


def test_mapper_can_load_trade(testing_session, generic_trade_defaults):
    testing_session.execute(
        f"""
        INSERT INTO trade (symbol, fiat_symbol, timeframe, stop_loss, entry_price,
        take_profit, status, fiat_entry, crypto_quantity_entry, entry_fee_fiat,
        position, entry_date, entry_order_exchange_id, percentage_change_1d_on_entry,
        percentage_change_7d_on_entry, percentage_change_1h_on_entry,
        strategy_name, is_real) VALUES 
        ('{generic_trade_defaults.symbol}', 
        '{generic_trade_defaults.fiat_symbol}', '{generic_trade_defaults.timeframe}', 
        {generic_trade_defaults.stop_loss}, {generic_trade_defaults.entry_price},
        {generic_trade_defaults.take_profit}, '{generic_trade_defaults.status}', 
        {generic_trade_defaults.fiat_entry}, {generic_trade_defaults.crypto_quantity_entry}, 
        {generic_trade_defaults.entry_fee_fiat}, '{generic_trade_defaults.position}', 
        '{generic_trade_defaults.entry_date}', '{generic_trade_defaults.entry_order_exchange_id}', 
        {generic_trade_defaults.percentage_change_1d_on_entry},
        {generic_trade_defaults.percentage_change_7d_on_entry}, 
        {generic_trade_defaults.percentage_change_1h_on_entry},
        '{generic_trade_defaults.strategy_name}', {generic_trade_defaults.is_real});
        """
    )

    assert testing_session.query(model.Trade).all()[0] == generic_trade_defaults


def test_mapper_can_save_trade(testing_session, generic_trade_defaults):
    testing_session.add(generic_trade_defaults)
    testing_session.commit()

    assert testing_session.query(model.Trade).all()[0] == generic_trade_defaults
