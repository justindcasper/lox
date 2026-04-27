import typing

from . import Expr, Binary, Unary, Literal, Grouping
from . import Token
from . import TokenType

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens: list[Token], error_handler: callable):
        self.tokens = tokens
        self.current: int = 0
        self.error_handler = error_handler

    def parse(self) -> Expr:
        try:
            return self.expression()
        except ParseError:
            return None

    def expression(self) -> Expr:
        return self.equality()
    
    def equality(self) -> Expr:
        expr = self.comparison()

        while self.match((TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL)):
            operator = self.previous()
            right = self.comparison()
            expr = Binary(expr, operator, right)

        return expr

    def comparison(self) -> Expr:
        expr = self.term()

        while self.match((TokenType.LESS, TokenType.LESS_EQUAL, TokenType.GREATER, TokenType.GREATER_EQUAL)):
            operator = self.previous()
            right = self.term()
            expr = Binary(expr, operator, right)

        return expr

    def term(self) -> Expr:
        expr = self.factor()

        while self.match((TokenType.PLUS, TokenType.MINUS)):
            operator = self.previous()
            right = self.factor()
            expr = Binary(expr, operator, right)

        return expr

    def factor(self) -> Expr:
        expr = self.unary()

        while self.match((TokenType.SLASH, TokenType.STAR)):
            operator = self.previous()
            right = self.unary()
            expr = Binary(expr, operator, right)

        return expr

    def unary(self) -> Expr:
        if self.match((TokenType.BANG, TokenType.MINUS)):
            return Unary(self.previous(), self.unary())
        
        return self.primary()

    def primary(self) -> Expr:
        if self.match((TokenType.NUMBER, TokenType.STRING)):
            return Literal(self.previous().literal)
        
        if self.match((TokenType.FALSE,)):
            return Literal(False)
        if self.match((TokenType.TRUE,)):
            return Literal(True)
        if self.match((TokenType.NIL,)):
            return Literal(None)
        
        if self.match((TokenType.LEFT_PAREN,)):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)
        
        raise self.error(self.peek(), "Expect expression.")

    def match(self, types: typing.Iterable[TokenType]) -> bool:
        for type in types:
            if self.check(type):
                self.advance()
                return True
            
        return False
    
    def consume(self, type: TokenType, message: str) -> Token:
        if self.check(type):
            return self.advance()
        
        raise self.error(self.peek(), message)

    def check(self, type: TokenType) -> bool:
        if self.at_end():
            return False
        return self.peek().type == type

    def advance(self) -> Token:
        if not self.at_end():
            self.current += 1
        return self.previous()

    def at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]
    
    def error(self, token: Token, message: str) -> ParseError:
        self.error_handler(token, message)
        return ParseError(message)
    
    def synchronize(self) -> None:
        self.advance()

        while not self.at_end():
            if self.previous().type == TokenType.SEMICOLON:
                return
            
            t = self.peek().type
            match t:
                case TokenType.CLASS | TokenType.FUN | TokenType.VAR | TokenType.IF | TokenType.FOR | \
                    TokenType.WHILE | TokenType.PRINT | TokenType.RETURN:
                    return
                
            self.advance()
