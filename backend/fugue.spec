# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — Fugue Backend Sidecar"""

import os
import sys
from pathlib import Path

block_cipher = None

# 项目根目录
BACKEND_DIR = os.path.dirname(os.path.abspath(SPEC))
APP_DIR = os.path.join(BACKEND_DIR, 'app')

a = Analysis(
    [os.path.join(APP_DIR, '__main__.py')],
    pathex=[BACKEND_DIR],
    binaries=[],
    datas=[
        # Alembic 迁移文件
        (os.path.join(BACKEND_DIR, 'alembic'), 'alembic'),
        (os.path.join(BACKEND_DIR, 'alembic.ini'), '.'),
        # 插件目录
        (os.path.join(APP_DIR, 'plugins', 'plugins'), os.path.join('app', 'plugins', 'plugins')),
    ],
    hiddenimports=[
        # uvicorn 组件
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        # FastAPI
        'fastapi',
        'fastapi.responses',
        'fastapi.middleware.cors',
        'pydantic',
        'pydantic_settings',
        # SQLAlchemy
        'sqlalchemy',
        'sqlalchemy.ext.asyncio',
        'sqlalchemy.pool',
        'aiosqlite',
        # 认证
        'passlib',
        'passlib.handlers.bcrypt',
        'bcrypt',
        'jose',
        'jose.jwt',
        # HTTP
        'httpx',
        'websockets',
        # 工具
        'simpleeval',
        'duckduckgo_search',
        'croniter',
        'minio',
        'redis',
        # 增强工具插件依赖（在嵌套函数中导入，PyInstaller 无法自动检测）
        'docx',
        'docx.document',
        'docx.opc',
        'openpyxl',
        'pdfplumber',
        'bs4',
        'markdown',
        'PIL',
        'PIL.Image',
        'PIL.ExifTags',
        'tabulate',
        'chardet',
        'yaml',
        # 其他
        'email.mime.text',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除大型 ML 依赖（可选功能）
        'torch',
        'torchvision',
        'torchaudio',
        'transformers',
        'sentence_transformers',
        'chromadb',
        'onnxruntime',
        'chroma-hnswlib',
        'tokenizers',
        'safetensors',
        'huggingface_hub',
        'scipy',
        'scikit-learn',
        'numpy',
        'pandas',
        # 排除 Celery（桌面模式不使用）
        'celery',
        # 排除开发/测试工具
        'pytest',
        'playwright',
        'vitest',
        # 排除 uvloop（Windows 不支持）
        'uvloop',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='fugue-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保留控制台输出用于日志
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
