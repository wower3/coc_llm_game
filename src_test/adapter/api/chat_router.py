"""
COC 对话服务路由
"""

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from src_test.infrastructure.log import get_logger

logger = get_logger("API")
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
        logger.info(f"[API] Agent初始化成功, 主线程ID: {tm.main_thread_id[:8]}")
        add_log('info', 'Agent初始化成功')
        return {'success': True, 'message': 'Agent初始化成功', 'thread_id': tm.main_thread_id[:8]}
    except Exception as e:
        logger.error(f"[API] Agent初始化失败: {str(e)}")
        add_log('error', f'Agent初始化失败: {str(e)}')
        raise HTTPException(status_code=500, detail=f'初始化失败: {str(e)}')


@router.post('/send')
def send_message(
    data: MessageRequest,
    authorization: Optional[str] = Header(None)
):
    """
    发送消息给Agent

    authorization: Bearer token格式的认证头，用于提取当前用户ID
    """
    from langchain.messages import HumanMessage
    global thread_messages

    # 解析token获取user_id
    user_id = None
    if authorization:
        try:
            from src_test.adapter.api.auth_router import verify_token
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            user_id = verify_token(token)
            if user_id:
                logger.info(f"[API] 已识别用户: {user_id}")
        except Exception as e:
            logger.warning(f"[API] Token解析失败: {str(e)}")
    else:
        logger.warning("[API] 未提供Authorization头")

    user_message = data.message.strip()
    if not user_message:
        logger.warning("[API] 收到空消息")
        raise HTTPException(status_code=400, detail='消息不能为空')

    logger.info(f"[API] 收到消息: {user_message[:50]}...")

    # 每次发送新消息时，清空AI返回的场景列表
    from src_test.service.agent_service import available_scenes
    available_scenes.clear()

    agent, tm, _ = get_agent()
    current_thread_id = tm.current_thread_id
    logger.debug(f"[API] 当前线程ID: {current_thread_id[:8]}, 场景: {tm.current_scene}, 深度: {tm.scene_depth}")

    # 将 user_id 存储到 thread_user_map 中
    from src_test.service.agent_service import set_user_id_for_thread
    set_user_id_for_thread(current_thread_id, user_id)
    logger.debug(f"[API] 设置线程用户映射: {current_thread_id[:8]} -> {user_id}")

    if current_thread_id not in thread_messages:
        thread_messages[current_thread_id] = []
    thread_messages[current_thread_id].append(HumanMessage(content=user_message))
    config = {"configurable": {"thread_id": current_thread_id}}

    def generate_stream():
        try:
            full_response = ""
            for token, _ in agent.stream(
                {"messages": thread_messages[current_thread_id]},
                stream_mode="messages", config=config
            ):
                if token.content:
                    full_response += token.content
                    yield f"data: {token.content}\n\n"
            logger.info(f"[API] AI响应完成: {full_response[:50]}...")
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"[API] 消息处理失败: {str(e)}", exc_info=True)
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
    """重置所有线程的记忆和场景进度"""
    global thread_messages
    try:
        import uuid
        _, tm, cp = get_agent()

        # 调用 reset_progress 重置场景进度
        tm.reset_progress()

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


@router.get('/scenes/available')
def get_available_scenes():
    """获取当前可用的场景选择列表（AI返回的列表经过次数限制过滤）"""
    try:
        from src_test.service.agent_service import available_scenes
        _, tm, _ = get_agent()
        available = tm.get_available_scenes(available_scenes)
        return {
            'success': True,
            'available_scenes': available,
            'scene_limits': tm.scene_limits,
            'entered_count': tm.entered_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class NewSceneRequest(BaseModel):
    scene: str


@router.post('/scene/new')
def enter_new_scene(data: NewSceneRequest):
    """进入新场景（只切换场景，不获取AI描述，让前端通过/send继续对话）"""
    try:
        from src_test.service.agent_service import mcp_service, available_scenes
        _, tm, _ = get_agent()

        result = mcp_service.new_scene(data.scene)
        add_log('info', f'进入新场景: {data.scene}')

        return {
            'success': True,
            'message': result,
            'scene': data.scene,
            'scene_depth': tm.scene_depth,
            'current_scene': tm.current_scene,
            'in_scene': tm.in_scene,
            'available_scenes': tm.get_available_scenes(available_scenes)
        }
    except ValueError as e:
        add_log('error', f'进入场景失败: {str(e)}')
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        add_log('error', f'进入场景失败: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/scene/exit')
def exit_current_scene():
    """退出当前场景（只切换场景，不获取AI描述，让前端通过/send继续对话）"""
    try:
        from src_test.service.agent_service import mcp_service, available_scenes
        _, tm, _ = get_agent()

        result = mcp_service.exit_scene()
        add_log('info', f'退出场景，当前深度: {tm.scene_depth}')

        return {
            'success': True,
            'message': result,
            'scene_depth': tm.scene_depth,
            'current_scene': tm.current_scene,
            'in_scene': tm.in_scene,
            'available_scenes': tm.get_available_scenes(available_scenes)
        }
    except Exception as e:
        add_log('error', f'退出场景失败: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/log-file')
def get_log_file():
    """获取最新的all.log日志文件内容"""
    import os
    import re

    try:
        # 获取项目根目录（从当前文件向上3级）
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        logs_dir = os.path.join(project_root, "logs")

        logger.info(f"查找日志目录: {logs_dir}")

        if not os.path.exists(logs_dir):
            return {'success': True, 'content': f'日志目录不存在: {logs_dir}'}

        # 获取所有日志文件夹
        log_folders = []
        try:
            for item in os.listdir(logs_dir):
                item_path = os.path.join(logs_dir, item)
                if os.path.isdir(item_path):
                    # 匹配格式: YYYYMMDD_HHMMSS_pidXXXXX
                    if re.match(r'^\d{8}_\d{6}_pid\d+$', item):
                        log_folders.append((item, item_path))
        except PermissionError:
            pass

        # 按名称排序（最新的在前）
        log_folders.sort(key=lambda x: x[0], reverse=True)

        if not log_folders:
            return {'success': True, 'content': '暂无日志文件'}

        # 获取最新的日志文件夹
        latest_log_dir_name, latest_log_dir = log_folders[0]
        all_log_path = os.path.join(latest_log_dir, "all.log")

        logger.info(f"读取日志文件: {all_log_path}")

        if not os.path.exists(all_log_path):
            return {'success': True, 'content': f'日志文件不存在: {all_log_path}'}

        # 读取日志文件内容（只读取最后1000行）
        try:
            with open(all_log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 只返回最后1000行
                content = ''.join(lines[-1000:]) if len(lines) > 1000 else ''.join(lines)
        except Exception as e:
            content = f'读取日志文件失败: {str(e)}'
            logger.error(f"读取日志文件失败: {str(e)}")

        return {
            'success': True,
            'content': content,
            'log_folder': latest_log_dir_name,
            'line_count': len(lines)
        }
    except Exception as e:
        logger.error(f'获取日志文件失败: {str(e)}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
