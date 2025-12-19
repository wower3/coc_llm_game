import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain.messages import HumanMessage, AIMessage, SystemMessage
from typing import Optional, Dict, Any
import json

# 导入骰子服务
from dice.dice_mcp import DiceService

# 加载环境变量
load_dotenv(override=True)

# 初始化骰子服务
dice_service = DiceService()

# 定义工具参数模型
class SceneName(BaseModel):
    scene: str = Field(description="场景名称")

class AttributeCheckInput(BaseModel):
    user_id: str = Field(description="执行检定的用户ID，用于查找角色卡")
    attribute_name: str = Field(description="要检定的属性或技能名称，例如 '力量', '侦查'，'图书馆使用'，'闪避'")
    target_value: Optional[int] = Field(default=None, description="检定的目标值。如果未提供，将自动从用户的角色卡中查找")

class SanityCheckInput(BaseModel):
    user_id: str = Field(description="执行检定的用户ID")
    success_penalty: str = Field(description="检定成功时理智惩罚的骰子表达式, 例如 '1'")
    failure_penalty: str = Field(description="检定失败时理智惩罚的骰子表达式, 例如 '1d6'")

# 定义工具
@tool(args_schema=SceneName)
def new_scene(scene: str) -> str:
    """
    进入新的场景。

    当模型判断需要进入新场景时调用此函数

    :param scene: 场景名称。
    :return: 是否调用成功标志
    """
    result = dice_service.roll_dice(scene)
    return json.dumps(result, ensure_ascii=False)

@tool(args_schema=AttributeCheckInput)
def roll_attribute_check_tool(user_id: str, attribute_name: str, target_value: Optional[int] = None) -> str:
    """
    对用户的某个属性或技能进行检定（1d100）。

    例如，当用户说“进行一次力量检定”，“进行一次说服检定”，“.ra 力量”，“.ra 说服”等类似请求时，LLM应调用此函数。

    :param user_id: 执行检定的用户ID，用于查找角色卡。
    :param attribute_name: 要检定的属性或技能名称，例如 "力量", "侦查"，“图书馆使用”，“闪避”。
    :param target_value: (可选) 检定的目标值。默认不提供，将自动从用户的角色卡中查找。
    :return: 包含检定结果、目标值、成功等级的字典。
    """
    result = dice_service.roll_attribute_check(user_id, attribute_name, target_value)
    return json.dumps(result, ensure_ascii=False)

@tool(args_schema=SanityCheckInput)
def roll_sanity_check_tool(user_id: str, success_penalty: str, failure_penalty: str) -> str:
    """
    为用户执行一次理智检定（Sanity Check）。

    例如，当用户说“sc 1/1d6”或“对理智值进行检定，惩罚为1/1d6”时，LLM应解析出参数并调用此函数。

    :param user_id: 执行检定的用户ID。
    :param success_penalty: 检定成功时理智惩罚的骰子表达式, 例如 "1"。
    :param failure_penalty: 检定失败时理智惩罚的骰子表达式, 例如 "1d6"。
    :return: 包含检定结果、SAN值变化的详细字典。
    """
    result = dice_service.roll_sanity_check(user_id, success_penalty, failure_penalty)
    return json.dumps(result, ensure_ascii=False)

