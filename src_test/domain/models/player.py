"""
COC 玩家角色模型
从原 agent/dice/model.py 提取的 Pydantic 模型
"""

import json
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from enum import Enum


class SexEnum(str, Enum):
    Male = "Male"
    Female = "Female"


class COCPlayerModel(BaseModel):
    """
    COC 7th版玩家角色模型 - 匹配数据库 players 表结构
    """
    # 配置：允许从数据库查询出的字典或类对象直接转换
    model_config = ConfigDict(from_attributes=True)

    # 主键与基本信息
    id: str = Field(..., description="用户唯一ID")
    year: int = Field(default=1920, description="时代背景年份")
    max_skill: int = Field(..., description="最大职业技能点")
    max_hobby_skill: int = Field(..., description="最大兴趣技能点")
    name: str = Field(..., description="调查员姓名")
    age: int = Field(..., description="年龄")
    sex: SexEnum = Field(..., description="性别")
    language: str = Field(..., description="母语")
    birth_place: Optional[str] = Field(None, description="出生地")
    live_place: Optional[str] = Field(None, description="现居地")

    # 核心属性 (Characteristics)
    strength: int = Field(..., description="力量 (STR)")
    constitution: int = Field(..., description="体质 (CON)")
    size: int = Field(..., description="体型 (SIZ)")
    dexterity: int = Field(..., description="敏捷 (DEX)")
    appearance: int = Field(..., description="外貌 (APP)")
    education: int = Field(..., description="教育 (EDU)")
    intelligence: int = Field(..., description="智力 (INT)")
    willpower: int = Field(..., description="意志 (POW)")
    luck: int = Field(..., description="幸运 (LUK)")

    # 派生属性 (Derived Attributes)
    damage_bonus: int = Field(default=0, description="伤害加值 (DB)")
    build: int = Field(default=0, description="体格 (Build)")
    movement: int = Field(default=0, description="移动速度 (MOV)")
    hit_points: int = Field(..., description="当前生命值 (HP)")
    magic_points: int = Field(..., description="当前魔法值 (MP)")
    sanity: int = Field(..., description="当前理智值 (SAN)")
    occupation_id: int = Field(..., description="职业编号")

    # 资产信息
    cash_amount: Decimal = Field(default=Decimal("0.00"), description="持有的现金")
    assets_amount: Decimal = Field(default=Decimal("0.00"), description="资产总额")
    credit_rating_spend: Decimal = Field(default=Decimal("0.00"), description="信用评级支出")

    # JSON 字段转换 (自动解析数据库中的 JSON 字符串为 Python 对象)
    skills: Optional[Dict[str, Any]] = Field(default=None, description="技能列表 (JSON)")
    weapons: Optional[List[Any]] = Field(default=None, description="武器列表 (JSON)")
    equipments: Optional[List[Any]] = Field(default=None, description="装备列表 (JSON)")
    notes: Optional[Union[Dict[str, Any], List[Any]]] = Field(default=None, description="备注信息 (JSON)")

    # 背景故事与描述 (TEXT / VARCHAR)
    personal_description: Optional[str] = Field(None, description="个人描述")
    beliefs: Optional[str] = Field(None, description="信念与宗教")
    traits: Optional[str] = Field(None, description="意识形态/思想特质")
    significant_people: Optional[str] = Field(None, description="重要人物")
    meaningful_locations: Optional[str] = Field(None, description="重要地点")
    treasured_possessions: Optional[str] = Field(None, description="珍视物品")
    injuries: Optional[str] = Field(None, description="伤痕与后遗症")
    phobias: Optional[str] = Field(None, description="恐惧症与狂躁症")
    encounters: Optional[str] = Field(None, description="第三类接触/遭遇经历")
    mythos: Optional[str] = Field(None, description="克苏鲁神话经验描述")
    relationships: Optional[str] = Field(None, description="社会关系")
    face_image_path: Optional[str] = Field(None, description="角色头像文件路径")

    # 【核心修复】添加校验器处理 JSON 字符串
    @field_validator('weapons', 'equipments', 'notes', 'skills', mode='before')
    @classmethod
    def decode_json_string(cls, v: Any) -> Any:
        # 如果输入是字符串且看起来像 JSON（以 [ 或 { 开头）
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return v
        return v


class ChineseNameModel(BaseModel):
    """技能 ID 与中文名称对应模型"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="技能ID")
    name: str = Field(..., description="技能中文名")


class WeaponModel(BaseModel):
    """COC 7th 版武器模型"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="武器ID")
    name: str = Field(..., description="名称")
    skill_used: str = Field(..., description="利用技能")
    damage: str = Field(..., description="伤害(如 1d6+db)")
    use_range: str = Field(..., description="射程")
    penetration: int = Field(..., description="穿刺次数")
    ammo_capacity: str = Field(..., description="装弹量")
    price_1920s: Optional[Decimal] = Field(None, description="价格 1920s($)")
    price_modern: Optional[Decimal] = Field(None, description="价格 现代($)")
    malfunction_rating: int = Field(..., description="故障值")
    common_era: str = Field(..., description="常见时代")
