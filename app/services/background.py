# app/services/background.py

from fastapi import BackgroundTasks
from typing import Callable, Any
import asyncio
import logging
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)


class TaskManager:
    def __init__(self):
        self.tasks = {}
        self._cleanup_lock = asyncio.Lock()

    async def add_task(
            self,
            task_id: str,
            func: Callable,
            *args,
            **kwargs
    ) -> None:
        """Add a new background task with tracking."""
        self.tasks[task_id] = {
            'status': 'pending',
            'start_time': datetime.utcnow(),
            'completion_time': None,
            'error': None
        }

        try:
            # Execute task
            await func(*args, **kwargs)

            # Update status on completion
            self.tasks[task_id].update({
                'status': 'completed',
                'completion_time': datetime.utcnow()
            })

        except Exception as e:
            # Update status on failure
            self.tasks[task_id].update({
                'status': 'failed',
                'completion_time': datetime.utcnow(),
                'error': str(e)
            })
            logger.error(f"Task {task_id} failed: {str(e)}")
            raise

        finally:
            # Cleanup old tasks
            await self._cleanup_old_tasks()

    async def get_task_status(self, task_id: str) -> dict:
        """Get the status of a specific task."""
        return self.tasks.get(task_id, {
            'status': 'not_found',
            'error': 'Task not found'
        })

    async def _cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up completed tasks older than specified hours."""
        async with self._cleanup_lock:
            current_time = datetime.utcnow()
            tasks_to_remove = []

            for task_id, task_info in self.tasks.items():
                if task_info['completion_time']:
                    age = current_time - task_info['completion_time']
                    if age.total_seconds() > max_age_hours * 3600:
                        tasks_to_remove.append(task_id)

            for task_id in tasks_to_remove:
                del self.tasks[task_id]


# Create singleton instance
task_manager = TaskManager()


def background_task(func: Callable):
    """Decorator for background tasks with error handling and logging."""

    @wraps(func)
    async def wrapper(
            background_tasks: BackgroundTasks,
            *args,
            **kwargs
    ):
        task_id = f"{func.__name__}_{datetime.utcnow().timestamp()}"

        async def wrapped_func():
            try:
                logger.info(f"Starting background task: {task_id}")
                await task_manager.add_task(task_id, func, *args, **kwargs)
                logger.info(f"Completed background task: {task_id}")

            except Exception as e:
                logger.error(f"Background task failed: {task_id}", exc_info=True)
                raise

        background_tasks.add_task(wrapped_func)
        return {"task_id": task_id}

    return wrapper