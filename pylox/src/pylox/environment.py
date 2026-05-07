from . import RuntimeError
from . import Token

class UninitializedValue:
    pass

class Environment:
    def __init__(self, enclosing: "Environment" = None):
        self.enclosing: "Environment" = enclosing
        self.values : dict[str, object] = {}

    def get(self, name: Token) -> object:
        if name.lexeme in self.values:
            value = self.values[name.lexeme]
            if isinstance(value, UninitializedValue):
                raise RuntimeError(name, f"Uninitialized variable '{name.lexeme}'.")
            return value
        
        if self.enclosing is not None:
            return self.enclosing.get(name)
        
        raise RuntimeError(name, f"Undefined variable '{name.lexeme}.")
    
    def get_at(self, distance: int, name: str) -> object:
        return self.ancestor(distance).values[name]
    
    def assign_at(self, distance: int, name: Token, value: object) -> None:
        self.ancestor(distance).values[name.lexeme] = value

    def ancestor(self, distance: int) -> "Environment":
        environment = self
        for i in range(distance):
            environment = environment.enclosing

        return environment

    def define(self, name: str, value: object = UninitializedValue()) -> None:
        self.values[name] = value

    def assign(self, name: Token, value: object) -> None:
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
        elif self.enclosing is not None:
            self.enclosing.assign(name, value)
        else:
            raise RuntimeError(name, f"Undefined variable '{name.lexeme}'.")
