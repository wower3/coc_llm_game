"""
COC 对话服务管理器
用于启动和停止 chat_api.py 服务
端口: 5003
"""

import os
import sys
import subprocess
import signal
import socket
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 全局变量
chat_process = None
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
CHAT_API_SCRIPT = os.path.join(SCRIPT_DIR, 'chat_api.py')
CHAT_API_PORT = 5002


def check_port(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


@app.route('/launcher/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'success': True, 'status': 'online'})


@app.route('/launcher/status', methods=['GET'])
def status():
    """获取对话服务状态"""
    is_running = check_port(CHAT_API_PORT)
    return jsonify({
        'success': True,
        'running': is_running,
        'port': CHAT_API_PORT
    })


@app.route('/launcher/start', methods=['POST'])
def start_chat():
    """启动对话服务"""
    global chat_process

    if check_port(CHAT_API_PORT):
        return jsonify({'success': True, 'message': '服务已在运行'})

    try:
        chat_process = subprocess.Popen(
            [sys.executable, CHAT_API_SCRIPT],
            cwd=PROJECT_ROOT,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )

        # 等待服务启动
        import time
        for _ in range(10):
            time.sleep(0.5)
            if check_port(CHAT_API_PORT):
                return jsonify({'success': True, 'message': '服务启动成功'})

        return jsonify({'success': False, 'error': '服务启动超时'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/launcher/stop', methods=['POST'])
def stop_chat():
    """停止对话服务"""
    if not check_port(CHAT_API_PORT):
        return jsonify({'success': True, 'message': '服务未运行'})

    try:
        if sys.platform == 'win32':
            # Windows: 通过端口找到PID并终止
            import os
            result = os.popen(f'netstat -ano | findstr :{CHAT_API_PORT} | findstr LISTENING').read()
            if result:
                pid = result.strip().split()[-1]
                os.system(f'taskkill /PID {pid} /F >nul 2>&1')
        else:
            # Linux/Mac
            os.system(f"kill $(lsof -t -i:{CHAT_API_PORT}) 2>/dev/null")

        # 等待服务停止
        import time
        for _ in range(5):
            time.sleep(0.5)
            if not check_port(CHAT_API_PORT):
                return jsonify({'success': True, 'message': '服务已停止'})

        return jsonify({'success': False, 'error': '服务停止超时'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    print("启动对话服务管理器...")
    print("端口: 5003")
    app.run(host='0.0.0.0', port=5003, debug=False)
