"""
COC 技能模型
从原 agent/dice/model.py 提取的技能相关模型
"""

from pydantic import BaseModel, Field, ConfigDict, create_model


# 基础模型
class SkillBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., description="调查员ID")


# 动态创建技能字段
skill_fields = {
    f"skill_{i:03d}": (int | None, Field(default=None, description=f"技能 {i:03d} 数值"))
    for i in range(1, 109)
}

# 动态创建技能模型类
SkillsModel = create_model(
    'SkillsModel',
    __base__=SkillBase,
    **skill_fields
)
