"""
COC 对话服务启动器
用于管理对话服务(agent_chat.py)的启动和关闭
运行在端口5003，管理端口5002的对话服务
"""

import subprocess
import sys
import os
from flask import Flask, jsonify
from flask_cors import CORS
import time
import socket

app = Flask(__name__)
CORS(app)

# 全局变量存储对话服务进程
chat_process = None
chat_status = {
    'running': False,
    'pid': None,
    'start_time': None
}

# 获取目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.join(os.path.dirname(CURRENT_DIR), 'agent')  # src/agent目录
CHAT_SCRIPT = os.path.join(CURRENT_DIR, 'agent_chat.py')
CHAT_PORT = 5002


def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def kill_process_on_port(port):
    """杀死占用指定端口的进程"""
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True, capture_output=True, text=True
            )
            for line in result.stdout.strip().split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    pid = line.strip().split()[-1]
                    os.system(f'taskkill /F /PID {pid}')
                    return True
        else:  # Linux/Mac
            subprocess.run(f'fuser -k {port}/tcp', shell=True)
            return True
    except Exception as e:
        print(f"杀死进程失败: {e}")
    return False


@app.route('/launcher/status', methods=['GET'])
def get_status():
    """获取对话服务状态"""
    global chat_process, chat_status

    is_running = is_port_in_use(CHAT_PORT)
    chat_status['running'] = is_running

    if not is_running:
        chat_status['pid'] = None
        chat_process = None

    return jsonify({
        'success': True,
        'data': chat_status
    })


@app.route('/launcher/start', methods=['POST'])
def start_chat():
    """启动对话服务"""
    global chat_process, chat_status

    if chat_status['running'] or is_port_in_use(CHAT_PORT):
        chat_status['running'] = True
        return jsonify({
            'success': True,
            'message': '对话服务已在运行中'
        })

    try:
        # 启动对话服务，工作目录设为agent目录
        chat_process = subprocess.Popen(
            [sys.executable, CHAT_SCRIPT],
            cwd=AGENT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )

        # 等待服务启动
        time.sleep(2)

        if chat_process.poll() is None:
            chat_status['running'] = True
            chat_status['pid'] = chat_process.pid
            chat_status['start_time'] = time.strftime('%Y-%m-%d %H:%M:%S')

            return jsonify({
                'success': True,
                'message': '对话服务已启动',
                'data': chat_status
            })
        else:
            stderr = chat_process.stderr.read().decode('utf-8', errors='ignore')
            return jsonify({
                'success': False,
                'error': f'对话服务启动失败: {stderr}'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/launcher/stop', methods=['POST'])
def stop_chat():
    """停止对话服务"""
    global chat_process, chat_status

    if not is_port_in_use(CHAT_PORT):
        return jsonify({
            'success': False,
            'error': '对话服务未在运行'
        })

    try:
        kill_process_on_port(CHAT_PORT)
        time.sleep(1)

        chat_status['running'] = False
        chat_status['pid'] = None
        chat_process = None

        return jsonify({
            'success': True,
            'message': '对话服务已停止'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/launcher/health', methods=['GET'])
def health():
    """启动器健康检查"""
    return jsonify({'status': 'ok', 'message': '对话管理服务运行中'})


if __name__ == '__main__':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 50)
    print("COC 对话服务管理器")
    print("=" * 50)
    print(f"管理服务: http://localhost:5003")
    print(f"对话服务: http://localhost:5002")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5003, debug=False)
