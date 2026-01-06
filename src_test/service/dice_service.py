"""
骰子服务
从原 agent/dice/dice_mcp.py 提取
"""

from typing import Dict, Any

from src_test.domain.dice import roll
from src_test.infrastructure.database import get_repository
from src_test.infrastructure.log import get_logger

logger = get_logger("DICE")


class DiceService:
    """骰子和角色卡相关的核心服务"""

    def __init__(self, repository=None):
        self.repository = repository or get_repository()

    def roll_dice(self, expression: str, is_hidden: bool = False) -> Dict[str, Any]:
        """执行骰子投掷"""
        logger.debug(f"[骰子] 开始投掷: {expression}, 暗骰: {is_hidden}")
        try:
            messages, roll_result = roll(expression)
            result = {
                "success": True,
                "result": roll_result,
                "process": messages,
                "is_hidden": is_hidden,
            }
            logger.info(f"[骰子] 投掷成功: {expression} = {roll_result}, 过程: {messages}")
            return result
        except Exception as e:
            logger.error(f"[骰子] 投掷失败: {expression}, 错误: {str(e)}")
            return {"success": False, "error": str(e)}

    def roll_attribute_check(self, user_id: str, attribute_name: str) -> Dict[str, Any]:
        """属性或技能检定"""
        logger.info(f"[骰子] 属性检定: 用户={user_id}, 属性={attribute_name}")
        player_obj = self.repository.get_user_card(user_id)
        skill_obj = self.repository.get_skill_card(user_id)
        card_data = player_obj.model_dump()
        skill_data = skill_obj.model_dump()
        attribute_id = self.repository.get_id(attribute_name)

        target_value = 0
        if attribute_id in card_data and card_data[attribute_id] is not None:
            target_value = card_data[attribute_id]
        elif attribute_id in skill_data and skill_data[attribute_id] is not None:
            target_value = skill_data[attribute_id]

        messages, roll_result = roll("1d100")

        success_level = "失败"
        if roll_result <= target_value:
            success_level = "成功"
        if roll_result <= target_value / 2:
            success_level = "困难成功"
        if roll_result <= target_value / 5:
            success_level = "极限成功"
        if roll_result == 1:
            success_level = "大成功"
        if roll_result == 99:
            success_level = "大失败"

        result = {
            "属性名": attribute_name,
            "属性值": target_value,
            "骰子值": roll_result,
            "结果": success_level,
        }
        logger.info(f"[骰子] 属性检定结果: {attribute_name}({target_value}) = {roll_result} ({success_level})")
        return result

    def roll_sanity_check(self, user_id: str, success_penalty: str, failure_penalty: str) -> Dict[str, Any]:
        """理智检定"""
        logger.info(f"[骰子] 理智检定: 用户={user_id}, 成功惩罚={success_penalty}, 失败惩罚={failure_penalty}")
        player_obj = self.repository.get_user_card(user_id)
        card_data = player_obj.model_dump()
        san_id = self.repository.get_id("理智")
        if san_id is None:
            logger.error(f"[骰子] 角色卡中未找到理智属性")
            return {"success": False, "error": "角色卡中未找到理智属性"}
        current_san = card_data[san_id]

        messages, roll_result = roll("1d100")
        is_success = roll_result <= current_san

        penalty_expr = success_penalty if is_success else failure_penalty
        messages_penalty, penalty_result = roll(penalty_expr)
        san_loss = penalty_result

        new_san = current_san - san_loss
        flag = self.repository.set_user_card(user_id, {san_id: new_san})

        result = {
            "success": flag,
            "check_result": "成功" if is_success else "失败",
            "current_san": current_san,
            "san_loss": san_loss,
            "penalty_process": messages_penalty,
            "new_san": new_san
        }
        logger.info(f"[骰子] 理智检定结果: {current_san} -> {roll_result} ({'成功' if is_success else '失败'}), 损失: {san_loss}, 新SAN: {new_san}")
        return result
