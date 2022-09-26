from __future__ import annotations

from asyncio import (
    TimeoutError,
    ensure_future,
    gather,
    get_event_loop,
    run,
    sleep,
    wait_for,
)
from atexit import register
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from copy import copy
from enum import Enum
from itertools import chain
from logging import DEBUG, WARNING, Logger, NullHandler, getLogger
from multiprocessing import Pipe, Process, cpu_count, current_process
from multiprocessing.connection import _ConnectionBase as Connection
from random import choice
from signal import SIGINT, SIGTERM, signal
from time import time
from typing import Any, ClassVar, Generic, Literal, ParamSpec, TypeVar, overload
from warnings import catch_warnings, simplefilter

from attr import attrs
from dill import dumps, loads, pickles
from dill.detect import badtypes
from func_timeout import FunctionTimedOut, func_timeout
from nest_asyncio import apply as allow_nesting

from foundry.core.gui import Signal, SignalInstance

LOGGER_NAME: Literal["TASK"] = "TASK"

log: Logger = getLogger(LOGGER_NAME)
log.addHandler(NullHandler())

_P = ParamSpec("_P")
_T = TypeVar("_T")

RequestValue = TypeVar("RequestValue")
ReplyValue = TypeVar("ReplyValue")

FAST_CONNECTION_POLLING_RATE: float = 0.0001
"""
The desired rate of polling for an real-time process.
"""

SLOW_CONNECTION_POLLING_RATE: float = FAST_CONNECTION_POLLING_RATE * 10
"""
The desired rate of polling for a process that only requires periodic updates from the parent.
"""

MANAGER_SLEEP_DURATION: float = FAST_CONNECTION_POLLING_RATE
"""
The desired rate of polling for the task manager.
"""

WORKER_SLEEP_DURATION: float = SLOW_CONNECTION_POLLING_RATE
"""
The desired rate of polling for a worker process of the task manager.
"""

AUTOMATED_REMOVAL_DURATION: float = 5
"""
The amount of seconds the task manager will wait without any response from the parent process until it will
automatically stop itself and terminate gracefully.

Notes
-----
    The automated removal servers two primary purposes: If the user tabs out and does not require multiprocessing, then
they won't be burdened with unnecessary processing.  During testing, PyTest does not end the process until all
processes finish, so testing does not require a SEGKILL signal to end the testing.  Also, it likely it also provides
redundancy in killing the process.
"""

FORCE_TERMINATION_TIMEOUT: float = 0.5
"""
The amount of time a terminating task manager is willing to wait on its workers to terminate.
"""

FORCE_KILL_TIMEOUT: float = 0.1
"""
The amount of time a task manager is willing to wait on its workers to terminate if a kill signal is sent.
"""

RESPONSIVE_TIMEOUT: float = 0.1
"""
The maximum amount of time a responsive task should take without getting timed out.
"""


class NotAPickleException(ValueError):
    pass


