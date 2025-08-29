from threading import Lock
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.dialects.mysql import insert
from tenacity import retry, stop_after_attempt, wait_incrementing, retry_if_exception_type

from app.common.logger import log
from app.config.nacos_config import get_db_config

"""
get database connect configuration
"""
db_config = get_db_config()

"""
define a global lock
"""
_db_lock = Lock()

"""
sqlalchemy engine dictionary
"""
db_dict = {}

"""
create a database engine
"""
def get_engine(
        db: str,
        user: str,
        password: str,
        host: str = "localhost",
        port: int = 3306,
        driver: str = "mysql+pymysql",
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False,
) -> Engine:
    """
    create and return sqlalchemy engine object

    Args:
    Db (str): database name
    User (str): Database username
    Password (str): database password
    Host (str): Database host address, default localhost
    Port (int): database port, default 3306
    Driver (str): database driver, default 'mysql+pymysql'
    Pool_2 (int): The number of persistent connections in the connection pool
    Max_overflow (int): The number of temporary connections that overflow from the connection pool
    Pool_timeout (int): Get the timeout time (in seconds) for the connection
    Pool_decycle (int): Maximum lifecycle of the connection (in seconds)
    Echo (boolean): Whether to print SQL logs, default False

    Returns:
        Engine: SQLAlchemy Engine 对象
    """
    conn_str = f"{driver}://{user}:{quote_plus(password)}@{host}:{port}/{db}"
    engine = create_engine(
        conn_str,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=True, # 自动检查连接
        echo=echo,
    )

    db_dict[db] = engine
    return engine

"""
retrieve link engine based on database name
"""
def get_engine_by_db(db_name: str) -> Engine:
    if db_name is None:
        raise ValueError("db_name cannot be None")

    engine = db_dict.get(db_name)
    if engine is None:
        with _db_lock:
            engine = db_dict.get(db_name)
            if engine is None:
                engine = get_engine(db_name, db_config['user'], db_config['password'], db_config['host'],
                                    db_config['port'])
    return engine


"""
execute sql statements general
e.g. create, delete tables etc
"""
@retry(
    retry=retry_if_exception_type(),
    stop=stop_after_attempt(3),
    wait=wait_incrementing(start=60, increment=10, max=90),
    reraise=True,
)
def execute_sql(db_name: str, sql: str) -> bool:
    engine = get_engine_by_db(db_name)
    try:
        with engine.begin() as conn:
            conn.execute(text(sql))
            conn.commit()
        return True
    except Exception as e:
        log.exception(f"failed to execute sql:{str(e)}")
        return False


"""
query and convert the result to a dataframe
"""
@retry(
    retry=retry_if_exception_type(),
    stop=stop_after_attempt(3),
    wait=wait_incrementing(start=60, increment=10, max=90),
    reraise=True,
)
def query_mysql_to_df(db_name: str, sql: str) -> pd.DataFrame:
    """
    Execute MySQL query and return the result as a DataFrame.
    Args:
    db_name: Database name, search for the corresponding engine based on the database name
    sql: The SQL query statement to be executed.
    Returns:
        The query result is of type pandas.DataFrame.
    """
    engine = get_engine_by_db(db_name)
    with engine.connect() as conn:
        return pd.read_sql_query(sql, conn)


"""
    query -> convert results to dict
"""
@retry(
    retry=retry_if_exception_type(),
    stop=stop_after_attempt(3),
    wait=wait_incrementing(start=60, increment=10, max=90),
    reraise=True,
)
def query_mysql_to_dict(db_name: str, sql: str, params: dict = None) -> list[dict]:
    """
        Execute MySQL queries and directly return a dictionary list.

        Args:
            db_name: The database name is used to obtain the connection engine for get_engine_by_db.
            sql:the sql query statement to be executed

        Returns:
            Query result, type dictionary list [{col1: val1, col2: val2},...]
        """
    engine = get_engine_by_db(db_name)
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        # convert the result row to a dictionary list
        return [dict(row) for row in result.mappings().all()]


