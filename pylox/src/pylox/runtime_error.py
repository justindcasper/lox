from . import Token

class RuntimeError(Exception):
    def __init__(self, token: Token, message: str):
        super().__init__(message)
        self.token = token
        