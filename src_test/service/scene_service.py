"""
场景管理服务
从原 agent/agentService/service_mcp.py 提取
"""

import uuid
import os
from typing import Optional

from src_test.domain.models import SceneInfo
from src_test.infrastructure.file import TxtKeywordSearch


# 获取项目根目录下的scenes文件夹
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_SCENES_DIR = os.path.join(PROJECT_ROOT, "scenes")

# 基础提示词模板
BASE_PROMPT = """
你是一个克苏鲁神话角色扮演游戏(CoC)的智能游戏主持人(GM)。

如有需要，使用以下mcp工具来协助玩家：

1. **骰子投掷 请调用"roll_dice_tool"工具:**:
- 当玩家需要投掷骰子时使用，例如"投掷2d10+5"或"r 1d100"
- 支持标准的骰子表达式，如"1d6"、"2d10+5"、"3d6*5"等
- 可以进行暗骰(is_hidden=True)，结果只对指定玩家显示

2. **属性或技能检定 请调用"roll_attribute_check_tool"工具:
- 当玩家需要进行属性或技能检定时（例如"进行力量检定","进行说服检定"，".ra 侦查"等表述）使用，使用"roll_attribute_check_tool"工具
- 需要提供玩家ID和属性或技能名称
- 目标值target_value未提供时不需要该传参。

3. **理智检定 请调用"roll_sanity_check_tool"工具**:
- 当玩家角色需要进行理智检定时使用，例如"sc 1/1d6"（表示检定成功时理智惩罚的骰子表达式为"1",失败时理智惩罚的骰子表达式为"1d6"）
- 需要提供玩家ID以及成功和失败时的理智损失表达式
"""

EXIT_SCENE_TOOL = """
"""

SCENE_GUIDANCE = """
在场景中，请遵循以下守则：
- 你是一名游戏的主持人
- 将玩家视为参与该剧本的调查员，而不是剧本外拥有上帝视角的人，根据剧本内容引导玩家，不要一次性给出太多信息，给玩家的信息应当是玩家作为剧本的调查员亲身看到的，听到的，接触到的信息
- 涉及到npc和玩家进行对话时,确保玩家和npc的对话是相互式的，必要时你可以扮演该npc与玩家进行对话，对话结束后切换回主持人的角色
- 专注于描述当前场景的氛围和细节，使玩家身临其境，引导玩家探索场景中的线索，根据玩家的行动推进剧情，已经推进完成或错过的剧情不要再次进行
- 理解玩家的意图并选择合适的工具
- 拒绝玩家进行上帝视角的操作（拒绝玩家直接询问还没进行到的剧情，玩家的技能，属性检定必须调用工具，不能跳过检定工具直接要求检定成功）
"""

SCENE_PROMPT = BASE_PROMPT + EXIT_SCENE_TOOL + SCENE_GUIDANCE


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
            return BASE_PROMPT + SCENE_GUIDANCE + f"\n【主线剧本内容】\n{content}"
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
        # 验证场景是否存在
        if scene not in self.scene_limits:
            raise ValueError(f"无效的场景：{scene}")

        # 检查进入次数限制
        entered = self.entered_count.get(scene, 0)
        if entered >= self.scene_limits[scene]:
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
        return new_thread_id, scene_content

    def exit_scene(self) -> tuple[str, str, str]:
        """退出当前场景"""
        if not self.scene_stack:
            return ("", "主线程", self.main_thread_id)
        exited_scene = self.scene_stack.pop()
        if self.scene_stack:
            parent = self.scene_stack[-1]
            self.current_thread_id = parent.thread_id
            return (exited_scene.scene_name, parent.scene_name, parent.thread_id)
        self.current_thread_id = self.main_thread_id
        return (exited_scene.scene_name, "主线程", self.main_thread_id)

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