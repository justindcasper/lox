#include <ctype.h>
#include <string.h>

#include "scanner.h"

static bool at_end(Scanner * scanner);
static char advance(Scanner * scanner);
static char peek(Scanner * scanner);
static char peek_next(Scanner * scanner);
static bool match(Scanner * scanner, char expected);
static Token make_token(Scanner * scanner, TokenType type);
static Token error_token(Scanner * scanner, const char * message);
static void skip_whitespace(Scanner * scanner);
static void skip_block_comment(Scanner * scanner);
static Token string(Scanner * scanner);
static Token number(Scanner * scanner);
static Token identifier(Scanner * scanner);
static TokenType identifier_type(Scanner * scanner);
static TokenType check_keyword(Scanner * scanner, unsigned int start, unsigned int length,
    const char * rest, TokenType type);


void scanner_init(Scanner * scanner, const char * source)
{
    scanner->start = source;
    scanner->current = source;
    scanner->line = 1;
}

Token scan_token(Scanner * scanner)
{
    skip_whitespace(scanner);
    scanner->start = scanner->current;

    if(at_end(scanner)) {
        return make_token(scanner, TOKEN_EOF);
    }

    char c = advance(scanner);
    if(isalpha(c)) {
        return identifier(scanner);
    }
    if(isdigit(c)) {
        return number(scanner);
    }

    switch(c) {
        case '(':
            return make_token(scanner, TOKEN_LEFT_PAREN);
        case ')':
            return make_token(scanner, TOKEN_RIGHT_PAREN);
        case '{':
            return make_token(scanner, TOKEN_LEFT_BRACE);
        case '}':
            return make_token(scanner, TOKEN_RIGHT_BRACE);
        case ';':
            return make_token(scanner, TOKEN_SEMICOLON);
        case ',':
            return make_token(scanner, TOKEN_COMMA);
        case '.':
            return make_token(scanner, TOKEN_DOT);
        case '+':
            return make_token(scanner, TOKEN_PLUS);
        case '-':
            return make_token(scanner, TOKEN_MINUS);
        case '*':
            return make_token(scanner, TOKEN_STAR);
        case '/':
            return make_token(scanner, TOKEN_SLASH);
        case '!':
            return make_token(scanner, match(scanner, '=') ? TOKEN_BANG_EQUAL : TOKEN_BANG);
        case '=':
            return make_token(scanner, match(scanner, '=') ? TOKEN_EQUAL_EQUAL : TOKEN_EQUAL);
        case '<':
            return make_token(scanner, match(scanner, '=') ? TOKEN_LESS_EQUAL : TOKEN_LESS);
        case '>':
            return make_token(scanner, match(scanner, '=') ? TOKEN_GREATER_EQUAL : TOKEN_GREATER);
        case '"':
            return string(scanner);
        case '?':
            return make_token(scanner, TOKEN_QUESTION);
        case ':':
            return make_token(scanner, TOKEN_COLON);
    }

    return error_token(scanner, "Unexpected character.");
}

static bool at_end(Scanner * scanner)
{
    return *(scanner->current) == '\0';
}

static char advance(Scanner * scanner)
{
    scanner->current++;
    return scanner->current[-1];
}

static char peek(Scanner * scanner)
{
    return *scanner->current;
}

static char peek_next(Scanner * scanner)
{
    if(at_end(scanner)) {
        return '\0';
    }
    return scanner->current[1];
}

static bool match(Scanner * scanner, char expected)
{
    if(at_end(scanner)) {
        return false;
    }

    if(*scanner->current != expected) {
        return false;
    }

    scanner->current++;
    return true;
}

static Token make_token(Scanner * scanner, TokenType type)
{
    Token token;
    token.type = type;
    token.start = scanner->start;
    token.length = (unsigned int)(scanner->current - scanner->start);
    token.line = scanner->line;
    return token;
}

static Token error_token(Scanner * scanner, const char * message)
{
    Token token;
    token.type = TOKEN_ERROR;
    token.start = message;
    token.length = (unsigned int)strlen(message);
    token.line = scanner->line;
    return token;
}

