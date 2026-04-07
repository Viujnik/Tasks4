import datetime
import json
from src.validators.fields import ValidatedField
from src.validators.rules import TypeRule, MinLenRule, MaxLenRule, MinValueRule, MaxValueRule, StatusRule


class Task:
    """Модель задачи с валидацией полей через дескрипторы."""
    task_id = ValidatedField(TypeRule(int))
    task_type = ValidatedField(TypeRule(str), MinLenRule(3), MaxLenRule(16))
    description = ValidatedField(TypeRule(str), MinLenRule(8), MaxLenRule(128))
    priority = ValidatedField(TypeRule(int), MinValueRule(1), MaxValueRule(5))
    status = ValidatedField(TypeRule(str), StatusRule({"created", "in_progress", "in_review", "finished"}))
    created_at = ValidatedField(TypeRule(datetime.datetime))
    deadline = ValidatedField(TypeRule(datetime.datetime))
    payload = ValidatedField(TypeRule(dict))

    def __init__(self, task_id: int, task_type: str, description: str,
                 priority: int, status: str, deadline: datetime.datetime, payload: dict) -> None:
        """Инициализирует задачу и устанавливает дату создания."""
        self.task_id = task_id
        self.task_type = task_type
        self.description = description
        self.priority = priority
        self.status = status
        self.created_at = datetime.datetime.now()
        self.deadline = deadline
        self.payload = payload

    @property
    def is_on_time(self) -> bool:
        """Проверяет, завершена ли задача в течение 3 дней с момента создания."""
        return self.status == "finished" and self.created_at + datetime.timedelta(days=3) <= self.deadline

    @property
    def summary(self) -> str:
        """Возвращает краткую сводку о состоянии задачи с иконкой успеха."""
        return f"Task #{self.task_id} ({self.task_type})\t{self.status.upper()}"

    def __repr__(self) -> str:
        """Строковое представление объекта задачи."""
        return f"Task(id={self.task_id}, type='{self.task_type}', status='{self.status}')"

    def log_data(self, detailed: bool = False) -> dict:
        """
        Возвращает структурированные данные для логирования.
        """
        base = {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "deadline": self.deadline.isoformat(),
            "created_at": self.created_at.isoformat(),
        }

        if "user_id" in self.payload:
            base["created_by"] = self.payload["user_id"]

        if detailed:
            payload_str = json.dumps(self.payload, ensure_ascii=False, default=str)
            base["payload"] = payload_str
        else:
            if self.task_type == "file":
                base["file"] = self.payload.get("filename", "N/A")
                base["file_size"] = self.payload.get("file_size", 0)
                base["sender"] = self.payload.get("sender_id", 0)
                base["receiver"] = self.payload.get("receiver_id", 0)
            elif self.task_type == "console":
                base["command"] = self.payload.get("command", "N/A")
                base["result"] = self.payload.get("status", "N/A")
            elif self.task_type == "api":
                base["method"] = self.payload.get("HTTP_METHOD", "N/A")
                base["url"] = self.payload.get("url", "N/A")
                base["client"] = self.payload.get("client_id", 0)

        return base

    def log_message(self, detailed: bool = False) -> str:
        """
        Возвращает строку для логирования.
        """
        data = self.log_data(detailed)

        if detailed:
            return f"Task created: {json.dumps(data, ensure_ascii=False, indent=2)}"
        else:
            parts = [
                f"Task #{data['task_id']} ({data['task_type']})",
                f"status={data['status']}",
                f"priority={data['priority']}",
                f"deadline={data['deadline'][:16]}"
            ]

            if "created_by" in data:
                parts.insert(1, f"user={data['created_by']}")

            if "file" in data:
                parts.append(f"file={data['file']} ({data['file_size']}MB)")
                if "sender" in data:
                    parts.append(f"from={data['sender']}")
                if "receiver" in data:
                    parts.append(f"to={data['receiver']}")
            elif "command" in data:
                parts.append(f"cmd='{data['command']}'")
                parts.append(f"result={data['result']}")
            elif "method" in data:
                parts.append(f"{data['method']} {data['url']}")
                parts.append(f"client={data['client']}")

            return " | ".join(parts)
