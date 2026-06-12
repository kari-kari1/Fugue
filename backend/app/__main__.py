"""Fugue 后端入口 — F2: 支持 python -m app 和 PyInstaller 打包"""

import socket
import sys


def find_available_port(start: int = 8000, max_tries: int = 10) -> int:
    """E6: 端口冲突检测 — 自动寻找可用端口"""
    for port in range(start, start + max_tries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    print(f"ERROR: No available port found in range {start}-{start + max_tries}")
    sys.exit(1)


if __name__ == "__main__":
    import uvicorn
    # 直接导入 app 对象 — PyInstaller 打包后字符串引用 "app.main:app" 无法解析
    from app.main import app

    port = find_available_port(8000)
    print(f"Starting Fugue on http://127.0.0.1:{port}")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="info",
    )
