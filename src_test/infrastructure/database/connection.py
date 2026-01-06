"""
数据库连接管理
从原 agent/dice/model.py 提取的数据库连接逻辑
"""

import os
import pymysql
from typing import List, Dict, Any
from dotenv import load_dotenv
from pathlib import Path
from src_test.infrastructure.log import get_logger

logger = get_logger("DATABASE")


class DatabaseConnection:
    """数据库连接管理类"""

    def __init__(self, env_path: str = None):
        """
        初始化数据库连接

        :param env_path: .env 文件路径，默认为 src_test 目录下的 .env
        """
        if env_path is None:
            # 默认查找项目根目录下的 .env 文件
            env_path = Path(__file__).parent.parent.parent.parent / ".env"

        load_dotenv(env_path, override=True)

        self.host = os.getenv('HOST')
        self.user = os.getenv('USER')
        self.mysql_pw = os.getenv('MYSQL_PW')
        self.db = os.getenv('DB_NAME')
        self.port = os.getenv('PORT')

        if not all([self.host, self.user, self.mysql_pw, self.db, self.port]):
            raise ValueError("数据库配置不完整，请检查 .env 文件")

    def get_connection(self):
        """获取数据库连接"""
        return pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.mysql_pw,
            db=self.db,
            port=int(self.port),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    def execute_query(self, sql_query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        执行 SQL 查询并返回字典列表

        :param sql_query: SQL 查询语句
        :param params: 查询参数元组，用于参数化查询
        :return: 查询结果字典列表
        """
        try:
            connection = self.get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(sql_query, params)
                    return cursor.fetchall()
            finally:
                connection.close()
        except Exception as e:
            logger.error(f"数据库查询错误: {e}", exc_info=True)
            return []

    def execute_update(self, sql_query: str, params: tuple = None) -> bool:
        """
        执行 SQL 更新操作

        :param sql_query: SQL 更新语句
        :param params: 更新参数元组，用于参数化查询
        :return: 是否执行成功
        """
        try:
            connection = self.get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(sql_query, params)
                connection.commit()
                return True
            except Exception as e:
                connection.rollback()
                logger.error(f"数据库更新错误: {e}", exc_info=True)
                return False
            finally:
                connection.close()
        except Exception as e:
            logger.error(f"数据库连接错误: {e}", exc_info=True)
            return False
