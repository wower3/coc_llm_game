"""
场景管理服务
从原 agent/agentService/service_mcp.py 提取
"""

import uuid
import os
from typing import Optional

from src_test.domain.models import SceneInfo
from src_test.infrastructure.file import TxtKeywordSearch
from src_test.infrastructure.log import get_logger

logger = get_logger("SCENE")


# 获取项目根目录下的scenes文件夹
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_SCENES_DIR = os.path.join(PROJECT_ROOT, "scenes")

# 基础提示词模板
SCENE_PROMPT = """
你是一个克苏鲁神话角色扮演游戏(CoC)的智能游戏主持人(GM)，需要引导玩家以沉浸式游戏的氛围，根据当前剧本进行文字游戏。

如有需要，使用以下mcp工具来协助玩家：

1. **骰子投掷 请调用"roll_dice_tool"工具:**:
- 当玩家需要投掷骰子时使用，例如"投掷2d10+5"或"r 1d100"
- 支持标准的骰子表达式，如"1d6"、"2d10+5"、"3d6*5"等
- 可以进行暗骰(is_hidden=True)，结果不对玩家显示

2. **属性或技能检定 请调用"roll_attribute_check_tool"工具:
- 当玩家需要进行属性或技能检定时（例如"进行力量检定","进行说服检定"，".ra 侦查"等表述）使用，使用"roll_attribute_check_tool"工具
- 需要提供玩家ID和属性或技能名称
- 调用该工具前需要向玩家进行确认，在得到玩家的允许后才调用该工具

3. **理智检定 请调用"roll_sanity_check_tool"工具**:
- 当玩家角色需要进行理智检定时使用，例如"sc 1/1d6"（表示检定成功时理智惩罚的骰子表达式为"1",失败时理智惩罚的骰子表达式为"1d6"）
- 需要提供玩家ID以及成功和失败时的理智损失表达式
- 调用该工具前需要向玩家进行确认

在场景中，请遵循以下守则：
- 你是一名游戏的主持人
- 将玩家视为参与该剧本的调查员，而不是剧本外拥有上帝视角的人，根据剧本内容引导玩家，不要一次性给出太多信息，给玩家的信息应当是玩家作为剧本的调查员亲身看到的，听到的，接触到的信息
- 涉及到npc和玩家进行对话时,确保玩家和npc的对话是相互式的，必要时你可以扮演该npc与玩家进行对话
- 描述场景时注重氛围和细节，尽可能给出沉浸式的描述，使玩家身临其境，引导玩家探索场景中的线索，根据玩家的行动推进剧情，已经推进完成或错过的剧情不要再次进行
- 理解玩家的意图并选择合适的工具
- 拒绝玩家进行上帝视角的操作（拒绝玩家直接询问还没进行到的剧情，玩家的技能，属性检定必须调用工具，不能跳过检定工具直接要求检定成功）
- 给玩家返回信息时，注意不要返回玩家不应该知道的信息（例如不能出现，玩家还没有检定就能知道每个检定成功或失败后对应剧情的发展）
- 你的所有输出内容都要基于剧本（即在剧本中能找到根据，而不是随意输出的）
"""


