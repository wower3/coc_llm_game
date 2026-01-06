"""
数据仓储
从原 agent/dice/model.py 提取的数据访问逻辑
"""

import json
import re
from typing import Dict, Any, Optional

from src_test.infrastructure.database.connection import DatabaseConnection
from src_test.domain.models import COCPlayerModel, SkillsModel
from src_test.infrastructure.log import get_logger

logger = get_logger("DATABASE")


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
        logger.debug(f"[数据库] 查询玩家卡片: user_id={user_id}")
        try:
            sql_query = "SELECT * FROM players WHERE id = %s"
            results = self.db.execute_query(sql_query, (user_id,))

            if results:
                logger.debug(f"[数据库] 查询玩家卡片成功: user_id={user_id}")
                return COCPlayerModel.model_validate(results[0])

            logger.debug(f"[数据库] 未找到玩家卡片: user_id={user_id}")
            return None
        except Exception as e:
            logger.error(f"[数据库] 查询玩家卡片失败: user_id={user_id}, error={str(e)}", exc_info=True)
            return None

    def set_user_card(self, user_id: str, update_data: dict) -> bool:
        """
        动态更新玩家卡片信息

        :param user_id: 玩家ID
        :param update_data: 要更新的字段字典
        :return: 是否更新成功
        """
        if not update_data:
            return False

        logger.debug(f"[数据库] 更新玩家卡片: user_id={user_id}, fields={list(update_data.keys())}")

        # 允许的列名白名单
        allowed_columns = {
            'name', 'age', 'sex', 'strength', 'constitution', 'size', 'dexterity',
            'appearance', 'education', 'intelligence', 'willpower', 'luck',
            'hit_points', 'magic_points', 'sanity', 'damage_bonus', 'build',
            'movement', 'occupation_id', 'skills', 'weapons', 'equipments', 'notes'
        }

        set_clauses = []
        values = []

        for key, value in update_data.items():
            # 验证列名是否在白名单中
            if key not in allowed_columns:
                logger.warning(f"[数据库] 忽略非法列名: {key}")
                continue

            if key in ['skills', 'weapons', 'equipments', 'notes'] and isinstance(value, (dict, list)):
                formatted_value = f"'{json.dumps(value, ensure_ascii=False)}'"
            elif isinstance(value, str):
                # 使用 pymysql 的 escape_string 或者用参数化
                safe_val = value.replace("\\", "\\\\").replace("'", "\\'")
                formatted_value = f"'{safe_val}'"
            elif value is None:
                formatted_value = "NULL"
            else:
                formatted_value = str(value)

            set_clauses.append(f"`{key}` = {formatted_value}")

        if not set_clauses:
            logger.warning(f"[数据库] 没有有效的列需要更新: user_id={user_id}")
            return False

        sql_query = f"UPDATE players SET {', '.join(set_clauses)} WHERE id = %s"
        result = self.db.execute_update(sql_query, (user_id,))
        if result:
            logger.debug(f"[数据库] 更新玩家卡片成功: user_id={user_id}")
        else:
            logger.warning(f"[数据库] 更新玩家卡片失败: user_id={user_id}")
        return result

    def get_skill_card(self, user_id: str):
        """获取玩家技能卡片信息"""
        logger.debug(f"[数据库] 查询玩家技能卡片: user_id={user_id}")
        try:
            sql_query = "SELECT * FROM skills WHERE id = %s"
            results = self.db.execute_query(sql_query, (user_id,))

            if results:
                logger.debug(f"[数据库] 查询玩家技能卡片成功: user_id={user_id}")
                return SkillsModel.model_validate(results[0])

            logger.debug(f"[数据库] 未找到玩家技能卡片: user_id={user_id}")
            return SkillsModel(id=user_id)
        except Exception as e:
            logger.error(f"[数据库] 查询玩家技能卡片失败: user_id={user_id}, error={str(e)}", exc_info=True)
            return SkillsModel(id=user_id)

    def get_id(self, attribute_name: str) -> str:
        """根据中文名获取属性/技能的 ID"""
        logger.debug(f"[数据库] 查询属性/技能ID: name={attribute_name}")
        try:
            sql_query = "SELECT id FROM chinese_name WHERE name = %s LIMIT 1"
            results = self.db.execute_query(sql_query, (attribute_name,))

            if results:
                result_id = str(results[0]['id'])
                logger.debug(f"[数据库] 查询属性/技能ID成功: name={attribute_name}, id={result_id}")
                return result_id

            logger.debug(f"[数据库] 未找到属性/技能: name={attribute_name}")
            return attribute_name
        except Exception as e:
            logger.error(f"[数据库] 查询属性/技能ID失败: name={attribute_name}, error={str(e)}", exc_info=True)
            return attribute_name

    def get_name_by_id(self, skill_id: str) -> str:
        """
        根据ID获取属性/技能的中文名

        :param skill_id: 技能ID
        :return: 技能中文名，如果未找到返回原ID
        """
        logger.debug(f"[数据库] 查询技能中文名: skill_id={skill_id}")
        try:
            sql_query = "SELECT name FROM chinese_name WHERE id = %s LIMIT 1"
            results = self.db.execute_query(sql_query, (skill_id,))

            if results:
                result_name = str(results[0]['name'])
                logger.debug(f"[数据库] 查询技能中文名成功: skill_id={skill_id}, name={result_name}")
                return result_name

            logger.debug(f"[数据库] 未找到技能: skill_id={skill_id}")
            return skill_id
        except Exception as e:
            logger.error(f"[数据库] 查询技能中文名失败: skill_id={skill_id}, error={str(e)}", exc_info=True)
            return skill_id

    def get_single_skill_value(self, user_id: str, skill_id: str) -> Any:
        """
        获取玩家单个技能的值

        :param user_id: 玩家ID
        :param skill_id: 技能ID
        :return: 技能值，如果未找到返回 None
        """
        logger.debug(f"[数据库] 查询单个技能值: user_id={user_id}, skill_id={skill_id}")
        try:
            # 验证 skill_id 是合法的列名（只允许ASCII字母、数字、下划线，且必须以字母或下划线开头）
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', skill_id):
                logger.debug(f"[数据库] 跳过非法的技能ID（可能是中文名）: skill_id={skill_id}")
                return None

            # skill_id 作为列名需要拼接，user_id 使用参数化查询
            sql_query = f"SELECT `{skill_id}` FROM skills WHERE id = %s"
            results = self.db.execute_query(sql_query, (user_id,))

            if results and skill_id in results[0]:
                skill_value = results[0][skill_id]
                logger.debug(f"[数据库] 查询单个技能值成功: user_id={user_id}, skill_id={skill_id}, value={skill_value}")
                return skill_value

            logger.debug(f"[数据库] 未找到技能值: user_id={user_id}, skill_id={skill_id}")
            return None
        except Exception as e:
            logger.error(f"[数据库] 查询单个技能值失败: user_id={user_id}, skill_id={skill_id}, error={str(e)}", exc_info=True)
            return None

    def get_all_chinese_names(self) -> Dict[str, str]:
        """
        获取所有技能的中文名映射

        :return: 技能ID到中文名称的映射字典
        """
        logger.debug(f"[数据库] 查询所有技能中文名映射")
        try:
            sql = "SELECT id, name FROM chinese_name"
            results = self.db.execute_query(sql)
            name_map = {row['id']: row['name'] for row in results}
            logger.debug(f"[数据库] 查询所有技能中文名映射成功，共 {len(name_map)} 条")
            return name_map
        except Exception as e:
            logger.error(f"[数据库] 查询所有技能中文名映射失败: error={str(e)}", exc_info=True)
            return {}

    def get_skill_id_by_name(self, skill_name: str) -> Optional[str]:
        """
        通过技能中文名获取技能ID

        :param skill_name: 技能中文名
        :return: 技能ID，如果未找到返回 None
        """
        logger.debug(f"[数据库] 通过中文名查询技能ID: skill_name={skill_name}")
        try:
            sql = "SELECT id FROM chinese_name WHERE name = %s"
            results = self.db.execute_query(sql, (skill_name,))

            if results:
                skill_id = results[0]['id']
                logger.debug(f"[数据库] 通过中文名查询技能ID成功: {skill_name} → {skill_id}")
                return skill_id

            logger.debug(f"[数据库] 未找到技能: skill_name={skill_name}")
            return None
        except Exception as e:
            logger.error(f"[数据库] 通过中文名查询技能ID失败: skill_name={skill_name}, error={str(e)}", exc_info=True)
            return None


# 全局实例（保持向后兼容）
_default_repository = None


def get_repository() -> PlayerRepository:
    """获取默认仓储实例"""
    global _default_repository
    if _default_repository is None:
        _default_repository = PlayerRepository()
    return _default_repository
