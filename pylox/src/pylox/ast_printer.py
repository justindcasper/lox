import typing

from . import Expr, Visitor, Ternary, Binary, Grouping, Literal, Unary
from . import Token, TokenType

class AstPrinter(Visitor):
    def print(self, expr: Expr) -> str:
        return expr.accept(self)
    
    def visit_ternary_expr(self, ternary: Ternary) -> str:
        return self.parenthesize(ternary.question.lexeme + ternary.colon.lexeme,
                                 (ternary.condition, ternary.then_expr, ternary.else_expr))
    
    def visit_binary_expr(self, binary: Binary) -> str:
        return self.parenthesize(binary.operator.lexeme, (binary.left, binary.right))
    
    def visit_grouping_expr(self, grouping: Grouping) -> str:
        return self.parenthesize('group', (grouping.expression,))
    
    def visit_literal_expr(self, literal: Literal) -> str:
        if literal.value is None:
            return 'nil'
        return str(literal.value)
    
    def visit_unary_expr(self, unary: Unary) -> str:
        return self.parenthesize(unary.operator.lexeme, (unary.right,))
    
    def parenthesize(self, name: str, exprs: typing.Iterable[Expr]) -> str:
        return f'({name} ' + ' '.join([expr.accept(self) if expr else '' for expr in exprs]) + ')'
    
    
def test():
    expr: Expr = Binary(
        Unary(
            Token(TokenType.MINUS, '-', None, 1),
            Literal(123)
        ),
        Token(TokenType.STAR, '*', None, 1),
        Grouping(
            Literal(45.67)
        )
    )

    print(AstPrinter().print(expr))