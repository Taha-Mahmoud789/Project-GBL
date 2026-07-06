import uuid
import time
from typing import Optional


class TaskManager:
    def __init__(self):
        self._tasks: dict[str, dict] = {}

    def create_task(self) -> str:
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = {
            "status": "pending",
            "progress": 0.0,
            "message": "Task created",
            "created_at": time.time(),
        }
        return task_id

    def update(self, task_id: str, progress: float, message: str, status: Optional[str] = None) -> None:
        if task_id in self._tasks:
            self._tasks[task_id].update({
                "progress": progress,
                "message": message,
            })
            if status:
                self._tasks[task_id]["status"] = status

    def get(self, task_id: str) -> Optional[dict]:
        return self._tasks.get(task_id)

    def complete(self, task_id: str) -> None:
        if task_id in self._tasks:
            self._tasks[task_id].update({
                "status": "completed",
                "progress": 1.0,
                "message": "Conversion complete",
            })

    def fail(self, task_id: str, error: str) -> None:
        if task_id in self._tasks:
            self._tasks[task_id].update({
                "status": "failed",
                "message": error,
            })
