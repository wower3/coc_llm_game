"""
COC 对话 API 服务
独立的 Flask 服务，用于处理 langchain agent 对话
端口: 5002
"""

import os
import sys
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# 添加 src/agent 目录到路径（用于导入 dice 模块）
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'agent'))

# 加载环境变量
load_dotenv(override=True)

app = Flask(__name__)
CORS(app)

# 全局变量存储 agent 相关对象
agent = None
thread_manager = None
mcp_service = None
checkpointer = None

# 系统日志存储
system_logs = []
MAX_LOGS = 200  # 最大日志条数

def add_log(log_type, content):
    """添加日志"""
    from datetime import datetime
    system_logs.append({
        'time': datetime.now().strftime('%H:%M:%S'),
        'type': log_type,
        'content': content
    })
    # 保持日志数量在限制内
    if len(system_logs) > MAX_LOGS:
        system_logs.pop(0)

def init_agent():
    """初始化 langchain agent - 直接从 test_agent.py 导入"""
    global agent, thread_manager

    try:
        # 直接导入 test_agent.py 中的 agent 和 thread_manager
        from src.agent.test_agent import agent as test_agent, thread_manager as tm

        agent = test_agent
        thread_manager = tm

        add_log('system', 'Agent 初始化成功 (使用 test_agent.py)')
        return True
    except Exception as e:
        print(f"初始化 agent 失败: {e}")
        import traceback
        traceback.print_exc()
        add_log('system', f'Agent 初始化失败: {e}')
        return False


@app.route('/chat/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'success': True,
        'status': 'online',
        'agent_ready': agent is not None
    })


@app.route('/chat/logs', methods=['GET'])
def get_logs():
    """获取系统日志"""
    return jsonify({
        'success': True,
        'logs': system_logs
    })


@app.route('/chat/logs/clear', methods=['POST'])
def clear_logs():
    """清空系统日志"""
    system_logs.clear()
    add_log('system', '日志已清空')
    return jsonify({'success': True})


@app.route('/chat/init', methods=['POST'])
def initialize():
    """初始化 agent"""
    global agent
    if agent is not None:
        return jsonify({'success': True, 'message': 'Agent 已经初始化'})

    success = init_agent()
    if success:
        return jsonify({'success': True, 'message': 'Agent 初始化成功'})
    else:
        return jsonify({'success': False, 'error': 'Agent 初始化失败'}), 500


@app.route('/chat/send', methods=['POST'])
def send_message():
    """发送消息到 agent 并获取回复"""
    global agent, thread_manager

    if agent is None:
        return jsonify({'success': False, 'error': 'Agent 未初始化，请先调用 /chat/init'}), 400

    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'success': False, 'error': '缺少 message 参数'}), 400

    user_message = data['message']
    add_log('user', user_message)

    try:
        # 获取当前线程ID用于记忆隔离
        current_thread_id = thread_manager.current_thread_id
        config = {"configurable": {"thread_id": current_thread_id}}

        # 使用agent处理用户输入
        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]},
            config
        )
        result = response["messages"][-1].content
        add_log('agent', result)

        # 获取场景信息
        scene_info = {
            'scene_path': thread_manager.get_scene_path(),
            'scene_depth': thread_manager.scene_depth,
            'in_scene': thread_manager.in_scene,
            'thread_id': current_thread_id[:8]
        }

        return jsonify({
            'success': True,
            'response': result,
            'scene_info': scene_info
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/chat/reset', methods=['POST'])
def reset_agent():
    """重置 agent 状态"""
    global agent, thread_manager, mcp_service, checkpointer

    agent = None
    thread_manager = None
    mcp_service = None
    checkpointer = None

    success = init_agent()
    if success:
        return jsonify({'success': True, 'message': 'Agent 已重置'})
    else:
        return jsonify({'success': False, 'error': 'Agent 重置失败'}), 500


@app.route('/chat/scene', methods=['GET'])
def get_scene_info():
    """获取当前场景信息"""
    global thread_manager

    if thread_manager is None:
        return jsonify({'success': False, 'error': 'Agent 未初始化'}), 400

    return jsonify({
        'success': True,
        'scene_path': thread_manager.get_scene_path(),
        'scene_depth': thread_manager.scene_depth,
        'in_scene': thread_manager.in_scene
    })


if __name__ == '__main__':
    print("正在启动 COC 对话 API 服务...")
    print("端口: 5002")
    print("初始化 Agent...")

    if init_agent():
        print("Agent 初始化成功!")
    else:
        print("Agent 初始化失败，但服务仍将启动。请通过 /chat/init 手动初始化。")

    app.run(host='0.0.0.0', port=5002, debug=False)
