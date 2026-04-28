from . import TokenType
from . import Token

class Scanner:
    keywords: dict[str, TokenType] = {
        "and": TokenType.AND,
        "class": TokenType.CLASS,
        "else": TokenType.ELSE,
        "false": TokenType.FALSE,
        "for": TokenType.FOR,
        "fun": TokenType.FUN,
        "if": TokenType.IF,
        "nil": TokenType.NIL,
        "or": TokenType.OR,
        "print": TokenType.PRINT,
        "return": TokenType.RETURN,
        "super": TokenType.SUPER,
        "this": TokenType.THIS,
        "true": TokenType.TRUE,
        "var": TokenType.VAR,
        "while": TokenType.WHILE
    }

    def __init__(self, source: str, error_handler: callable):
        self.source = source
        self.tokens: list[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.error_handler = error_handler

    def scan_tokens(self) -> list[Token]:
        while not self.at_end():
            # We are at the beginning of the next lexeme
            self.start = self.current
            self.scan_token()

        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens
    
    def scan_token(self) -> None:
        c: str = self.advance()
        match c:
            case '(':
                self.add_token(TokenType.LEFT_PAREN)
            case ')':
                self.add_token(TokenType.RIGHT_PAREN)
            case '{':
                self.add_token(TokenType.LEFT_BRACE)
            case '}':
                self.add_token(TokenType.RIGHT_BRACE)
            case ',':
                self.add_token(TokenType.COMMA)
            case '.':
                self.add_token(TokenType.DOT)
            case '-':
                self.add_token(TokenType.MINUS)
            case '+':
                self.add_token(TokenType.PLUS)
            case ';':
                self.add_token(TokenType.SEMICOLON)
            case ':':
                self.add_token(TokenType.COLON)
            case '*':
                self.add_token(TokenType.STAR)
            case '?':
                self.add_token(TokenType.QUESTION)
            case '!':
                self.add_token(TokenType.BANG_EQUAL if self.match('=') else TokenType.BANG)
            case '=':
                self.add_token(TokenType.EQUAL_EQUAL if self.match('=') else TokenType.EQUAL)
            case '<':
                self.add_token(TokenType.LESS_EQUAL if self.match('=') else TokenType.LESS)
            case '>':
                self.add_token(TokenType.GREATER_EQUAL if self.match('=') else TokenType.GREATER)
            case '/':
                if self.match('/'):
                    # A comment goes to the end of the line
                    while self.peek() != '\n' and not self.at_end():
                        self.advance()
                elif self.match('*'):
                    self.handle_block_comment()
                else:
                    self.add_token(TokenType.SLASH)
            # Ignore whitespace
            case ' ' | '\t' | '\r':
                pass
            case '\n':
                self.line += 1
            case '"':
                self.handle_string()
            case _:
                if c.isdigit():
                    self.handle_number()
                elif c.isalpha():
                    self.handle_identifier()
                else:
                    self.error_handler(self.line, "Unexpected character")

    def handle_identifier(self) -> None:
        while self.peek().isalnum():
            self.advance()

        text = self.source[self.start:self.current]
        type = Scanner.keywords.get(text, TokenType.IDENTIFIER)
        self.add_token(type)

    def handle_number(self) -> None:
        while self.peek().isdigit():
            self.advance()
        
        # Look for a fractional part
        if self.peek() == '.'and self.peek_next().isdigit():
            # Consume the .
            self.advance()

            while self.peek().isdigit():
                self.advance()

        self.add_token(TokenType.NUMBER, literal=float(self.source[self.start:self.current]))

    def handle_string(self) -> None:
        while self.peek() != '"' and not self.at_end():
            if self.peek() == '\n':
                self.line += 1
            self.advance()

        if self.at_end():
            self.error_handler(self.line, "Unterminated string")
            return
        
        # The closing "
        self.advance()

        # Trim the surrounding quotes
        value = self.source[self.start + 1:self.current - 1]
        self.add_token(TokenType.STRING, literal=value)

    def handle_block_comment(self) -> None:
        while not (self.peek() == '*' and self.peek_next() == '/') and not self.at_end():
            if self.peek() == '\n':
                self.line += 1
            # Support nesting through recursion
            if self.match('/') and self.match('*'):
                self.handle_block_comment()
            self.advance()

        if self.at_end():
            # Not worth erroring for this?
            return
        
        # The close of the block comment
        self.advance()
        self.advance()

    def match(self, expected: str) -> bool:
        if self.at_end():
            return False
        if self.source[self.current] != expected:
            return False
        
        self.current += 1
        return True
    
    def peek(self) -> str:
        if self.at_end():
            return '\0'
        return self.source[self.current]
    
    def peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def at_end(self) -> bool:
        return self.current >= len(self.source)
    
    def advance(self) -> str:
        c = self.source[self.current]
        self.current += 1
        return c
    
    def add_token(self, type: TokenType, literal: object = None) -> None:
        text = self.source[self.start:self.current]
        self.tokens.append(Token(type, text, literal, self.line))
    