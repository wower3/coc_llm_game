"""
Domain Layer - 领域层

包含业务领域模型和核心业务逻辑：
- models: 数据模型（玩家、技能、场景等）
- dice: 骰子投掷系统
"""

# 导入所有领域模块
from src_test.domain.models import (
    COCPlayerModel,
    ChineseNameModel,
    WeaponModel,
    SexEnum,
    SkillsModel,
    SkillBase,
    SceneInfo
)
from src_test.domain.dice import roll

__all__ = [
    # Models
    'COCPlayerModel',
    'ChineseNameModel',
    'WeaponModel',
    'SexEnum',
    'SkillsModel',
    'SkillBase',
    'SceneInfo',
    # Dice
    'roll',
]