class DilledConnection(Connection):
    """
    Decorates a connection object to use `dill` instead of `pickle` so we can serialize additional objects.
    """

    def __init__(self, connection: Connection):
        self.connection = connection

    @property
    def closed(self):
        """True if the connection is closed"""
        return self.connection.closed

    @property
    def readable(self):
        """True if the connection is readable"""
        return self.connection.readable

    @property
    def writable(self):
        """True if the connection is writable"""
        return self.connection.writable

    def fileno(self):
        """File descriptor or handle of the connection"""
        return self.connection.fileno()

    def close(self):
        """Close the connection"""
        self.connection.close()

    def send_bytes(self, buf, offset=0, size=None):
        """Send the bytes data from a bytes-like object"""
        self.connection.send_bytes(buf, offset, size)

    def send(self, obj):
        """Send a (picklable) object"""
        self.connection.send_bytes(dumps(obj))

    def recv_bytes(self, maxlength=None):
        """
        Receive bytes data as a bytes object.
        """
        return self.connection.recv_bytes(maxlength)

    def recv_bytes_into(self, buf, offset=0):
        """
        Receive bytes data into a writeable bytes-like object.
        Return the number of bytes read.
        """
        return self.recv_bytes_into(buf, offset)

    def recv(self):
        """Receive a (picklable) object"""
        buf = self.connection._recv_bytes()  # type: ignore
        return loads(buf.getbuffer())

    def poll(self, timeout=0.0):
        """Whether there is any input available to be read"""
        return self.connection.poll(timeout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()


def dill_connection(con1: Connection, con2: Connection) -> tuple[DilledConnection, DilledConnection]:
    return DilledConnection(con1), DilledConnection(con2)


class Requests(Enum):
    """
    The types of requests that can be sent between a requester and receiver.

    Attributes
    ----------
    NOT_DEFINED
        A request which is not defined.  This should only be sent to denote an exception.
    GET_STATUS
        A request to receive the status of the receiver.
    START_SLEEPING
        A request for the receiver to enter sleep mode.
    STOP_SLEEPING
        A request for the receiver to exit sleep mode.
    STOP
        A request for the receiver to stop working and terminate.
    JOIN
        A request for the receiver to finish all tasks currently active.
    LIMIT
        A request for the receiver to not start tasks.
    """

    NOT_DEFINED = -1
    GET_STATUS = 0
    START_SLEEPING = 1
    STOP_SLEEPING = 2
    STOP = 3
    JOIN = 4
    LIMIT = 5


class Status(Enum):
    """
    The possible states a receiver may possess.

    ..mermaid::

        stateDiagram-v2

            [*] --> STARTUP
            STARTUP --> RUNNING
            RUNNING --> RUNNING
            RUNNING --> SLEEPING : START SLEEPING
            SLEEPING --> RUNNING : STOP SLEEPING
            SLEEPING --> SLEEPING
            RUNNING --> STOPPED : STOP
            SLEEPING --> STOPPED : STOP
            STOPPED --> ZOMBIE
            ZOMBIE --> [*]
            end

    Attributes
    ----------
    NOT_DEFINED
        A status which is not defined.  This should only be sent to denote an exception.
    STARTUP
        A status which denotes that the receiver is still initializing.
    RUNNING
        A status which denotes that the receiver is actively receiving.
    SLEEPING
        A status which denotes that the receiver is not receiving.
    STOPPED
        A status which denotes that the receiver is no longer working.
    ZOMBIE
        A status which denotes that the receiver only exists in presence and should be deleted promptly.
    SUCCESS
        A status which generically denotes that the operation was successful.
    FAILURE
        A status which generically denotes that the operation was not successful.
    """

    NOT_DEFINED = -1
    STARTUP = 0
    RUNNING = 1
    SLEEPING = 2
    STOPPED = 3
    ZOMBIE = 4
    SUCCESS = 5
    FAILURE = 6


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class Task(Generic[_P, _T]):
    """
    A task to be paralyzed.

    Attributes
    ----------
    task: Callable[_P, _T]
        The task that contains the complex computation which requires paralyzation.
    identity: int
        The identity of the task.
    required_tasks: Sequence[int] = []
        Tasks which are required to be complete prior to execution of this task.
    """

    _last_identity: ClassVar[int] = 0
    task: Callable[_P, _T]
    identity: int
    required_tasks: Sequence[int] = []

    def __str__(self) -> str:
        return f"<{self.task.__name__}, 0x{self.identity:02X}>"

    @classmethod
    def generate_identity(cls) -> int:
        """
        Generates a unique identity for a task.

        Returns
        -------
        int
            The unique identity generated.
        """
        cls._last_identity += 1
        return cls._last_identity


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class WorkerTask(Generic[_P, _T]):
    """
    A task to be sent to a worker.

    Attributes
    ----------
    task: Task[_P, _T]
        The task to be ran by the worker.
    arguments: Sequence[Any] = []
        The arguments of the task provided.
    """

    task: Task[_P, _T]
    arguments: Sequence[Any] = []

    def __str__(self) -> str:
        return f"WorkerTask<{self.task}, {', '.join(str(a) for a in self.arguments)}>"

    @property
    def identity(self) -> int:
        return self.task.identity

    def begin_task(self) -> _T:
        """
        Begins execution of the task.

        Returns
        -------
        _T
            The result of the task.
        """
        return self.task.task(*self.arguments)  # type: ignore

    @classmethod
    def from_task(cls, task: Task[_P, _T], *args: _P.args, **kwargs: _P.kwargs):
        """
        Generates a worker task from a task and a set of arguments.

        Parameters
        ----------
        task : Task[_P, _T]
            The task to be wrapped.

        Returns
        -------
        Self
            A worker task specified by `task`.
        """
        return cls(task, args)


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class TaskCallback(Generic[_P, _T]):
    """
    A task which will execute additional information after the result of a task is complete.

    ..mermaid::

        graph TD
            subgraph Main Process
                A[Task Callback]
                P[Manager Proxy]
                D --> P
                E --> P
            end
            subgraph Manager Process
                B[Task]
                A -->|schedule task| B
            end
            subgraph Worker Process
                C{Worker Task}
                C -.->|Success| D[Result]
                C -.->|Failure| E[Exception]
            end
            A --> P
            P --> A
            B --> C
            end

    Attributes
    ----------
    start_task: Callable[_P, _T]
        The task to be paralyzed.
    return_task: Callable[[_T], None]
        A function that will receive the result of the task.
    exception_handler: Callable[[Exception], None] | None = None
        A handler that resolves exceptions inside the task provided.
    """

    start_task: Callable[_P, _T]
    return_task: Callable[[_T], None]
    exception_handler: Callable[[Exception], None] | None = None

    def __str__(self) -> str:
        return (
            f"<{self.start_task.__name__}, {self.return_task.__name__ if self.return_task else None}, "
            f"{self.exception_handler.__name__ if self.exception_handler else None}>"
        )

    @property
    def internal_task(self) -> Task[_P, _T]:
        """
        The internal task to be executed.

        Returns
        -------
        Task[_P, _T]
            The internal task.
        """
        return Task(self.start_task, Task.generate_identity())


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class FinishedTask(Generic[_T]):
    """
    A receipt of a finished task.

    Attributes
    ----------
    identity: int
        The identity of the task completely.
    result: _T | None
        The result of the task completed.  If None is returned, it is implied an exception occurred.
    exception: Exception | None = None
        An exception that was raised during the completion of a task, None if there does not exist.
    """

    identity: int
    result: _T | None
    exception: Exception | None = None

    def __str__(self) -> str:
        if self.result is not None:
            return f"<0x{self.identity:02X}, success:{self.result}>"
        else:
            return f"<0x{self.identity:02X}, failure:{self.exception}>"

    @classmethod
    def as_exception(cls, identity: int, exception: Exception):
        """
        Generates a finished task for an exception.

        Parameters
        ----------
        identity: int
            The identity of the task completely.
        exception: Exception | None = None
            An exception that was raised during the completion of a task.

        Returns
        -------
        Self
            The finished task that raised an exception.
        """
        return cls(identity, None, exception)


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class RequestPipe(Generic[RequestValue, ReplyValue]):
    """
    A network of pipes to transmit requests and replies between two processes without causing conflicts.

    ..mermaid::

        sequenceDiagram
            participant Parent
            participant Child
            Parent->>+Child: Request Status
            Child-->>-Parent: Return Status
            end

    Attributes
    ----------
    parent_send_to_child_pipe: Connection
        A connection for a parent to send messages to a child process.
    parent_recv_from_child_pipe: Connection
        A connection for a parent to receive messages for a child process.
    child_send_to_parent_pipe: Connection
        A connection for a child to send messages to a parent process.
    child_recv_from_parent_pipe: Connection
        A connection for a child to receive messages for a parent process.
    """

    parent_send_to_child_pipe: Connection
    parent_recv_from_child_pipe: Connection
    child_send_to_parent_pipe: Connection
    child_recv_from_parent_pipe: Connection

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}>"

    @classmethod
    def generate(cls):
        """
        Generates a request pipe with a series of connections.

        Returns
        -------
        Self
            A new simple request pipe.
        """
        parent_send_to_child_pipe, child_recv_from_parent_pipe = dill_connection(*Pipe())
        child_send_to_parent_pipe, parent_recv_from_child_pipe = dill_connection(*Pipe())
        return cls(
            parent_send_to_child_pipe,
            parent_recv_from_child_pipe,
            child_send_to_parent_pipe,
            child_recv_from_parent_pipe,
        )

    @property
    def requester(self) -> Requester[RequestValue, ReplyValue]:
        """
        Provides a requester object to be utilized by the parent process.

        Returns
        -------
        Requester[RequestValue, ReplyValue]
            The requester object for the associated pipes.
        """
        return Requester(self)

    @property
    def replier(self) -> Replier[RequestValue, ReplyValue]:
        """
        Provides a replier object to be utilized by the child process.

        Returns
        -------
        Replier[RequestValue, ReplyValue]
            The replier object for the associated pipes.
        """
        return Replier(self)


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class Request(Generic[RequestValue]):
    """
    A request to be sent to a replier.

    value: RequestValue
        The request token.
    identity: int
        The identity associated with the request to receive a reply later.
    """

    _internal_count: ClassVar[int] = 0
    value: RequestValue
    identity: int

    def __str__(self) -> str:
        return f"<{self.value}, 0x{self.identity:02X}>"

    @classmethod
    def generate(cls, value: RequestValue):
        """
        Generates a request with a unique identity.

        Parameters
        ----------
        value : RequestValue
            The request token.

        Returns
        -------
        Self
            A request object for the request token provided.
        """
        request = cls(value, cls._internal_count)
        cls._internal_count += 1
        return request


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class Reply(Generic[ReplyValue]):
    """
    A reply to be returned to a requester.

    Attributes
    ----------
    value: ReplyValue
        The reply token.
    identity: int
        The identity associated with the request to receive a reply later.
    """

    value: ReplyValue
    identity: int

    def __str__(self) -> str:
        return f"<{self.value}, 0x{self.identity:02X}>"


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class Requester(Generic[RequestValue, ReplyValue]):
    """
    An abstraction of a parent process to facilitate requesting information between its children.

    Attributes
    ----------
    request: RequestPipe[RequestValue, ReplyValue]
        An object to transmit data between processes.
    """

    _unhandled_requests: ClassVar[list[Reply]] = []
    request: RequestPipe[RequestValue, ReplyValue]

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}({self.request})>"

    async def send_request(self, request: RequestValue) -> int:
        """
        Sends a request to the child process.

        Parameters
        ----------
        request : RequestValue
            The request token to be provided to the child process.

        Returns
        -------
        int
            The identity to receive the reply from the child process.
        """
        request_message: Request[RequestValue] = Request.generate(request)
        self.request.parent_send_to_child_pipe.send(request_message)
        return request_message.identity

    async def check_received(self, identity: int) -> ReplyValue | None:
        """
        Check if a reply has been received for a given request.

        Parameters
        ----------
        identity : int
            The identity of the request provided to the child.

        Returns
        -------
        ReplyValue | None
            The reply value if the child had replied, otherwise None.
        """
        found_index: int = -1
        for index, request in enumerate(self._unhandled_requests):
            if identity == request.identity:
                found_index = index
                break
        else:
            return None
        answer: ReplyValue = self._unhandled_requests[found_index].value
        del self._unhandled_requests[found_index]
        return answer

    async def receive_answer(self, identity: int) -> ReplyValue:
        """
        Ensures that an reply has been received from a child process.

        Parameters
        ----------
        identity : int
            The identity of the request to be replied to.

        Returns
        -------
        ReplyValue
            The reply value.
        """
        while True:
            value: ReplyValue | None = await self.check_received(identity)
            if value is not None:
                return value
            if self.request.parent_recv_from_child_pipe.poll():
                reply: Reply = self.request.parent_recv_from_child_pipe.recv()
                if identity == reply.identity:
                    return reply.value
                self._unhandled_requests.append(reply)
            await sleep(FAST_CONNECTION_POLLING_RATE)

    async def get_answer(self, request: RequestValue) -> ReplyValue:
        """
        Sends a request and waits for a reply.

        Parameters
        ----------
        request : RequestValue
            The request token.

        Returns
        -------
        ReplyValue
            The reply value.
        """
        identity = await self.send_request(request)
        return await self.receive_answer(identity)


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class Replier(Generic[RequestValue, ReplyValue]):
    """
    An abstraction of a child process to facilitate the responses between its parent.

    Attributes
    ----------
    request: RequestPipe[RequestValue, ReplyValue]
        An object to transmit data between processes.
    """

    _received_request: ClassVar[Signal] = Signal()
    request: RequestPipe[RequestValue, ReplyValue]

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}({self.request})>"

    @property
    def received_request(self) -> SignalInstance[RequestValue]:
        """
        A signal to emit when a request is received.

        Returns
        -------
        SignalInstance[RequestValue]
            The signal instance related to a received request.
        """
        return SignalInstance(self, self._received_request)

    async def _emit_request(self, value: RequestValue) -> None:
        self.received_request.emit(value)

    async def handle_requests(self) -> None:
        """
        Handles a series of requests from a parent process.
        """
        while self.request.child_recv_from_parent_pipe.poll():
            request: RequestValue = self.request.child_recv_from_parent_pipe.recv()
            ensure_future(self._emit_request(request))
            log.debug(f"{self} handled request {request}")

    async def reply(self, reply: Reply) -> None:
        """
        Sends a reply back to a parent process once finished.

        Parameters
        ----------
        reply : Reply
            The reply to be sent back to the parent.
        """
        self.request.child_send_to_parent_pipe.send(reply)
        log.debug(f"{self} sent reply {reply}")


