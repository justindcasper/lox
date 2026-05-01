from . import RuntimeError
from . import Token

class Environment:
    def __init__(self, enclosing: "Environment" = None):
        self.enclosing: "Environment" = enclosing
        self.values : dict[str, object] = {}

    def get(self, name: Token) -> object:
        if name.lexeme in self.values:
            return self.values[name.lexeme]
        
        if self.enclosing is not None:
            return self.enclosing.get(name)
        
        raise RuntimeError(name, f"Undefined variable '{name.lexeme}.")

    def define(self, name: str, value: object) -> None:
        self.values[name] = value

    def assign(self, name: Token, value: object) -> None:
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
        elif self.enclosing is not None:
            self.enclosing.assign(name, value)
        else:
            raise RuntimeError(name, f"Undefined variable '{name.lexeme}'.")
