import datetime

import pytest

from src.models import Task

pytestmark = pytest.mark.asyncio


async def test_add_and_len(sample_queue):
    """Проверка добавления и длины."""
    assert sample_queue.qsize() == 3
    new_task = Task(99, "test", "description", 1, "created", datetime.datetime.now(), {})
    await sample_queue.add_task(new_task)
    assert sample_queue.qsize() == 4


async def test_iteration(sample_queue):
    """Проверка итерация по очереди."""
    ids = [task.task_id async for task in sample_queue]
    assert ids == [1, 2, 3]


async def test_filter_by_status(sample_queue):
    """Проверка фильтрации по статусу."""
    created = [task.task_id async for task in sample_queue.filter_by_status("created")]
    assert created == [1, 2]
    finished = [task.task_id async for task in sample_queue.filter_by_status("finished")]
    assert finished == [3]
    unknown = [task.task_id async for task in sample_queue.filter_by_status("unknown")]
    assert unknown == []


async def test_filter_by_priority(sample_queue):
    """Проверка фильтрации по приоритету."""
    priority_2 = [task.task_id async for task in sample_queue.filter_by_priority(2)]
    assert len(priority_2) == 1 and priority_2[0] == 2
    priority_5 = [task.task_id async for task in sample_queue.filter_by_priority(5)]
    assert priority_5 == []


async def test_filter_by_deadline(sample_queue):
    """Проверка фильтрация просроченных задач."""
    overdue_task = Task(10, "test", "description", 1, "created",
                        datetime.datetime.now() - datetime.timedelta(days=1), {})
    await sample_queue.add_task(overdue_task)
    overdue = [task.task_id async for task in sample_queue.filter_by_deadline()]
    assert len(overdue) == 1
    assert overdue[0] == 10


async def test_find_by_id(sample_queue):
    """Проверка поиска по ID."""
    task = await sample_queue.find_by_id(2)
    assert task is not None and task.task_id == 2
    assert await sample_queue.find_by_id(999) is None


async def test_get_task(sample_queue):
    """Проверка извлечения слева."""
    first = await sample_queue.get_task()
    assert first.task_id == 1
    assert sample_queue.qsize() == 2
    second = await sample_queue.get_task()
    assert second.task_id == 2
    await sample_queue.get_task()
    assert sample_queue.qsize() == 0
