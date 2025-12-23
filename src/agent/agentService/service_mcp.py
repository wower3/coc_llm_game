from typing import Dict, Any, Optional
import uuid
import dice.roll as roll
from dice.model import model
from load_txt_with_keyword import TxtKeywordSearch


# 场景信息数据类
class SceneInfo:
    """存储场景信息"""
    def __init__(self, scene_name: str, thread_id: str, prompt: str):
        self.scene_name = scene_name
        self.thread_id = thread_id
        self.prompt = prompt


# 主提示词模板
MAIN_PROMPT = """
你是一个克苏鲁神话角色扮演游戏(CoC)的智能游戏主持人(GM)，能够帮助玩家进行各种骰子投掷和角色管理。

在对话过程中，请遵循以下规则：
- 理解玩家的意图并选择合适的工具
- 准确提取必要的参数
- 清晰地解释骰子结果和检定含义
- 保持克苏鲁神话的氛围和风格

请记住，你是玩家在神秘和危险的克苏鲁世界中的骰子智能体，你的职责是确保骰子结果符合规则，不需要进行太多的延申。
"""


def get_scene_prompt(scene: str, scene_content: str) -> str:
    """
    根据场景名称和内容生成场景特定的提示词

    :param scene: 场景名称
    :param scene_content: 从txt文件读取的场景内容
    :return: 完整的场景提示词
    """
    return f"""
            你是一个克苏鲁神话角色扮演游戏(CoC)的智能游戏主持人(GM)。

            如有需要，使用以下mcp工具来协助玩家：

            1. **骰子投掷 请调用"roll_dice_tool"工具:**:
            - 当玩家需要投掷骰子时使用，例如"投掷2d10+5"或"r 1d100"
            - 支持标准的骰子表达式，如"1d6"、"2d10+5"、"3d6*5"等
            - 可以进行暗骰(is_hidden=True)，结果只对指定玩家显示

            2. **属性或技能检定 请调用"roll_attribute_check_tool"工具:
            - 当玩家需要进行属性或技能检定时（例如"进行力量检定"或".ra 侦查"）使用，使用"roll_attribute_check_tool"工具
            - 需要提供玩家ID和属性或技能名称
            - 目标值target_value未提供时不需要该传参。

            3. **理智检定 请调用“roll_sanity_check_tool”工具**:
            - 当玩家角色需要进行理智检定时使用，例如"sc 1/1d6"（表示检定成功时理智惩罚的骰子表达式为"1",失败时理智惩罚的骰子表达式为"1d6"）
            - 需要提供玩家ID以及成功和失败时的理智损失表达式

            4. **进入新场景 请调用“new_scene”工具**:
            - 当剧本涉及到进入新场景时，根据玩家选择的调查方向调用new_scene，传入的参数为场景名称

            5. **退出当前场景 请调用"exit_scene工具"：
            - 当场景探索完成或玩家要求离开时，请调用 exit_scene 工具返回上一个场景。

            当前场景：{scene}

            【场景剧本内容】
            {scene_content}

            在此场景中，请：
            - 根据上述剧本内容引导玩家，不要一次性给出太多信息，需要玩家逐渐探索场景中包含的内容,确保玩家和npc的对话是相互式的
            - 专注于描述当前场景的氛围和细节，引导玩家探索场景中的线索，根据玩家的行动推进剧情
            - 理解玩家的意图并选择合适的工具
            - 拒绝玩家进行上帝视角的操作（拒绝玩家直接询问还没进行到的剧情，玩家的技能，属性检定必须调用工具）
            """


