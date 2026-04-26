import pytest
import datetime
from src.models import Task
from src.validators.errors import LenError, StatusError


def test_correct_task_creation(valid_task_data):
    """Правильный случай: задача создаётся без ошибок."""
    task = Task(**valid_task_data)
    assert task.task_id == 123
    assert task.status == "created"


def test_invalid_type(valid_task_data):
    """Ошибка типа: task_id должен быть int."""
    valid_task_data["task_id"] = "not_an_int"
    with pytest.raises(TypeError, match="должен быть <class 'int'>"):
        Task(**valid_task_data)


def test_invalid_status(valid_task_data):
    """Ошибка статуса: недопустимое значение."""
    valid_task_data["status"] = "hacking_rkn"
    with pytest.raises(StatusError, match="должно быть одним из"):
        Task(**valid_task_data)


def test_min_len_description(valid_task_data):
    """Ошибка длины: описание слишком короткое."""
    valid_task_data["description"] = "short"
    with pytest.raises(LenError, match="не меньше 8"):
        Task(**valid_task_data)


def test_max_len_description(valid_task_data):
    """Ошибка длины: описание слишком длинное."""
    valid_task_data["description"] = "x" * 260
    with pytest.raises(LenError, match="не больше 128"):
        Task(**valid_task_data)


def test_priority_too_low(valid_task_data):
    """Ошибка значения: приоритет не меньше 1."""
    valid_task_data["priority"] = 0
    with pytest.raises(ValueError, match="не меньше 1"):
        Task(**valid_task_data)


def test_priority_too_high(valid_task_data):
    """Ошибка значения: приоритет не больше 5"""
    valid_task_data["priority"] = 10
    with pytest.raises(ValueError, match="не больше 5"):
        Task(**valid_task_data)


def test_is_on_time_property(valid_task_data):
    """Вычисляемое свойство is_on_time: условия 'в срок' и 'просрочено'."""
    valid_task_data["status"] = "finished"
    valid_task_data["deadline"] = datetime.datetime.now() + datetime.timedelta(days=5)
    task = Task(**valid_task_data)
    assert task.is_on_time is True

    valid_task_data["deadline"] = datetime.datetime.now() - datetime.timedelta(days=1)
    task_late = Task(**valid_task_data)
    assert task_late.is_on_time is False


def test_summary_content(valid_task_data):
    """Свойство summary содержит id, тип и статус."""
    task = Task(**valid_task_data)
    summary = task.summary
    assert str(task.task_id) in summary
    assert task.task_type in summary
    assert "CREATED" in summary
