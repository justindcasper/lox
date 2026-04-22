import sys

from .token_type import TokenType
from .token import Token
from .scanner import Scanner
from .lox import Lox

def main():
    lox_instance = Lox()
    return lox_instance.main(sys.argv[1:])
