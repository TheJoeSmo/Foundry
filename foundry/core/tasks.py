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
from collections.abc import Callable, Generator, Mapping, Sequence
from contextlib import suppress
from enum import Enum
from itertools import chain
from logging import Logger, NullHandler, getLogger
from multiprocessing import Pipe, Process, cpu_count
from multiprocessing.connection import _ConnectionBase as Connection
from random import choice
from threading import Timer
from typing import (
    Any,
    ClassVar,
    Generic,
    Literal,
    NoReturn,
    ParamSpec,
    TypeVar,
    overload,
)

from attr import attrs

from foundry.core.gui import Signal, SignalInstance

LOGGER_NAME: Literal["TASK"] = "TASK"

log: Logger = getLogger(LOGGER_NAME)
log.addHandler(NullHandler())

_P = ParamSpec("_P")
_T = TypeVar("_T")

RequestValue = TypeVar("RequestValue")
ReplyValue = TypeVar("ReplyValue")


class Requests(Enum):
    NOT_DEFINED = -1
    GET_STATUS = 0
    START_SLEEPING = 1
    STOP_SLEEPING = 2
    STOP = 3
    JOIN = 4


class Status(Enum):
    NOT_DEFINED = -1
    STARTUP = 0
    RUNNING = 1
    SLEEPING = 2
    STOPPED = 3
    ZOMBIE = 4


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class Task(Generic[_P, _T]):
    _last_identity: ClassVar[int] = 0
    task: Callable[_P, _T]
    identity: int
    required_tasks: Sequence[int] = []

    @classmethod
    def generate_identity(cls) -> int:
        cls._last_identity += 1
        return cls._last_identity


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class WorkerTask(Generic[_P, _T]):
    task: Task[_P, _T]
    arguments: Sequence[Any] = []

    def begin_task(self) -> _T:
        return self.task.task(*self.arguments)  # type: ignore

    @classmethod
    def from_task(cls, task: Task[_P, _T], *args: _P.args, **kwargs: _P.kwargs):
        return cls(task, args)


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class TaskCallback(Generic[_P, _T]):
    start_task: Callable[_P, _T]
    return_task: Callable[[_T], None]
    exception_handler: Callable[[Exception], None] | None = None

    @property
    def child_task(self) -> Task[_P, _T]:
        return Task(self.start_task, Task.generate_identity())


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class FinishedTask(Generic[_T]):
    identity: int
    result: _T | None
    exception: Exception | None = None

    @classmethod
    def as_exception(cls, identity: int, exception: Exception):
        return cls(identity, None, exception)


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class RequestPipe(Generic[RequestValue, ReplyValue]):
    parent_send_to_child_pipe: Connection
    parent_recv_from_child_pipe: Connection
    child_send_to_parent_pipe: Connection
    child_recv_from_parent_pipe: Connection

    @classmethod
    def generate(cls):
        parent_send_to_child_pipe, child_recv_from_parent_pipe = Pipe()
        child_send_to_parent_pipe, parent_recv_from_child_pipe = Pipe()
        return cls(
            parent_send_to_child_pipe,
            parent_recv_from_child_pipe,
            child_send_to_parent_pipe,
            child_recv_from_parent_pipe,
        )

    @property
    def requester(self) -> Requester[RequestValue, ReplyValue]:
        return Requester(self)

    @property
    def replier(self) -> Replier[RequestValue, ReplyValue]:
        return Replier(self)


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class Request(Generic[RequestValue]):
    _internal_count: ClassVar[int] = 0
    value: RequestValue
    identity: int

    @classmethod
    def generate(cls, value: RequestValue):
        request = cls(value, cls._internal_count)
        cls._internal_count += 1
        return request


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class Reply(Generic[RequestValue]):
    value: RequestValue
    identity: int


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class Requester(Generic[RequestValue, ReplyValue]):
    _unhandled_requests: ClassVar[list[Reply]] = []
    request: RequestPipe[RequestValue, ReplyValue]

    async def send_request(self, request: RequestValue) -> int:
        request_message: Request[RequestValue] = Request.generate(request)
        self.request.parent_send_to_child_pipe.send(request_message)
        return request_message.identity

    async def check_received(self, identity: int) -> ReplyValue | None:
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
        while True:
            value: ReplyValue | None = await self.check_received(identity)
            if value is not None:
                return value
            if self.request.parent_recv_from_child_pipe.poll():
                reply: Reply = self.request.parent_recv_from_child_pipe.recv()
                if identity == reply.identity:
                    return reply.value
                self._unhandled_requests.append(reply)
            await sleep(0.0001)

    async def get_answer(self, request: RequestValue) -> ReplyValue:
        identity = await self.send_request(request)
        return await self.receive_answer(identity)


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class Replier(Generic[RequestValue, ReplyValue]):
    _received_request: ClassVar[Signal] = Signal()
    request: RequestPipe[RequestValue, ReplyValue]

    @property
    def received_request(self) -> SignalInstance[RequestValue]:
        return SignalInstance(self, self._received_request)

    async def _emit_request(self, value: RequestValue) -> None:
        self.received_request.emit(value)

    async def handle_requests(self) -> None:
        while self.request.child_recv_from_parent_pipe.poll():
            ensure_future(self._emit_request(self.request.child_recv_from_parent_pipe.recv()))

    async def reply(self, reply: Reply) -> None:
        self.request.child_send_to_parent_pipe.send(reply)


