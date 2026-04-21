from src.sources import FileSource, ConsoleSource, APISource
from src.models import Task


def test_file_source_get_task():
    """FileSource всегда возвращает задачу с правильными полями."""
    source = FileSource()
    task = source.get_task()
    assert isinstance(task, Task)
    assert task.task_type == "file"
    assert task.status in {"created", "in_progress", "in_review", "finished"}
    assert "filename" in task.payload
    assert 1 <= task.priority <= 5


def test_console_source_get_task(monkeypatch):
    """ConsoleSource использует ввод пользователя для команды."""
    monkeypatch.setattr("builtins.input", lambda _: "test_command")
    source = ConsoleSource()
    task = source.get_task()
    assert task.task_type == "console"
    assert task.payload["command"] == "test_command"
    assert task.payload["status"] in {"OK", "ERROR", "WARNING", "CRITICAL"}


def test_api_source_get_task():
    """APISource: статус может быть finished или in_review."""
    source = APISource()
    task = source.get_task()
    assert task.task_type == "api"
    assert task.status in {"finished", "in_review"}
    assert "HTTP_METHOD" in task.payload
    assert task.payload["url"] == "https://rkn.gov.ru"