class ThreadManager:
    """线程管理器"""

    def __init__(self, scenes_dir: str = None):
        if scenes_dir is None:
            scenes_dir = DEFAULT_SCENES_DIR
        self.main_thread_id = str(uuid.uuid4())
        self.current_thread_id = self.main_thread_id
        self.scene_stack: list[SceneInfo] = []
        self.scenes_dir = scenes_dir
        self.txt_search = TxtKeywordSearch(scenes_dir)
        self.main_prompt = self._load_main_prompt()
        # 主场景名称
        self.main_scene_name = "开始场景"
        # 场景进入次数限制
        self.scene_limits: dict[str, int] = {}
        self.entered_count: dict[str, int] = {}
        self._load_scene_limits()

    def _load_main_prompt(self) -> str:
        """加载主线程提示词"""
        main_prompt_file = os.path.join(self.scenes_dir, "开始-连接-结尾.txt")
        try:
            with open(main_prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return SCENE_PROMPT + f"\n【主线剧本内容】\n{content}"
        except FileNotFoundError:
            return SCENE_PROMPT

    def _load_scene_limits(self):
        """从 scenes.txt 加载场景进入次数限制"""
        scenes_file = os.path.join(self.scenes_dir, "scenes.txt")
        self.scene_limits = {}
        try:
            with open(scenes_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if ':' in line:
                        scene, limit = line.split(':', 1)
                        self.scene_limits[scene.strip()] = int(limit.strip())
        except FileNotFoundError:
            pass  # 如果文件不存在，使用空字典

    @property
    def in_scene(self) -> bool:
        return len(self.scene_stack) > 0

    @property
    def current_scene(self) -> str:
        return self.scene_stack[-1].scene_name if self.scene_stack else ""

    @property
    def scene_depth(self) -> int:
        return len(self.scene_stack)

    def get_scene_path(self) -> str:
        if not self.scene_stack:
            return "主线程"
        return " -> ".join([s.scene_name for s in self.scene_stack])

    def get_available_scenes(self, ai_returned: list[str] = None) -> list[str]:
        """
        获取可进入的场景列表
        规则：在 AI 返回的列表中 且 在 scene_limits 中 且 已进入次数 < 可进入次数

        :param ai_returned: AI通过select_scene工具返回的场景列表，如果为None则返回所有满足次数限制的场景
        """
        available = []
        for scene, limit in self.scene_limits.items():
            entered = self.entered_count.get(scene, 0)
            # 检查次数限制
            if entered < limit:
                # 如果提供了AI返回的列表，则只返回该列表中的场景
                if ai_returned is None or scene in ai_returned:
                    available.append(scene)
        return available

    def reset_progress(self):
        """重置场景进度（重置记忆时调用）"""
        self.scene_stack.clear()
        self.entered_count.clear()
        self.current_thread_id = self.main_thread_id

    def _load_scene_content(self, scene: str) -> str:
        """从txt文件加载场景内容"""
        for root, dirs, files in os.walk(self.scenes_dir):
            for file in files:
                if file.endswith('.txt') and scene in file:
                    file_path = os.path.join(root, file)
                    content = self.txt_search.loader.read_txt_file(file_path)
                    if content:
                        return content
        return f"（未找到场景文件 '{scene}'）"

    def enter_scene(self, scene: str) -> tuple[str, str]:
        """进入新场景，增加进入次数"""
        logger.info(f"[场景] 尝试进入场景: {scene}")

        # 验证场景是否存在
        if scene not in self.scene_limits:
            logger.error(f"[场景] 无效的场景: {scene}")
            raise ValueError(f"无效的场景：{scene}")

        # 检查进入次数限制
        entered = self.entered_count.get(scene, 0)
        if entered >= self.scene_limits[scene]:
            logger.warning(f"[场景] 场景进入次数已达上限: {scene}")
            raise ValueError(f"场景进入次数已达上限：{scene}")

        # 增加进入次数
        self.entered_count[scene] = entered + 1

        # 原有逻辑：进入场景
        new_thread_id = str(uuid.uuid4())
        scene_content = self._load_scene_content(scene)
        new_prompt = SCENE_PROMPT + f"\n当前场景：{scene}\n{scene_content}"
        scene_info = SceneInfo(scene, new_thread_id, new_prompt)
        self.scene_stack.append(scene_info)
        self.current_thread_id = new_thread_id
        logger.info(f"[场景] 成功进入场景: {scene}, 新线程ID: {new_thread_id[:8]}, 当前深度: {self.scene_depth}")
        return new_thread_id, scene_content

    def exit_scene(self) -> tuple[str, str, str]:
        """退出当前场景"""
        logger.info(f"[场景] 尝试退出场景，当前深度: {self.scene_depth}")
        if not self.scene_stack:
            logger.warning("[场景] 当前不在任何场景中")
            return ("", self.main_scene_name, self.main_thread_id)
        exited_scene = self.scene_stack.pop()
        if self.scene_stack:
            parent = self.scene_stack[-1]
            self.current_thread_id = parent.thread_id
            logger.info(f"[场景] 退出场景: {exited_scene.scene_name}, 返回: {parent.scene_name}, 新深度: {self.scene_depth}")
            return (exited_scene.scene_name, parent.scene_name, parent.thread_id)
        self.current_thread_id = self.main_thread_id
        logger.info(f"[场景] 退出场景: {exited_scene.scene_name}, 返回: {self.main_scene_name}")
        return (exited_scene.scene_name, self.main_scene_name, self.main_thread_id)

    def get_current_prompt(self) -> str:
        """获取当前提示词"""
        return self.scene_stack[-1].prompt if self.scene_stack else self.main_prompt


class McpService:
    """MCP服务"""

    def __init__(self, thread_manager: ThreadManager = None):
        self.thread_manager = thread_manager

    def new_scene(self, scene: str) -> str:
        if self.thread_manager is None:
            return "线程管理器未初始化"
        self.thread_manager.enter_scene(scene)
        return f"已进入场景：{scene}"

    def exit_scene(self) -> str:
        if self.thread_manager is None:
            return "线程管理器未初始化"
        if not self.thread_manager.in_scene:
            return "当前不在任何场景中"
        exited, return_to, _ = self.thread_manager.exit_scene()
        return f"已退出：{exited}，返回：{return_to}"
    
    def select_scene(self, scenes: str) -> list[str]:
        """将场景字符串以空格分隔符拆分成列表"""
        if not scenes or not scenes.strip():
            return []
        return scenes.strip().split()

    def exit_scene_with_agent(self, exited_scene: str, return_scene: str, thread_messages: list = None) -> str:
        """
        退出场景并调用模型生成场景总结

        :param exited_scene: 退出的场景名称
        :param return_scene: 返回的场景名称
        :param thread_messages: 当前场景的对话历史
        :return: 模型生成的响应文本
        """
        from langchain.messages import HumanMessage, SystemMessage, AIMessage
        from src_test.service.single_agent_service import model as summary_model

        logger.info(f"[场景] 调用场景总结模型，退出场景: {exited_scene} -> {return_scene}")

        # 构建消息列表
        messages = []

        # 添加空的系统提示词 TODO
        messages.append(SystemMessage(content=f"""指令： 
                                      我结束了在{exited_scene}的调查。请代入我的角色，用 1-2 句话向主场景的 Agent 汇报我的经历。 
                                      过滤原则： 删掉所有细节信息和过程信息，只保留我在{exited_scene}场景中解决了什么问题、或知道了什么秘密，或达成了什么重要成就。 
                                      示例1： “我在“{exited_scene}”场景中，得知了艾利亚教堂的主教其实是个黄衣之王的信徒。”
                                      示例2： “我在“{exited_scene}”场景完成了一场战斗，该场景中的邪教徒被我杀死了2个，逃走了1个。”
                                      示例3： “我在“{exited_scene}”场景经过不断的探索，发现了xxx这个重要的线索，得到了yyy这个重要的物品。”"""))

        # 添加对话历史
        if thread_messages:
            logger.debug(f"[场景] 开始添加 {len(thread_messages)} 条对话历史:")
            for i, msg in enumerate(thread_messages):
                messages.append(msg)
                # 记录每条消息的详细内容
                msg_type = type(msg).__name__
                if hasattr(msg, 'content'):
                    content = msg.content
                    # 截断过长的内容以便日志查看
                    content_preview = content[:10] + "..." if len(content) > 10 else content
                    logger.debug(f"[场景]   消息 {i+1}: [{msg_type}] {content_preview}")
                else:
                    logger.debug(f"[场景]   消息 {i+1}: [{msg_type}] (无 content 属性)")
        else:
            # 如果没有对话历史，添加默认提示
            messages.append(HumanMessage(content=f"玩家从场景「{exited_scene}」退回到场景「{return_scene}」。"))

        try:
            logger.debug(f"[场景] 开始调用模型，消息数量: {len(messages)}")

            # 使用非流式调用（model 直接调用，不需要 {"messages": ...} 格式）
            response = summary_model.invoke(messages)

            logger.debug(f"[场景] 模型返回，响应类型: {type(response)}")

            # 提取响应内容（model.invoke 返回 AIMessage 对象）
            content = ""
            if isinstance(response, AIMessage):
                content = response.content
            elif hasattr(response, 'content'):
                content = str(response.content)
            else:
                content = str(response)

            logger.info(f"[场景] 场景总结响应: {content[:100] if content else '(empty)'}...")
            return content if content else f"你离开了{exited_scene}，回到了{return_scene}。"
        except Exception as e:
            logger.error(f"[场景] 场景总结模型调用失败: {e}", exc_info=True)
            # 返回默认描述
            return f"你离开了{exited_scene}，回到了{return_scene}。" 