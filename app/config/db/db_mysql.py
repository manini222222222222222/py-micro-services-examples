from threading import Lock
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.dialects.mysql import insert
from tenacity import retry, stop_after_attempt, wait_incrementing, retry_if_exception_type

from app.common.logger import log
from app.config.nacos_config import get_db_config

db_config = get_db_config()

# 定义一个全局锁
_db_lock = Lock()

db_dict = {}

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
    创建并返回 SQLAlchemy Engine 对象.

    Args:
        db (str): 数据库名称
        user (str): 数据库用户名
        password (str): 数据库密码
        host (str): 数据库主机地址，默认 localhost
        port (int): 数据库端口，默认 3306
        driver (str): 数据库驱动，默认 'mysql+pymysql'
        pool_size (int): 连接池的持久连接数量
        max_overflow (int): 连接池溢出的临时连接数量
        pool_timeout (int): 获取连接的超时时间（秒）
        pool_recycle (int): 连接的最大生命周期（秒）
        echo (bool): 是否打印 SQL 日志，默认 False

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

# 根据数据库名称获取链接引擎
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
    执行sql语句-通用
    e.g. 创建表 删除表等
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
        log.exception(f"执行sql语句失败:{str(e)}")
        return False


"""
    查询，结果转为DataFrame
"""
@retry(
    retry=retry_if_exception_type(),
    stop=stop_after_attempt(3),
    wait=wait_incrementing(start=60, increment=10, max=90),
    reraise=True,
)
def query_mysql_to_df(db_name: str, sql: str) -> pd.DataFrame:
    """执行 MySQL 查询并返回结果为 DataFrame。

    Args:
        engine: SQLAlchemy 创建的 MySQL 引擎对象。
        sql: 要执行的 SQL 查询语句。

    Returns:
        查询结果，类型为 pandas.DataFrame。
    """
    engine = get_engine_by_db(db_name)
    with engine.connect() as conn:
        return pd.read_sql_query(sql, conn)


"""
    查询，结果转为dict
"""
@retry(
    retry=retry_if_exception_type(),
    stop=stop_after_attempt(3),
    wait=wait_incrementing(start=60, increment=10, max=90),
    reraise=True,
)
def query_mysql_to_dict(db_name: str, sql: str, params: dict = None) -> list[dict]:
    """
        执行 MySQL 查询并直接返回字典列表。

        Args:
            db_name: 数据库名称，供 get_engine_by_db 获取连接引擎。
            sql: 要执行的 SQL 查询语句。

        Returns:
            查询结果，类型为字典列表 [{col1: val1, col2: val2}, ...]
        """
    engine = get_engine_by_db(db_name)
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        # 将结果行转换为字典列表
        return [dict(row) for row in result.mappings().all()]


"""
# 更新示例
rows_updated = update_mysql('webgis_bi', "UPDATE user SET age = age + 1 WHERE id = :id", {'id': 1001})
"""
@retry(
    retry=retry_if_exception_type(),
    stop=stop_after_attempt(3),
    wait=wait_incrementing(start=60, increment=10, max=90),
    reraise=True,
)
def update_mysql(db_name: str, sql: str, params: dict = None) -> int:
    """执行 UPDATE 或 DELETE。"""
    engine = get_engine_by_db(db_name)
    with engine.begin() as conn:
        result = conn.execute(text(sql), params or {})
        return result.rowcount

"""
# 单条插入示例
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
    """单条插入，无事务显式提交。"""
    return update_mysql(db_name, sql, params)


"""
# 批量插入示例
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
    """批量插入"""
    engine = get_engine_by_db(db_name)
    with engine.begin() as conn:
        result = conn.execute(text(sql), params_list)
        return result.rowcount


"""
    直接把dataframe数据存入数据库
"""
@retry(
    retry=retry_if_exception_type(),
    stop=stop_after_attempt(3),
    wait=wait_incrementing(start=60, increment=10, max=90),
    reraise=True,
)
def df_to_db(df, db_name, tb_name, UNIQUE_KEY_COLUMNS):
    '''
     直接把dataframe数据存入数据库
     Args:
         df: 要存入的dataframe
         db_name: 数据库里的库名
         tb_name: 存入数据库的表的名字
         UNIQUE_KEY_COLUMNS: 
         typedict: 
         engine_name: 
     Returns:
     '''

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
        # 创建插入语句
        insert_stmt = insert(table.table).values(list(data_iter))
        # 定义冲突更新逻辑（更新除主键外的所有字段）: 冲突是指主键的值重复了
        update = {col: insert_stmt.inserted[col] for col in keys if col not in UNIQUE_KEY_COLUMNS}
        # 生成 ON DUPLICATE KEY UPDATE 语句
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