@attrs(slots=True, auto_attribs=True)
class TaskManagerProxy:
    """
    An abstraction of a task manager to be ran on the main process to provide synchronized commands.

    The task manager proxy servers as an interface to a multiple-staged process for distributing and paralyzing tasks
    in a continuous fashion.  The model is as follows.

    ..mermaid::

        graph TD
            B -.- D
            subgraph Main Process
                B(Task Manager Proxy)
                end
            subgraph Manager Process
                D[Task Manager]; D --- E; D --- F; D --- G
                E[Task Worker Proxy]; F[Task Worker Proxy]; G[Task Worker Proxy]
                end
            subgraph Worker Process
                direction LR
                E -.- H; H[Task Worker]
                end
            subgraph Worker Process
                direction LR
                I[Task Worker]; F -.- I
                end
            subgraph Worker Process
                direction LR
                J[Task Worker]; G -.- J
                end
            end

    process: Process | None
        The process which contains the asynchronous task manager.
    outgoing_pipe: Connection
        A pipe to send tasks to worker processes.
    incoming_pipe: Connection
        A pipe to receive tasks from worker processes.
    requester: Requester[Requests, Status]
        A requester object to receive simple commands to workers.
    name: str = "manager"
        The name of the task manager, used for debugging.
    """

    _task_finished: ClassVar[Signal] = Signal(name="task_finished")
    process: Process | None
    outgoing_pipe: Connection
    incoming_pipe: Connection
    requester: Requester[Requests, Status]
    name: str = "manager"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    @property
    def task_finished(self) -> SignalInstance:
        """
        A signal that is emitted when a task finishes.

        Returns
        -------
        SignalInstance
            The signal instance associated with finished tasks.
        """
        return SignalInstance(self, self._task_finished)

    def start(self, outgoing_pipe: Connection, incoming_pipe: Connection, replier: Replier) -> None:
        """
        Begins running the task manager in another process.

        Parameters
        ----------
        outgoing_pipe : Connection
            The pipe for the task manager process to send results to this process.
        incoming_pipe : Connection
            The pipe for the task manager process to receive tasks from this process.
        replier : Replier
            A network of pipes to receive simple requests from the parent process.
        """
        run(TaskManager(self.name, outgoing_pipe, incoming_pipe, replier).update())

    def make_request(self, request: Requests, timeout: float | None = None) -> Status:
        """
        Makes a request to the task manager to change its operational status.

        Parameters
        ----------
        request : Requests
            The request token.
        timeout : float | None, optional
            The amount of time the program will wait for the task manager to respond, by default None or infinite.

        Returns
        -------
        Status
            The new state the task manager process has entered.
        """
        return exit_after(synchronize(self.requester.get_answer), timeout)(request)  # type: ignore

    def join(self, timeout: float | None = None) -> bool:
        """
        Stops the task manager from receiving additional tasks and waits for all pending tasks to complete.

        Parameters
        ----------
        timeout : float | None, optional
            The amount of time permitted to wait until pending tasks are canceled, by default infinite.

        Returns
        -------
        bool
            If all tasks finished in the alloted amount of time.
        """
        try:
            exit_after(synchronize(self.requester.get_answer), timeout)(Requests.JOIN)
        except TimeoutError:
            return False
        log.info(f"{self} is joined")
        try:
            exit_after(synchronize(self.requester.get_answer), timeout)(Requests.STOP_SLEEPING)
        except TimeoutError:
            return False
        return True

    def is_alive(self) -> bool:
        """
        Determines if the manager process is alive and exists.

        Returns
        -------
        bool
            If the manager process is alive.
        """
        return self.process is not None and self.process.is_alive()

    def terminate(self) -> None:
        """
        Tries to terminate and stop operation of te manager process in a timely fashion to provide a graceful death.
        """
        log.info(f"{self} making request: {Requests.STOP}")
        self.make_request(Requests.STOP, FORCE_TERMINATION_TIMEOUT)
        if self.process is not None:
            self.process.terminate()
            self.process = None
        log.info(f"{self} is terminated")

    def kill(self) -> None:
        """
        Abruptly kills and stops operation of the manager process quickly, likely leaving pending tasks in an
        indeterminate state.
        """
        if self.process is not None:
            log.info(f"{self} making request: {Requests.STOP}")
            exit_after(synchronize(self.requester.get_answer), FORCE_KILL_TIMEOUT)(Requests.STOP)
            self.process.kill()
            self.process = None
        log.info(f"{self} is killed")

    def check_if_child_task_finished(self, task: TaskCallback, internal_task: Task) -> Callable[[FinishedTask], None]:
        """
        Checks if a task is finished from a receiver and performs the appropriate action depending if the task
        successfully completely.

        Parameters
        ----------
        task : TaskCallback
            The task callback.
        internal_task : Task
            The task containing its unique identity.

        Returns
        -------
        Callable[[FinishedTask], None]
            A function to perform the required actions for the task provided.
        """

        def check_if_child_task_finished(result: FinishedTask) -> None:
            """
            Checks if a task finished and performs the return callback if the task completely successfully, otherwise
            handles the exception.

            Parameters
            ----------
            result : FinishedTask
                The finished task.
            """
            if internal_task.identity == result.identity:
                if result.exception and task.exception_handler is not None:
                    task.exception_handler(result.exception)
                elif result.exception:
                    log.warning(f"{self} received unhandled exception {result.exception} from {task}")
                else:
                    task.return_task(result.result)

        return check_if_child_task_finished

    def _schedule_task(self, task: TaskCallback, internal_task: Task) -> None:
        if DEBUG >= log.level:
            status = self.make_request(Requests.GET_STATUS, 1)
            if status != Status.RUNNING:
                log.warning(f"{self} scheduling tasks when status is not running")
                assert status == Status.RUNNING  # A task was scheduled in an invalid state.

            # Make sure the user provided a task that can be pickled, otherwise we won't be able to send it.
            if not pickles(internal_task):
                log.critical(f"{internal_task} is not a pickle with bad types: {badtypes(internal_task)}")
                raise NotAPickleException(f"{internal_task} is not a pickle!")

        # We cannot garbage collect tasks easily, so we only keep the last 100 tasks sent.
        self.task_finished.connect(self.check_if_child_task_finished(task, internal_task), weak=False, max_uses=100)
        self.outgoing_pipe.send(internal_task)
        log.debug(f"{self} started task {task}")

    def _limit(self, limit: bool) -> bool:
        # We will keep setting limit until it provides the correct value or we timeout.
        return wait_until(self.make_request, Status.SUCCESS if limit else Status.FAILURE, RESPONSIVE_TIMEOUT)(
            Requests.LIMIT
        )

    def schedule_task(self, task: TaskCallback) -> None:
        """
        Schedules a single task.

        Parameters
        ----------
        task : TaskCallback
            The task to be scheduled.
        """
        self._schedule_task(task, task.internal_task)

    def schedule_tasks(self, tasks: Mapping[str, tuple[TaskCallback, set[str]]]) -> None:
        """
        Schedules a series of tasks.

        Parameters
        ----------
        tasks : Mapping[str, tuple[TaskCallback, set[str]]]
            A mapping of a task name, task, and a set of required tasks.

        Notes
        -----
            Only the tasks and their associated identities inside `tasks` are ensured to exist.
        """
        name_to_identity: dict[str, int] = {task_name: Task.generate_identity() for task_name in tasks.keys()}

        # Temporarily stop tasks from finishing, to ensure that tasks don't get garbage collected too quickly.
        self._limit(True)

        for task_name, (task, required_tasks) in tasks.items():
            self._schedule_task(
                task, Task(task.start_task, name_to_identity[task_name], [name_to_identity[n] for n in required_tasks])
            )

        self._limit(False)

    def poll_tasks(self) -> int:
        """
        Gets all the newly finished tasks and handles them.

        Returns
        -------
        int
            The amount of tasks completed.
        """
        if WARNING >= log.level and not self.is_alive():
            log.warning(f"{self} polled a process which is not alive")
        tasks_completed = 0
        while self.incoming_pipe.poll():
            finished_task: FinishedTask = self.incoming_pipe.recv()
            log.debug(f"{self} finished task {finished_task}")
            self.task_finished.emit(finished_task)
            tasks_completed += 1
        return tasks_completed


