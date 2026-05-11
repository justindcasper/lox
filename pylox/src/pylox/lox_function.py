from typing import Any

from . import Environment
from . import FunctionStmt
from . import Interpreter, ReturnSignal
from . import LoxCallable

class LoxFunction(LoxCallable):
    def __init__(self, declaration: FunctionStmt, closure: Environment, is_initializer: bool = False):
        self.declaration = declaration
        self.closure = closure
        self.is_initializer = is_initializer

    def __str__(self):
        name = getattr(self.declaration, "name", None)
        return f"<fn {name.lexeme}>" if name is not None else "<anonymous fn>"

    def arity(self):
        return len(self.declaration.params)

    def call(self, interpreter: Interpreter, arguments: list[Any]):
        environment = Environment(self.closure)
        if self.declaration.params is not None:
            for param, arg in zip(self.declaration.params, arguments):
                environment.define(param.lexeme, arg)

        try:
            interpreter.execute_block(self.declaration.body, environment)
        except ReturnSignal as r:
            return self.closure.get_at(0, 'this') if self.is_initializer else r.value
        
        return self.closure.get_at(0, 'this') if self.is_initializer else None
    
    # instance should be a LoxInstance
    def bind(self, instance) -> "LoxFunction":
        environment = Environment(self.closure)
        environment.define('this', instance)
        return LoxFunction(self.declaration, environment, is_initializer=self.is_initializer)
