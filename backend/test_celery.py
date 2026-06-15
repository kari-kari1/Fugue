#!/usr/bin/env python3
"""
Celery集成测试脚本

测试Celery配置和任务定义是否正确
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_celery_config():
    """测试Celery配置"""
    print("=== 测试Celery配置 ===")

    try:
        from app.core.config import settings
        print(f"[OK] 配置加载成功")
        print(f"  - CELERY_BROKER_URL: {settings.CELERY_BROKER_URL}")
        print(f"  - CELERY_RESULT_BACKEND: {settings.CELERY_RESULT_BACKEND}")
        print(f"  - USE_CELERY: {settings.USE_CELERY}")
    except Exception as e:
        print(f"[FAIL] 配置加载失败: {e}")
        return False

    return True


def test_celery_app():
    """测试Celery应用创建"""
    print("\n=== 测试Celery应用 ===")

    try:
        from app.tasks.celery_app import celery_app
        print(f"[OK] Celery应用创建成功")
        print(f"  - 应用名称: {celery_app.main}")
        print(f"  - Broker: {celery_app.conf.broker_url}")
        print(f"  - Backend: {celery_app.conf.result_backend}")
        print(f"  - 序列化器: {celery_app.conf.task_serializer}")
        print(f"  - 时区: {celery_app.conf.timezone}")
        return True
    except Exception as e:
        print(f"[FAIL] Celery应用创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tasks_import():
    """测试任务导入"""
    print("\n=== 测试任务导入 ===")

    try:
        from app.tasks import execute_workflow, cancel_execution
        print(f"[OK] 任务导入成功")
        print(f"  - execute_workflow: {execute_workflow.name}")
        print(f"  - cancel_execution: {cancel_execution.name}")
        return True
    except Exception as e:
        print(f"[FAIL] 任务导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_changes():
    """测试模型变更"""
    print("\n=== 测试Execution模型 ===")

    try:
        from app.models.execution import Execution
        # 检查是否有celery_task_id字段
        if hasattr(Execution, 'celery_task_id'):
            print(f"[OK] Execution模型包含celery_task_id字段")
            col = Execution.__table__.columns.get('celery_task_id')
            print(f"  - 字段类型: {col.type}")
            print(f"  - 可空: {col.nullable}")
            return True
        else:
            print(f"[FAIL] Execution模型缺少celery_task_id字段")
            return False
    except Exception as e:
        print(f"[FAIL] 模型检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_import():
    """测试API导入"""
    print("\n=== 测试执行API ===")

    try:
        from app.api.v1.executions import router
        print(f"[OK] 执行API导入成功")
        # 检查路由
        routes = [route.path for route in router.routes]
        print(f"  - 路由数量: {len(routes)}")
        for route in routes:
            print(f"    - {route}")
        return True
    except Exception as e:
        print(f"[FAIL] API导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("Fugue Celery集成测试")
    print("=" * 50)

    results = []
    results.append(("Celery配置", test_celery_config()))
    results.append(("Celery应用", test_celery_app()))
    results.append(("任务导入", test_tasks_import()))
    results.append(("模型变更", test_model_changes()))
    results.append(("API导入", test_api_import()))

    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print("=" * 50)

    all_passed = True
    for name, passed in results:
        status = "[OK] 通过" if passed else "[FAIL] 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("[OK] 所有测试通过！Celery集成配置正确。")
        print("\n下一步:")
        print("1. 启动Docker服务: docker-compose up -d redis postgres celery-worker")
        print("2. 测试任务提交: 调用执行API")
        return 0
    else:
        print("[FAIL] 部分测试失败，请检查上述错误。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