@attrs(slots=True, auto_attribs=True)
class TaskManagerProxy:
    _task_finished: ClassVar[Signal] = Signal()
    _task_group_finished: ClassVar[Signal] = Signal()
    process: Process | None
    outgoing_pipe: Connection
    incoming_pipe: Connection
    requester: Requester[Requests, Status]
    name: str = "manager"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def __del__(self) -> None:
        self.kill()

    @property
    def task_finished(self) -> SignalInstance:
        return SignalInstance(self, self._task_finished)

    @property
    def task_group_finished(self) -> SignalInstance:
        return SignalInstance(self, self._task_group_finished)

    def start(self, outgoing_pipe: Connection, incoming_pipe: Connection, replier: Replier) -> None:
        run(TaskManager(self.name, outgoing_pipe, incoming_pipe, replier).update())

    def make_request(self, request: Requests, timeout: float | None = None) -> Status:
        return exit_after(synchronize(self.requester.get_answer)(request), timeout)  # type: ignore

    def join(self, timeout: int | None = None) -> bool:
        try:
            exit_after(synchronize(self.requester.get_answer)(Requests.JOIN), timeout)
        except TimeoutError:
            return False
        log.debug(f"{self} is joined")
        try:
            exit_after(synchronize(self.requester.get_answer)(Requests.STOP_SLEEPING), timeout)
        except TimeoutError:
            return False
        return True

    def is_alive(self) -> bool:
        return self.process is not None and self.process.is_alive()

    def terminate(self) -> None:
        with suppress(TimeoutError):
            self.make_request(Requests.STOP, 1)
        if self.process is not None:
            self.process.terminate()
        log.debug(f"{self} is terminated")

    def kill(self) -> None:
        if self.process is not None:
            # Kill the process regardless if it terminates successfully.
            with suppress(TimeoutError):
                exit_after(synchronize(self.requester.get_answer)(Requests.STOP), 1)
            self.process.kill()
        log.debug(f"{self} is killed")

    def check_if_child_task_finished(self, task: TaskCallback, child_task: Task) -> Callable[[FinishedTask], None]:
        def check_if_child_task_finished(result: FinishedTask) -> None:
            if child_task.identity == result.identity:
                if result.exception and task.exception_handler is not None:
                    task.exception_handler(result.exception)
                elif result.exception:
                    log.warning(f"{self} received unhandled exception {result.exception} from {task}")
                else:
                    task.return_task(result.result)

        return check_if_child_task_finished

    def schedule_task(self, task: TaskCallback) -> None:
        child_task: Task = task.child_task
        self.task_finished.connect(self.check_if_child_task_finished(task, child_task), weak=False)
        self.outgoing_pipe.send(child_task)
        log.debug(f"{self} started task {task}")

    def schedule_tasks(self, tasks: Mapping[str, tuple[TaskCallback, set[str]]]) -> None:
        name_to_identity: dict[str, int] = {task_name: Task.generate_identity() for task_name in tasks.keys()}

        for task_name, (task, required_tasks) in tasks.items():
            child_task: Task = Task(
                task.start_task, name_to_identity[task_name], [name_to_identity[n] for n in required_tasks]
            )
            self.task_finished.connect(self.check_if_child_task_finished(task, child_task), weak=False)
            self.outgoing_pipe.send(child_task)
            log.debug(f"{self} started task {task}")

    def poll_tasks(self) -> None:
        while self.incoming_pipe.poll():
            finished_task = self.incoming_pipe.recv()
            log.debug(f"{self} finished task {finished_task}")
            self.task_finished.emit(finished_task)


