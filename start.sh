#!/bin/bash
# COC Game - 一键启动脚本 (Linux/Mac)

echo ""
echo "================================================"
echo "  COC Game - 一键启动"
echo "================================================"
echo ""

# 获取脚本所在目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "[错误] 虚拟环境不存在！"
    echo ""
    echo "请先运行 ./setup_venv.sh 安装环境"
    echo ""
    exit 1
fi

# 激活虚拟环境
echo "[0/4] 激活虚拟环境..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[错误] 激活虚拟环境失败"
    exit 1
fi

# 检查并关闭占用的端口
echo "[1/4] 检查端口占用..."
lsof -ti:5780 | xargs kill -9 2>/dev/null
lsof -ti:5770 | xargs kill -9 2>/dev/null
sleep 1

# 启动后端服务
echo "[2/4] 启动后端服务 (FastAPI - 端口 5780)..."
gnome-terminal --title="Backend-5780" -- bash -c "cd '$SCRIPT_DIR' && source venv/bin/activate && python -m src_test.adapter.api.main; exec bash" 2>/dev/null \
|| xterm -title "Backend-5780" -e "bash -c 'cd \"$SCRIPT_DIR\" && source venv/bin/activate && python -m src_test.adapter.api.main; exec bash'" 2>/dev/null \
|| osascript -e 'tell app "Terminal" to do script "cd '"$SCRIPT_DIR"' && source venv/bin/activate && python -m src_test.adapter.api.main"' 2>/dev/null \
|| (source venv/bin/activate && python -m src_test.adapter.api.main > /tmp/backend.log 2>&1 &)

sleep 3

# 启动前端服务
echo "[3/4] 启动前端服务 (HTTP - 端口 5770)..."
gnome-terminal --title="Frontend-5770" -- bash -c "cd '$SCRIPT_DIR/src_test/front' && source ../../venv/bin/activate && python -m http.server 5770; exec bash" 2>/dev/null \
|| xterm -title "Frontend-5770" -e "bash -c 'cd \"$SCRIPT_DIR/src_test/front\" && source ../../venv/bin/activate && python -m http.server 5770; exec bash'" 2>/dev/null \
|| osascript -e 'tell app "Terminal" to do script "cd '"$SCRIPT_DIR/src_test/front"' && source ../../venv/bin/activate && python -m http.server 5770"' 2>/dev/null \
|| (cd "$SCRIPT_DIR/src_test/front" && source ../../venv/bin/activate && python -m http.server 5770 > /tmp/frontend.log 2>&1 &)

sleep 2

# 打开浏览器
echo "[4/4] 打开游戏页面..."
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:5770/game.html" 2>/dev/null
elif command -v open &> /dev/null; then
    open "http://localhost:5770/game.html" 2>/dev/null
else
    echo "请手动打开浏览器访问: http://localhost:5770/game.html"
fi

echo ""
echo "================================================"
echo "  启动完成！"
echo "================================================"
echo ""
echo "服务地址:"
echo "  - 后端 (FastAPI):  http://localhost:5780"
echo "  - 前端 (HTTP):     http://localhost:5770"
echo "  - API 文档:        http://localhost:5780/docs"
echo ""
echo "按 Ctrl+C 停止所有服务..."
echo ""

# 等待用户中断
trap "echo ''; echo '正在关闭所有服务...'; lsof -ti:5780 | xargs kill -9 2>/dev/null; lsof -ti:5770 | xargs kill -9 2>/dev/null; echo '所有服务已关闭'; exit 0" INT TERM

while true; do
    sleep 1
done