# 创建提示词模板
prompt = """
你是一位专业的《克苏鲁的呼唤》(Call of Cthulhu)角色扮演游戏主持人(GM)，专注于提供沉浸式的恐怖体验和流畅的游戏进程。
如有需要，使用以下mcp工具：

1. **进入新的场景 请调用"new_scene"工具:**:
   - 当玩家选择进入新的场景时调用，传参为对应的场景名

2. **进入战斗 请调用"fight"工具:
   - 当玩家需要进行属性或技能检定时（例如"进行力量检定"或".ra 侦查"）使用，使用"roll_attribute_check_tool"工具
   - 需要提供玩家ID和属性或技能名称
   - 目标值target_value未提供时不需要该传参。

3. **进入双人对话模式 请调用“chat”工具**:
   - 当玩家角色需要进行理智检定时使用，例如"sc 1/1d6"（表示检定成功时理智惩罚的骰子表达式为"1",失败时理智惩罚的骰子表达式为"1d6"）
   - 需要提供玩家ID以及成功和失败时的理智损失表达式

在对话过程中，请遵循以下规则：
- 理解玩家的意图并选择合适的工具
- 准确提取必要的参数
- 根据提供的剧本结构推进故事，在关键节点提供清晰的选择指引
- 保持克苏鲁神话的氛围和风格

剧本如下：
# 剧本：食尸鬼的秘密

## 关键点一：接收委托与安顿

*   **入口**：调查员抵达密骛根市，与委托人托马斯·金博尔会面。
*   **内容**：
    *   托马斯说明委托背景：其叔叔道格拉斯·金博尔（特征：白发、秃顶、中等身高、圆框眼镜）于一年前神秘失踪。近日，叔叔书房内一些特定书籍被盗。
    *   明确委托三项任务：
        1.  找到偷书的贼人。
        2.  尽可能追回被盗书籍。
        3.  调查道格拉斯的去向，确认其生死。
    *   提供报酬与资源：愿意承担调查所有花销，并支付10美元作为最终报酬（相当于今日约240美元）。邀请调查员入住其家中空房间，便于调查。
    *   特别说明：托马斯未将失窃案报告警方，认为警方不会重视几本书的盗窃。
*   **出口**：调查员接受委托并入住金博尔家。**必须选择开始初步调查**（进入关键点二）。

## 关键点二：展开初步调查

*   **入口**：调查员决定从以下平行路径中选择一项或多项展开调查。所有路径线索最终会收敛，引导调查方向。
    *   询问附近居民
    *   查看墓地周边
    *   在图书馆调查本地消息
    *   询问警方
    *   查阅本地报纸《阿诺兹堡广告报》旧刊
    *   查看金博尔家周边
*   **收敛线索与引导**：
    *   所有调查路径均将怀疑指向阿诺兹堡公墓与道格拉斯对超自然知识的追求。
    *   日记残页与邻居目击暗示存在夜间活动的非人实体及地下通道。
    *   如果调查员未能自行总结，托马斯·金博尔会主动询问进展，并逻辑性地建议：监视房屋或墓地，以防窃贼再次光顾。
*   **出口**：调查员获得足够线索，意识到下一步需针对墓地或房屋采取直接行动。进入关键点三。

## 关键点三：深入核心区域

*   **入口**：调查员根据线索，决定采取以下平行行动之一（选择后，故事沿此路径发展，其他路径暂时关闭）：
    *   检查道格拉斯最喜欢的墓碑
    *   监视屋子或墓地
*   **共通发现与确认**：
    *   窃贼并非人类，其行为特征符合传说中的食尸鬼。
    *   地下隧道网络确实存在，并连接着墓地与金博尔家（很可能直通道格拉斯原来的书房下方）。
    *   道格拉斯的失踪与此超自然群体有直接关联。
*   **出口**：无论选择哪条路径，调查员都会直面超自然的证据。必须决定如何最终应对这一威胁（进入关键点四）。

## 关键点四：结局与后果

*   **入口**：调查员在证实食尸鬼与隧道的存在后，必须决定如何处理并结束事件。
*   **核心抉择**：
    *   调查员可以提出自己的解决方案（例如，用水泥封闭坟墓入口）。
    *   但需注意：此类行动可能无法根本解决食尸鬼群体，它们可能只是废弃这处墓地。
    *   最终，调查员需决定是否将关于道格拉斯的真相告诉托马斯·金博尔，还是将其隐瞒。
*   **结局与奖励结算**：
    *   **奖励条件1（理智与技能）**：
        *   假如调查员曾陷入临时性疯狂，他的克苏鲁神话技能会增长5%。
        *   假如调查员与道格拉斯·金博尔交谈过，就会得知这只食尸鬼不管怎样都不会计划再次回来。因为这条消息，调查员可以获得 1D6的理智值。
    *   **奖励条件2（报酬）**：
        *   托马斯·金博尔愿意给完成任务的调查员支付10美元。
        *   特别扣除项：如果调查员在途中损坏了屋里的贵重物品，则报酬减少5美元。
    *   **最终状态**：
        *   根据调查员的行动与选择，事件可能以多种方式了结：
            1.  **部分解决**：盗窃停止，但道格拉斯的下落成谜。
            2.  **真相揭示**：托马斯得知叔叔的可怕命运。
            3.  **未解之谜**：调查员未能深入或选择隐瞒，秘密得以保留。
            4.  **调查员失踪**：在调查隧道或对抗中，调查员可能同样消失（一个符合克苏鲁风格的结局）。
*   **守秘人笔记**：并非每一个谜团都会被揭开，有时连调查员自己都会失踪。这在《克苏鲁的呼唤》中时有发生。
*   **剧本结束**。
"""

# 定义可用工具
tools = [
    new_scene,
    roll_attribute_check_tool,
    roll_sanity_check_tool
]

# 初始化模型
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = os.getenv("DEEPSEEK_URL")

model = ChatDeepSeek(
    model="deepseek-chat",
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_URL,
    temperature=1.2
)

# 创建Agent
agent = create_agent(model=model, tools=tools, system_prompt=prompt)
system_message = SystemMessage(
    content=prompt
)

# 主对话循环
def main():
    print("🎲 欢迎来到克苏鲁神话角色扮演游戏!")
    print("🔹 输入 'exit' 或 'quit' 退出游戏\n")

    # 初始化对话历史
    messages = [system_message]

    while True:
        user_input = input("👤 玩家: ")
        if user_input.lower() in {"exit", "quit"}:
            print("游戏副本结束，期待下次冒险再见！")
            break

        # 使用agent处理用户输入
        messages.append(HumanMessage(content=user_input))

        # 显示AI回复
        print("🤖 游戏主持人:", end="", flush=True)
        response = agent.invoke({"messages":messages})
        result = response["messages"][-1].content

        # ✅ LangChain 1.0 标准写法
        print(result)
        print("\n" + "-" * 40)  # 分隔线

        # 更新对话历史
        messages.append(AIMessage(content=result))

        # 保持消息长度（只保留最近50轮）
        messages = messages[-50:]

if __name__ == "__main__":
    main()