"""
日志配置模块
使用loguru记录所有调用、传输消息、报错信息
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from loguru import logger

# 获取项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"

# 确保logs目录存在
LOGS_DIR.mkdir(exist_ok=True)

# 生成唯一的运行标识（启动时间 + 进程ID）
START_TIME = datetime.now()
RUN_ID = f"{START_TIME.strftime('%Y%m%d_%H%M%S')}_pid{os.getpid()}"

# 为每次运行创建独立的日志文件夹
RUN_LOG_DIR = LOGS_DIR / RUN_ID
RUN_LOG_DIR.mkdir(exist_ok=True)

# 移除默认的handler
logger.remove()

# 配置日志格式
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# 添加控制台输出（INFO及以上级别）
logger.add(
    sys.stdout,
    format=log_format,
    level="INFO",
    colorize=True,
)

# 添加所有日志文件（DEBUG及以上级别）
logger.add(
    RUN_LOG_DIR / "all.log",
    format=log_format,
    level="DEBUG",
    rotation="00:00",  # 每天午夜轮转
    retention="30 days",  # 保留30天
    compression="zip",  # 压缩旧日志
    encoding="utf-8",
)

# 添加错误日志文件（ERROR及以上级别）
logger.add(
    RUN_LOG_DIR / "error.log",
    format=log_format,
    level="ERROR",
    rotation="00:00",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
)

# 添加API调用日志文件（记录所有API请求和响应）
logger.add(
    RUN_LOG_DIR / "api.log",
    format=log_format,
    level="INFO",
    rotation="00:00",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
    filter=lambda record: "API" in record["extra"].get("context", ""),
)

# 添加Agent调用日志文件（记录AI交互）
logger.add(
    RUN_LOG_DIR / "agent.log",
    format=log_format,
    level="DEBUG",
    rotation="00:00",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
    filter=lambda record: "AGENT" in record["extra"].get("context", ""),
)

# 添加场景切换日志文件
logger.add(
    RUN_LOG_DIR / "scene.log",
    format=log_format,
    level="INFO",
    rotation="00:00",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
    filter=lambda record: "SCENE" in record["extra"].get("context", ""),
)

# 添加骰子投掷日志文件
logger.add(
    RUN_LOG_DIR / "dice.log",
    format=log_format,
    level="INFO",
    rotation="00:00",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
    filter=lambda record: "DICE" in record["extra"].get("context", ""),
)


def get_logger(context: str = ""):
    """
    获取带有上下文的logger

    :param context: 上下文标识（如API、AGENT、SCENE、DICE等）
    :return: 带有上下文的logger实例
    """
    if context:
        return logger.bind(context=context)
    return logger


# 导出logger
__all__ = ["logger", "get_logger"]