class TaskManager:
    """
    An abstraction of a process responsible for delegating tasks to a network of processes.

    Attributes
    ----------
    name: str
        The name of the underlying process.
    outgoing_pipe: Connection
        A pipe to send finished tasks to the parent process.
    incoming_pipe: Connection
        A pipe to receive tasks from the parent process.
    replier: Replier
        A network of pipes to easily reply to simple status requests from the parent process.
    recent_returned_values: dict[int, Any]
        A mapping of finished tasks identities and their associated values.
    queued_tasks: dict[int, Task]
        A mapping of tasks identities and their associated task that have not started.
    workers: list[TaskWorkerProxy]
        A series of workers that can perform tasks.
    status: Status
        The current status of the manager processes.
    last_event: float
        The last time stamp that an event was sent to the task manager.
    """

    name: str
    outgoing_pipe: Connection
    incoming_pipe: Connection
    replier: Replier
    recent_returned_values: dict[int, Any]
    queued_tasks: dict[int, Task]
    is_limited: bool
    workers: list[TaskWorkerProxy]
    status: Status
    last_event: float

    def __init__(self, name: str, outgoing_pipe: Connection, incoming_pipe: Connection, replier: Replier) -> None:
        self.name = name
        self.status = Status.STARTUP
        log.info(f"Starting {self}")
        self.outgoing_pipe = outgoing_pipe
        self.incoming_pipe = incoming_pipe
        self.replier = replier
        self.replier.received_request.connect(self.handle_request)
        self.queued_tasks = {}
        self.recent_returned_values = {}
        self.is_limited = False
        self.last_event = time()
        self.workers = []
        for _ in range(cpu_count()):
            synchronize(self.add_worker)()
        run(self.update())
        current_process().terminate()  # Terminate the active process.

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name}, {self.outgoing_pipe}, {self.incoming_pipe}, {self.replier})"

    def __str__(self) -> str:
        return f"<{self.name}>"

    async def check_time(self) -> None:
        """
        Checks if the task manager is not actively being used.  If the task manager is not being used, it will end
        itself.
        """
        if time() - self.last_event >= AUTOMATED_REMOVAL_DURATION:
            # We will stop running the task manager if nothing has occurred in five seconds.
            log.info(f"{self} has begun stopping from inactivity")

            self.status = Status.STOPPED

            for worker in self.workers:
                log.info(f"stopping worker from inactivity {worker}")
                await worker.join(1)
                await worker.kill()  # Force kill a worker if it did not respond.

            self.workers.clear()

            log.info(f"{self} has stopped from inactivity")

            current_process().terminate()

    async def add_worker(self) -> None:
        """
        Adds an additional worker process to perform tasks.
        """
        parent_outgoing_pipe, child_incoming_pipe = dill_connection(*Pipe())
        child_outgoing_pipe, parent_incoming_pipe = dill_connection(*Pipe())
        request_pipe = RequestPipe.generate()
        worker: TaskWorkerProxy = TaskWorkerProxy(
            None, parent_outgoing_pipe, parent_incoming_pipe, request_pipe.requester, f"worker_{len(self.workers)}"
        )
        process: Process = Process(
            target=worker.start, args=(child_outgoing_pipe, child_incoming_pipe, request_pipe.replier)
        )
        worker.process = process
        process.start()
        self.workers.append(worker)

    async def send_task_to_worker(self, task: Task, *args: Any) -> None:
        """
        Sends a task to one of the workers to be performed.

        Parameters
        ----------
        task : Task
            The task to be sent and completed.
        """
        assigned_worker = choice(self.workers)
        worker_task = WorkerTask.from_task(task, *args)
        assigned_worker.outgoing_pipe.send(worker_task)
        log.debug(f"{self} sent {worker_task} to {assigned_worker}")

    async def get_important_return_values(self) -> set[int]:
        """
        Acquires all return value identities that are required for queued tasks.

        Returns
        -------
        set[int]
            The set of all return value identities that should not be removed.
        """
        return set(chain.from_iterable(q.required_tasks for q in self.queued_tasks.values()))

    async def remove_stale_return_values(self) -> None:
        """
        Removes return values that are no longer required by any queued task.
        """
        stale_return_values: set[int] = set(self.recent_returned_values.keys()).difference(
            await self.get_important_return_values()
        )
        for stale_return_value in stale_return_values:
            del self.recent_returned_values[stale_return_value]

    async def get_arguments_of_task(self, identity: int) -> list[Any]:
        """
        Acquires the arguments for a task which depends on other tasks.

        Parameters
        ----------
        identity : int
            The identity of the task to generate arguments for.

        Returns
        -------
        list[Any]
            The list of arguments for the task.

        Notes
        -----
            We assume that every return value exists.
        """
        return [self.recent_returned_values[r] for r in self.queued_tasks[identity].required_tasks]

    async def poll_queued_tasks(self, identity: int, return_value: Any) -> None:
        """
        Checks if any tasks that are queued are able to be started.

        Parameters
        ----------
        identity : int
            The identity of an additional task completed.
        return_value : Any
            The return value of the additional task completed.

        Notes
        -----
            This should be called after each task is completed, so its data can be added and referenced later.
        """
        newly_queued_tasks: set[int] = set()
        self.recent_returned_values |= {identity: return_value}
        await self.remove_stale_return_values()
        finished_tasks: set[int] = set(self.recent_returned_values.keys())
        for identity, queued_task in self.queued_tasks.items():
            if finished_tasks.issuperset(queued_task.required_tasks):
                await self.send_task_to_worker(queued_task, *await self.get_arguments_of_task(identity))
                newly_queued_tasks.add(identity)
        for queued_task in newly_queued_tasks:
            del self.queued_tasks[queued_task]

    async def poll_workers(self) -> None:
        """
        Checks every worker to determine if any tasks have been completed and performs the required operations to
        send any finished tasks back to the main process.
        """
        for worker in self.workers:
            if worker.incoming_pipe.poll():
                log.debug(f"{self} receiving task result from {worker}")
                try:
                    value: FinishedTask = worker.incoming_pipe.recv()
                except EOFError:
                    # Something went wrong, so we log and ignore it.
                    log.warning(f"{self} dropped task from worker {worker}")
                    return
                self.outgoing_pipe.send(value)
                await self.poll_queued_tasks(value.identity, value.result)
                self.last_event = time()  # Add additional time to the process if work is actively getting done.

    async def poll_tasks(self) -> None:
        """
        Checks if the main process has sent any additional tasks to be performed.
        """
        while self.incoming_pipe.poll():
            task: Task = self.incoming_pipe.recv()
            log.debug(f"{self} received {task}")
            if task.required_tasks:
                self.queued_tasks |= {task.identity: task}
            else:
                ensure_future(self.send_task_to_worker(task))
            self.last_event = time()  # Update last event time.

    async def update(self) -> None:
        """
        Standard operations to be done every fixed unit of time.
        """
        self.status = Status.RUNNING
        log.info(f"{self} is running")
        while self.status != Status.STOPPED:
            await self.replier.handle_requests()
            if self.status == Status.RUNNING:
                await self.poll_tasks()
                if not self.is_limited:
                    await self.poll_workers()
            await self.check_time()
            await sleep(MANAGER_SLEEP_DURATION)
        self.status = Status.ZOMBIE
        log.info(f"{self} is a zombie")

    def handle_request(self, request: Request[Requests]) -> None:
        """
        Determines how to handle a simple request from the main process.

        Parameters
        ----------
        request : Request[Requests]
            The request token.
        """
        match request.value:
            case Requests.GET_STATUS:
                ensure_future(self.get_status(request.identity))
            case Requests.START_SLEEPING:
                ensure_future(self.start_sleeping(request.identity))
            case Requests.STOP_SLEEPING:
                ensure_future(self.stop_sleeping(request.identity))
            case Requests.STOP:
                ensure_future(self.stop(request.identity))
            case Requests.JOIN:
                ensure_future(self.join(request.identity))
            case Requests.LIMIT:
                ensure_future(self.limit(request.identity))
            case _:
                ensure_future(self.default(request.identity))

    async def get_status(self, identity: int) -> None:
        """
        Provides the status of the manager process to the main process.

        Parameters
        ----------
        identity : int
            The identity associated with the reply.
        """
        await self.replier.reply(Reply(self.status, identity))

    async def start_sleeping(self, identity: int) -> None:
        """
        Tries to put the manager process into sleep mode, refusing to receive additional tasks.

        Parameters
        ----------
        identity : int
            The identity associated with the reply.
        """
        if self.status == Status.RUNNING:
            for worker in self.workers:
                await worker.make_request(Requests.START_SLEEPING)
            self.status = Status.SLEEPING
            log.info(f"{self} is sleeping")
        await self.replier.reply(Reply(self.status, identity))

    async def stop_sleeping(self, identity: int) -> None:
        """
        Tries to put the manager process into the running mode to undergo normal operation.

        Parameters
        ----------
        identity : int
            The identity associated with the reply.
        """
        if self.status == Status.SLEEPING:
            self.status = Status.RUNNING
            self.is_limited = False
            for worker in self.workers:
                await worker.make_request(Requests.STOP_SLEEPING)
            log.info(f"{self} is running")
        await self.replier.reply(Reply(self.status, identity))

    async def stop(self, identity: int) -> None:
        """
        Stops the activity of the manager process.

        Parameters
        ----------
        identity : int
            The identity associated with the reply.
        """
        log.info(f"{self} has begun stopping")

        async def stop_worker(worker: TaskWorkerProxy):
            log.info(f"stopping worker {worker}")
            await worker.make_request(Requests.STOP, FORCE_KILL_TIMEOUT)
            await worker.kill()

        self.status = Status.STOPPED

        # Clear workers to stop receiving tasks from workers, as they may have closed their pipes.
        workers: list[TaskWorkerProxy] = self.workers
        self.workers.clear()
        await gather(*[stop_worker(worker) for worker in workers])

        log.info(f"{self} has stopped")
        await self.replier.reply(Reply(self.status, identity))

    async def join(self, identity: int) -> None:
        """
        Tries to finish all active tasks and enters sleeping mode.

        Parameters
        ----------
        identity : int
            The identity associated with the reply.
        """
        if self.status == Status.RUNNING:
            self.status = Status.SLEEPING

            async def join_worker(worker: TaskWorkerProxy) -> None:
                # Force kill a worker if it did not respond.
                if not await worker.join(10000):
                    await worker.kill()
                    await self.add_worker()

            if self.workers:
                await gather(
                    *[await join_worker(worker) for worker in self.workers], return_exceptions=True  # type: ignore
                )

        await self.replier.reply(Reply(self.status, identity))

    async def limit(self, identity: int) -> None:
        """
        A temporary effect used to ensure that tasks won't finish until all tasks are provided.

        Parameters
        ----------
        identity : int
            The identity associated with the reply.

        Notes
        -----
            Unlike other requests, only a success or failure is provided.  A success will be emitted if the manager
        begun limiting tasks, otherwise a failure.
        """
        if self.status == Status.RUNNING:
            self.is_limited = not self.is_limited
            if self.is_limited:
                await self.replier.reply(Reply(Status.SUCCESS, identity))
        await self.replier.reply(Reply(Status.FAILURE, identity))

    async def default(self, identity: int) -> None:
        """
        Handles invalid requests by forwarding an invalid status to the main process.

        Parameters
        ----------
        identity : int
            The identity associated with the reply.
        """
        log.warning(f"{self} has received an invalid request")
        await self.replier.reply(Reply(Status.NOT_DEFINED, identity))


