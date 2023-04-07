import logging
import threading
import time
from typing import Callable

from telegram import Bot, TelegramError
from telegram.error import TimedOut, NetworkError, RetryAfter, BadRequest, ChatMigrated, Conflict, InvalidToken, \
    Unauthorized

from pokerapp.entity.entities import ChatId


class MessageDelayBot(Bot):
    def __init__(
            self,
            *args,
            tasks_delay=3,
            **kwargs,
    ):
        super(MessageDelayBot, self).__init__(*args, **kwargs)

        self._chat_tasks_lock = threading.Lock()
        self._tasks_delay = tasks_delay
        self._chat_tasks = {}
        self._stop_chat_tasks = threading.Event()
        self._chat_tasks_thread = threading.Thread(
            target=self._tasks_manager_loop,
            args=(self._stop_chat_tasks,),
        )
        # TODO: Add @decorator to functions in view?

    def run_tasks_manager(self) -> None:
        self._chat_tasks_thread.start()

    def _process_chat_tasks(self) -> None:
        now = time.time()

        for (chat_id, time_tasks) in self._chat_tasks.items():
            task_time = time_tasks.get("last_time", 0)
            tasks = time_tasks.get("tasks", [])

            if now - task_time < self._tasks_delay:
                continue

            if len(tasks) == 0:
                continue

            task_callable = tasks.pop()

            try:
                task_callable()
            except (
                    TimedOut,
                    NetworkError,
                    RetryAfter
            ):
                tasks.insert(0, task_callable)
            except (
                    BadRequest,
                    ChatMigrated,
                    Conflict,
                    InvalidToken,
                    TelegramError,
                    Unauthorized,
            ) as e:
                logging.error(e)
            finally:
                self._chat_tasks[chat_id]["last_time"] = now

    def _tasks_manager_loop(self, stop_event: threading.Event) -> None:
        while not stop_event.is_set():
            self._chat_tasks_lock.acquire()
            try:
                self._process_chat_tasks()
            finally:
                self._chat_tasks_lock.release()
            time.sleep(0.05)

    def __del__(self):
        try:
            self._stop_chat_tasks.set()
            self._chat_tasks_thread.join()
        except Exception as e:
            logging.error(e)

    def _add_task(self, chat_id: ChatId, task: Callable) -> None:
        self._chat_tasks_lock.acquire()
        try:
            if chat_id not in self._chat_tasks:
                self._chat_tasks[chat_id] = {"last_time": 0, "tasks": []}
            self._chat_tasks[chat_id]["tasks"].insert(0, task)
        finally:
            self._chat_tasks_lock.release()

    def send_photo(self, *args, **kwargs) -> None:
        self._add_task(
            chat_id=kwargs.get("chat_id", 0),
            task=lambda:
            super(MessageDelayBot, self).send_photo(*args, **kwargs),
        )

    def send_message(self, *args, **kwargs) -> None:
        self._add_task(
            chat_id=kwargs.get("chat_id", 0),
            task=lambda:
            super(MessageDelayBot, self).send_message(*args, **kwargs),
        )

    def edit_message_reply_markup(self, *args, **kwargs) -> None:
        def task():
            super(MessageDelayBot, self).edit_message_reply_markup(
                *args,
                **kwargs,
            )

        try:
            task()
        except (
                TimedOut,
                NetworkError,
                RetryAfter
        ):
            self._add_task(
                chat_id=kwargs.get("chat_id", 0),
                task=task,
            )
        except (
                BadRequest,
                ChatMigrated,
                Conflict,
                InvalidToken,
                TelegramError,
                Unauthorized,
        ) as e:
            logging.error(e)
