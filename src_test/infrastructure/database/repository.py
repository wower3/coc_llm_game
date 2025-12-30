"""
数据仓储
从原 agent/dice/model.py 提取的数据访问逻辑
"""

import json
from typing import Dict, Any

from src_test.infrastructure.database.connection import DatabaseConnection
from src_test.domain.models import COCPlayerModel, SkillsModel


class PlayerRepository:
    """玩家数据仓储"""

    def __init__(self, db_connection: DatabaseConnection = None):
        """
        初始化仓储

        :param db_connection: 数据库连接实例
        """
        self.db = db_connection or DatabaseConnection()

    def get_user_card(self, user_id: str) -> COCPlayerModel:
        """获取玩家卡片信息"""
        sql_query = f"SELECT * FROM players WHERE id = '{user_id}'"
        results = self.db.execute_query(sql_query)

        if results:
            return COCPlayerModel.model_validate(results[0])

        return None

    def set_user_card(self, user_id: str, update_data: dict) -> bool:
        """动态更新玩家卡片信息"""
        if not update_data:
            return False

        set_clauses = []

        for key, value in update_data.items():
            if key in ['skills', 'weapons', 'equipments', 'notes'] and isinstance(value, (dict, list)):
                formatted_value = f"'{json.dumps(value, ensure_ascii=False)}'"
            elif isinstance(value, str):
                safe_val = value.replace("'", "''")
                formatted_value = f"'{safe_val}'"
            elif value is None:
                formatted_value = "NULL"
            else:
                formatted_value = str(value)

            set_clauses.append(f"`{key}` = {formatted_value}")

        sql_query = f"UPDATE players SET {', '.join(set_clauses)} WHERE id = '{user_id}'"
        return self.db.execute_update(sql_query)

    def get_skill_card(self, user_id: str) -> SkillsModel:
        """获取玩家技能卡片信息"""
        sql_query = f"SELECT * FROM skills WHERE id = '{user_id}'"
        results = self.db.execute_query(sql_query)

        if results:
            return SkillsModel.model_validate(results[0])

        return SkillsModel(id=user_id)

    def get_id(self, attribute_name: str) -> str:
        """根据中文名获取属性/技能的 ID"""
        sql_query = f"SELECT id FROM chinese_name WHERE name = '{attribute_name}' LIMIT 1"
        results = self.db.execute_query(sql_query)

        if results:
            return str(results[0]['id'])

        return attribute_name


# 全局实例（保持向后兼容）
_default_repository = None


def get_repository() -> PlayerRepository:
    """获取默认仓储实例"""
    global _default_repository
    if _default_repository is None:
        _default_repository = PlayerRepository()
    return _default_repository
