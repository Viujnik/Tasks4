import asyncio
import shlex
import aiohttp
from src.models import Task
from src.functions import logger


class FileHandler:
    """Обработчик задачи, связанный с файлами."""

    async def handle(self, task: Task) -> None:
        logger.info(f"FileHandler: processing file task {task.task_id}")
        filename = task.payload.get("filename", "unknown")
        await asyncio.sleep(0.2)
        logger.info(f"FileHandler: finished processing file {filename}")


class ConsoleHandler:
    """Обработчик задачи, связанный с консолью."""

    async def handle(self, task: Task) -> None:
        logger.info(f"ConsoleHandler: processing console task {task.task_id}")

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
            logger.info(f"Command executed successfully: {stdout.decode()}")
        else:
            logger.error(f"Command failed: {stderr.decode()}")


class APIHandler:
    """Обработчик задачи, связанный с HTTP."""

    async def handle(self, task: Task) -> None:
        url = task.payload.get("url", "https://httpbin.org/get")
        method = task.payload.get("HTTP_METHOD", "GET")
        logger.info(f"APIHandler: processing request: {method} {url}")
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url) as resp:
                logger.info(f"Response status: {resp.status}")
