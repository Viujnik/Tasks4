import datetime
import random
from loguru import logger
from src.sources import FileSource, ConsoleSource, APISource
from src.models import Task
from src.validators.errors import LenError, StatusError
from src.queue import TaskQueue

logger.add("tasks.log", rotation="10 MB", retention="1 week", encoding="utf-8")



def get_task_deadline() -> datetime.datetime:
    dl_year = input("Введите год для дедлайна:\t")
    dl_month = input("Введите месяц для дедлайна:\t")
    dl_day = input("Введите день для дедлайна:\t")
    return datetime.datetime(int(dl_year), int(dl_month), int(dl_day))


def get_task_payload() -> dict[str, str]:
    """
    Собирает ввод пользователя в словарь для поля задачи - payload.
    """
    payload = {}
    cnt = int(input("Введите количество ключей для поля payload: "))
    for i in range(cnt):
        key, value = input("key:\t"), input("value:\t")
        payload[key] = value
    return payload


async def create_task(current_user_id, task_queue: TaskQueue) -> None:
    """
    Создает задачи, базовые настройки для которых выбирает пользователь.
    """
    try:

        task_type = input("Введите тип для новой задачи(file, cli, api):\t").lower()
        print(
            "Вам будет предложено выбрать значения некоторых полей. Вы можете ничего не вводить и нажать Enter, тогда значения будут выбираться случайно.")
        choice = input("Вы хотите настроить поля задачи?(\"y\" для подтверждения, иначе - любой символ):\t").lower()
        if task_type == "file":
            source = FileSource()
        elif task_type == "cli":
            source = ConsoleSource()
        elif task_type == "api":
            source = APISource()
        else:
            logger.warning(f"Пользователь {current_user_id} попытался создать задачу с неизвестным типом: {task_type}")
            return None

        if choice == "y":
            deadline = get_task_deadline()
            payload = get_task_payload()
            payload["user_id"] = str(random.randint(1000000, 9999999))
            created_task = Task(task_id=int(input("id:\t")), task_type=task_type, description=input("description:\t"),
                                priority=int(input("priority:\t")), status="created",
                                deadline=deadline,
                                payload=payload)
            logger.info("User {created_task.payload['user_id']} created a new task:")
            logger.info(created_task.log_message(detailed=False))
            logger.debug(created_task.log_message(detailed=True))
            await task_queue.add_task(created_task)

        else:
            new_tasks_num = int(input("Введите, сколько задач вы бы хотели создать: "))
            for _ in range(new_tasks_num):
                task = source.get_task()
                logger.info(f"Automatically generated task: {task.log_message(detailed=False)}")
                logger.debug(task.log_message(detailed=True))
                await task_queue.add_task(task)
    except (TypeError, ValueError, LenError, StatusError) as e:
        logger.error(f"Validation error during task creation: {e}")
        return None


async def set_task_status(current_user_id, task_id: int, task_status: str, task_queue: TaskQueue) -> None:
    task = await task_queue.find_by_id(task_id)
    if task:
        if task.status == "finished" and task_status != "finished":
            logger.warning(f"User {current_user_id} tries to reopen finished task #{task_id}")
        task.status = task_status
        logger.info(f"User {current_user_id} changed task #{task_id} status to {task_status}")
    else:
        logger.error(f"Task #{task_id} not found in registry")


async def get_left_tasks(current_user_id: str, task_num: int, task_queue: TaskQueue) -> None:
    count = 0
    while not task_queue.empty() and count < task_num:
        count += 1
        task = await task_queue.get_task()
        task_queue.task_done()
        logger.info(
            f"User {current_user_id} removed task #{task.task_id} from queue (manual cleanup)")
        print(task)
