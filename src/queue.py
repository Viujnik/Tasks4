import asyncio
import datetime
from asyncio import Queue, Lock
from typing import Callable, List, Any, AsyncIterator, AsyncGenerator

from src.tasks_models import Task


class TaskQueue:
    """
    Асинхронная очередь задач с реестром для фильтрации и поиска.
    """

    def __init__(self) -> None:
        self._tasks_queue: Queue[Task] = Queue()
        self._storage: List[Task] = []
        self._lock: Lock = Lock()

    async def add_task(self, task: Task) -> None:
        """Добавить задачу в реестр и очередь с использованием блокировки."""
        async with self._lock:
            self._storage.append(task)
            await self._tasks_queue.put(task)

    async def get_task(self) -> Task:
        """Извлечь задачу из очереди для обработки."""
        return await self._tasks_queue.get()

    def task_done(self) -> None:
        """Подтвердить выполнение задачи и уменьшить счетчик незавершенных дел."""
        self._tasks_queue.task_done()

    async def join(self) -> None:
        """Ожидать завершения всех задач, находящихся в очереди."""
        await self._tasks_queue.join()

    def qsize(self) -> int:
        """Получить текущее количество задач в очереди."""
        return self._tasks_queue.qsize()

    def empty(self) -> bool:
        """Проверить, пуста ли очередь в данный момент."""
        return self._tasks_queue.empty()

    async def __aiter__(self) -> AsyncIterator[Task]:
        """Получить итератор по текущему снимку всех задач в реестре."""
        async with self._lock:
            current_tasks = self._storage.copy()
        for task in current_tasks:
            yield task

    async def filter(self, condition: Callable[[Task], bool]) -> AsyncGenerator[Task, None]:
        """Асинхронная фильтрация задач с защитой от изменения данных во время обхода."""
        async with self._lock:
            current_tasks = self._storage.copy()

        for task in current_tasks:
            if condition(task):
                yield task
                await asyncio.sleep(0)

    async def filter_by_status(self, status: str) -> AsyncGenerator[Task, None]:
        """Отфильтровать задачи по их статусу."""
        async for task in self.filter(lambda t: t.status == status):
            yield task

    async def filter_by_priority(self, priority: int) -> AsyncGenerator[Task, None]:
        """Отфильтровать задачи по уровню приоритета."""
        async for task in self.filter(lambda t: t.priority == priority):
            yield task

    async def filter_by_deadline(self) -> AsyncGenerator[Task, None]:
        """Получить задачи, чей дедлайн наступил относительно текущего времени."""
        now = datetime.datetime.now()
        async for task in self.filter(lambda t: t.deadline <= now):
            yield task

    async def find_by_id(self, task_id: int) -> Task | None:
        """Найти конкретную задачу по её идентификатору в реестре."""
        async with self._lock:
            for task in self._storage:
                if task.task_id == task_id:
                    return task
        return None

    async def __aenter__(self) -> TaskQueue:
        """Вход в асинхронный контекст управления очередью."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Выход из контекста с ожиданием завершения всех активных задач."""
        await self.join()
