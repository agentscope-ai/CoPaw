#!/bin/bash
# Copaw Agent System 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🦞 Copaw Agent System"
echo "===================="

# 检查 Python 依赖
check_python_deps() {
    python3 -c "import fastapi, uvicorn, yaml" 2>/dev/null
}

# 检查 Node 依赖
check_node_deps() {
    cd dashboard/frontend
    [ -d "node_modules" ] || npm install
    cd ../..
}

# 启动后端
start_backend() {
    echo "📦 启动后端服务..."
    cd dashboard/backend
    python3 server.py &
    BACKEND_PID=$!
    cd ../..
    echo "后端 PID: $BACKEND_PID"
}

# 启动前端
start_frontend() {
    echo "🎨 启动前端服务..."
    cd dashboard/frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ../..
    echo "前端 PID: $FRONTEND_PID"
}

# 主流程
main() {
    echo ""
    echo "1. 检查依赖..."
    
    if ! check_python_deps; then
        echo "安装 Python 依赖..."
        pip3 install -r dashboard/backend/requirements.txt
    fi
    
    echo ""
    echo "2. 启动服务..."
    start_backend
    sleep 2
    start_frontend
    
    echo ""
    echo "✅ 服务已启动!"
    echo "   Dashboard: http://localhost:3000"
    echo "   API:       http://localhost:8766"
    echo ""
    echo "按 Ctrl+C 停止所有服务"
    
    # 等待
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
    wait
}

main "$@"