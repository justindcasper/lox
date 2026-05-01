import typing

from . import Expr, Assign, Ternary, Binary, Unary, Literal, Grouping, Variable
from . import Stmt, Block, ExpressionStmt, PrintStmt, VarStmt
from . import Token
from . import TokenType

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens: list[Token], error_handler: callable):
        self.tokens = tokens
        self.current: int = 0
        self.error_handler = error_handler

    def parse(self) -> list[Stmt]:
        statements = []
        while not self.at_end():
            statements.append(self.declaration())
        
        return statements
    
    def declaration(self) -> Stmt:
        try:
            if self.match((TokenType.VAR,)):
                return self.var_declaration()
            
            return self.statement()
        except ParseError:
            self.synchronize()
            return None
    
    def statement(self) -> Stmt:
        if self.match((TokenType.PRINT,)):
            return self.print_statement()
        if self.match((TokenType.LEFT_BRACE,)):
            return Block(self.block())
        
        return self.expression_statement()
    
    def block(self) -> Stmt:
        statements: list[Stmt] = []

        while not self.check(TokenType.RIGHT_BRACE) and not self.at_end():
            statements.append(self.declaration())

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements
    
    def expression_statement(self) -> Stmt:
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return ExpressionStmt(expr)
    
    def print_statement(self) -> Stmt:
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return PrintStmt(expr)
    
    def var_declaration(self) -> Stmt:
        name = self.consume(TokenType.IDENTIFIER, "Expect variable name.")

        initializer = None
        if self.match((TokenType.EQUAL,)):
            initializer = self.expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        return VarStmt(name, initializer)

    def expression(self) -> Expr:
        return self.assignment()
    
    def assignment(self) -> Expr:
        expr = self.comma_expression()

        if self.match((TokenType.EQUAL,)):
            equals = self.previous()
            value = self.assignment()

            if isinstance(expr, Variable):
                name = expr.name
                return Assign(name, value)
            
            self.error(equals, "Invalid assignment target.")

        return expr
    
    def comma_expression(self) -> Expr:
        operator_types = (TokenType.COMMA,)
        token = self.peek()
        if token.type in operator_types:
            self.error(token, f"Need expression before '{token.lexeme}'.")
            self.advance()
            self.comma_expression()
            return None
            
        expr = self.ternary()

        while self.match(operator_types):
            operator = self.previous()
            right = self.ternary()
            expr = Binary(expr, operator, right)

        return expr
    
    def ternary(self) -> Expr:
        expr = self.equality()

        if self.match((TokenType.QUESTION,)):
            question = self.previous()
            then_case = self.ternary()
            self.consume(TokenType.COLON, "Expect ':' in ternary expression.")
            colon = self.previous()
            else_case = self.ternary()
            expr = Ternary(expr, question, then_case, colon, else_case)

        return expr
    
    def equality(self) -> Expr:
        operator_types = (TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL)
        token = self.peek()
        if token.type in operator_types:
            self.error(token, f"Need expression before '{token.lexeme}'.")
            self.advance()
            self.equality()
            return None
        
        expr = self.comparison()

        while self.match(operator_types):
            operator = self.previous()
            right = self.comparison()
            expr = Binary(expr, operator, right)

        return expr

    def comparison(self) -> Expr:
        operator_types = (TokenType.LESS, TokenType.LESS_EQUAL, TokenType.GREATER, TokenType.GREATER_EQUAL)
        token = self.peek()
        if token.type in operator_types:
            self.error(token, f"Need expression before '{token.lexeme}'.")
            self.advance()
            self.comparison()
            return None
        
        expr = self.term()

        while self.match(operator_types):
            operator = self.previous()
            right = self.term()
            expr = Binary(expr, operator, right)

        return expr

    def term(self) -> Expr:
        operator_types = (TokenType.PLUS, TokenType.MINUS)
        token = self.peek()
        if token.type == TokenType.PLUS:
            self.error(token, f"Need expression before '{token.lexeme}'.")
            self.advance()
            self.term()
            return None
        
        expr = self.factor()

        while self.match(operator_types):
            operator = self.previous()
            right = self.factor()
            expr = Binary(expr, operator, right)

        return expr

    def factor(self) -> Expr:
        operator_types = (TokenType.SLASH, TokenType.STAR)
        token = self.peek()
        if token.type in operator_types:
            self.error(token, f"Need expression before '{token.lexeme}'.")
            self.advance()
            self.factor()
            return None
        
        expr = self.unary()

        while self.match(operator_types):
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
        
        if self.match((TokenType.IDENTIFIER,)):
            return Variable(self.previous())
        
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