"""
# update example
rows_updated = update_mysql('webgis_bi', "UPDATE user SET age = age + 1 WHERE id = :id", {'id': 1001})
"""
@retry(
    retry=retry_if_exception_type(),
    stop=stop_after_attempt(3),
    wait=wait_incrementing(start=60, increment=10, max=90),
    reraise=True,
)
def update_mysql(db_name: str, sql: str, params: dict = None) -> int:
    """execute update or delete"""
    engine = get_engine_by_db(db_name)
    with engine.begin() as conn:
        result = conn.execute(text(sql), params or {})
        return result.rowcount

"""
# single insertion example
sql_insert_one = "INSERT INTO user (name, age) VALUES (:name, :age)"
rows_inserted = insert_mysql('webgis_bi', sql_insert_one, {'name': '李四', 'age': 20})
"""
@retry(
    retry=retry_if_exception_type(),
    stop=stop_after_attempt(3),
    wait=wait_incrementing(start=60, increment=10, max=90),
    reraise=True,
)
def insert_mysql(db_name: str, sql: str, params: dict) -> int:
    """Single insertion"""
    return update_mysql(db_name, sql, params)


"""
# batch insertion example
sql_insert_many = "INSERT INTO user (name, age) VALUES (:name, :age)"
params_list = [{'name': '张三', 'age': 18}, {'name': '王五', 'age': 22}]
rows_inserted = insert_batch_mysql('webgis_bi', sql_insert_many, params_list)
"""
@retry(
    retry=retry_if_exception_type(),
    stop=stop_after_attempt(3),
    wait=wait_incrementing(start=60, increment=10, max=90),
    reraise=True,
)
def insert_batch_mysql(db_name: str, sql: str, params_list: list) -> int:
    """batch insert"""
    engine = get_engine_by_db(db_name)
    with engine.begin() as conn:
        result = conn.execute(text(sql), params_list)
        return result.rowcount


"""
Directly store the dataframe data into the database
"""
@retry(
    retry=retry_if_exception_type(),
    stop=stop_after_attempt(3),
    wait=wait_incrementing(start=60, increment=10, max=90),
    reraise=True,
)
def df_to_db(df, db_name, tb_name, UNIQUE_KEY_COLUMNS):
    """
    Directly store the dataframe data into the database

    :param df: Data frame to be stored
    :param db_name: The database name is used to obtain the connection engine for get_engine_by_db.
    :param tb_name: database table name
    :param UNIQUE_KEY_COLUMNS: unique index
    :return: affect rows
    """


    def on_duplicate_update(table, conn, keys, data_iter):
        '''
        Execute SQL statement inserting data
        Parameters
        ----------
        table : pandas.io.sql.SQLTable
        conn : sqlalchemy.engine.Engine or sqlalchemy.engine.Connection
        keys : list of str
            Column names
        data_iter : Iterable that iterates the values to be inserted
        '''
        # create insert statement
        insert_stmt = insert(table.table).values(list(data_iter))
        # Define conflict update logic (update all fields except for the primary key): Conflict refers to the value of the primary key being duplicated
        update = {col: insert_stmt.inserted[col] for col in keys if col not in UNIQUE_KEY_COLUMNS}
        # generate on duplicate key update statement
        on_duplicate_stmt = insert_stmt.on_duplicate_key_update(**update)
        conn.execute(on_duplicate_stmt)

    engine = get_engine_by_db(db_name)
    with engine.begin() as conn:
        df.to_sql(
            name=tb_name,
            con=engine,
            if_exists='append',
            index=False,
            method=on_duplicate_update,
            chunksize=3000
        )
        result = conn.execute(text(f"SELECT COUNT(*) FROM {tb_name}"))
        res = result.scalar_one()
    return res
