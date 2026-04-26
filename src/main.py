import asyncio
import random
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

from src.queue import TaskQueue
from src.functions import create_task, set_task_status, get_left_tasks
from src.handlers import FileHandler, ConsoleHandler, APIHandler
from src.executor import TasksExecutor


async def main():
    queue = TaskQueue()
    handlers = {
        "file": FileHandler(),
        "cli": ConsoleHandler(),
        "api": APIHandler()
    }

    session = PromptSession()
    current_user_id = str(random.randint(1000000, 9999999))

    async with TasksExecutor(queue, handlers, num_workers=3) as _:
        while True:
            await asyncio.sleep(0.5)

            with patch_stdout():
                print("\n")
                print(f"USER ID: {current_user_id}")
                print("1: Создать задачу(и)")
                print("2: Изменить статус")
                print("3: Очистить N задач")
                print("4: Выход")

                choice = await session.prompt_async("Выберите действие: ")

            if choice == "1":
                await create_task(current_user_id, queue)

            elif choice == "2":
                with patch_stdout():
                    task_id = await session.prompt_async("Введите ID задачи: ")
                    status_type = await session.prompt_async("Введите новый статус: ")
                if task_id and status_type:
                    await set_task_status(current_user_id, int(task_id), status_type, queue)

            elif choice == "3":
                with patch_stdout():
                    task_num = await session.prompt_async("Сколько задач извлечь?: ")
                if task_num:
                    await get_left_tasks(current_user_id, int(task_num), queue)

            elif choice == "4":
                print("Завершение работы...")
                break

            else:
                print("Некорректный ввод, попробуйте снова.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
