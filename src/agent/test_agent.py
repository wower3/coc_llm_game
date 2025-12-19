import os
import sys
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langgraph.checkpoint.memory import InMemorySaver

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 从 service_mcp 导入场景管理相关类
from src.agent.agentService.service_mcp import ThreadManager, McpService, MAIN_PROMPT

# 加载环境变量
load_dotenv(override=True)

# 创建全局线程管理器和MCP服务
thread_manager = ThreadManager(scenes_dir="./scenes/chapter1")
mcp_service = McpService(thread_manager=thread_manager)


# 定义工具（包装 McpService 的方法）
@tool()
def new_scene(scene: str) -> str:
    """
    进入新的场景。

    当模型判断需要进入新场景时调用此函数。
    这将切换到一个新的记忆线程，使用场景特定的提示词（从txt文件加载）。
    支持嵌套场景：可以在一个场景中进入另一个场景。

    :param scene: 场景名称/关键词。
    :return: 场景进入确认信息
    """
    return mcp_service.new_scene(scene)


@tool()
def exit_scene() -> str:
    """
    退出当前场景，返回上一个场景或主线程。

    当场景探索完成或玩家要求离开时调用此函数。
    如果当前在嵌套场景中，会返回到上一层场景；
    如果只有一层场景，会返回到主线程。

    :return: 退出确认信息
    """
    return mcp_service.exit_scene()


# 动态提示词中间件
@dynamic_prompt
def dynamic_system_prompt(request: ModelRequest) -> str:
    """根据当前状态动态返回系统提示词"""
    return thread_manager.get_current_prompt()


# 初始化模型
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = os.getenv("DEEPSEEK_URL")

model = ChatDeepSeek(
    model="deepseek-chat",
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_URL,
    temperature=1.2
)

# 创建checkpointer用于记忆持久化
checkpointer = InMemorySaver()

tools = [
    new_scene,
    exit_scene
]

# 创建Agent，使用动态提示词中间件和checkpointer
agent = create_agent(
    model=model,
    tools=tools,
    middleware=[dynamic_system_prompt],
    checkpointer=checkpointer
)


# 主对话循环
def main():
    print("🎲 欢迎来到克苏鲁神话角色扮演游戏!")
    print("🔹 输入 'exit' 或 'quit' 退出游戏")
    print(f"🔹 主线程ID: {thread_manager.main_thread_id[:8]}...\n")

    while True:
        # 显示当前场景路径
        scene_path = thread_manager.get_scene_path()
        depth = thread_manager.scene_depth
        if thread_manager.in_scene:
            print(f"📍 场景路径: {scene_path} (深度: {depth})")

        user_input = input("👤 玩家: ")
        if user_input.lower() in {"exit", "quit"}:
            print("游戏副本结束，期待下次冒险再见！")
            break

        # 获取当前线程ID用于记忆隔离
        current_thread_id = thread_manager.current_thread_id
        config = {"configurable": {"thread_id": current_thread_id}}

        # 显示AI回复
        print("🤖 游戏主持人:", end="", flush=True)

        # 使用agent处理用户输入，传入thread_id实现记忆隔离
        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config
        )
        result = response["messages"][-1].content

        print(result)
        print("\n" + "-" * 40)  # 分隔线

        # 显示当前线程信息（调试用）
        print(f"📝 线程: {thread_manager.current_thread_id[:8]}... | 场景深度: {thread_manager.scene_depth} | 路径: {thread_manager.get_scene_path()}")
        print("-" * 40 + "\n")


if __name__ == "__main__":
    main()
