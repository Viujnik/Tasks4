import random

from src.tasks_functions import create_task, set_task_status, get_left_tasks


def tasks_creator():
    flag = True
    current_user_id = str(random.randint(1000000, 9999999))
    while flag:
        choice = int(input("Для создания задачи - 1\nДля смены статуса - 2\nДля получения(и удаление из очереди) первых n задач в очереди - 3\nВведите число:\t"))
        if choice == 1:
            create_task(current_user_id)

        elif choice == 2:
            status_type = input("Введите новый статус задачи:\t")
            task_id = input("Введите id задачи, статус которой вы хотите изменить:\t")
            set_task_status(current_user_id, int(task_id), status_type)

        elif choice == 3:
            task_num = int(input("Введите количество задач для получения:\t"))
            get_left_tasks(current_user_id, task_num)

        new_choice = input("Вы хотите продолжить?(y - да, иначе - любой символ):\t").lower()
        if new_choice != "y":
            flag = False

if __name__ == "__main__":
    tasks_creator()
