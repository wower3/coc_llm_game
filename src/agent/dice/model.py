"""
一系列暴力的数据库操作
使用 MySQL 数据库连接，配置信息从 .env 文件读取
"""

import json
import os
import pymysql
from pydantic import BaseModel, Field, ConfigDict, create_model, field_validator
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from enum import Enum
from enum import Enum
from dotenv import load_dotenv
from pathlib import Path
import pymysql


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


# 基础模型
class SkillBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., description="调查员ID")

# 修正：直接使用类型对象，避免在字典中使用复杂的表达式
# 使用 (type, default_value) 的元组格式
skill_fields = {
    f"skill_{i:03d}": (int | None, Field(default=None, description=f"技能 {i:03d} 数值"))
    for i in range(1, 109)
}

# 动态创建类
SkillsModel = create_model(
    'SkillsModel',
    __base__=SkillBase,
    **skill_fields
)


class DataContainer:

    def __init__(self) -> None:
        # 加载 .env 文件
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(env_path, override=True)

        # 从环境变量获取数据库配置
        self.host = os.getenv('HOST')
        self.user = os.getenv('USER')
        self.mysql_pw = os.getenv('MYSQL_PW')
        self.db = os.getenv('DB_NAME')
        self.port = os.getenv('PORT')

        if not all([self.host, self.user, self.mysql_pw, self.db, self.port]):
            raise ValueError("数据库配置不完整，请检查 .env 文件")

    def _get_connection(self):
        """统一获取数据库连接的逻辑"""
        return pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.mysql_pw,
            db=self.db,
            port=int(self.port),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor  # 关键：返回字典格式
        )

    def _execute_query(self, sql_query: str) -> List[Dict[str, Any]]:
        """执行 SQL 查询并返回字典列表"""
        try:
            connection = self._get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(sql_query)
                    return cursor.fetchall()  # 返回的是 [{}, {}]
            finally:
                connection.close()
        except Exception as e:
            print(f"数据库查询错误: {e}")
            return []

    def _execute_update(self, sql_query: str) -> bool:
        """执行 SQL 更新操作"""
        try:
            connection = self._get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(sql_query)
                connection.commit()
                return True
            except Exception as e:
                connection.rollback()
                print(f"数据库更新错误: {e}")
                return False
            finally:
                connection.close()
        except Exception as e:
            print(f"数据库连接错误: {e}")
            return False

    def get_user_card(self, user_id: str) -> COCPlayerModel:
        """获取玩家卡片信息，返回 Pydantic 模型"""
        sql_query = f"SELECT * FROM players WHERE id = '{user_id}'"
        results = self._execute_query(sql_query)

        if results:
            # 直接使用 Pydantic 验证并转换
            return COCPlayerModel.model_validate(results[0])
        
        # 如果没查到，返回带 ID 的默认模型
        return COCPlayerModel(id=user_id)
    
    def set_user_card(self, user_id: str, update_data: dict) -> bool:
        """
        动态更新玩家卡片信息
        :param user_id: 玩家ID
        :param update_data: 需要更新的键值对，例如 {"sanity": 40, "skills": {"侦查": 50}}
        """
        if not update_data:
            return False

        set_clauses = []
        
        for key, value in update_data.items():
            # 1. 处理 JSON 字段 (根据你的表结构，这些字段需要转为 JSON 字符串)
            if key in ['skills', 'weapons', 'equipments', 'notes'] and isinstance(value, (dict, list)):
                formatted_value = f"'{json.dumps(value, ensure_ascii=False)}'"
            
            # 2. 处理字符串字段 (加单引号，并处理内部单引号防止报错)
            elif isinstance(value, str):
                safe_val = value.replace("'", "''") # 简单的 SQL 转义
                formatted_value = f"'{safe_val}'"
            
            # 3. 处理空值
            elif value is None:
                formatted_value = "NULL"
                
            # 4. 处理数值 (int, float, decimal)
            else:
                formatted_value = str(value)
                
            set_clauses.append(f"`{key}` = {formatted_value}")

        # 拼接完整的 SQL
        sql_query = f"UPDATE players SET {', '.join(set_clauses)} WHERE id = '{user_id}'"
        
        # 调用你已有的方法
        return self._execute_update(sql_query)

    def get_skill_card(self, user_id: str) -> 'SkillsModel': # type: ignore
        """获取玩家技能卡片信息"""
        sql_query = f"SELECT * FROM skills WHERE id = '{user_id}'"
        results = self._execute_query(sql_query)

        if results:
            # 这里的 SkillsModel 是你之前动态创建或定义的那个模型
            return SkillsModel.model_validate(results[0])
        
        return SkillsModel(id=user_id)

    def get_id(self, attribute_name: str) -> str:
        """根据中文名获取属性/技能的 ID (例如 '力量' -> 'strength')"""
        # 注意安全：防止简单的注入，虽然在跑团场景通常还好
        sql_query = f"SELECT id FROM chinese_name WHERE name = '{attribute_name}' LIMIT 1"
        results = self._execute_query(sql_query)
        
        if results:
            return str(results[0]['id'])
        
        # 如果找不到映射，原样返回（可能它本身就是 ID）
        return attribute_name

# 全局实例
model = DataContainer()