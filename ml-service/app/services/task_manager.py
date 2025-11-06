"""
Task Manager for async video processing with progress tracking
Tracks video processing tasks and their progress
"""
import asyncio
import uuid
import time
import logging
from typing import Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskProgress:
    """Progress information for a video processing task"""
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0  # 0.0 to 1.0
    current_frame: int = 0
    total_frames: int = 0
    message: str = "Task queued"
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON response"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "progress": round(self.progress, 2),
            "current_frame": self.current_frame,
            "total_frames": self.total_frames,
            "message": self.message,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "elapsed_time": round(time.time() - self.started_at, 2) if self.started_at else 0,
            "result": self.result,
            "error": self.error
        }


class TaskManager:
    """
    Manages video processing tasks with progress tracking
    Singleton instance shared across the application
    """

    def __init__(self, max_tasks: int = 100, task_ttl: int = 3600):
        """
        Initialize task manager

        Args:
            max_tasks: Maximum number of tasks to keep in memory
            task_ttl: Time to live for completed tasks (seconds)
        """
        self.tasks: Dict[str, TaskProgress] = {}
        self.max_tasks = max_tasks
        self.task_ttl = task_ttl
        self._cleanup_task: Optional[asyncio.Task] = None
        logger.info(f"TaskManager initialized (max_tasks={max_tasks}, ttl={task_ttl}s)")

    def create_task(self, total_frames: int = 0) -> str:
        """
        Create a new task and return task ID

        Args:
            total_frames: Total number of frames in video

        Returns:
            Task ID (UUID)
        """
        task_id = str(uuid.uuid4())
        task = TaskProgress(
            task_id=task_id,
            total_frames=total_frames,
            message="Task created, waiting to start"
        )
        self.tasks[task_id] = task
        logger.info(f"Created task {task_id} (total_frames={total_frames})")

        # Clean up old tasks if we have too many
        self._cleanup_old_tasks()

        return task_id

    def get_task(self, task_id: str) -> Optional[TaskProgress]:
        """
        Get task by ID

        Args:
            task_id: Task ID

        Returns:
            TaskProgress or None if not found
        """
        return self.tasks.get(task_id)

    def update_progress(
        self,
        task_id: str,
        current_frame: int,
        message: Optional[str] = None
    ) -> None:
        """
        Update task progress

        Args:
            task_id: Task ID
            current_frame: Current frame number
            message: Optional status message
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for progress update")
            return

        task.current_frame = current_frame
        if task.total_frames > 0:
            task.progress = min(current_frame / task.total_frames, 1.0)

        if message:
            task.message = message

        # Update status
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.PROCESSING
            task.started_at = time.time()

    def complete_task(self, task_id: str, result: Dict) -> None:
        """
        Mark task as completed

        Args:
            task_id: Task ID
            result: Result data
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for completion")
            return

        task.status = TaskStatus.COMPLETED
        task.progress = 1.0
        task.completed_at = time.time()
        task.result = result
        task.message = "Processing completed successfully"

        elapsed = task.completed_at - (task.started_at or task.created_at)
        logger.info(f"Task {task_id} completed in {elapsed:.2f}s")

    def fail_task(self, task_id: str, error: str) -> None:
        """
        Mark task as failed

        Args:
            task_id: Task ID
            error: Error message
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for failure")
            return

        task.status = TaskStatus.FAILED
        task.completed_at = time.time()
        task.error = error
        task.message = f"Processing failed: {error}"

        logger.error(f"Task {task_id} failed: {error}")

    def _cleanup_old_tasks(self) -> None:
        """Remove old completed/failed tasks if we exceed max_tasks"""
        if len(self.tasks) <= self.max_tasks:
            return

        # Sort by completion time, oldest first
        completed_tasks = [
            (task_id, task) for task_id, task in self.tasks.items()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            and task.completed_at is not None
        ]

        completed_tasks.sort(key=lambda x: x[1].completed_at)

        # Remove oldest tasks
        to_remove = len(self.tasks) - self.max_tasks + 10  # Remove a few extra
        for task_id, _ in completed_tasks[:to_remove]:
            del self.tasks[task_id]
            logger.debug(f"Cleaned up task {task_id}")

    def get_all_tasks(self) -> Dict[str, Dict]:
        """
        Get all tasks (for admin/debugging)

        Returns:
            Dictionary of task_id -> task dict
        """
        return {task_id: task.to_dict() for task_id, task in self.tasks.items()}

    def get_stats(self) -> Dict:
        """
        Get task manager statistics

        Returns:
            Statistics dictionary
        """
        statuses = {}
        for task in self.tasks.values():
            status = task.status.value
            statuses[status] = statuses.get(status, 0) + 1

        return {
            "total_tasks": len(self.tasks),
            "by_status": statuses,
            "max_tasks": self.max_tasks,
            "task_ttl": self.task_ttl
        }


# Global singleton instance
_task_manager_instance: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """Get or create the global TaskManager instance"""
    global _task_manager_instance
    if _task_manager_instance is None:
        _task_manager_instance = TaskManager()
    return _task_manager_instance
