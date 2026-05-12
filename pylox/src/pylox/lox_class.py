from typing import Any

from . import Interpreter
from . import LoxCallable
from . import LoxFunction
from . import RuntimeError
from . import Token

class LoxInstance:
    def __init__(self, lox_class: "LoxClass | None"):
        self.lox_class: "LoxClass" = lox_class
        self.fields: dict[str, Any] = {}

    def __str__(self):
        return f"{self.lox_class.name} instance" if self.lox_class is not None else "class"
    
    def get(self, name: Token, interpreter: Interpreter) -> Any:
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]
        
        if self.lox_class is not None:
            getter = self.lox_class.find_getter(name.lexeme)
            if getter is not None:
                return getter.bind(self).call(interpreter, [])
            
            method = self.lox_class.find_method(name.lexeme)
            if method is not None:
                return method.bind(self)
        
        raise RuntimeError(name, f"Undefined property '{name.lexeme}'.")
    
    def set(self, name: Token, value: object) -> None:
        self.fields[name.lexeme] = value

class LoxClass(LoxInstance, LoxCallable):
    def __init__(self, name: str, superclass: "LoxClass", methods: dict[str, LoxFunction],
                 getters: dict[str, LoxFunction], metaclass: "LoxClass | None" = None):
        super().__init__(metaclass)
        self.name = name
        self.superclass = superclass
        self.methods = methods
        self.getters = getters

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
        method = self.methods.get(name)
        if method is not None:
            return method
        
        if self.superclass is not None:
            return self.superclass.find_method(name)
        
        return None
    
    def find_getter(self, name: str) -> LoxFunction:
        getter = self.getters.get(name)
        if getter is not None:
            return getter
        
        if self.superclass is not None:
            return self.superclass.find_getter(name)
        
        return None
    