@attrs(slots=True, auto_attribs=True)
class TaskWorkerProxy:
    """
    An interface for the task manager to communicate to a worker process.

    Attributes
    ----------
    process: Process | None
        The process which contains the asynchronous task manager.
    outgoing_pipe: Connection
        A pipe to send tasks to worker processes.
    incoming_pipe: Connection
        A pipe to receive tasks from worker processes.
    requester: Requester[Requests, Status]
        A requester object to receive simple commands.
    name: str = "worker"
        The name of the worker, used for debugging.
    """

    process: Process | None
    outgoing_pipe: Connection
    incoming_pipe: Connection
    requester: Requester[Requests, Status]
    name: str = "worker"

    def __str__(self) -> str:
        return f"<{self.name}>"

    def __del__(self) -> None:
        synchronize(self.kill)()

    def start(self, outgoing_pipe: Connection, incoming_pipe: Connection, replier: Replier) -> None:
        """
        Begins running the worker in another process.

        Parameters
        ----------
        outgoing_pipe : Connection
            The pipe for the worker process to send results to this process.
        incoming_pipe : Connection
            The pipe for the worker process to receive tasks from this process.
        replier : Replier
            A network of pipes to receive simple requests from the task manager.
        """
        # We copy name to not have references
        run(TaskWorker(copy(self.name), outgoing_pipe, incoming_pipe, replier).update())

    async def make_request(self, request: Requests, timeout: float | None = None) -> Status:
        """
        Makes a request to the worker to change its operational status.

        Parameters
        ----------
        request : Requests
            The request token.
        timeout : float | None, optional
            The amount of time the program will wait for the task manager to respond, by default None or infinite.

        Returns
        -------
        Status
            The new state the worker process has entered.
        """
        return await wait_for(self.requester.get_answer(request), timeout)

    async def join(self, timeout: float | None = None) -> bool:
        """
        Stops the worker from receiving additional tasks and waits for all pending tasks to complete.

        Parameters
        ----------
        timeout : int | None, optional
            The amount of time permitted to wait until pending tasks are canceled, by default infinite.

        Returns
        -------
        bool
            If all tasks finished in the alloted amount of time.
        """
        try:
            await wait_for(self.requester.get_answer(Requests.JOIN), timeout)
        except TimeoutError:
            log.warning(f"{self} failed to join all tasks in time.")
            return False
        log.debug(f"{self} is joined")
        ensure_future(self.make_request(Requests.STOP_SLEEPING))
        return True

    async def is_alive(self) -> bool:
        """
        Determines if the worker process is alive and exists.

        Returns
        -------
        bool
            If the worker process is alive.
        """
        return self.process is not None and self.process.is_alive()

    async def terminate(self) -> None:
        """
        Tries to terminate and stop operation of te worker process in a timely fashion to provide a graceful death.
        """
        with suppress(TimeoutError):
            await wait_for(self.requester.get_answer(Requests.STOP), 1)
        if self.process is not None and await self.is_alive():
            self.process.terminate()
        log.debug(f"{self} is terminated")

    async def kill(self) -> None:
        """
        Abruptly kills and stops operation of the worker process quickly, likely not finishing all tasks.
        """
        if self.process is not None and await self.is_alive():
            try:
                self.process.kill()
            except AttributeError:
                log.warning(f"{self} exited ungracefully")
        log.debug(f"{self} is killed")


