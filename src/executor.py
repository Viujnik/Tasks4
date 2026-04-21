import asyncio
import datetime
from src.functions import logger
from src.protocols import TaskHandler
from src.queue import TaskQueue


class TasksExecutor:
    """Забирает задачи из очереди и вызывает обработчики."""

    def __init__(self, queue: TaskQueue, handlers: dict[str, TaskHandler], num_workers: int = 3):
        self._queue = queue
        self._handlers = handlers
        self._num_workers = num_workers
        self._workers: list[asyncio.Task] = []
        self._stop_event = asyncio.Event()

    def start(self):
        """Запускает воркеров в фоновом режиме."""
        self._stop_event.clear()
        for i in range(self._num_workers):
            task = asyncio.create_task(self._worker(i + 1))
            self._workers.append(task)
        logger.info(f"Executor started with {self._num_workers} workers")

    async def stop(self):
        """Инициирует мягкую остановку всех воркеров."""
        logger.info("Stopping tasks executor...")
        self._stop_event.set()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("Tasks executor stopped")

    async def _worker(self, worker_id) -> None:
        """Рабочая корутина: бесконечно получает задачи и обрабатывает."""
        while not self._stop_event.is_set():
            try:
                task = await asyncio.wait_for(self._queue.get_task(), timeout=1.0)
                if task.deadline < datetime.datetime.now():
                    logger.warning(f"Worker {worker_id}: Task #{task.task_id} is OVERDUE! Deadline: {task.deadline}")
                task.status = "in_progress"
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            try:
                handler = self._handlers[task.task_type]
                if not handler:
                    logger.critical(f"Worker {worker_id} — No handler for task type: '{task.task_type}'")
                logger.debug(f"Worker {worker_id} processing task {task.task_id}")
                await handler.handle(task)
                task.status = "finished"
                logger.info(f"Worker {worker_id} finished task {task.task_id}")
            except Exception as e:
                logger.error(f"Worker {worker_id} failed task {task.task_id}: {e}")
            finally:
                self._queue.task_done()

    async def __aenter__(self):
        self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
