"""
COC 对话服务路由
提供对话功能，所有agent逻辑都在test_agent.py中
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import sys
import os
from datetime import datetime
from langchain.messages import HumanMessage, AIMessage, SystemMessage

# 添加项目路径
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
agent_dir = os.path.join(src_dir, 'agent')
sys.path.insert(0, src_dir)
sys.path.insert(0, agent_dir)

# 从test_agent导入agent和thread_manager
from agent.test_agent import agent, thread_manager, checkpointer

router = APIRouter(prefix="/chat", tags=["对话服务"])

# 系统日志存储
system_logs = []

# 使用字典为每个线程维护独立的消息列表
thread_messages = {thread_manager.main_thread_id: []}


# 请求模型
class MessageRequest(BaseModel):
    message: str


def add_log(level: str, message: str):
    """添加系统日志"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'level': level,
        'message': message
    }
    system_logs.append(log_entry)
    if len(system_logs) > 100:
        system_logs.pop(0)


@router.get('/health')
def health_check():
    """健康检查接口"""
    return {
        'success': True,
        'agent_ready': True,
        'message': 'COC 对话服务运行中'
    }


@router.post('/init')
def init_agent():
    """初始化Agent（保留接口兼容性）"""
    try:
        add_log('info', 'Agent初始化成功')
        return {
            'success': True,
            'message': 'Agent初始化成功',
            'thread_id': thread_manager.main_thread_id[:8]
        }
    except Exception as e:
        add_log('error', f'Agent初始化失败: {str(e)}')
        raise HTTPException(status_code=500, detail=f'初始化失败: {str(e)}')


@router.post('/send')
def send_message(data: MessageRequest):
    """发送消息到Agent（流式输出）"""
    global thread_messages

    user_message = data.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail='消息不能为空')

    # 获取当前线程ID用于记忆隔离
    current_thread_id = thread_manager.current_thread_id

    # 确保当前线程有消息列表
    if current_thread_id not in thread_messages:
        thread_messages[current_thread_id] = []

    # 只向当前线程的消息列表添加消息
    thread_messages[current_thread_id].append(HumanMessage(content=user_message))

    config = {"configurable": {"thread_id": current_thread_id}}
    add_log('info', f'收到用户消息: {user_message[:50]}...')

    def generate_stream():
        """生成流式响应"""
        try:
            for token, metadata in agent.stream(
                {"messages": thread_messages[current_thread_id]},
                stream_mode="messages",
                config=config
            ):
                if token.content:
                    yield f"data: {token.content}\n\n"
            yield "data: [DONE]\n\n"
            add_log('info', 'Agent流式回复完成')
        except Exception as e:
            add_log('error', f'流式处理失败: {str(e)}')
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@router.post('/reset-all')
def reset_all_memory():
    """重置所有线程的记忆"""
    global thread_messages
    try:
        thread_manager.scene_stack.clear()
        import uuid
        thread_manager.main_thread_id = str(uuid.uuid4())
        thread_manager.current_thread_id = thread_manager.main_thread_id
        thread_messages = {thread_manager.main_thread_id: []}
        if hasattr(checkpointer, 'storage'):
            checkpointer.storage.clear()

        add_log('info', '所有记忆已重置')
        return {
            'success': True,
            'message': '所有记忆已重置',
            'new_thread_id': thread_manager.main_thread_id[:8]
        }
    except Exception as e:
        add_log('error', f'重置记忆失败: {str(e)}')
        raise HTTPException(status_code=500, detail=f'重置记忆失败: {str(e)}')


@router.get('/scene')
def get_scene_info():
    """获取当前场景信息"""
    try:
        return {
            'success': True,
            'scene_name': thread_manager.current_scene,
            'scene_path': thread_manager.get_scene_path(),
            'scene_depth': thread_manager.scene_depth,
            'in_scene': thread_manager.in_scene
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/logs')
def get_logs():
    """获取系统日志"""
    return {'success': True, 'logs': system_logs}


@router.post('/logs/clear')
def clear_logs():
    """清空系统日志"""
    global system_logs
    system_logs = []
    return {'success': True, 'message': '日志已清空'}