class TaskWorker:
    """
    An abstraction of a worker process which is assigned a series of tasks to perform.

    Attributes
    ----------
    name: str
        The name of the underlying process.
    outgoing_pipe: Connection
        A pipe to send finished tasks to the manager process.
    incoming_pipe: Connection
        A pipe to receive tasks from the manager process.
    replier: Replier
        A network of pipes to easily reply to simple status requests from the manager process.
    status: Status
        The current status of the worker processes.
    task_count: int
        The number of tasks that this process is actively working on.
    """

    name: str
    outgoing_pipe: Connection
    incoming_pipe: Connection
    replier: Replier
    status: Status
    task_count: int

    def __init__(self, name: str, outgoing_pipe: Connection, incoming_pipe: Connection, replier: Replier) -> None:
        self.name = name
        self.task_count = 0
        log.info(f"{self} entering startup")
        self.status = Status.STARTUP
        self.outgoing_pipe = outgoing_pipe
        self.incoming_pipe = incoming_pipe
        self.replier = replier
        self.replier.received_request.connect(self.handle_request)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, active_tasks={self.task_count})"

    def __str__(self) -> str:
        return f"<{self.name}>"

    async def execute_task(self, task: WorkerTask) -> None:
        """
        Begins actively working on a task.

        Parameters
        ----------
        task : WorkerTask
            The task to be performed.
        """
        log.debug(f"{self} begun executing {task.task} with arguments {task.arguments}")
        try:
            finished_task = FinishedTask(task.identity, task.begin_task())
        except Exception as e:
            finished_task = FinishedTask.as_exception(task.identity, e)
        if DEBUG >= log.level and not pickles(finished_task):
            log.critical(f"{finished_task} is not a pickle with bad types: {badtypes(finished_task)}")
            raise NotAPickleException(f"{finished_task} is not a pickle!")
        self.outgoing_pipe.send(finished_task)
        self.task_count -= 1

    async def poll_tasks(self) -> None:
        """
        Checks if the manager process has assigned the worker additional tasks.
        """
        while self.incoming_pipe.poll():
            task: WorkerTask = self.incoming_pipe.recv()
            log.debug(f"{self} received {task}")
            ensure_future(self.execute_task(task))
            self.task_count += 1

    async def update(self) -> None:
        """
        Standard operations to be done every fixed unit of time.
        """
        self.status = Status.RUNNING
        log.info(f"{self} is running")
        while self.status != Status.STOPPED:
            await self.replier.handle_requests()
            if self.status == Status.RUNNING:
                await self.poll_tasks()
            await sleep(WORKER_SLEEP_DURATION)
        self.status = Status.ZOMBIE
        log.debug(f"{self} is a zombie")

    def handle_request(self, request: Request[Requests]) -> None:
        """
        Determines how to handle a simple request from the main process.

        Parameters
        ----------
        request : Request[Requests]
            The request token.
        """
        match request.value:
            case Requests.GET_STATUS:
                ensure_future(self.get_status(request.identity))
            case Requests.START_SLEEPING:
                ensure_future(self.start_sleeping(request.identity))
            case Requests.STOP_SLEEPING:
                ensure_future(self.stop_sleeping(request.identity))
            case Requests.STOP:
                ensure_future(self.stop(request.identity))
            case Requests.JOIN:
                ensure_future(self.join(request.identity))
            case _:
                ensure_future(self.default(request.identity))

    async def get_status(self, identity: int) -> None:
        """
        Provides the status of the worker process to the manager process.

        Parameters
        ----------
        identity : int
            The identity associated with the reply.
        """
        await self.replier.reply(Reply(self.status, identity))

    async def start_sleeping(self, identity: int) -> None:
        """
        Tries to put the worker process into sleep mode, refusing to receive additional tasks.

        Parameters
        ----------
        identity : int
            The identity associated with the reply.
        """
        if self.status == Status.RUNNING:
            self.status = Status.SLEEPING
            log.info(f"{self} is sleeping")
        await self.replier.reply(Reply(self.status, identity))

    async def stop_sleeping(self, identity: int) -> None:
        """
        Tries to put the worker process into the running mode to undergo normal operation.

        Parameters
        ----------
        identity : int
            The identity associated with the reply.
        """
        if self.status == Status.SLEEPING:
            self.status = Status.RUNNING
            log.info(f"{self} is running")
        await self.replier.reply(Reply(self.status, identity))

    async def stop(self, identity: int) -> None:
        """
        Stops the activity of the worker process.

        Parameters
        ----------
        identity : int
            The identity associated with the reply.
        """
        self.status = Status.STOPPED
        log.info(f"{self} has stopped")
        await self.replier.reply(Reply(self.status, identity))

    async def join(self, identity: int) -> None:
        """
        Tries to finish all active tasks and enters sleeping mode.

        Parameters
        ----------
        identity : int
            The identity associated with the reply.
        """
        if self.status == Status.RUNNING:
            self.status = Status.SLEEPING
            log.debug(f"{self} is sleeping")
            while self.task_count > 0:
                await sleep(WORKER_SLEEP_DURATION)
        await self.replier.reply(Reply(self.status, identity))

    async def default(self, identity: int) -> None:
        """
        Handles invalid requests by forwarding an invalid status to the manager process.

        Parameters
        ----------
        identity : int
            The identity associated with the reply.
        """
        log.warning(f"{self} has received an invalid request")
        await self.replier.reply(Reply(Status.NOT_DEFINED, identity))


