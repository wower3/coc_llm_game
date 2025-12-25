"""
COC 对话服务 API
仅提供对话功能，所有agent逻辑都在test_agent.py中
"""

from flask import Flask, jsonify, request, Blueprint
from flask_cors import CORS
import sys
import os
from datetime import datetime
from langchain.messages import HumanMessage, AIMessage, SystemMessage

# 添加项目路径
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
agent_dir = os.path.join(src_dir, 'agent')
sys.path.insert(0, src_dir)
sys.path.insert(0, agent_dir)  # 添加agent目录以支持dice等相对导入

# 从test_agent导入agent和thread_manager
from agent.test_agent import agent, thread_manager

app = Flask(__name__)
CORS(app)

# 创建chat蓝图
chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# 系统日志存储
system_logs = []

# Agent状态
agent_ready = False

# 对话历史 - 参照chat.py维护完整对话上下文
messages = []


def add_log(level: str, message: str):
    """添加系统日志"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'level': level,
        'message': message
    }
    system_logs.append(log_entry)
    # 保持日志数量在100条以内
    if len(system_logs) > 100:
        system_logs.pop(0)


@chat_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'success': True,
        'agent_ready': agent_ready,
        'message': 'COC 对话服务运行中'
    })


@chat_bp.route('/init', methods=['POST'])
def init_agent():
    """初始化Agent"""
    global agent_ready
    try:
        # agent已在test_agent.py中初始化，这里只需标记为就绪
        agent_ready = True
        add_log('info', 'Agent初始化成功')
        return jsonify({
            'success': True,
            'message': 'Agent初始化成功',
            'thread_id': thread_manager.main_thread_id[:8]
        })
    except Exception as e:
        add_log('error', f'Agent初始化失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'初始化失败: {str(e)}'
        }), 500


@chat_bp.route('/send', methods=['POST'])
def send_message():
    """发送消息到Agent"""
    global agent_ready, messages

    if not agent_ready:
        return jsonify({
            'success': False,
            'error': 'Agent未初始化，请先初始化'
        }), 400

    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({
            'success': False,
            'error': '缺少message参数'
        }), 400

    user_message = data['message'].strip()
    if not user_message:
        return jsonify({
            'success': False,
            'error': '消息不能为空'
        }), 400

    try:
        # 获取当前线程ID用于记忆隔离
        current_thread_id = thread_manager.current_thread_id
        config = {"configurable": {"thread_id": current_thread_id}}

        add_log('info', f'收到用户消息: {user_message[:50]}...')

        # 使用HumanMessage构建消息并添加到对话历史
        messages.append(HumanMessage(content=user_message))

        # 使用agent处理用户输入，传入完整的messages历史
        response = agent.invoke(
            {"messages": messages},
            config
        )
        result = response["messages"][-1].content

        add_log('info', f'Agent回复: {result[:50]}...')

        # 返回响应和场景信息（参照chat.py的显示方式）
        return jsonify({
            'success': True,
            'response': result,
            'scene_info': {
                'scene_name': thread_manager.current_scene,  # 当前场景名称
                'scene_path': thread_manager.get_scene_path(),  # 完整场景路径
                'scene_depth': thread_manager.scene_depth,  # 场景深度
                'in_scene': thread_manager.in_scene,
                'thread_id': current_thread_id[:8]
            }
        })
    except Exception as e:
        add_log('error', f'处理消息失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'处理消息失败: {str(e)}'
        }), 500


@chat_bp.route('/reset', methods=['POST'])
def reset_agent():
    """重置Agent状态"""
    global agent_ready, messages
    try:
        # 重置线程管理器到主线程
        thread_manager.scene_stack.clear()
        thread_manager.in_scene = False
        thread_manager.scene_depth = 0

        # 清空对话历史
        messages = []

        add_log('info', 'Agent已重置，对话历史已清空')
        return jsonify({
            'success': True,
            'message': 'Agent已重置到初始状态'
        })
    except Exception as e:
        add_log('error', f'重置失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'重置失败: {str(e)}'
        }), 500


@chat_bp.route('/scene', methods=['GET'])
def get_scene_info():
    """获取当前场景信息"""
    try:
        return jsonify({
            'success': True,
            'scene_name': thread_manager.current_scene,  # 当前场景名称
            'scene_path': thread_manager.get_scene_path(),  # 完整场景路径
            'scene_depth': thread_manager.scene_depth,  # 场景深度
            'in_scene': thread_manager.in_scene
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chat_bp.route('/logs', methods=['GET'])
def get_logs():
    """获取系统日志"""
    return jsonify({
        'success': True,
        'logs': system_logs
    })


@chat_bp.route('/logs/clear', methods=['POST'])
def clear_logs():
    """清空系统日志"""
    global system_logs
    system_logs = []
    return jsonify({
        'success': True,
        'message': '日志已清空'
    })


# 注册蓝图
app.register_blueprint(chat_bp)


if __name__ == '__main__':
    print("启动 COC 对话服务...")
    print("访问 http://localhost:5002/chat/health 检查服务状态")
    add_log('info', '对话服务启动')
    app.run(host='0.0.0.0', port=5002, debug=False)
