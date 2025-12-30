# 主对话循环模块
import sys
from pathlib import Path

# 将 coc_structure 目录添加到 Python 路径（src_test 的父目录）
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src_test.service.agent_service import agent
from src_test.service.scene_service import ThreadManager
from langchain.messages import HumanMessage, AIMessage, SystemMessage

thread_manager = ThreadManager()

def main():
    print("欢迎来到克苏鲁神话角色扮演游戏!")
    print("输入 'exit' 或 'quit' 退出游戏")
    print(f"主线程ID: {thread_manager.main_thread_id[:8]}...\n")

    # 使用字典为每个线程维护独立的消息列表
    thread_messages = {thread_manager.main_thread_id: []}

    while True:
        # 显示当前场景路径
        scene_path = thread_manager.get_scene_path()
        depth = thread_manager.scene_depth
        if thread_manager.in_scene:
            print(f"场景路径: {scene_path} (深度: {depth})")

        user_input = input("玩家: ")
        extra_text = "（当前用户id为：00000002）"
        if user_input.lower() in {"exit", "quit"}:
            print("游戏副本结束，期待下次冒险再见！")
            break

        # 获取当前线程ID用于记忆隔离
        current_thread_id = thread_manager.current_thread_id

        # 确保当前线程有消息列表
        if current_thread_id not in thread_messages:
            thread_messages[current_thread_id] = []

        # 只向当前线程的消息列表添加消息
        thread_messages[current_thread_id].append(
            HumanMessage(content=f"{user_input}\n{extra_text}")
        )

        config = {"configurable": {"thread_id": current_thread_id}}

        # 显示AI回复
        print("游戏主持人:", end="", flush=True)

        # 使用agent处理用户输入，传入thread_id实现记忆隔离 TODO
        for token, metadata in agent.stream(
            {"messages": thread_messages[current_thread_id]},
            stream_mode="messages",
            config=config
        ):
            print(token.content, end="", flush=True)
        print("\n" + "-" * 40)  # 分隔线
        # 测试记忆内容
        # print(thread_messages[current_thread_id])

        # 显示当前线程信息（调试用）
        print(f"线程: {thread_manager.current_thread_id[:8]}... | 场景深度: {thread_manager.scene_depth} | 路径: {thread_manager.get_scene_path()}")
        print("-" * 40 + "\n")


if __name__ == "__main__":
    main()
