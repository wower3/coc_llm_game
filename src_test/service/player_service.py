"""
玩家服务
封装玩家数据相关的业务逻辑
"""

from typing import Dict, List, Any, Optional
from src_test.infrastructure.database import get_repository
from src_test.infrastructure.log import get_logger
from src_test.domain.models import COCPlayerModel, SkillsModel

logger = get_logger("PLAYER_SERVICE")


class PlayerService:
    """玩家数据服务"""

    def __init__(self):
        self.repository = get_repository()

    def get_player_info(self, player_id: str) -> Optional[Dict[str, Any]]:
        """
        获取玩家基本信息（包含衍生的计算属性）

        :param player_id: 玩家ID
        :return: 玩家信息字典，如果未找到返回 None
        """
        logger.debug(f"[玩家服务] 查询玩家信息: player_id={player_id}")
        player = self.repository.get_user_card(player_id)

        if not player or not player.id:
            logger.debug(f"[玩家服务] 未找到玩家: player_id={player_id}")
            return None

        data = player.model_dump()

        # 计算衍生属性
        con = data.get('constitution', 0) or 0
        siz = data.get('size', 0) or 0
        pow_val = data.get('willpower', 0) or 0

        return {
            'id': data.get('id'),
            'name': data.get('name'),
            'age': data.get('age'),
            'sex': data.get('sex', 'Male'),
            'strength': data.get('strength'),
            'constitution': con,
            'size': siz,
            'dexterity': data.get('dexterity'),
            'appearance': data.get('appearance'),
            'education': data.get('education'),
            'intelligence': data.get('intelligence'),
            'willpower': pow_val,
            'luck': data.get('luck'),
            'hit_points': data.get('hit_points'),
            'magic_points': data.get('magic_points'),
            'sanity': data.get('sanity'),
            'max_hp': (con + siz) // 10 if (con and siz) else 0,
            'max_mp': pow_val // 5 if pow_val else 0,
            'max_san': 99,
            'damage_bonus': data.get('damage_bonus', 0),
            'build': data.get('build', 0),
            'movement': data.get('movement', 0),
            'occupation_id': data.get('occupation_id')
        }

    def get_filtered_skills(self, player_id: str, min_value: int = 10) -> List[Dict[str, Any]]:
        """
        获取玩家技能信息（过滤数值大于等于指定值的技能）

        :param player_id: 玩家ID
        :param min_value: 最小技能值过滤阈值，默认为 10
        :return: 过滤后的技能列表，按技能值降序排序
        """
        logger.debug(f"[玩家服务] 查询玩家技能: player_id={player_id}, min_value={min_value}")
        skills_data = self.repository.get_skill_card(player_id)

        if not skills_data:
            logger.debug(f"[玩家服务] 未找到玩家技能: player_id={player_id}")
            return []

        skills_dict = skills_data.model_dump()
        chinese_names = self.get_all_chinese_names()

        # 过滤并格式化技能
        filtered_skills = []
        for key, value in skills_dict.items():
            if key.startswith('skill_') and value is not None and value >= min_value:
                skill_id = key
                skill_name = chinese_names.get(skill_id, skill_id)
                filtered_skills.append({
                    'id': skill_id,
                    'name': skill_name,
                    'value': value
                })

        # 按技能值降序排序
        filtered_skills.sort(key=lambda x: x['value'], reverse=True)
        return filtered_skills

    def get_skill_chinese_name(self, skill_id: str) -> str:
        """
        获取技能的中文名称

        :param skill_id: 技能ID
        :return: 技能中文名称，如果未找到返回原ID
        """
        logger.debug(f"[玩家服务] 查询技能中文名: skill_id={skill_id}")
        return self.repository.get_id(skill_id)

    def get_all_chinese_names(self) -> Dict[str, str]:
        """
        获取所有技能的中文名映射

        :return: 技能ID到中文名称的映射字典
        """
        sql = "SELECT id, name FROM chinese_name"
        results = self.repository.db.execute_query(sql)
        return {row['id']: row['name'] for row in results}


# 全局服务实例（延迟加载）
_player_service = None


def get_player_service() -> PlayerService:
    """获取玩家服务实例"""
    global _player_service
    if _player_service is None:
        _player_service = PlayerService()
    return _player_service
