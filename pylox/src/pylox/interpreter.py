import time
from typing import Any

from . import Environment, UninitializedValue
from . import Expr, ExprVisitor, Assign, Ternary, Binary, Grouping, Call, Literal, Logical, Unary, Variable, LambdaFun
from . import RuntimeError
from . import Stmt, StmtVisitor, Block, BreakStmt, ExpressionStmt, FunctionStmt, IfStmt, PrintStmt, ReturnStmt, VarStmt, WhileStmt
from . import Token
from . import TokenType

class BreakSignal(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class ReturnSignal(Exception):
    def __init__(self, value: object, *args):
        self.value = value
        super().__init__(*args)

class Interpreter(ExprVisitor, StmtVisitor):
    # Using the LoxCallable interface, but without importing to avoid a circular import
    class clock_function:
        def __str__(self) -> str:
            return "<native fn>"
        
        def arity(self):
            return 0
        
        def call(self, interpreter: "Interpreter", arguments: list[Any]):
            return time.time_ns() / 1_000_000
        
    def __init__(self, error_handler: callable):
        self.globals = Environment()
        self.locals: dict[Expr, int] = {}
        self.globals.define('clock', Interpreter.clock_function())
        self.environment = self.globals
        self.error_handler = error_handler
        # Late binding + dependency injection to avoid a circular import
        from . import LoxFunction
        self.function_class = LoxFunction

    def interpret(self, statements: list[Stmt]) -> None:
        try:
            for statement in statements:
                self.execute(statement)
        except RuntimeError as e:
            self.error_handler(e)

    def interpret_expr(self, expr: Expr) -> object:
        try:
            return self.evaluate(expr)
        except RuntimeError as e:
            self.error_handler(e)
            return UninitializedValue()

    def visit_assign_expr(self, assign: Assign) -> object:
        value = self.evaluate(assign.value)
        
        distance = self.locals.get(assign)
        if distance is not None:
            self.environment.assign_at(distance, assign.name, value)
        else:
            self.globals.assign(assign.name, value)

        return value

    def visit_ternary_expr(self, ternary: Ternary) -> object:
        condition = self.evaluate(ternary.condition)

        if Interpreter.truthy(condition):
            return self.evaluate(ternary.then_expr)
        
        return self.evaluate(ternary.else_expr)
    
    def visit_binary_expr(self, binary: Binary) -> object:
        left = self.evaluate(binary.left)
        right = self.evaluate(binary.right)

        match binary.operator.type:
            case TokenType.BANG_EQUAL:
                return not (left == right)
            case TokenType.EQUAL_EQUAL:
                return left == right
            case TokenType.GREATER:
                Interpreter.check_number_operands(binary.operator, left, right)
                return float(left) > float(right)
            case TokenType.GREATER_EQUAL:
                Interpreter.check_number_operands(binary.operator, left, right)
                return float(left) >= float(right)
            case TokenType.LESS:
                Interpreter.check_number_operands(binary.operator, left, right)
                return float(left) < float(right)
            case TokenType.LESS_EQUAL:
                Interpreter.check_number_operands(binary.operator, left, right)
                return float(left) <= float(right)
            case TokenType.PLUS:
                if isinstance(left, float) and isinstance(right, float):
                    return float(left) + float(right)
                
                if isinstance(left, str) or isinstance(right, str):
                    return Interpreter.stringify(left) + Interpreter.stringify(right)
                
                raise RuntimeError(binary.operator, 'Operands must be two numbers or two strings.')
            case TokenType.MINUS:
                Interpreter.check_number_operands(binary.operator, left, right)
                return float(left) - float(right)
            case TokenType.STAR:
                Interpreter.check_number_operands(binary.operator, left, right)
                return float(left) * float(right)
            case TokenType.SLASH:
                Interpreter.check_number_operands(binary.operator, left, right)
                try:
                    return float(left) / float(right)
                except ZeroDivisionError:
                    raise RuntimeError(binary.operator, 'Cannot divide by 0.')
            case TokenType.COMMA:
                return right
            case _:
                # Unreachable
                return None
    
    def visit_grouping_expr(self, grouping: Grouping) -> object:
        return self.evaluate(grouping.expression)
    
    def visit_literal_expr(self, literal: Literal) -> object:
        return literal.value
    
    def visit_logical_expr(self, logical: Logical) -> object:
        left = self.evaluate(logical.left)

        if logical.operator.type == TokenType.OR:
            if Interpreter.truthy(left):
                return left
        else:
            if not Interpreter.truthy(left):
                return left
            
        return self.evaluate(logical.right)
    
    def visit_unary_expr(self, unary: Unary) -> object:
        right = self.evaluate(unary.right)

        match unary.operator.type:
            case TokenType.BANG:
                return not Interpreter.truthy(right)
            case TokenType.MINUS:
                Interpreter.check_number_operand(unary.operator, right)
                return -float(right)
            case _:
                # Unreachable
                return None
            
    def visit_call_expr(self, call: Call) -> object:
        callee = self.evaluate(call.callee)

        arguments = []
        for argument in call.arguments:
            arguments.append(self.evaluate(argument))

        if not hasattr(callee, "call") or not hasattr(callee, "arity"):
            raise RuntimeError(call.paren, "Can only call functions and classes.")
        
        arity = callee.arity()
        num_arguments = len(arguments)
        if num_arguments != arity:
            raise RuntimeError(call.paren, f"Expected {arity} arguments but got {num_arguments}.")

        return callee.call(self, arguments)
            
    def visit_variable_expr(self, variable: Variable) -> object:
        return self.lookup_variable(variable.name, variable)
    
    def visit_lambdafun_expr(self, lambdafun: LambdaFun) -> object:
        return self.function_class(lambdafun, self.environment)
    
    def evaluate(self, expr: Expr) -> object:
        return expr.accept(self)
    
    def visit_block_stmt(self, block: Block) -> None:
        self.execute_block(block.statements, Environment(self.environment))
    
    def visit_expressionstmt_stmt(self, expressionstmt: ExpressionStmt) -> None:
        self.evaluate(expressionstmt.expression)

    def visit_ifstmt_stmt(self, ifstmt: IfStmt) -> None:
        if Interpreter.truthy(self.evaluate(ifstmt.condition)):
            self.execute(ifstmt.then_branch)
        elif ifstmt.else_branch is not None:
            self.execute(ifstmt.else_branch)

    def visit_printstmt_stmt(self, printstmt: PrintStmt) -> None:
        value = self.evaluate(printstmt.expression)
        print(Interpreter.stringify(value))

    def visit_breakstmt_stmt(self, breakstmt: BreakStmt) -> None:
        raise BreakSignal()
    
    def visit_returnstmt_stmt(self, returnstmt: ReturnStmt) -> None:
        value = None if returnstmt.value == None else self.evaluate(returnstmt.value)

        raise ReturnSignal(value)

    def visit_varstmt_stmt(self, varstmt: VarStmt) -> None:
        if varstmt.initializer is not None:
            value = self.evaluate(varstmt.initializer)
            self.environment.define(varstmt.name.lexeme, value=value)
        else:
            self.environment.define(varstmt.name.lexeme)

    def visit_functionstmt_stmt(self, functionstmt: FunctionStmt) -> None:
        func = self.function_class(functionstmt, self.environment)
        self.environment.define(functionstmt.name.lexeme, func)

    def visit_whilestmt_stmt(self, whilestmt: WhileStmt) -> None:
        try:
            while Interpreter.truthy(self.evaluate(whilestmt.condition)):
                self.execute(whilestmt.body)
        except BreakSignal:
            pass

    def execute(self, stmt: Stmt) -> None:
        return stmt.accept(self)
    
    def execute_block(self, statements: list[Stmt], environment: Environment):
        previous = self.environment
        try:
            self.environment = environment

            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous

    def resolve(self, expr: Expr, depth: int) -> None:
        self.locals[expr] = depth

    def lookup_variable(self, name: Token, expr: Expr) -> object:
        distance = self.locals.get(expr)
        return self.globals.get(name) if distance is None else self.environment.get_at(distance, name.lexeme)
    
    @staticmethod
    def truthy(obj: object) -> bool:
        if obj is None:
            return False
        if isinstance(obj, bool):
            return obj
        return True
    
    @staticmethod
    def check_number_operand(operator: Token, operand: object) -> None:
        if not isinstance(operand, float):
            raise RuntimeError(operator, 'Operand must be a number.')
        
    @staticmethod
    def check_number_operands(operator: Token, left: object, right: object) -> None:
        if not isinstance(left, float) or not isinstance(right, float):
            raise RuntimeError(operator, 'Operands must be numbers.')
        
    @staticmethod
    def stringify(obj: object) -> str:
        if obj is None:
            return 'nil'
        
        if isinstance(obj, float):
            text = str(obj)
            if text.endswith('.0'):
                text = text[:-2]
            return text
        
        if isinstance(obj, bool):
            if obj:
                return 'true'
            return 'false'
        
        if isinstance(obj, UninitializedValue):
            return ''
        
        return str(obj)
    