class TaskManager:
    name: str
    outgoing_pipe: Connection
    incoming_pipe: Connection
    replier: Replier
    recent_returned_values: dict[int, Any]
    queued_tasks: dict[int, Task]
    workers: list[TaskWorkerProxy]
    status: Status

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
        self.workers = []
        for _ in range(cpu_count()):
            synchronize(self.add_worker)()
        run(self.update())

    async def add_worker(self) -> None:
        parent_outgoing_pipe, child_incoming_pipe = Pipe()
        child_outgoing_pipe, parent_incoming_pipe = Pipe()
        request_pipe = RequestPipe.generate()
        worker: TaskWorkerProxy = TaskWorkerProxy(
            None, parent_incoming_pipe, parent_outgoing_pipe, request_pipe.requester
        )
        process: Process = Process(
            target=worker.start,
            args=(child_outgoing_pipe, child_incoming_pipe, request_pipe.replier),
            name=f"worker_{len(self.workers)}",
        )
        worker.process = process
        process.start()
        self.workers.append(worker)

    async def send_task_to_worker(self, task: Task, *args: Any) -> None:
        choice(self.workers).outgoing_pipe.send(WorkerTask.from_task(task, args))

    async def get_important_return_values(self) -> set[int]:
        return set(chain.from_iterable(q.required_tasks for q in self.queued_tasks.values()))

    async def remove_stale_return_values(self) -> None:
        stale_return_values: set[int] = set(self.recent_returned_values.keys()).difference(
            await self.get_important_return_values()
        )
        for stale_return_value in stale_return_values:
            del self.recent_returned_values[stale_return_value]

    async def get_arguments_of_task(self, identity: int) -> list[Any]:
        return [self.recent_returned_values[r] for r in self.queued_tasks[identity].required_tasks]

    async def poll_queued_tasks(self, identity: int, return_value: Any) -> None:
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
        for worker in self.workers:
            if worker.incoming_pipe.poll():
                value = worker.incoming_pipe.recv()
                self.outgoing_pipe.send(value)

    async def poll_tasks(self) -> None:
        while self.incoming_pipe.poll():
            task: Task = self.incoming_pipe.recv()
            if task.required_tasks:
                self.queued_tasks |= {task.identity: task}
            else:
                ensure_future(self.send_task_to_worker(task))

    async def update(self) -> None:
        self.status = Status.RUNNING
        log.debug(f"{self} is running")
        while self.status != Status.STOPPED:
            await self.replier.handle_requests()
            if self.status == Status.RUNNING:
                await self.poll_tasks()
                await self.poll_workers()
            await sleep(0.0001)
        self.status = Status.ZOMBIE

    def handle_request(self, request: Request[Requests]) -> None:
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
        await self.replier.reply(Reply(self.status, identity))

    async def start_sleeping(self, identity: int) -> None:
        if self.status == Status.RUNNING:
            for worker in self.workers:
                await worker.make_request(Requests.START_SLEEPING)
            self.status = Status.SLEEPING
            log.debug(f"{self} is sleeping")
        await self.replier.reply(Reply(self.status, identity))

    async def stop_sleeping(self, identity: int) -> None:
        if self.status == Status.SLEEPING:
            self.status = Status.RUNNING
            for worker in self.workers:
                await worker.make_request(Requests.STOP_SLEEPING)
            log.debug(f"{self} is running")
        await self.replier.reply(Reply(self.status, identity))

    async def stop(self, identity: int) -> None:
        self.status = Status.STOPPED
        for worker in self.workers:
            await worker.make_request(Requests.STOP)
            await worker.kill()
        log.debug(f"{self} has stopped")
        await self.replier.reply(Reply(self.status, identity))

    async def join(self, identity: int) -> None:
        if self.status == Status.RUNNING:
            self.status = Status.SLEEPING

            async def join_worker(worker: TaskWorkerProxy) -> None:
                # Force kill a worker if it did not respond.
                if not await worker.join(10000):
                    await worker.kill()
                    await self.add_worker()

            await gather(join_worker(worker) for worker in self.workers)

        await self.replier.reply(Reply(self.status, identity))

    async def default(self, identity: int) -> None:
        log.warning(f"{self} has received an invalid request")
        await self.replier.reply(Reply(Status.NOT_DEFINED, identity))


