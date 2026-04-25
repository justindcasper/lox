import os
import subprocess
import sys

from .token_type import TokenType
from .token import Token
from .scanner import Scanner

util_path = os.path.join(__path__[0], '..', 'util')
try:
    from .generated.Expr import Expr, Visitor, Binary, Grouping, Literal, Unary
except ImportError:
    subprocess.run([sys.executable, os.path.join(util_path, 'generate_ast.py'),
                    os.path.join(__path__[0], 'generated')])
    from .generated.Expr import Expr, Visitor, Binary, Grouping, Literal, Unary

from .ast_printer import AstPrinter
from .lox import Lox

def main():
    lox_instance = Lox()
    return lox_instance.main(sys.argv[1:])
