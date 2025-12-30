"""
COC 对话服务路由
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/chat", tags=["对话服务"])

# 延迟导入，避免循环依赖
_agent = None
_thread_manager = None
_checkpointer = None
thread_messages = {}
system_logs = []


class MessageRequest(BaseModel):
    message: str


def get_agent():
    """延迟加载agent"""
    global _agent, _thread_manager, _checkpointer, thread_messages
    if _agent is None:
        from src_test.service.agent_service import agent, thread_manager, checkpointer
        _agent = agent
        _thread_manager = thread_manager
        _checkpointer = checkpointer
        thread_messages[_thread_manager.main_thread_id] = []
    return _agent, _thread_manager, _checkpointer


def add_log(level: str, message: str):
    log_entry = {'timestamp': datetime.now().isoformat(), 'level': level, 'message': message}
    system_logs.append(log_entry)
    if len(system_logs) > 100:
        system_logs.pop(0)


@router.get('/health')
def health_check():
    return {'success': True, 'agent_ready': True, 'message': 'COC 对话服务运行中'}


@router.post('/init')
def init_agent():
    try:
        _, tm, _ = get_agent()
        add_log('info', 'Agent初始化成功')
        return {'success': True, 'message': 'Agent初始化成功', 'thread_id': tm.main_thread_id[:8]}
    except Exception as e:
        add_log('error', f'Agent初始化失败: {str(e)}')
        raise HTTPException(status_code=500, detail=f'初始化失败: {str(e)}')


@router.post('/send')
def send_message(data: MessageRequest):
    from langchain.messages import HumanMessage
    global thread_messages
    user_message = data.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail='消息不能为空')

    agent, tm, _ = get_agent()
    current_thread_id = tm.current_thread_id
    if current_thread_id not in thread_messages:
        thread_messages[current_thread_id] = []
    thread_messages[current_thread_id].append(HumanMessage(content=user_message))
    config = {"configurable": {"thread_id": current_thread_id}}

    def generate_stream():
        try:
            for token, _ in agent.stream(
                {"messages": thread_messages[current_thread_id]},
                stream_mode="messages", config=config
            ):
                if token.content:
                    yield f"data: {token.content}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@router.get('/scene')
def get_scene_info():
    """获取当前场景信息"""
    try:
        _, tm, _ = get_agent()
        return {
            'success': True,
            'scene_name': tm.current_scene,
            'scene_path': tm.get_scene_path(),
            'scene_depth': tm.scene_depth,
            'in_scene': tm.in_scene
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/reset-all')
def reset_all_memory():
    """重置所有线程的记忆"""
    global thread_messages
    try:
        import uuid
        _, tm, cp = get_agent()

        # 清除场景栈
        tm.scene_stack.clear()

        # 重新生成主线程ID
        tm.main_thread_id = str(uuid.uuid4())
        tm.current_thread_id = tm.main_thread_id

        # 重置消息列表
        thread_messages = {tm.main_thread_id: []}

        # 清除checkpointer存储
        if hasattr(cp, 'storage'):
            cp.storage.clear()

        add_log('info', '所有记忆已重置')
        return {
            'success': True,
            'message': '所有记忆已重置',
            'new_thread_id': tm.main_thread_id[:8]
        }
    except Exception as e:
        add_log('error', f'重置记忆失败: {str(e)}')
        raise HTTPException(status_code=500, detail=f'重置记忆失败: {str(e)}')


@router.get('/logs')
def get_logs():
    return {'success': True, 'logs': system_logs}


@router.post('/logs/clear')
def clear_logs():
    global system_logs
    system_logs = []
    return {'success': True}
