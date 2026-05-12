import importlib
import os
import subprocess
import sys

from .token_type import TokenType
from .token import Token
from .scanner import Scanner

util_path = os.path.join(__path__[0], '..', 'util')
try:
    from .generated.Expr import Expr, ExprVisitor, Assign, Ternary, Binary, Call, Get, Grouping, Literal, Logical, Set, Supr, This, Unary, Variable, LambdaFun
    from .generated.Stmt import Stmt, StmtVisitor, Block, BreakStmt, ClassStmt, ExpressionStmt, FunctionStmt, IfStmt, PrintStmt, ReturnStmt, VarStmt, WhileStmt
except ImportError:
    subprocess.run([sys.executable, os.path.join(util_path, 'generate_ast.py'),
                    os.path.join(__path__[0], 'generated')], check=True)
    importlib.invalidate_caches()
    from .generated.Expr import Expr, ExprVisitor, Assign, Ternary, Binary, Call, Get, Grouping, Literal, Logical, Set, Supr, This, Unary, Variable, LambdaFun
    from .generated.Stmt import Stmt, StmtVisitor, Block, BreakStmt, ClassStmt, ExpressionStmt, FunctionStmt, IfStmt, PrintStmt, ReturnStmt, VarStmt, WhileStmt

from .ast_printer import AstPrinter
from .parser import Parser, ParseError

from .runtime_error import RuntimeError
from .environment import UninitializedValue, Environment
from .interpreter import Interpreter, ReturnSignal
from .lox_callable import LoxCallable
from .lox_function import LoxFunction
from .lox_class import LoxInstance, LoxClass
from .resolver import Resolver

from .lox import Lox

def main():
    lox_instance = Lox()
    return lox_instance.main(sys.argv[1:])