static void skip_whitespace(Scanner * scanner)
{
    while(true) {
        char c = peek(scanner);
        switch(c) {
            case ' ':
            case '\r':
            case '\t':
                advance(scanner);
                break;
            case '\n':
                scanner->line++;
                advance(scanner);
                break;
            case '/':
                if(peek_next(scanner) == '/') {
                    // A comment goes to the end of the line
                    while(peek(scanner) != '\n' && !at_end(scanner)) {
                        advance(scanner);
                    }
                } else if(peek_next(scanner) == '*') {
                    skip_block_comment(scanner);
                } else {
                    return;
                }
                break;
            default:
                return;
        }
    }
}

static void skip_block_comment(Scanner * scanner)
{
    advance(scanner);
    advance(scanner);

    while(!(peek(scanner) == '*' && peek_next(scanner) == '/') && !at_end(scanner)) {
        if(peek(scanner) == '\n') {
            scanner->line++;
        }
        // Support nesting through recursion
        if(peek(scanner) == '/' && peek_next(scanner) == '*') {
            skip_block_comment(scanner);
        }

        advance(scanner);
    }

    if(!at_end(scanner)) {
        advance(scanner);
        advance(scanner);
    }
}

static Token string(Scanner * scanner)
{
    while(peek(scanner) != '"' && !at_end(scanner)) {
        if(peek(scanner) == '\n') {
            scanner->line++;
        }
        advance(scanner);
    }

    if(at_end(scanner)) {
        return error_token(scanner, "Unterminated string.");
    }

    advance(scanner);
    return make_token(scanner, TOKEN_STRING);
}

static Token number(Scanner * scanner)
{
    while(isdigit(peek(scanner))) {
        advance(scanner);
    }

    // Look for a fractional part
    if(peek(scanner) == '.' && isdigit(peek_next(scanner))) {
        // Consume the '.'
        advance(scanner);

        while(isdigit(peek(scanner))) {
            advance(scanner);
        }
    }

    return make_token(scanner, TOKEN_NUMBER);
}

static Token identifier(Scanner * scanner)
{
    while(isalpha(peek(scanner)) || isdigit(peek(scanner))) {
        advance(scanner);
    }

    return make_token(scanner, identifier_type(scanner));
}

static TokenType identifier_type(Scanner * scanner)
{
    switch(scanner->start[0]) {
        case 'a':
            return check_keyword(scanner, 1, 2, "nd", TOKEN_AND);
        case 'c':
            return check_keyword(scanner, 1, 4, "lass", TOKEN_CLASS);
        case 'e':
            return check_keyword(scanner, 1, 3, "lse", TOKEN_ELSE);
        case 'f':
            if(scanner->current - scanner->start > 1) {
                switch(scanner->start[1]) {
                    case 'a':
                        return check_keyword(scanner, 2, 3, "lse", TOKEN_FALSE);
                    case 'o':
                        return check_keyword(scanner, 2, 1, "r", TOKEN_FOR);
                    case 'u':
                        return check_keyword(scanner, 2, 1, "n", TOKEN_FUN);
                }
            }
            break;
        case 'i':
            return check_keyword(scanner, 1, 1, "f", TOKEN_IF);
        case 'n':
            return check_keyword(scanner, 1, 2, "il", TOKEN_NIL);
        case 'o':
            return check_keyword(scanner, 1, 1, "r", TOKEN_OR);
        case 'p':
            return check_keyword(scanner, 1, 4, "rint", TOKEN_PRINT);
        case 'r':
            return check_keyword(scanner, 1, 5, "eturn", TOKEN_RETURN);
        case 's':
            return check_keyword(scanner, 1, 4, "uper", TOKEN_SUPER);
        case 't':
            if(scanner->current - scanner->start > 1) {
                switch(scanner->start[1]) {
                    case 'h':
                        return check_keyword(scanner, 2, 2, "is", TOKEN_THIS);
                    case 'r':
                        return check_keyword(scanner, 2, 2, "ue", TOKEN_TRUE);
                }
            }
            break;
        case 'v':
            return check_keyword(scanner, 1, 2, "ar", TOKEN_VAR);
        case 'w':
            return check_keyword(scanner, 1, 4, "hile", TOKEN_WHILE);
    }

    return TOKEN_IDENTIFIER;
}

static TokenType check_keyword(Scanner * scanner, unsigned int start, unsigned int length,
    const char * rest, TokenType type)
{
    if(scanner->current - scanner->start == start + length &&
        memcmp(scanner->start + start, rest, length) == 0) {
        return type;
    }

    return TOKEN_IDENTIFIER;
}