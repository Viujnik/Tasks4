import datetime
import random
from loguru import logger
from src.sources import FileSource, ConsoleSource, APISource
from src.tasks_models import Task
from src.validators.errors import LenError, StatusError
from src.queue import TaskQueue

logger.add("tasks.log", rotation="10 MB", retention="1 week", encoding="utf-8")

task_queue = TaskQueue()


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


def create_task(current_user_id) -> None:
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
            logger.info(f"Пользователь с id: {created_task.payload["user_id"]} создал новую задачу:")
            logger.info(created_task.log_message(detailed=False))
            logger.debug(created_task.log_message(detailed=True))
            task_queue.add_task(created_task)

        else:
            task = source.get_task()
            logger.info(task.log_message(detailed=False))
            logger.debug(task.log_message(detailed=True))
            task_queue.add_task(task)
    except (TypeError, ValueError, LenError, StatusError) as e:
        logger.error(f"Ошибка валидации при создании задачи: {e}")
        print(f"Ошибка: {e}")
        return None


def set_task_status(current_user_id, task_id: int, task_status: str):
    try:
        for task in task_queue:
            if task.task_id == task_id:
                task.status = task_status
                logger.info(
                    f"Пользователь с  id {current_user_id} сменил статус задачи с id: {task_id} на {task_status}")
    except KeyError as e:
        print(e)


def get_left_tasks(current_user_id: str, task_num: int):
    count = 0
    while task_queue and count < task_num:
        count += 1
        logger.info(
            f"Пользователь с  id {current_user_id} удалил {count} левых задач из очереди")
        print(task_queue.pop_left())
