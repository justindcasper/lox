from typing import Protocol, runtime_checkable, Any

from . import Interpreter

@runtime_checkable
class LoxCallable(Protocol):
    def arity(self) -> int:
        pass

    def call(self, interpreter: Interpreter, arguments: list[Any]) -> Any:
        pass
