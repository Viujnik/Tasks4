import pytest
from unittest.mock import MagicMock
from src import functions
from src.queue import TaskQueue


@pytest.fixture(autouse=True)
def clean_queue():
    """Автоматически подменяет глобальную очередь на новую перед каждым тестом."""
    tasks_functions.task_queue = TaskQueue()
    yield


def test_create_task_with_custom_fields(monkeypatch):
    """Пользователь вводит все поля вручную и задача добавляется в очередь."""
    inputs = iter([
        "file", "y",  # тип и выбор ручного ввода
        "2025", "12", "31",  # год, месяц, день дедлайна
        "2",  # количество ключей в payload
        "key1", "value1",  # первая пара key-value
        "key2", "value2",  # вторая пара
        "42",  # task_id
        "My task description",  # description
        "4"  # priority
    ])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(tasks_functions.logger, "info", MagicMock())
    monkeypatch.setattr(tasks_functions.logger, "debug", MagicMock())

    tasks_functions.create_task("user123")
    assert len(tasks_functions.task_queue) == 1
    task = tasks_functions.task_queue.pop_left()
    assert task.task_id == 42
    assert task.description == "My task description"
    assert task.priority == 4
    assert task.status == "created"
    assert "user_id" in task.payload


def test_create_task_from_source(monkeypatch):
    """Автоматическая генерация задачи из источника."""
    inputs = iter(["file", "n"])  # тип = file, выбор "n"
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(tasks_functions.logger, "info", MagicMock())
    monkeypatch.setattr(tasks_functions.logger, "debug", MagicMock())

    tasks_functions.create_task("user123")
    assert len(tasks_functions.task_queue) == 1
    task = tasks_functions.task_queue.pop_left()
    assert task.task_type == "file"


def test_create_task_with_unknown_type(monkeypatch):
    """Неизвестный тип задачи с предупреждением в лог."""
    monkeypatch.setattr("builtins.input", lambda _: "unknown")
    tasks_functions.create_task("user123")
    assert len(tasks_functions.task_queue) == 0


def test_create_task_validation_error(monkeypatch):
    """Ошибка валидации с логом ошибки."""
    inputs = iter([
        "file", "y",
        "2025", "12", "31",
        "1", "key", "value",
        "1", "shrt", "3"  # слишком короткое описание – вызов LenError
    ])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    tasks_functions.create_task("user123")
    assert len(tasks_functions.task_queue) == 0


def test_set_task_status_success(monkeypatch):
    """Успешное изменение статуса существующей задачи."""
    inputs = iter(["file", "n"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(tasks_functions.logger, "info", MagicMock())
    tasks_functions.create_task("user123")

    assert len(tasks_functions.task_queue) == 1
    task_id = tasks_functions.task_queue[0].task_id

    tasks_functions.set_task_status("user123", task_id, "finished")

    updated = tasks_functions.task_queue.find_by_id(task_id)
    assert updated is not None
    assert updated.status == "finished"


def test_set_task_status_not_found():
    """Попытка изменить статус несуществующей задачи не вызывает ошибок."""
    tasks_functions.set_task_status("user", 999, "finished")


def test_get_left_tasks(monkeypatch, capsys):
    """Извлечение первых N задач из очереди."""
    for _ in range(3):
        inputs = iter(["file", "n"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        tasks_functions.create_task("user")
    assert len(tasks_functions.task_queue) == 3

    tasks_functions.get_left_tasks("user", 2)
    assert len(tasks_functions.task_queue) == 1


def test_get_left_tasks_more_than_available(monkeypatch, capsys):
    """Запрос большего количества задач, чем есть в очереди."""
    inputs = iter(["file", "n"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    tasks_functions.create_task("user")
    assert len(tasks_functions.task_queue) == 1

    tasks_functions.get_left_tasks("user", 5)
    captured = capsys.readouterr()
    assert len(captured.out.strip().split('\n')) >= 1
    assert len(tasks_functions.task_queue) == 0


def test_get_left_tasks_empty_queue(capsys):
    """Крайний случай: очередь пуста – ничего не печатается и не удаляется."""
    tasks_functions.get_left_tasks("user", 3)
    captured = capsys.readouterr()
    assert captured.out == ""
