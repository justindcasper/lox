from . import Expr, Visitor, Ternary, Binary, Grouping, Literal, Unary
from . import RuntimeError
from . import Token
from . import TokenType

class Interpreter(Visitor):
    def __init__(self, error_handler: callable):
        self.error_handler = error_handler

    def interpret(self, expression: Expr) -> None:
        try:
            value = self.evaluate(expression)
            print(Interpreter.stringify(value))
        except RuntimeError as e:
            self.error_handler(e)

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
            case _:
                # Unreachable
                return None
    
    def visit_grouping_expr(self, grouping: Grouping) -> object:
        return self.evaluate(grouping.expression)
    
    def visit_literal_expr(self, literal: Literal) -> object:
        return literal.value
    
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
    
    def evaluate(self, expr: Expr) -> object:
        return expr.accept(self)
    
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
        
        return str(obj)
    