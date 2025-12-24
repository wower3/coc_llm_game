"""
COC 跑团游戏启动器
用于管理后端API服务的启动和关闭
"""

import subprocess
import sys
import os
import signal
import webbrowser
from flask import Flask, jsonify
from flask_cors import CORS
import threading
import time
import socket
import requests

app = Flask(__name__)
CORS(app)

# 全局变量存储API服务进程
api_process = None
api_status = {
    'running': False,
    'pid': None,
    'start_time': None
}

# 获取当前目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
API_SCRIPT = os.path.join(CURRENT_DIR, 'api.py')
API_PORT = 5000


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
                    # 使用 os.system 执行 Windows 命令
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
    """获取API服务状态"""
    global api_process, api_status

    # 通过端口检测服务是否在运行
    is_running = is_port_in_use(API_PORT)
    api_status['running'] = is_running

    if not is_running:
        api_status['pid'] = None
        api_process = None

    return jsonify({
        'success': True,
        'data': api_status
    })


@app.route('/launcher/start', methods=['POST'])
def start_api():
    """启动API服务"""
    global api_process, api_status

    if api_status['running']:
        return jsonify({
            'success': False,
            'error': 'API服务已在运行中'
        })

    try:
        # 启动API服务
        api_process = subprocess.Popen(
            [sys.executable, API_SCRIPT],
            cwd=CURRENT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )

        # 等待一下确保服务启动
        time.sleep(1)

        # 检查是否启动成功
        if api_process.poll() is None:
            api_status['running'] = True
            api_status['pid'] = api_process.pid
            api_status['start_time'] = time.strftime('%Y-%m-%d %H:%M:%S')

            return jsonify({
                'success': True,
                'message': 'API服务已启动',
                'data': api_status
            })
        else:
            return jsonify({
                'success': False,
                'error': 'API服务启动失败'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/launcher/stop', methods=['POST'])
def stop_api():
    """停止API服务"""
    global api_process, api_status

    # 检查端口是否在使用
    if not is_port_in_use(API_PORT):
        return jsonify({
            'success': False,
            'error': 'API服务未在运行'
        })

    try:
        # 通过端口杀死进程
        kill_process_on_port(API_PORT)

        # 等待进程结束
        time.sleep(1)

        api_status['running'] = False
        api_status['pid'] = None
        api_process = None

        return jsonify({
            'success': True,
            'message': 'API服务已停止'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/launcher/health', methods=['GET'])
def health():
    """启动器健康检查"""
    return jsonify({'status': 'ok', 'message': '启动器服务运行中'})


def open_browser():
    """延迟打开浏览器"""
    time.sleep(1.5)
    html_path = os.path.join(CURRENT_DIR, 'game.html')
    webbrowser.open(f'file:///{html_path}')


if __name__ == '__main__':
    # 设置控制台编码
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 50)
    print("COC TRPG Game Launcher")
    print("=" * 50)
    print(f"Launcher: http://localhost:5001")
    print(f"API: http://localhost:5000")
    print("=" * 50)

    # 在新线程中打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()

    # 启动启动器服务
    app.run(host='0.0.0.0', port=5001, debug=False)
