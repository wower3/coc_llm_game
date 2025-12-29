# dice_mcp.py

from typing import Dict, Any, Optional

# Adjust imports to be absolute from the project structure
import dice.roll as roll
from dice.model import model
# from nonebot_plugin_orangedice import message # message is for formatting, not needed in core logic

class DiceService:
    """
    提供所有与骰子和角色卡相关的核心服务。
    每个方法都是一个独立的、可由LLM直接调用的工具。
    """

    def __init__(self):
        """
        初始化服务，未来可以用于注入数据库连接等依赖。
        """
        pass

    def roll_dice(self, expression: str, is_hidden: bool = False) -> Dict[str, Any]:
        """
        执行一个标准的骰子投掷表达式。

        例如，当用户说“丢个2d10+5”或“.r 2d10+5”时，LLM应调用此函数。

        :param expression: 骰子表达式字符串，例如 "2d10+5" 或 "3d6"。
        :param is_hidden: 是否为暗骰。如果是，结果应只对调用者可见。
        :return: 一个包含投掷结果和计算过程的字典。
                 例如: {'result': 15, 'process': '2d10(5, 10) + 5 = 15'}
        """
        try:
            messages,roll_result = roll.roll(expression)
            return {
                "success": True,
                "result": roll_result,
                "process": messages,
                "is_hidden": is_hidden,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def roll_attribute_check(self, user_id: str, attribute_name: str) -> Dict[str, Any]:
        """
        对用户的某个属性或技能进行检定（1d100）。

        例如，当用户说“进行一次力量检定”，“进行一次说服检定”，“.ra 力量”，“.ra 说服”等类似请求时，LLM应调用此函数。

        :param user_id: 执行检定的用户ID，用于查找角色卡。
        :param attribute_name: 要检定的属性或技能名称，例如 "力量", "侦查"，“图书馆使用”，“闪避”。
        :param target_value: (可选) 检定的目标值。如果未提供，将自动从用户的角色卡中查找。
        :return: 包含检定结果、目标值、成功等级的字典。
        """
        target_value = "0"
        if target_value == "0":
            # 1. 获取 Pydantic 对象
            player_obj = model.get_user_card(user_id)
            skill_obj = model.get_skill_card(user_id)
            
            # 2. 将对象转换为字典（model_dump 是 Pydantic V2 的标准方法）
            card_data = player_obj.model_dump()
            skill_data = skill_obj.model_dump()
            
            # 3. 获取转换后的英文 ID（例如 "力量" -> "strength"）
            attribute_id = model.get_id(attribute_name)
            
            # 4. 现在 card_data 是字典了，可以使用 'in' 进行判断
            if attribute_id in card_data and card_data[attribute_id] is not None:
                target_value = card_data[attribute_id]
            elif attribute_id in skill_data and skill_data[attribute_id] is not None:
                target_value = skill_data[attribute_id]
            else:
                # 如果都没有找到，设为默认值（CoC 默认通常是 0 或 1）
                target_value = 0

        messages,roll_result = roll.roll("1d100")

        # 判断成功等级 (这里的逻辑可以更复杂)
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
        """
        为用户执行一次理智检定（Sanity Check）。

        例如，当用户说“sc 1/1d6”或“对理智值进行检定，惩罚为1/1d6”时，LLM应解析出参数并调用此函数。

        :param user_id: 执行检定的用户ID。
        :param success_penalty: 检定成功时理智惩罚的骰子表达式, 例如 "1"。
        :param failure_penalty: 检定失败时理智惩罚的骰子表达式, 例如 "1d6"。
        :return: 包含检定结果、SAN值变化的详细字典。
        """
        player_obj = model.get_user_card(user_id)
        card_data = player_obj.model_dump()
        san_id = model.get_id("理智")
        if san_id is None:
            return {"success": False, "error": "角色卡中未找到理智属性"}
        current_san = card_data[san_id]

        messages,roll_result = roll.roll("1d100")
        is_success = roll_result <= current_san

        penalty_expr = success_penalty if is_success else failure_penalty
        messages_penalty,penalty_result = roll.roll(penalty_expr)
        san_loss = penalty_result

        new_san = current_san - san_loss
        flag = model.set_user_card(user_id, {san_id: new_san})

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

        例如，当用户说“st 力量50 敏捷60”时，LLM应将其解析为字典并调用此函数。

        :param user_id: 要设置角色卡的用户ID。
        :param attributes: 包含属性名和属性值的字典, 例如 {"力量": 50, "敏捷": 60}。
        :return: 操作结果的确认信息。
        """
        model.set_user_card(user_id, attributes)
        return {"success": True, "message": "角色卡已更新。"}

    def get_character_sheet(self, user_id: str) -> Dict[str, Any]:
        """
        获取指定用户的角色卡数据。

        :param user_id: 要查询的用户ID。
        :return: 包含角色卡所有属性的字典，如果找不到则返回错误信息。
        """
        card_data = model.get_user_card(user_id)
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
            # 这里的逻辑是从旧代码中提取或重写的
            str_val = roll.roll("3d6*5").get("total", 0)
            con_val = roll.roll("3d6*5").get("total", 0)
            siz_val = roll.roll("2d6+6*5").get("total", 0)
            dex_val = roll.roll("3d6*5").get("total", 0)
            app_val = roll.roll("3d6*5").get("total", 0)
            int_val = roll.roll("2d6+6*5").get("total", 0)
            pow_val = roll.roll("3d6*5").get("total", 0)
            edu_val = roll.roll("2d6+6*5").get("total", 0)
            sheets.append({
                "力量": str_val, "体质": con_val, "体型": siz_val,
                "敏捷": dex_val, "外貌": app_val, "智力": int_val,
                "意志": pow_val, "教育": edu_val,
                "理智": pow_val, "幸运": roll.roll("3d6*5").get("total", 0),
            })
        return {"success": True, "sheets": sheets}