@attrs(slots=True, auto_attribs=True)
class TaskWorkerProxy:
    process: Process | None
    incoming_pipe: Connection
    outgoing_pipe: Connection
    requester: Requester[Requests, Status]
    name: str = "worker"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def __del__(self) -> None:
        synchronize(self.kill())

    def start(self, outgoing_pipe: Connection, incoming_pipe: Connection, replier: Replier) -> None:
        run(TaskWorker(self.name, outgoing_pipe, incoming_pipe, replier).update())

    async def make_request(self, request: Requests, timeout: float | None = None) -> Status:
        return await wait_for(self.requester.get_answer(request), timeout)

    async def join(self, timeout: float | None = None) -> bool:
        try:
            await wait_for(self.requester.get_answer(Requests.JOIN), timeout)
        except TimeoutError:
            return False
        log.debug(f"{self} is joined")
        ensure_future(self.make_request(Requests.STOP_SLEEPING))
        return True

    async def is_alive(self) -> bool:
        return self.process is not None and self.process.is_alive()

    async def terminate(self) -> None:
        with suppress(TimeoutError):
            await wait_for(self.requester.get_answer(Requests.STOP), 1)
        if self.process is not None:
            self.process.terminate()
        log.debug(f"{self} is terminated")

    async def kill(self) -> None:
        if self.process is not None:
            self.process.kill()
        log.debug(f"{self} is killed")


class TaskWorker:
    name: str
    outgoing_pipe: Connection
    incoming_pipe: Connection
    replier: Replier
    status: Status
    task_count: int

    def __init__(self, name: str, outgoing_pipe: Connection, incoming_pipe: Connection, replier: Replier) -> None:
        self.name = name
        self.task_count = 0
        log.debug(f"{self} entering startup")
        self.status = Status.STARTUP
        self.outgoing_pipe = outgoing_pipe
        self.incoming_pipe = incoming_pipe
        self.replier = replier
        self.replier.received_request.connect(self.handle_request)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, active_tasks={self.task_count})"

    async def make_task(self, task: Task) -> None:
        try:
            finished_task = FinishedTask(task.identity, await task.task())
        except Exception as e:
            finished_task = FinishedTask.as_exception(task.identity, e)
        self.outgoing_pipe.send(FinishedTask(task.identity, finished_task))
        self.task_count -= 1

    async def poll_tasks(self) -> None:
        while self.incoming_pipe.poll():
            ensure_future(self.make_task(self.incoming_pipe.recv()))
            self.task_count += 1

    async def update(self) -> None:
        self.status = Status.RUNNING
        log.debug(f"{self} is running")
        while self.status != Status.STOPPED:
            await self.replier.handle_requests()
            if self.status == Status.RUNNING:
                await self.poll_tasks()
            await sleep(0.001)
        self.status = Status.ZOMBIE

    def handle_request(self, request: Request[Requests]) -> None:
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
        await self.replier.reply(Reply(self.status, identity))

    async def start_sleeping(self, identity: int) -> None:
        if self.status == Status.RUNNING:
            self.status = Status.SLEEPING
            log.debug(f"{self} is sleeping")
        await self.replier.reply(Reply(self.status, identity))

    async def stop_sleeping(self, identity: int) -> None:
        if self.status == Status.SLEEPING:
            self.status = Status.RUNNING
            log.debug(f"{self} is running")
        await self.replier.reply(Reply(self.status, identity))

    async def stop(self, identity: int) -> None:
        self.status = Status.STOPPED
        log.debug(f"{self} has stopped")
        await self.replier.reply(Reply(self.status, identity))

    async def join(self, identity: int) -> None:
        if self.status == Status.RUNNING:
            self.status = Status.SLEEPING
            log.debug(f"{self} is sleeping")
            while self.task_count > 0:
                await sleep(0.001)
        await self.replier.reply(Reply(self.status, identity))

    async def default(self, identity: int) -> None:
        log.warning(f"{self} has received an invalid request")
        await self.replier.reply(Reply(Status.NOT_DEFINED, identity))


