#!/bin/bash
# COC Game - 虚拟环境安装/更新脚本 (Linux/Mac)

echo ""
echo "================================================"
echo "  COC Game - 虚拟环境安装/更新"
echo "================================================"
echo ""
echo "此脚本将："
echo "  1. 创建虚拟环境（如果不存在）"
echo "  2. 检查并安装/更新所有依赖"
echo ""

# 获取脚本所在目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查 Python3 是否可用
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3，请先安装 Python 3.10 或更高版本"
    exit 1
fi

echo "Python 版本: $(python3 --version)"
echo ""

# 创建虚拟环境
echo "[1/4] 检查虚拟环境..."
if [ -d "venv" ]; then
    echo "虚拟环境已存在"
else
    echo "创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[错误] 创建虚拟环境失败"
        exit 1
    fi
    echo "虚拟环境创建成功"
fi

echo ""
echo "[2/4] 激活虚拟环境..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[错误] 激活虚拟环境失败"
    exit 1
fi

echo ""
echo "[3/4] 升级 pip..."
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

echo ""
echo "[4/4] 安装/更新项目依赖..."
echo ""
echo "正在检查并安装以下包："
echo "  - langchain (AI框架)"
echo "  - fastapi (Web框架)"
echo "  - PyMySQL (数据库)"
echo "  - cryptography (MySQL加密连接)"
echo "  - loguru (日志)"
echo "  - PyJWT (认证)"
echo "  - 其他依赖..."
echo ""

pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if [ $? -ne 0 ]; then
    echo "[错误] 依赖安装失败"
    exit 1
fi

echo ""
echo "================================================"
echo "  安装/更新完成！"
echo "================================================"
echo ""
echo "虚拟环境位置: $SCRIPT_DIR/venv"
echo ""
echo "现在可以运行 ./start.sh 启动游戏"
echo ""
