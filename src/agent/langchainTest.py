from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, AIMessage, SystemMessage
import os
from dotenv import load_dotenv 
load_dotenv(override=True)

MODELSCOPE_API_KEY = os.getenv("MODELSCOPE_API_KEY")
MODELSCOPE_URL = os.getenv("MODELSCOPE_URL")

# 1️⃣ 初始化模型（LangChain 1.0 接口）
model = ChatOpenAI(
    model="deepseek-ai/DeepSeek-V3.1",
    api_key=MODELSCOPE_API_KEY,
    base_url=MODELSCOPE_URL,
    temperature=1.0
)

# 2️⃣ 初始化系统提示词（System Prompt）
system_message = SystemMessage(
    content="你叫小智，是一名乐于助人的智能助手。请在对话中保持温和、有耐心的语气。"
)

# 3️⃣ 初始化消息历史
messages = [system_message]

print("🔹 输入 exit 退出对话\n")

# 4️⃣ 主循环（支持多轮对话 + 流式输出）
while True:
    user_input = input("👤 你：")
    if user_input.lower() in {"exit", "quit"}:
        print("🧩 对话结束，再见！")
        break

    # 追加用户消息
    messages.append(HumanMessage(content=user_input))

    # 实时输出模型生成内容
    print("🤖 小智：", end="", flush=True)
    full_reply = ""

    # ✅ LangChain 1.0 标准写法：流式输出
    for chunk in model.stream(messages):
        if chunk.content:
            print(chunk.content, end="", flush=True)
            full_reply += chunk.content

    print("\n" + "-" * 40)  # 分隔线

    # 追加 AI 回复消息
    messages.append(AIMessage(content=full_reply))

    # 保持消息长度（只保留最近50轮）
    messages = messages[-50:]