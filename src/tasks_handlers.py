import asyncio
import shlex
import aiohttp
from src.tasks_models import Task
from src.tasks_functions import logger


class FileHandler:
    """Обработчик задачи, связанный с файлами."""

    async def handle(self, task: Task) -> None:
        logger.info(f"FileHandler: обработка файловой задачи {task.task_id}")
        filename = task.payload.get("filename", "unknown")
        await asyncio.sleep(0.2)
        logger.info(f"FileHandler: окончена обработка файла {filename}")


class ConsoleHandler:
    """Обработчик задачи, связанный с консолью."""

    async def handler(self, task: Task) -> None:
        logger.info(f"ConsoleHandler: обработка консольной задачи {task.task_id}")

        command = task.payload.get("command", "top")
        args = shlex.split(command)
        if not args:
            return

        process = await asyncio.create_subprocess_exec(
            args[0],
            *args[1:],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            logger.info(f"Команда выполнена успешно: {stdout.decode()}")
        else:
            logger.error(f"Команда завершилась ошибкой: {stderr.decode()}")


class APIHandler:
    """Обработчик задачи, связанный с HTTP."""

    async def handle(self, task: Task) -> None:
        url = task.payload.get("url", "https://httpbin.org/get")
        method = task.payload.get("HTTP_METHOD", "GET")
        logger.info(f"APIHandler: обработка запроса: {method} {url}")
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url) as resp:
                logger.info(f"Response status: {resp.status}")
