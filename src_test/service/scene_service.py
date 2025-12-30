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

2. **属性或技能检定 请调用"roll_attribute_check_tool"工具:
- 当玩家需要进行属性或技能检定时使用

3. **理智检定 请调用"roll_sanity_check_tool"工具**:
- 当玩家角色需要进行理智检定时使用

4. **进入新场景 请调用"new_scene"工具**:
- 当剧本涉及到进入新场景时调用
"""

EXIT_SCENE_TOOL = """
5. **退出当前场景 请调用"exit_scene工具"：
- 当场景探索完成或玩家要求离开时调用
"""

SCENE_GUIDANCE = """
在场景中，请遵循以下守则：
- 你是一名游戏的主持人
- 将玩家视为参与该剧本的调查员
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

    def _load_main_prompt(self) -> str:
        """加载主线程提示词"""
        main_prompt_file = os.path.join(self.scenes_dir, "开始-连接-结尾.txt")
        try:
            with open(main_prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return BASE_PROMPT + SCENE_GUIDANCE + f"\n【主线剧本内容】\n{content}"
        except FileNotFoundError:
            return SCENE_PROMPT

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
        """进入新场景"""
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
