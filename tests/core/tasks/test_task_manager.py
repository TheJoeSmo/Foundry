from pytest import fixture

from foundry.core.gui import Signal, SignalInstance, SignalTester
from foundry.core.tasks import (
    Requests,
    Status,
    TaskCallback,
    TaskManagerProxy,
    exit_after,
    start_task_manager,
    synchronize,
    task,
    wait_until,
)


@fixture(scope="module")
def task_manager():
    manager = start_task_manager()
    yield manager
    manager.terminate()


def test_synchronize():
    async def increment(value: int) -> int:
        return value + 1

    assert synchronize(increment)(0) == 1


def test_exit_after_success():
    def increment(value: int) -> int:
        return value + 1

    assert exit_after(increment, 10)(0) == 1


def test_exit_after_failure():
    def forever(value: int) -> int:
        while True:
            value += 1

    exit_after(forever, 0.0001)(0)


def test_task_manager_kill():
    task_manager: TaskManagerProxy = start_task_manager()
    assert task_manager.is_alive()
    task_manager.kill()
    assert not task_manager.is_alive()


def test_task_manager_terminate():
    task_manager: TaskManagerProxy = start_task_manager()
    assert task_manager.is_alive()
    task_manager.terminate()
    assert not task_manager.is_alive()


def test_task_method_simple():
    class Obj:
        _updated = Signal(name="test_updated")

        def __init__(self, value: bool = False):
            self.value = value

        def __str__(self) -> str:
            return f"<{self.value}>"

        @property
        def task_updated(self) -> SignalInstance:
            return SignalInstance(self, self._updated)

        @task
        @staticmethod
        def increment():
            return True

        @increment.return_task
        @staticmethod
        def increment(instance, value: bool) -> None:
            instance.value = value

        @increment.handler
        @staticmethod
        def increment(exception: Exception) -> None:
            raise exception

        increment.fsignal = _updated

    obj = Obj()
    obj.increment(obj)
    from foundry.core.tasks import _task_manager

    assert _task_manager() is not None
    assert _task_manager().join(0.1)
    with SignalTester(obj.task_updated) as signal_tester:
        _task_manager().poll_tasks()
        assert signal_tester.count == 1

    _task_manager().terminate()

    assert obj.value


class TestTaskManager:
    manager: TaskManagerProxy

    @fixture(autouse=True)
    def _manager(self, task_manager):
        self.manager = task_manager

    class Obj:
        def __init__(self, value: int = 0):
            self.value = value
            self.return_times = 0
            self.exception_times = 0

        def __repr__(self) -> str:
            return f"<{self.value}, {self.return_times}, {self.exception_times}>"

        def callback(self, value: int | None) -> TaskCallback:
            return TaskCallback(self.increment(value), self.increment_return, self.increment_exception)

        def increment(self, value: int | None = None):
            def increment(v: int | None = None):
                return value + 1 if value is not None else v + 1  # type: ignore

            return increment

        def increment_return(self, value) -> None:
            self.value = value
            self.return_times += 1

        def increment_exception(self, exception: Exception) -> None:
            self.exception_times += 1
            raise exception

    def test_get_status(self):
        assert self.manager.make_request(Requests.GET_STATUS) == Status.RUNNING

    def test_schedule_task_simple(self):
        obj = self.Obj()
        manager: TaskManagerProxy = self.manager
        manager.schedule_task(obj.callback(0))
        wait_until(manager.poll_tasks, True, 10)()
        assert obj.value == 1
        assert obj.return_times == 1
        assert obj.exception_times == 0

    def test_schedule_task_complex(self):
        obj1, obj2 = self.Obj(), self.Obj()
        tasks_completed = 0

        def wait() -> int:
            nonlocal tasks_completed
            result = manager.poll_tasks()
            if result:
                tasks_completed += result

            return tasks_completed

        manager: TaskManagerProxy = self.manager
        manager.schedule_task(obj1.callback(0))
        manager.schedule_task(obj2.callback(2))
        wait_until(wait, 2, 10)()
        assert obj1.value == 1
        assert obj1.return_times == 1
        assert obj1.exception_times == 0
        assert obj2.value == 3
        assert obj2.return_times == 1
        assert obj2.exception_times == 0

    def test_schedule_tasks_simple(self):
        obj1, obj2 = self.Obj(), self.Obj()
        tasks_completed = 0

        def wait() -> int:
            nonlocal tasks_completed
            result = manager.poll_tasks()
            if result:
                tasks_completed += result

            return tasks_completed

        manager: TaskManagerProxy = self.manager
        manager.schedule_tasks(
            {
                "task1": (obj1.callback(0), set()),
                "task2": (
                    obj2.callback(None),
                    {
                        "task1",
                    },
                ),
            }
        )
        wait_until(wait, 2, 10)()
        assert obj1.value == 1
        assert obj1.return_times == 1
        assert obj1.exception_times == 0
        assert obj2.value == 2
        assert obj2.return_times == 1
        assert obj2.exception_times == 0
