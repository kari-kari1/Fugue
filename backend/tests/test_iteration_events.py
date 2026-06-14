from app.services.event_publisher import EventType


def test_iteration_event_types():
    """测试迭代事件类型"""
    assert EventType.ITERATION_STARTED == "iteration.started"
    assert EventType.ITERATION_PROGRESS == "iteration.progress"
    assert EventType.ITERATION_COMPLETED == "iteration.completed"
    assert EventType.ITERATION_FAILED == "iteration.failed"
