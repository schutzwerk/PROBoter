# Copyright (C) 2023 SCHUTZWERK GmbH
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import logging
from dataclasses import dataclass
from typing import TypeVar, Optional, List

from proboter.event_bus import EventBus
from proboter.model import TaskInfo, TaskStatus

from .task import Task
from .events import TaskStartedEvent, TaskFinishedEvent, TaskScheduledEvent

T = TypeVar("T")
S = TypeVar("S")


@dataclass
class ScheduledTask:
    """
    Scheduled task

    For internal task processor use only
    """
    # Lock to delay the task execution
    lock: asyncio.locks.Lock
    # asyncio task that executes the task's logic
    runner: asyncio.Task
    # The wrapped scheduled task
    task: Task


class TaskProcessor:
    """
    Processor that handles task scheduling and execution
    """

    log = logging.getLogger(__name__)

    def __init__(self, event_bus: EventBus):
        """
        Initialize a new task processor instance
        """
        self._event_bus = event_bus
        self._task_queue: List[ScheduledTask] = []
        self._task_queue_lock = asyncio.locks.Lock()
        self._current_task: ScheduledTask = None
        self._scheduler_task = None

    @ property
    def current_task(self) -> Optional[Task]:
        """
        Currently executed task

        :rtype: Task
        """
        if self._current_task is not None:
            return self._current_task.task
        return None

    async def start(self) -> None:
        """
        Start the task processor
        """
        # Stop the scheduler if it is active
        await self.stop()
        self._scheduler_task = asyncio.create_task(self.task_scheduler_loop())
        self.log.info("Task scheduler started")

    async def stop(self) -> None:
        """
        Stop the task processor
        """
        if self._scheduler_task is not None:
            self._scheduler_task.cancel()
            await asyncio.wait([self._scheduler_task,])
            self.log.info("Task processor stopped")

    async def house_keeping(self) -> None:
        """
        Perform house keeing tasks
        """
        self.log.info("Start task processor house keeping")
        # Mark all scheduled tasks as CANCELLED
        tasks = await TaskInfo.get_all()
        for task in tasks:
            if task.status == TaskStatus.SCHEDULED:
                self.log.info("Mark task %d as cancelled", task.id)
                task.status = TaskStatus.CANCELLED
                await task.save()

    async def schedule_task(self, task: Task[S, T]) -> int:
        """
        Schedule a task for later execution

        :param task: Task to execute
        :type task: Task[S, T]
        :return: ID of the scheduled task
        :rtype: int
        """
        self.log.info("Schedule task for execution")
        # Wrap the task execution into a delayed executed asyncio task
        lock = asyncio.locks.Lock()
        await lock.acquire()
        await task.info.save()
        runner = asyncio.create_task(self._run_task_delayed(task, lock))

        # Schedule the task for execution
        async with self._task_queue_lock:
            self._task_queue.append(ScheduledTask(lock, runner, task))

        return task.info.id

    async def execute_task(self, task: Task[S, T]) -> T:
        """
        Synchronously execute a task

        :param task: Task to execute
        :type task: Task[S, T]
        :return: Task result
        :rtype: T
        :raise asyncio.CancelledError: If the task has been cancelled by the user
        """
        self.log.info("Schedule task for sync. execution")
        # Wrap the task execution into a delayed executed asyncio task
        lock = asyncio.locks.Lock()
        await lock.acquire()
        runner = asyncio.create_task(self._run_task_delayed(task, lock))

        # Schedule the task for execution
        async with self._task_queue_lock:
            self._task_queue.append(ScheduledTask(lock, runner, task))

        # Wait for the result
        self.log.info("Wait for task to be executed by scheduler")
        await asyncio.wait([runner,])
        self.log.info("Task finished (cancelled=%s, result=%s)",
                      runner.cancelled(), runner.result())

        result = runner.result()
        if runner.cancelled():
            raise asyncio.CancelledError()

        self.log.info("Result: %s", result)
        return result

    async def cancel(self) -> None:
        """
        Cancel the current task if any
        """
        if self._current_task is not None:
            self._current_task.runner.cancel()

    async def cancel_task(self, task_id: int) -> None:
        """
        Cancel the task with a given ID

        :param task_id: ID of the task to cancel
        :type task_id: int
        """
        # Check if the task is the current one
        if self.current_task is not None and self.current_task.info.id == task_id:
            await self.cancel()
            return

        # Check if the task is in the scheduled tasks
        async with self._task_queue_lock:
            scheduled_tasks = [scheduled_task for scheduled_task in self._task_queue
                               if scheduled_task.task.info.id == task_id]
            # Cancel the task(s) and remove them from the queue
            for scheduled_task in scheduled_tasks:
                scheduled_task.runner.cancel()
                self._task_queue.remove(scheduled_task)

    async def _run_task_delayed(self, task: Task, lock: asyncio.locks.Lock):
        try:
            # Inject the event bus instance
            task.event_bus = self._event_bus

            # Notify about scheduled task
            await task.info.save()
            await self._event_bus.emit_event(TaskScheduledEvent(task.info.id,
                                                                task.info.name))

            async with lock:
                # Check if the task has been cancelled in the mean time
                self.log.info("Checking status of task: %d", task.info.id)
                task_info = await TaskInfo.get_by_id(task.info.id)
                if task_info.status == TaskStatus.CANCELLED:
                    # Task execution has been cancelled
                    self.log.info("Cancelled execution of task %s (ID=%d) before its execution",
                                  task.info.name, task.info.id)
                    # Reraise the cancelled error
                    raise asyncio.CancelledError()

                self.log.info("Start execution of task: %s", type(task))

                # Set the task status to RUNNING
                task.info.status = TaskStatus.RUNNING
                await task.info.save()
                await self._event_bus.emit_event(TaskStartedEvent(task.info.id,
                                                                  task.info.name))

                # Trigger task execution
                result = await task.run()

                # Finished execution
                self.log.info("Execution of task %s (ID=%d) finished",
                              task.info.name, task.info.id)
                if task.info.status == TaskStatus.RUNNING:
                    task.info.status = TaskStatus.FINISHED
                    await task.info.save()
                await self._event_bus.emit_event(
                    TaskFinishedEvent(task.info.id,
                                      task.info.name,
                                      cancelled=task.info.status == TaskStatus.CANCELLED,
                                      had_error=task.info.status == TaskStatus.ERRORED))

                return result

        except Exception as exc:
            # Task failed with unhandled error
            self.log.error(("Execution of task %s (ID=%d) failed due "
                           "to unhandled error"), task.info.name, task.info.id)
            task.info.status = TaskStatus.ERRORED
            await task.info.save()
            await self._event_bus.emit_event(TaskFinishedEvent(task.info.id,
                                                               task.info.name,
                                                               had_error=True))
            # Reraise exception
            raise exc
        except asyncio.CancelledError as exc:
            # Task execution has been cancelled
            self.log.info("Execution of task %s (ID=%d) was cancelled",
                          task.info.name, task.info.id)
            task.info.status = TaskStatus.CANCELLED
            await task.info.save()
            await self._event_bus.emit_event(TaskFinishedEvent(task.info.id,
                                                               task.info.name,
                                                               cancelled=True))
            # Reraise the cancelled error
            raise asyncio.CancelledError() from exc

    async def task_scheduler_loop(self) -> None:
        """
        Task scheduler main loop

        The loop handles the linear execution of all
        requested tasks
        """
        self.log.info("Starting task scheduler main loop")
        # This is accepted here as we want to ensure that the task processor never
        # fails because of an error in one of the tasks
        # pylint: disable=broad-exception-caught
        try:
            while True:
                # Fetch the next scheduled task
                if len(self._task_queue) < 1:
                    await asyncio.sleep(0.1)
                    continue

                # Pop the task from the 'queue'
                async with self._task_queue_lock:
                    scheduled_task = self._task_queue[0]
                    self._task_queue = self._task_queue[1:]

                # Trigger task execution
                scheduled_task.lock.release()
                self._current_task = scheduled_task
                # Wait for the task execution to finish
                await asyncio.wait([scheduled_task.runner,])
                self._current_task = None
        except Exception as exc:
            self.log.error("Unexpected exception in task scheduler main loop: %s %s",
                           type(exc), exc)
        except asyncio.CancelledError:
            ...
        self.log.info("Stopped task scheduler main loop")