def start_task_manager(name: str | None = None) -> TaskManagerProxy:
    """
    Provides and starts a task manager to begin receiving and executing tasks.

    Parameters
    ----------
    name : str | None, optional
        The name of the task manager process.

    Returns
    -------
    TaskManagerProxy
        An interface to communicate to the task manager process.
    """
    parent_outgoing_pipe, child_incoming_pipe = dill_connection(*Pipe())
    child_outgoing_pipe, parent_incoming_pipe = dill_connection(*Pipe())
    request_pipe = RequestPipe.generate()
    manager: TaskManagerProxy = TaskManagerProxy(
        None, parent_outgoing_pipe, parent_incoming_pipe, request_pipe.requester, name or "manager"
    )
    process: Process = Process(
        target=manager.start, args=(child_outgoing_pipe, child_incoming_pipe, request_pipe.replier), name=manager.name
    )
    manager.process = process

    def handle_exit(*_):
        with suppress(AttributeError):
            manager.terminate()
            if manager.is_alive() and manager.process is not None:
                manager.process.kill()  # Really kill it

    register(handle_exit)
    signal(SIGTERM, handle_exit)  # type: ignore
    signal(SIGINT, handle_exit)  # type: ignore
    process.start()
    return manager


def synchronize(func):
    """
    Allows for an asynchronous coroutine to be executed in the main process.

    Parameters
    ----------
    func
        A coroutine to be executed in the main process.
    """

    def synchronize(*args, **kwargs):
        log.debug(f"Running {func.__name__} with {args}, {kwargs}")

        # We have to do a bunch of annoying stuff as asyncio does not support multiple loops at a single time.
        # To get around it, we ignore a couple warnings and use a dependency and it 'works'.
        try:
            with catch_warnings():
                simplefilter("ignore")
                loop = get_event_loop()
        except RuntimeError:
            return run(func(*args, **kwargs))
        allow_nesting()
        task = loop.create_task(func(*args, **kwargs))
        loop.run_until_complete(task)
        return task.result()

    return synchronize


