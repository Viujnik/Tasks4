import pytest
import datetime
from src.tasks_models import Task
from src.queue import TaskQueue


@pytest.fixture
def valid_task_data() -> dict:
    """Базовая валидная задача для тестов."""
    return {
        "task_id": 123,
        "task_type": "service",
        "description": "This is a very long description for testing",
        "priority": 3,
        "status": "created",
        "deadline": datetime.datetime.now() + datetime.timedelta(days=1),
        "payload": {"key": "value"}
    }


@pytest.fixture
def sample_queue() -> TaskQueue:
    """Очередь с несколькими предустановленными задачами."""
    queue = TaskQueue()
    for i in range(1, 4):
        task = Task(
            task_id=i,
            task_type="test",
            description=f"Описание {i} задачи",
            priority=i,
            status="created" if i != 3 else "finished",
            deadline=datetime.datetime.now() + datetime.timedelta(days=i),
            payload={}
        )
        queue.add_task(task)
    return queue
