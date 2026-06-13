"""Fugue 一键启动脚本 — 自动启动后端+前端开发服务器

用法:
    python dev.py          # 启动后端+前端（默认）
    python dev.py backend   # 仅启动后端
    python dev.py frontend  # 仅启动前端
    python dev.py kill      # 清理残留进程
"""

import subprocess
import sys
import os
import time
import signal
import platform
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"

processes = []


def print_step(msg: str):
    print(f"\n{'='*60}\n  {msg}\n{'='*60}")


def kill_port(port: int):
    """终止占用指定端口的进程"""
    print(f"  检查端口 {port}...")
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    print(f"  端口 {port} 被 PID {pid} 占用，正在终止...")
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
                    print(f"  PID {pid} 已终止")
                    time.sleep(0.5)
        else:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"], capture_output=True, text=True
            )
            for pid in result.stdout.strip().split("\n"):
                if pid:
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"  已终止 PID {pid}")
    except Exception as e:
        print(f"  端口清理异常: {e}")


def start_backend():
    """启动 FastAPI 后端"""
    print_step("启动后端 (FastAPI + Uvicorn)")
    os.chdir(str(BACKEND_DIR))

    # 清理残留的 sidecar 进程
    if platform.system() == "Windows":
        subprocess.run(
            ["taskkill", "/F", "/IM", "fugue-backend.exe"],
            capture_output=True,
        )
    kill_port(8000)
    time.sleep(0.5)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)
    env["PYTHONUNBUFFERED"] = "1"

    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload",
            "--reload-dir", str(BACKEND_DIR / "app"),
        ],
        env=env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0,
    )
    processes.append(("Backend", proc))
    print("  后端启动中 (PID: {})...".format(proc.pid))

    # 等待后端就绪
    print("  等待后端就绪...", end="", flush=True)
    for _ in range(30):
        try:
            import urllib.request
            urllib.request.urlopen("http://127.0.0.1:8000/docs", timeout=1)
            print(" 就绪!")
            return
        except Exception:
            print(".", end="", flush=True)
            time.sleep(1)
    print("\n  ⚠ 后端可能未完全就绪，继续启动前端...")


def start_frontend():
    """启动 Vite 前端开发服务器（纯 Web 模式，无需编译 Tauri）"""
    print_step("启动前端 (Vite Dev Server)")
    os.chdir(str(FRONTEND_DIR))

    npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
    env = os.environ.copy()
    env["VITE_API_BASE_URL"] = "http://127.0.0.1:8000/api/v1"
    proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        env=env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0,
    )
    processes.append(("Frontend", proc))
    print("  前端启动中 (PID: {})...".format(proc.pid))


def cleanup():
    """清理所有子进程"""
    if not processes:
        return
    print_step("正在关闭...")
    for name, proc in processes:
        try:
            if platform.system() == "Windows":
                proc.terminate()
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            print(f"  {name} 已终止")
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode == "kill":
        print_step("清理残留进程")
        kill_port(8000)
        kill_port(1420)
        print("  清理完成")
        return

    if mode == "backend":
        signal.signal(signal.SIGINT, lambda s, f: cleanup())
        signal.signal(signal.SIGTERM, lambda s, f: cleanup())
        start_backend()
        print("\n  后端运行中 (http://127.0.0.1:8000) — Ctrl+C 停止\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            cleanup()

    elif mode == "frontend":
        signal.signal(signal.SIGINT, lambda s, f: cleanup())
        signal.signal(signal.SIGTERM, lambda s, f: cleanup())
        start_frontend()
        print("\n  前端运行中 — Ctrl+C 停止\n")
        # 自动打开浏览器
        print("  正在打开浏览器...")
        webbrowser.open("http://localhost:1420")
        print("  浏览器已打开!\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            cleanup()

    else:  # all
        signal.signal(signal.SIGINT, lambda s, f: cleanup())
        signal.signal(signal.SIGTERM, lambda s, f: cleanup())
        print_step("Fugue 一键启动")
        start_backend()
        start_frontend()
        print(f"\n{'='*60}")
        print("  后端:  http://127.0.0.1:8000")
        print("  API文档: http://127.0.0.1:8000/docs")
        print("  前端:  http://localhost:1420")
        print(f"  Ctrl+C 停止所有服务\n{'='*60}\n")
        # 自动打开浏览器
        print("  正在打开浏览器...")
        webbrowser.open("http://localhost:1420")
        print("  浏览器已打开 — 开始使用 Fugue!\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            cleanup()
            print("\n  Fugue 已停止\n")


if __name__ == "__main__":
    main()
