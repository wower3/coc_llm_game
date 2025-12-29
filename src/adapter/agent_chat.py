"""
COC 对话服务 API
仅提供对话功能，所有agent逻辑都在test_agent.py中
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

app = FastAPI(title="COC Chat API", description="COC 对话服务 API")

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 系统日志存储
system_logs = []

# Agent状态
agent_ready = False

# 对话历史
messages = []


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


@app.get('/chat/health')
def health_check():
    """健康检查接口"""
    return {
        'success': True,
        'agent_ready': agent_ready,
        'message': 'COC 对话服务运行中'
    }


@app.post('/chat/init')
def init_agent():
    """初始化Agent"""
    global agent_ready
    try:
        agent_ready = True
        add_log('info', 'Agent初始化成功')
        return {
            'success': True,
            'message': 'Agent初始化成功',
            'thread_id': thread_manager.main_thread_id[:8]
        }
    except Exception as e:
        add_log('error', f'Agent初始化失败: {str(e)}')
        raise HTTPException(status_code=500, detail=f'初始化失败: {str(e)}')


@app.post('/chat/send')
def send_message(data: MessageRequest):
    """发送消息到Agent（流式输出）"""
    global agent_ready, messages

    if not agent_ready:
        raise HTTPException(status_code=400, detail='Agent未初始化，请先初始化')

    user_message = data.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail='消息不能为空')

    current_thread_id = thread_manager.current_thread_id
    config = {"configurable": {"thread_id": current_thread_id}}
    add_log('info', f'收到用户消息: {user_message[:50]}...')
    messages.append(HumanMessage(content=user_message))

    def generate_stream():
        """生成流式响应"""
        try:
            for token, metadata in agent.stream(
                {"messages": messages},
                stream_mode="messages",
                config=config
            ):
                if token.content:
                    yield f"data: {token.content}\n\n"
            # 发送结束标记
            yield "data: [DONE]\n\n"
            add_log('info', 'Agent流式回复完成')
        except Exception as e:
            add_log('error', f'流式处理失败: {str(e)}')
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )


@app.post('/chat/reset-all')
def reset_all_memory():
    """重置所有线程的记忆（包括checkpointer中的历史）"""
    global agent_ready, messages
    try:
        # 清空场景栈
        thread_manager.scene_stack.clear()
        # 清空当前对话历史
        messages = []
        # 清空checkpointer中的所有存储
        if hasattr(checkpointer, 'storage'):
            checkpointer.storage.clear()
        # 重新生成主线程ID
        import uuid
        thread_manager.main_thread_id = str(uuid.uuid4())
        thread_manager.current_thread_id = thread_manager.main_thread_id

        add_log('info', '所有记忆已重置')
        return {
            'success': True,
            'message': '所有记忆已重置',
            'new_thread_id': thread_manager.main_thread_id[:8]
        }
    except Exception as e:
        add_log('error', f'重置记忆失败: {str(e)}')
        raise HTTPException(status_code=500, detail=f'重置记忆失败: {str(e)}')


@app.get('/chat/scene')
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


@app.get('/chat/logs')
def get_logs():
    """获取系统日志"""
    return {'success': True, 'logs': system_logs}


@app.post('/chat/logs/clear')
def clear_logs():
    """清空系统日志"""
    global system_logs
    system_logs = []
    return {'success': True, 'message': '日志已清空'}


if __name__ == '__main__':
    import uvicorn
    print("启动 COC 对话服务...")
    print("访问 http://localhost:5782/chat/health 检查服务状态")
    add_log('info', '对话服务启动')
    uvicorn.run(app, host='0.0.0.0', port=5782)
