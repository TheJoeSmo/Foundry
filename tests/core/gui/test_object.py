from functools import cached_property

from attr import attrs

from foundry.core.gui import (
    BaseModel,
    Object,
    SignalInstance,
    SignalTester,
    emitting_property,
)


class TestObject:
    @cached_property
    def SimpleChildObject(self):
        class SimpleChildObject(Object):
            a: SignalInstance[int]

            @attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True, repr=False)
            class Model(BaseModel):
                b: int

                def __repr__(self) -> str:
                    return f"<{self.b}>"

            def __repr__(self) -> str:
                return f"SimpleChildObject({self.b})"

            def initialize_state(self, model: Model, *args, **kwargs) -> None:
                super().initialize_state(model, *args, **kwargs)
                self.a.link(self._b_updated)

        return SimpleChildObject

    @cached_property
    def SimpleObject(self):
        class SimpleObject(Object):
            a: SignalInstance[int]
            b: SignalInstance[str]
            c: SignalInstance[tuple[int, str]]

            @attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True, repr=False)
            class Model(BaseModel):
                d: int
                e: str

                def __repr__(self) -> str:
                    return f"<{self.d}, {self.e}>"

                @emitting_property("d", "e")
                def f(self) -> tuple[int, str]:
                    return self.d, self.e

                @f.setter
                def f(self, value):
                    self.d = value[0]  # type: ignore
                    self.e = value[1]  # type: ignore

            def __repr__(self) -> str:
                return f"SimpleObject({self.d}, {self.e})"  # type: ignore

            def initialize_state(self_, model: Model, *args, **kwargs) -> None:
                super().initialize_state(model, *args, **kwargs)
                self_.child = self.SimpleChildObject(self.SimpleChildObject.Model(model.d))
                self_.a.link(self_._d_updated)
                self_.b.link(self_._e_updated)
                self_.c.link(self_._f_updated)
                self_.connect_child("d", self_.child, "a", "b")

        return SimpleObject

    def test_initialize_child(self):
        self.SimpleChildObject(self.SimpleChildObject.Model(0))

    def test_initialize_parent(self):
        self.SimpleObject(self.SimpleObject.Model(0, "test"))

    def test_user_defined_signal_linking_with_model_property(self):
        obj = self.SimpleChildObject(self.SimpleChildObject.Model(0))
        with SignalTester(obj.updated) as tester_updated:
            with SignalTester(obj.a) as tester:
                print(obj)
                obj.b = 1  # type: ignore
                print(obj)
                assert obj.b == 1
                assert obj.model.b == 1  # type: ignore
                assert tester.count == 1
                assert tester_updated.count == 1

    def test_private_defined_signal_linking_with_model_property(self):
        obj = self.SimpleChildObject(self.SimpleChildObject.Model(0))
        with SignalTester(obj.updated) as tester_updated:
            with SignalTester(obj._b_updated) as tester:
                obj.b = 1  # type: ignore
                assert obj.b == 1
                assert obj.model.b == 1  # type: ignore
                assert tester.count == 1
                assert tester_updated.count == 1

    def test_signal_blocker(self):
        obj = self.SimpleChildObject(self.SimpleChildObject.Model(0))
        with SignalTester(obj.updated) as tester_updated:
            with SignalTester(obj.a) as tester:
                with obj.signal_blocker:
                    obj.b = 1  # type: ignore
                    assert obj.b == 1
                    assert obj.model.b == 1  # type: ignore
                    assert tester.count == 0
                    assert tester_updated.count == 0

    def test_user_defined_property_setting(self):
        obj = self.SimpleObject(self.SimpleObject.Model(0, "test"))
        with SignalTester(obj.updated) as tester_updated:
            with SignalTester(obj.a) as tester_a:
                with SignalTester(obj.b) as tester_b:
                    with SignalTester(obj.c) as tester_c:
                        obj.f = (1, "success")  # type: ignore
                        assert obj.d == 1
                        assert obj.e == "success"
                        assert tester_updated.count == 1
                        assert tester_a.count == 1
                        assert tester_b.count == 1
                        assert tester_c.count == 1

    def test_private_defined_property_setting(self):
        obj = self.SimpleObject(self.SimpleObject.Model(0, "test"))
        with SignalTester(obj.updated) as tester_updated:
            with SignalTester(obj._d_updated) as tester_d:
                with SignalTester(obj._e_updated) as tester_e:
                    with SignalTester(obj._f_updated) as tester_f:
                        obj.f = (1, "success")  # type: ignore
                        assert obj.d == 1
                        assert obj.e == "success"
                        assert tester_updated.count == 1
                        assert tester_d.count == 1
                        assert tester_e.count == 1
                        assert tester_f.count == 1

    def test_property_updated_on_setting_model(self):
        obj = self.SimpleObject(self.SimpleObject.Model(0, "test"))
        with SignalTester(obj.updated) as tester_updated:
            with SignalTester(obj._d_updated) as tester_d:
                with SignalTester(obj._f_updated) as tester_f:
                    obj.d = 1  # type: ignore
                    assert obj.d == 1
                    assert obj.f == (1, "test")
                    assert tester_updated.count == 1
                    assert tester_d.count == 1
                    assert tester_f.count == 1
