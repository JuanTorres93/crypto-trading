from sqlalchemy import create_engine, Table, Column, Integer, Float, String, Boolean
from sqlalchemy.orm import registry

import filesystemutils as fs
import model


# Database directories
_home_dir = fs.home_directory(True)
_real_db_path = f"{_home_dir}/trading.db"

#                      "kind_of_db+API://(path)"
engine = create_engine(f"sqlite+pysqlite:///{_real_db_path}", future=True)
test_engine = create_engine(f"sqlite+pysqlite:///:memory:", future=True)


# Database definition
mapper_registry = registry()

trade_table = Table(
    'trade', mapper_registry.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('symbol', String),
    Column('vs_currency_symbol', String),
    Column('timeframe', String),
    Column('stop_loss', Float),
    Column('entry_price', Float),
    Column('take_profit', Float),
    Column('status', String),
    Column('vs_currency_entry', Float),
    Column('crypto_quantity_entry', Float),
    Column('entry_fee_vs_currency', Float),
    Column('position', String),
    Column('entry_date', String),
    Column('entry_order_exchange_id', String),
    Column('percentage_change_1h_on_entry', String),
    Column('percentage_change_1d_on_entry', String),
    Column('percentage_change_7d_on_entry', String),
    Column('strategy_name', String),
    Column('is_real', Boolean),
    Column('oco_stop_exchange_id', String, nullable=True),
    Column('oco_limit_exchange_id', String, nullable=True),
    Column('vs_currency_result_no_fees', Float, nullable=True),
    Column('modified_stop_loss', Float, nullable=True),
    Column('modified_take_profit', Float, nullable=True),
    Column('crypto_quantity_exit', Float, nullable=True),
    Column('exit_fee_vs_currency', Float, nullable=True),
    Column('exit_date', String, nullable=True),
)

# Create database
mapper_registry.metadata.create_all(engine)
mapper_registry.metadata.create_all(test_engine)


# Apply Dependency Inversion Principle
def perform_mapping():
    global mapper_registry
    mapper_registry.map_imperatively(model.Trade, trade_table)


perform_mapping()