@overload
def exit_after(
    func: None = None, timeout: float | None = None
) -> Callable[[Callable[_P, _T]], Callable[_P, _T | None]]:
    ...


@overload
def exit_after(func: Callable[_P, _T], timeout: float | None = None) -> Callable[_P, _T | None]:
    ...


def exit_after(
    func: Callable[_P, _T] | None = None, timeout: float | None = None
) -> Callable[[Callable[_P, _T]], Callable[_P, _T | None]] | Callable[_P, _T | None]:
    """
    A decorator for a function to allow it to gracefully timeout and exit after a given period of time.

    Parameters
    ----------
    func : Callable[_P, _T] | None, optional
        The function to be wrapped, by default None.
    timeout : float | None, optional
        The amount of time until the function will time out, by default None or infinite.

    Returns
    -------
    Callable[[Callable[_P, _T]], Callable[_P, _T]] | Callable[_P, _T]
        If `func` is provided, the decorated function will be returned.  Otherwise, a decorator will be provided.
    """

    def exit_after(func: Callable[_P, _T]) -> Callable[_P, _T | None]:
        def exit_after(*args: _P.args, **kwargs: _P.kwargs) -> _T | None:
            try:
                return func_timeout(timeout, func, args, kwargs)
            except FunctionTimedOut:
                return None

        return exit_after

    return exit_after if func is None else exit_after(func)


def wait_until(func: Callable[_P, _T], expected: _T, timeout: float) -> Callable[_P, bool]:
    def wait_until(*args: _P.args, **kwargs: _P.kwargs) -> bool:
        def wait_until():
            while True:
                if func(*args, **kwargs) == expected:
                    return True

        result = exit_after(wait_until, timeout)()
        return result if result is not None else False

    return wait_until


class _TaskManager:
    """
    A simple descriptor to automatically handle creating the required task managers.
    """

    _task_manager: TaskManagerProxy | None
    _last_event: float

    def __init__(self, is_alive: bool = False):
        self._task_manager = start_task_manager("task manager") if is_alive else None
        self._last_event = time()

    def __get__(self, instance, owner) -> TaskManagerProxy:
        if (
            self._task_manager is not None
            and time() - AUTOMATED_REMOVAL_DURATION > self._last_event
            and not self._task_manager.is_alive()
        ):
            self._task_manager = None

        if self._task_manager is None:
            self._task_manager = start_task_manager("task manager")

        return self._task_manager

    def __call__(self) -> TaskManagerProxy:
        return self.__get__(self, None)


_task_manager: _TaskManager = _TaskManager()


class TaskMethod(Generic[_P, _T]):
    """
    A method which will be executed and paralyzed.

    Attributes
    ----------
    name: str | None
        The name associated with the method, by default will use the name of `fstart`
    fstart: Callable[_P, _T]
        The task to be executed in another process.
    _freturn: Callable[[_T], None] | None
        A method to handle the result of task.
    fsignal: Signal[_T] | None
        A signal to emit the result of fstart.
    ehandler: Callable[[Exception], None] | None
        A handler to resolve any exceptions from the task.
    """

    __slots__ = ("name", "fstart", "_freturn", "fsignal", "ehandler")

    name: str | None
    fstart: Callable[_P, _T]
    _freturn: Callable[[Any, _T], None] | None
    fsignal: Signal[_T] | None
    ehandler: Callable[[Exception], None] | None

    def __init__(
        self,
        fstart: Callable[_P, _T],
        freturn: Callable[[Any, _T], None] | None = None,
        fsignal: Signal[_T] | None = None,
        ehandler: Callable[[Exception], None] | None = None,
        name: str | None = None,
    ) -> None:
        self.name = fstart.__name__ if name is None and fstart is not None else name
        self.fstart = fstart
        self.fsignal = fsignal
        self._freturn = freturn
        self.ehandler = ehandler

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({self.fstart}, {self._freturn}, {self.fsignal}, {self.ehandler}, "
            f"{self.name}, {self.__doc__}"
        )

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"{self.fstart.__name__ if self.fstart else None}, "
            f"{self._freturn.__name__ if self._freturn else None}, "
            f"{self.fsignal}, {self.ehandler.__name__ if self.ehandler else None}"
            f"{self.name}, {self.__doc__})"
        )

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> None:
        def _inner(*args, **kwargs):
            return self.fstart(*args, **kwargs)  # type: ignore

        _inner.__name__ = self.fstart.__name__

        _task_manager().schedule_task(TaskCallback(_inner, self.freturn(args[0]), self.ehandler))

    def freturn(self, instance: object) -> Callable[[_T], None]:
        """
        A wrapped return function to enabled the use of a signal for successful completion of the task.

        Parameters
        ----------
        instance : object
            The instance of the method.

        Returns
        -------
        Callable[[_T], None]
            The wrapped return function.
        """

        def freturn(value: _T) -> None:
            if self._freturn is not None:
                self._freturn(instance, value)
            if self.fsignal is not None:
                self.fsignal.emit(value, instance)

        return freturn

    def task_callback(self, instance: object) -> TaskCallback[_P, _T]:
        return TaskCallback(self.fstart, self.freturn(instance), self.ehandler)

    def start(self, fstart: Callable[_P, _T]):
        return type(self)(fstart, self._freturn, self.fsignal, self.ehandler, self.name)

    def return_task(self, freturn: Callable[[Any, _T], None] | None):
        return type(self)(self.fstart, freturn, self.fsignal, self.ehandler, self.name)

    def signal(self, fsignal: Signal[_T] | None = None):
        return type(self)(self.fstart, self._freturn, fsignal, self.ehandler, self.name)

    def handler(self, ehandler: Callable | None = None):
        return type(self)(self.fstart, self._freturn, self.fsignal, ehandler, self.name)


task: type[TaskMethod] = TaskMethod


def stage_task(instance: object, tasks: Mapping[str, tuple[TaskMethod, set[str]]]) -> None:
    """
    Allows for the staging of multiple task method to be ran in parallel.

    Parameters
    ----------
    instance : object
        The instance staging tasks.
    tasks : Mapping[str, tuple[TaskMethod, set[str]]]
        A mapping of a task name, task, and a set of required tasks.
    """
    _task_manager().schedule_tasks({k: (t.task_callback(instance), r) for k, (t, r) in tasks.items()})