def _counter(value=0) -> Generator[int, None, None]:
    count: int = value
    while True:
        yield count
        count += 1


counter: Generator[int, None, None] = _counter(0)


def start_task_manager(name: str | None) -> TaskManagerProxy:
    parent_outgoing_pipe, child_incoming_pipe = Pipe()
    child_outgoing_pipe, parent_incoming_pipe = Pipe()
    request_pipe = RequestPipe.generate()
    manager: TaskManagerProxy = TaskManagerProxy(
        None, parent_outgoing_pipe, parent_incoming_pipe, request_pipe.requester, name or "manager"
    )
    process: Process = Process(
        target=manager.start, args=(child_outgoing_pipe, child_incoming_pipe, request_pipe.replier), name=manager.name
    )
    manager.process = process
    process.start()
    return manager


def synchronize(func):
    def synchronize(*args, **kwargs):
        return get_event_loop().run_until_complete(func(*args, **kwargs))

    return synchronize


@overload
def exit_after(func: None = None, timeout: float | None = None) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]:
    ...


@overload
def exit_after(func: Callable[_P, _T], timeout: float | None = None) -> Callable[_P, _T]:
    ...


def exit_after(
    func: Callable[_P, _T] | None = None, timeout: float | None = None
) -> Callable[[Callable[_P, _T]], Callable[_P, _T]] | Callable[_P, _T]:
    def graceful_exit() -> NoReturn:
        raise TimeoutError

    def exit_after(func: Callable[_P, _T]) -> Callable[_P, _T]:
        if timeout is None or timeout == 0:
            return func

        def exit_after(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            timer: Timer = Timer(timeout, graceful_exit)  # type: ignore
            timer.start()
            try:
                result = func(*args, **kwargs)
            finally:
                timer.cancel()
            return result

        return exit_after

    return exit_after if func is None else exit_after(func)


_task_manager: TaskManagerProxy | None


class TaskMethod(Generic[_P, _T]):
    __slots__ = ("name", "fstart", "_freturn", "ehandler", "__doc__")

    name: str | None
    fstart: Callable[_P, _T]
    _freturn: Callable[[_T], None] | None
    ehandler: Callable[[Exception], None] | None

    def __init__(
        self,
        fstart: Callable[_P, _T],
        freturn: Callable[[_T], None] | None = None,
        ehandler: Callable[[Exception], None] | None = None,
        name: str | None = None,
        doc: str | None = None,
    ) -> None:
        self.name = name
        self.fstart = fstart
        self._freturn = freturn
        self.ehandler = ehandler
        self.__doc__ = doc

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.fstart}, {self._freturn}, {self.name}, {self.__doc__})"

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"{self.fstart.__name__ if self.fstart else None}, "
            f"{self.freturn.__name__ if self._freturn else None}, "
            f"{self.name}, {self.__doc__})"
        )

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> None:
        if _task_manager is None:
            global _task_manager
            _task_manager = start_task_manager("task manager")
        self._task_manager.schedule_task(  # type: ignore
            TaskCallback(lambda: self.fstart(*args, **kwargs), self.freturn, self.ehandler)
        )

    @property
    def freturn(self) -> Callable[[_T], None]:
        return lambda _: None if self._freturn is None else self._freturn  # type: ignore

    @property
    def task_callback(self) -> TaskCallback[_P, _T]:
        return TaskCallback(self.fstart, self.freturn, self.ehandler)

    def start(self, fstart: Callable[_P, _T]):
        return type(self)(fstart, self._freturn, self.ehandler, self.name, self.__doc__)

    def return_task(self, freturn: Callable[[_T], None] | None):
        return type(self)(self.fstart, freturn, self.ehandler, self.name, self.__doc__)

    def handler(self, ehandler: Callable[[Exception], None] | None = None):
        return type(self)(self.fstart, self._freturn, ehandler, self.name, self.__doc__)


task: type[TaskMethod] = TaskMethod


def stage_task(tasks: Mapping[str, tuple[TaskMethod, set[str]]]):
    if _task_manager is None:
        global _task_manager
        _task_manager = start_task_manager("task manager")
    _task_manager.schedule_tasks({k: (t.task_callback, r) for k, (t, r) in tasks.items()})
