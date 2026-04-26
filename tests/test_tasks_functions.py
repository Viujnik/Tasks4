import pytest
from unittest.mock import MagicMock, patch

from src.models import Task
from src import functions
from src.queue import TaskQueue


@pytest.fixture
async def task_queue() -> TaskQueue:
    """Фикстура создаёт новую пустую очередь для каждого теста."""
    return TaskQueue()


@pytest.fixture(autouse=True)
def mock_logger(monkeypatch):
    """Отключаем логирование во всех тестах."""
    monkeypatch.setattr(functions.logger, "info", MagicMock())
    monkeypatch.setattr(functions.logger, "debug", MagicMock())
    monkeypatch.setattr(functions.logger, "warning", MagicMock())
    monkeypatch.setattr(functions.logger, "error", MagicMock())


async def test_create_task_with_custom_fields(monkeypatch, task_queue: TaskQueue):
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

    await functions.create_task("user123", task_queue)
    assert task_queue.qsize() == 1
    task = await task_queue.get_task()
    assert task.task_id == 42
    assert task.description == "My task description"
    assert task.priority == 4
    assert task.status == "created"
    assert "user_id" in task.payload


async def test_create_task_from_source(monkeypatch, task_queue: TaskQueue):
    """Автоматическая генерация задачи из источника."""
    inputs = iter(["file", "n", "5"])  # тип = file, выбор "n"
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    await functions.create_task("user123", task_queue)
    assert task_queue.qsize() == 5
    task = await task_queue.get_task()
    assert task.task_type == "file"


async def test_create_task_with_unknown_type(monkeypatch, task_queue: TaskQueue):
    """Неизвестный тип задачи с предупреждением в лог."""
    monkeypatch.setattr("builtins.input", lambda _: "unknown")
    await functions.create_task("user123", task_queue)
    assert task_queue.qsize() == 0


async def test_create_task_validation_error(monkeypatch, task_queue: TaskQueue):
    """Ошибка валидации с логом ошибки."""
    inputs = iter([
        "file", "y",
        "2025", "12", "31",
        "1", "key", "value",
        "1", "shrt", "3"  # слишком короткое описание – вызов LenError
    ])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    await functions.create_task("user123", task_queue)
    assert task_queue.qsize() == 0


async def test_set_task_status_success(monkeypatch, task_queue: TaskQueue):
    """Успешное изменение статуса существующей задачи."""
    inputs = iter(["file", "n", "1"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    await functions.create_task("user123", task_queue)

    assert task_queue.qsize() == 1
    task_id = (await task_queue.get_task()).task_id
    task = await task_queue.find_by_id(task_id)
    assert task is not None

    await functions.set_task_status("user123", task_id, "finished", task_queue)

    updated = await task_queue.find_by_id(task_id)
    assert updated is not None
    assert updated.status == "finished"


async def test_set_task_status_not_found(task_queue: TaskQueue):
    """Попытка изменить статус несуществующей задачи не вызывает ошибок."""
    await functions.set_task_status("user", 999, "finished", task_queue)


async def test_get_left_tasks(monkeypatch, capsys, task_queue: TaskQueue):
    """Извлечение первых N задач из очереди."""
    for _ in range(3):
        inputs = iter(["file", "n", "1"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        await functions.create_task("user", task_queue)
    assert task_queue.qsize() == 3

    await functions.get_left_tasks("user", 2, task_queue)
    assert task_queue.qsize() == 1


async def test_get_left_tasks_more_than_available(monkeypatch, capsys, task_queue: TaskQueue):
    """Запрос большего количества задач, чем есть в очереди."""
    inputs = iter(["file", "n", "1"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    await functions.create_task("user", task_queue)
    assert task_queue.qsize() == 1

    await functions.get_left_tasks("user", 5, task_queue)
    captured = capsys.readouterr()
    assert len(captured.out.strip().split('\n')) >= 1
    assert task_queue.qsize() == 0


async def test_get_left_tasks_empty_queue(capsys, task_queue: TaskQueue):
    """Крайний случай: очередь пуста – ничего не печатается и не удаляется."""
    await functions.get_left_tasks("user", 3, task_queue)
    captured = capsys.readouterr()
    assert captured.out == ""


async def test_set_status_after_finished(valid_task_data, task_queue: TaskQueue):
    """Нельзя менять статус завершенной задаче"""
    task = Task(**valid_task_data)
    task.status = "finished"
    await task_queue.add_task(task)

    with patch("src.functions.logger") as mock_logger:
        await functions.set_task_status(
            current_user_id="user123",
            task_id=task.task_id,
            task_status="created",
            task_queue=task_queue
        )

        mock_logger.warning.assert_called_once()
        args, _ = mock_logger.warning.call_args
        assert "user123 tries to reopen finished task #123" in args[0]
