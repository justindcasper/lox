from typing import Any

from . import Interpreter
from . import LoxCallable
from . import LoxFunction
from . import RuntimeError
from . import Token

class LoxInstance:
    def __init__(self, lox_class: "LoxClass"):
        self.lox_class: "LoxClass" = lox_class
        self.fields: dict[str, Any] = {}

    def __str__(self):
        return f"{self.lox_class.name} instance"
    
    def get(self, name: Token) -> Any:
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]
        
        method = self.lox_class.find_method(name.lexeme)
        if method is not None:
            return method.bind(self)
        
        raise RuntimeError(name, f"Undefined property '{name.lexeme}'.")
    
    def set(self, name: Token, value: object) -> None:
        self.fields[name.lexeme] = value

class LoxClass(LoxCallable):
    def __init__(self, name: str, methods: dict[str, LoxFunction]):
        self.name = name
        self.methods = methods

    def __str__(self):
        return self.name
    
    def arity(self):
        initializer = self.find_method('init')
        if initializer is None:
            return 0
        return initializer.arity()
    
    def call(self, interpreter: Interpreter, arguments: list[Any]):
        instance = LoxInstance(self)
        initializer = self.find_method('init')
        if initializer is not None:
            initializer.bind(instance).call(interpreter, arguments)

        return instance
    
    def find_method(self, name: str) -> LoxFunction:
        return self.methods.get(name)
    