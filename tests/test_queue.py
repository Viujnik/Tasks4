import datetime
from src.tasks_models import Task


def test_add_and_len(sample_queue):
    """Проверка добавления и длины."""
    assert len(sample_queue) == 3
    new_task = Task(99, "test", "description", 1, "created", datetime.datetime.now(), {})
    sample_queue.add_task(new_task)
    assert len(sample_queue) == 4


def test_iteration(sample_queue):
    """Проверка итерация по очереди."""
    ids = [task.task_id for task in sample_queue]
    assert ids == [1, 2, 3]


def test_filter_by_condition(sample_queue):
    """Проверка фильтрации по произвольному условию."""
    result = list(sample_queue.filter(lambda t: t.priority > 1))
    assert [t.task_id for t in result] == [2, 3]


def test_filter_by_status(sample_queue):
    """Проверка фильтрации по статусу."""
    created = list(sample_queue.filter_by_status("created"))
    assert [t.task_id for t in created] == [1, 2]
    finished = list(sample_queue.filter_by_status("finished"))
    assert [t.task_id for t in finished] == [3]
    unknown = list(sample_queue.filter_by_status("unknown"))
    assert unknown == []


def test_filter_by_priority(sample_queue):
    """Проверка фильтрации по приоритету."""
    priority_2 = list(sample_queue.filter_by_priority(2))
    assert len(priority_2) == 1 and priority_2[0].task_id == 2
    priority_5 = list(sample_queue.filter_by_priority(5))
    assert priority_5 == []


def test_filter_by_deadline(sample_queue):
    """Проверка фильтрация просроченных задач."""
    overdue_task = Task(10, "test", "description", 1, "created",
                        datetime.datetime.now() - datetime.timedelta(days=1), {})
    sample_queue.add_task(overdue_task)
    overdue = list(sample_queue.filter_by_deadline())
    assert len(overdue) == 1
    assert overdue[0].task_id == 10


def test_find_by_id(sample_queue):
    """Проверка поиска по ID."""
    task = sample_queue.find_by_id(2)
    assert task is not None and task.task_id == 2
    assert sample_queue.find_by_id(999) is None


def test_pop_left(sample_queue):
    """Проверка извлечения слева."""
    first = sample_queue.pop_left()
    assert first.task_id == 1
    assert len(sample_queue) == 2
    second = sample_queue.pop_left()
    assert second.task_id == 2
    sample_queue.pop_left()
    assert sample_queue.pop_left() is None
