from dataclasses import dataclass
from enum import Enum, IntFlag, auto

from . import Expr, ExprVisitor, Assign, Binary, Call, Get, Grouping, LambdaFun, Literal, Logical, Set, Ternary, This, Unary, Variable
from . import Interpreter
from . import Stmt, StmtVisitor, Block, BreakStmt, ClassStmt, ExpressionStmt, FunctionStmt, IfStmt, PrintStmt, ReturnStmt, VarStmt, WhileStmt
from . import Token

class FunctionType(Enum):
    NONE = auto()
    FUNCTION = auto()
    INITIALIZER = auto()
    METHOD = auto()

class ClassType(Enum):
    NONE = auto()
    CLASS = auto()

class VarFlag(IntFlag):
    NONE = 0
    INITIALIZED = auto()
    ACCESSED = auto()

@dataclass
class LocalVar:
    token: Token
    flags: VarFlag = VarFlag.NONE

class Resolver(ExprVisitor, StmtVisitor):
    def __init__(self, interpreter: Interpreter, error_handler: callable):
        self.interpreter: Interpreter = interpreter
        self.scopes: list[dict[str, LocalVar]] = []
        self.current_function: FunctionType = FunctionType.NONE
        self.current_class: ClassType = ClassType.NONE
        self.loop_depth: int = 0
        self.error_handler = error_handler

    def visit_assign_expr(self, assign: Assign) -> None:
        self.resolve(assign.value)
        self.resolve_local(assign, assign.name, mark_access=False)

    def visit_binary_expr(self, binary: Binary) -> None:
        self.resolve(binary.left)
        self.resolve(binary.right)

    def visit_call_expr(self, call: Call) -> None:
        self.resolve(call.callee)

        for argument in call.arguments:
            self.resolve(argument)

    def visit_get_expr(self, get: Get) -> None:
        self.resolve(get.obj)

    def visit_grouping_expr(self, grouping: Grouping) -> None:
        self.resolve(grouping.expression)

    def visit_lambdafun_expr(self, lambdafun: LambdaFun) -> None:
        self.resolve_function(lambdafun, FunctionType.FUNCTION)

    def visit_literal_expr(self, literal: Literal) -> None:
        return
    
    def visit_logical_expr(self, logical: Logical) -> None:
        self.resolve(logical.left)
        self.resolve(logical.right)

    def visit_set_expr(self, set: Set) -> None:
        self.resolve(set.value)
        self.resolve(set.obj)

    def visit_ternary_expr(self, ternary: Ternary) -> None:
        self.resolve(ternary.condition)
        self.resolve(ternary.then_expr)
        self.resolve(ternary.else_expr)

    def visit_this_expr(self, this: This) -> None:
        if self.current_class == ClassType.NONE:
            self.error_handler(this.keyword, "Can't use 'this' outside of a class.")
            return

        self.resolve_local(this, this.keyword)

    def visit_unary_expr(self, unary: Unary) -> None:
        self.resolve(unary.right)

    def visit_variable_expr(self, variable: Variable) -> None:
        if len(self.scopes) > 0:
            local = self.scopes[-1].get(variable.name.lexeme)
            if local is not None and not (local.flags & VarFlag.INITIALIZED):
                self.error_handler(variable.name, "Can't read local variable in its own initializer.")
        
        self.resolve_local(variable, variable.name)

    def visit_block_stmt(self, block: Block) -> None:
        self.begin_scope()
        self.resolve(block.statements)
        self.end_scope()

    def visit_breakstmt_stmt(self, breakstmt: BreakStmt) -> None:
        if self.loop_depth == 0:
            self.error_handler(breakstmt.keyword, "Can't use 'break' outside of a loop.")

    def visit_classstmt_stmt(self, classstmt: ClassStmt) -> None:
        enclosing_class = self.current_class
        self.current_class = ClassType.CLASS

        self.declare(classstmt.name)
        self.define(classstmt.name)

        self.begin_scope()
        # 'this' is special, it's initialized and accessed as far as the resolver is concerned
        self.scopes[-1]['this'] = LocalVar(classstmt.name, flags=(VarFlag.INITIALIZED | VarFlag.ACCESSED))

        for method in classstmt.methods:
            declaration = FunctionType.INITIALIZER if method.name.lexeme == 'init' else FunctionType.METHOD
            self.resolve_function(method, declaration)

        self.end_scope()
        self.current_class = enclosing_class

    def visit_expressionstmt_stmt(self, expressionstmt: ExpressionStmt) -> None:
        self.resolve(expressionstmt.expression)

    def visit_functionstmt_stmt(self, functionstmt: FunctionStmt) -> None:
        self.declare(functionstmt.name)
        self.define(functionstmt.name)

        self.resolve_function(functionstmt, FunctionType.FUNCTION)

    def visit_ifstmt_stmt(self, ifstmt: IfStmt) -> None:
        self.resolve(ifstmt.condition)
        self.resolve(ifstmt.then_branch)
        if ifstmt.else_branch is not None:
            self.resolve(ifstmt.else_branch)

    def visit_printstmt_stmt(self, printstmt: PrintStmt) -> None:
        self.resolve(printstmt.expression)

    def visit_returnstmt_stmt(self, returnstmt: ReturnStmt) -> None:
        if self.current_function == FunctionType.NONE:
            self.error_handler(returnstmt.keyword, "Can't return from top-level code.")

        if returnstmt.value is not None:
            if self.current_function == FunctionType.INITIALIZER:
                self.error_handler(returnstmt.keyword, "Can't return a value from an initializer.")
                
            self.resolve(returnstmt.value)

    def visit_varstmt_stmt(self, varstmt: VarStmt) -> None:
        self.declare(varstmt.name)
        if varstmt.initializer is not None:
            self.resolve(varstmt.initializer)
        self.define(varstmt.name)

    def visit_whilestmt_stmt(self, whilestmt: WhileStmt) -> None:
        self.loop_depth += 1
        self.resolve(whilestmt.condition)
        self.resolve(whilestmt.body)
        self.loop_depth -= 1
    
    def resolve(self, snippet: Expr | Stmt | list[Stmt]):
        if isinstance(snippet, list):
            for statement in snippet:
                self.resolve(statement)
        else:
            snippet.accept(self)

    def begin_scope(self):
        self.scopes.append(dict())

    def end_scope(self):
        scope = self.scopes.pop()

        for local in scope.values():
            if not local.flags & VarFlag.ACCESSED:
                self.error_handler(local.token, f"'{local.token.lexeme}' is never used.")

    def declare(self, name: Token):
        if len(self.scopes) == 0:
            return
        
        scope = self.scopes[-1]
        if name.lexeme in scope:
            self.error_handler(name, "Already a variable with this name in this scope.")

        scope[name.lexeme] = LocalVar(name)

    def define(self, name: Token):
        if len(self.scopes) == 0:
            return
        
        self.scopes[-1][name.lexeme].flags |= VarFlag.INITIALIZED

    def resolve_local(self, expr: Expr, name: Token, mark_access: bool = True):
        num_scopes = 0
        for scope in reversed(self.scopes):
            if name.lexeme in scope:
                if mark_access:
                    scope[name.lexeme].flags |= VarFlag.ACCESSED
                self.interpreter.resolve(expr, num_scopes)
                return
            num_scopes += 1

    def resolve_function(self, func: FunctionStmt | LambdaFun, type: FunctionType):
        enclosing_function = self.current_function
        self.current_function = type

        self.begin_scope()
        for param in func.params:
            self.declare(param)
            self.define(param)
        self.resolve(func.body)
        self.end_scope()
        self.current_function = enclosing_function
