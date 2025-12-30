"""
骰子服务
从原 agent/dice/dice_mcp.py 提取
"""

from typing import Dict, Any

from src_test.domain.dice import roll
from src_test.infrastructure.database import get_repository


class DiceService:
    """骰子和角色卡相关的核心服务"""

    def __init__(self, repository=None):
        self.repository = repository or get_repository()

    def roll_dice(self, expression: str, is_hidden: bool = False) -> Dict[str, Any]:
        """执行骰子投掷"""
        try:
            messages, roll_result = roll(expression)
            return {
                "success": True,
                "result": roll_result,
                "process": messages,
                "is_hidden": is_hidden,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def roll_attribute_check(self, user_id: str, attribute_name: str) -> Dict[str, Any]:
        """属性或技能检定"""
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

        return {
            "属性名": attribute_name,
            "属性值": target_value,
            "骰子值": roll_result,
            "结果": success_level,
        }

    def roll_sanity_check(self, user_id: str, success_penalty: str, failure_penalty: str) -> Dict[str, Any]:
        """理智检定"""
        player_obj = self.repository.get_user_card(user_id)
        card_data = player_obj.model_dump()
        san_id = self.repository.get_id("理智")
        if san_id is None:
            return {"success": False, "error": "角色卡中未找到理智属性"}
        current_san = card_data[san_id]

        messages, roll_result = roll("1d100")
        is_success = roll_result <= current_san

        penalty_expr = success_penalty if is_success else failure_penalty
        messages_penalty, penalty_result = roll(penalty_expr)
        san_loss = penalty_result

        new_san = current_san - san_loss
        flag = self.repository.set_user_card(user_id, {san_id: new_san})

        return {
            "success": flag,
            "check_result": "成功" if is_success else "失败",
            "current_san": current_san,
            "san_loss": san_loss,
            "penalty_process": messages_penalty,
            "new_san": new_san
        }

    def set_character_attributes(self, user_id: str, attributes: Dict[str, int]) -> Dict[str, Any]:
        """
        创建或更新用户的角色卡属性。

        :param user_id: 要设置角色卡的用户ID。
        :param attributes: 包含属性名和属性值的字典, 例如 {"力量": 50, "敏捷": 60}。
        :return: 操作结果的确认信息。
        """
        self.repository.set_user_card(user_id, attributes)
        return {"success": True, "message": "角色卡已更新。"}

    def get_character_sheet(self, user_id: str) -> Dict[str, Any]:
        """
        获取指定用户的角色卡数据。

        :param user_id: 要查询的用户ID。
        :return: 包含角色卡所有属性的字典，如果找不到则返回错误信息。
        """
        card_data = self.repository.get_user_card(user_id)
        if not card_data:
            return {"success": False, "error": "未找到该用户的角色卡。"}
        return {"success": True, "data": card_data}

    def generate_coc_character_sheet(self, count: int = 1) -> Dict[str, Any]:
        """
        随机生成一张或多张COC角色卡的核心属性。

        :param count: 要生成的角色卡数量，默认为1。
        :return: 包含生成的多张角色卡数据的列表。
        """
        sheets = []
        for _ in range(count):
            _, str_val = roll("3d6*5")
            _, con_val = roll("3d6*5")
            _, siz_val = roll("2d6+6*5")
            _, dex_val = roll("3d6*5")
            _, app_val = roll("3d6*5")
            _, int_val = roll("2d6+6*5")
            _, pow_val = roll("3d6*5")
            _, edu_val = roll("2d6+6*5")
            _, luck_val = roll("3d6*5")
            sheets.append({
                "力量": str_val, "体质": con_val, "体型": siz_val,
                "敏捷": dex_val, "外貌": app_val, "智力": int_val,
                "意志": pow_val, "教育": edu_val,
                "理智": pow_val, "幸运": luck_val,
            })
        return {"success": True, "sheets": sheets}