# 全局状态管理器（使用栈管理嵌套场景）
class ThreadManager:
    def __init__(self, scenes_dir: str = "./scenes/chapter1"):
        self.main_thread_id = str(uuid.uuid4())
        self.current_thread_id = self.main_thread_id
        # 场景栈：支持嵌套场景
        self.scene_stack: list[SceneInfo] = []
        # 场景文件搜索目录
        self.scenes_dir = scenes_dir
        # txt搜索器
        self.txt_search = TxtKeywordSearch(scenes_dir)
        # 加载主线程提示词
        self.main_prompt = self._load_main_prompt()

    def _load_main_prompt(self) -> str:
        """
        从文件加载主线程提示词

        :return: 主线程提示词内容
        """
        import os
        main_prompt_file = os.path.join(self.scenes_dir, "开始-连接-结尾.txt")
        try:
            with open(main_prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"""
                    你是一个克苏鲁神话角色扮演游戏(CoC)的智能游戏主持人(GM)。
            
                    如有需要，使用以下mcp工具来协助玩家：

                    1. **骰子投掷 请调用"roll_dice_tool"工具:**:
                    - 当玩家需要投掷骰子时使用，例如"投掷2d10+5"或"r 1d100"
                    - 支持标准的骰子表达式，如"1d6"、"2d10+5"、"3d6*5"等
                    - 可以进行暗骰(is_hidden=True)，结果只对指定玩家显示

                    2. **属性或技能检定 请调用"roll_attribute_check_tool"工具:
                    - 当玩家需要进行属性或技能检定时（例如"进行力量检定"或".ra 侦查"）使用，使用"roll_attribute_check_tool"工具
                    - 需要提供玩家ID和属性或技能名称
                    - 目标值target_value未提供时不需要该传参。

                    3. **理智检定 请调用“roll_sanity_check_tool”工具**:
                    - 当玩家角色需要进行理智检定时使用，例如"sc 1/1d6"（表示检定成功时理智惩罚的骰子表达式为"1",失败时理智惩罚的骰子表达式为"1d6"）
                    - 需要提供玩家ID以及成功和失败时的理智损失表达式

                    4. **进入新场景 请调用“new_scene”工具**:
                    - 当剧本涉及到进入新场景时，根据玩家选择的调查方向调用new_scene，传入的参数为场景名称


                    【主线剧本内容】
                    {content}

                    在主线程中，请：
                    - 根据上述剧本内容引导玩家，不要一次性给出太多信息，需要玩家逐渐探索场景中包含的内容,确保玩家和npc的对话是相互式的
                    - 理解玩家的意图并选择合适的工具
                    - 保持克苏鲁神话的氛围和风格
                    - - 拒绝玩家进行上帝视角的操作（拒绝玩家直接询问还没进行到的剧情，玩家的技能，属性检定必须调用工具）
                    """
        except FileNotFoundError:
            return MAIN_PROMPT

    @property
    def in_scene(self) -> bool:
        """是否在场景中"""
        return len(self.scene_stack) > 0

    @property
    def current_scene(self) -> str:
        """当前场景名称"""
        if self.scene_stack:
            return self.scene_stack[-1].scene_name
        return ""

    @property
    def scene_depth(self) -> int:
        """当前场景深度"""
        return len(self.scene_stack)

    def get_scene_path(self) -> str:
        """获取场景路径（用于显示嵌套层级）"""
        if not self.scene_stack:
            return "主线程"
        return " -> ".join([s.scene_name for s in self.scene_stack])

    def _load_scene_content(self, scene: str) -> str:
        """
        从txt文件加载场景内容

        :param scene: 场景关键词
        :return: 场景内容文本
        """
        results = self.txt_search.search_files(scene, recursive=True)
        scene_content = ""
        for result in results:
            if result['matches']:
                match = result['matches'][0]
                scene_content = match
                break

        if not scene_content:
            scene_content = f"（未找到场景 '{scene}' 的详细内容，请根据场景名称自由发挥）"

        return scene_content

    def enter_scene(self, scene: str) -> tuple[str, str]:
        """
        进入新场景，将场景压入栈

        :param scene: 场景名称/关键词
        :return: (新线程ID, 场景内容)
        """
        new_thread_id = str(uuid.uuid4())

        # 从txt文件加载场景内容
        scene_content = self._load_scene_content(scene)

        # 生成场景提示词
        new_prompt = get_scene_prompt(scene, scene_content)

        # 创建场景信息并压入栈
        scene_info = SceneInfo(scene, new_thread_id, new_prompt)
        self.scene_stack.append(scene_info)

        # 更新当前线程ID
        self.current_thread_id = new_thread_id
        return new_thread_id, scene_content

    def exit_scene(self) -> tuple[str, str, str]:
        """
        退出当前场景，从栈中弹出

        :return: (退出的场景名, 返回到的场景名/主线程, 新的线程ID)
        """
        if not self.scene_stack:
            return ("", "主线程", self.main_thread_id)

        # 弹出当前场景
        exited_scene = self.scene_stack.pop()

        # 确定返回到哪里
        if self.scene_stack:
            # 返回到上一个场景
            parent_scene = self.scene_stack[-1]
            self.current_thread_id = parent_scene.thread_id
            return (exited_scene.scene_name, parent_scene.scene_name, parent_scene.thread_id)
        else:
            # 返回到主线程
            self.current_thread_id = self.main_thread_id
            return (exited_scene.scene_name, "主线程", self.main_thread_id)

    def get_current_prompt(self) -> str:
        """获取当前应使用的提示词"""
        if self.scene_stack:
            return self.scene_stack[-1].prompt
        return self.main_prompt


class McpService:
    """
    提供所有与骰子和角色卡相关的核心服务。
    每个方法都是一个独立的、可由LLM直接调用的工具。
    """

    def __init__(self, thread_manager: ThreadManager = None):
        """
        初始化服务

        :param thread_manager: 线程管理器实例，用于管理场景和记忆
        """
        self.thread_manager = thread_manager

    def new_scene(self, scene: str) -> str:
        """
        进入新的场景。

        :param scene: 场景关键词
        :return: 场景进入确认信息
        """
        if self.thread_manager is None:
            # 兼容旧逻辑：直接返回场景内容
            search = TxtKeywordSearch("./scenes/chapter1")
            results = search.search_files(scene, recursive=True)
            drama = ""
            for result in results:
                if result['matches']:
                    match = result['matches'][0]
                    drama = match
                    break
            return drama

        # 使用线程管理器进入场景
        new_thread_id, scene_content = self.thread_manager.enter_scene(scene)
        depth = self.thread_manager.scene_depth

        return (
            f"已进入场景：{scene}（深度: {depth}）。\n"
            f"新的记忆线程已创建（ID: {new_thread_id[:8]}...）。\n"
            f"场景路径: {self.thread_manager.get_scene_path()}\n"
            f"---\n"
            f"场景内容已加载。"
        )

    def exit_scene(self) -> str:
        """
        退出当前场景，返回上一个场景或主线程。

        :return: 退出确认信息
        """
        if self.thread_manager is None:
            return "线程管理器未初始化。"

        if not self.thread_manager.in_scene:
            return "当前不在任何场景中。"

        exited_scene, return_to, new_thread_id = self.thread_manager.exit_scene()

        return (
            f"已退出场景：{exited_scene}。\n"
            f"已返回到：{return_to}（线程ID: {new_thread_id[:8]}...）。\n"
            f"当前场景路径: {self.thread_manager.get_scene_path()}"
        )
