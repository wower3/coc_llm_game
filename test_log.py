"""
测试日志功能
"""

import sys
from pathlib import Path

# 将 coc_structure 目录添加到 Python 路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src_test.infrastructure.log import logger, get_logger

# 测试不同类型的日志
print("测试日志功能...")

# 测试通用日志
logger.info("这是一条INFO级别的日志")
logger.debug("这是一条DEBUG级别的日志")
logger.warning("这是一条WARNING级别的日志")
logger.error("这是一条ERROR级别的日志")

# 测试带上下文的日志
api_logger = get_logger("API")
api_logger.info("API请求测试")

agent_logger = get_logger("AGENT")
agent_logger.info("Agent调用测试")

scene_logger = get_logger("SCENE")
scene_logger.info("场景切换测试")

dice_logger = get_logger("DICE")
dice_logger.info("骰子投掷测试: 1d20")

cli_logger = get_logger("CLI")
cli_logger.info("CLI启动测试")

print("\n日志测试完成！")
print(f"请检查 logs/ 目录下的日志文件夹：")
print("  - logs/{YYYYMMDD_HHMMSS}_pid{PID}/ - 每次运行的独立文件夹")
print("    - all.log       - 所有日志")
print("    - api.log       - API日志")
print("    - agent.log     - Agent日志")
print("    - scene.log     - 场景日志")
print("    - dice.log      - 骰子日志")
print("    - error.log     - 错误日志")
print("\n每次运行都会生成新的日志文件夹，不会互相覆盖！")
print("使用 logs/归档旧日志.bat 可以归档昨天及之前的日志。")
