from typing import runtime_checkable, Protocol

from src.tasks_models import Task


@runtime_checkable
class TasksGiver(Protocol):
    """Интерфейс для источников задач."""

    def get_tasks(self) -> list[Task]:
        """Получить список или итератор задач."""
        ...

    def printf_task(self, task: Task) -> str:
        """Сформировать строковое представление деталей задачи."""
        ...


@runtime_checkable
class TaskHandler(Protocol):
    """Интерфейс для обработчика задач из очереди."""

    async def handle(self, task: Task) -> None:
        ...
