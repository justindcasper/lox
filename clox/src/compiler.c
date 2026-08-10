#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>

#include "compiler.h"
#include "object.h"
#include "scanner.h"

#ifdef DEBUG_PRINT_CODE
 #include "debug.h"
#endif /* DEBUG_PRINT_CODE */

typedef struct {
    Token current;
    Token previous;
    bool had_error;
    bool panic_mode;
    VM * vm;
} Parser;

typedef enum {
  PREC_NONE,
  PREC_ASSIGNMENT,  // =
  PREC_TERNARY,     // ?:
  PREC_OR,          // or
  PREC_AND,         // and
  PREC_EQUALITY,    // == !=
  PREC_COMPARISON,  // < > <= >=
  PREC_TERM,        // + -
  PREC_FACTOR,      // * /
  PREC_UNARY,       // ! -
  PREC_CALL,        // . ()
  PREC_PRIMARY
} Precedence;

typedef void (*ParseFn)(bool can_assign);

typedef struct {
    ParseFn prefix;
    ParseFn infix;
    Precedence precedence;
} ParseRule;


Scanner scanner;
Parser parser;
Chunk * compiling_chunk;

static Chunk * current_chunk();
static void declaration();
static void var_declaration();
static void statement();
static void print_statement();
static void expression_statement();
static void expression();
static void grouping(bool can_assign);
static void ternary(bool can_assign);
static void binary(bool can_assign);
static void unary(bool can_assign);
static void number(bool can_assign);
static void literal(bool can_assign);
static void string(bool can_assign);
static void variable(bool can_assign);
static void named_variable(Token name, bool can_assign);
static void parse_precedence(Precedence precedence);
static uint32_t parse_variable(const char * error_msg);
static void define_variable(uint32_t global);
static ParseRule * get_rule(TokenType type);
static void advance();
static void consume(TokenType type, const char * message);
static bool check(TokenType type);
static bool match(TokenType type);
static void emit_byte(uint8_t byte);
static void emit_bytes(size_t count, ...);
static void emit_return();
static void emit_constant(Value value);
static void emit_indexed_instruction(uint8_t short_op, uint8_t long_op, uint32_t constant);
static uint32_t make_constant(Value value);
static uint32_t identifier_constant(Token * name);
static void end_compiler();
static void synchronize();
static void error(const char * message);
static void error_at_current(const char * message);
static void error_at(Token * token, const char * message);


ParseRule rules[] = {
    [TOKEN_LEFT_PAREN]    = {grouping, NULL,    PREC_NONE},
    [TOKEN_RIGHT_PAREN]   = {NULL,     NULL,    PREC_NONE},
    [TOKEN_LEFT_BRACE]    = {NULL,     NULL,    PREC_NONE}, 
    [TOKEN_RIGHT_BRACE]   = {NULL,     NULL,    PREC_NONE},
    [TOKEN_COMMA]         = {NULL,     NULL,    PREC_NONE},
    [TOKEN_DOT]           = {NULL,     NULL,    PREC_NONE},
    [TOKEN_MINUS]         = {unary,    binary,  PREC_TERM},
    [TOKEN_PLUS]          = {NULL,     binary,  PREC_TERM},
    [TOKEN_SEMICOLON]     = {NULL,     NULL,    PREC_NONE},
    [TOKEN_SLASH]         = {NULL,     binary,  PREC_FACTOR},
    [TOKEN_STAR]          = {NULL,     binary,  PREC_FACTOR},
    [TOKEN_QUESTION]      = {NULL,     ternary, PREC_TERNARY},
    [TOKEN_COLON]         = {NULL,     NULL,    PREC_NONE},
    [TOKEN_BANG]          = {unary,    NULL,    PREC_NONE},
    [TOKEN_BANG_EQUAL]    = {NULL,     binary,  PREC_EQUALITY},
    [TOKEN_EQUAL]         = {NULL,     NULL,    PREC_NONE},
    [TOKEN_EQUAL_EQUAL]   = {NULL,     binary,  PREC_EQUALITY},
    [TOKEN_GREATER]       = {NULL,     binary,  PREC_COMPARISON},
    [TOKEN_GREATER_EQUAL] = {NULL,     binary,  PREC_COMPARISON},
    [TOKEN_LESS]          = {NULL,     binary,  PREC_COMPARISON},
    [TOKEN_LESS_EQUAL]    = {NULL,     binary,  PREC_COMPARISON},
    [TOKEN_IDENTIFIER]    = {variable, NULL,    PREC_NONE},
    [TOKEN_STRING]        = {string,   NULL,    PREC_NONE},
    [TOKEN_NUMBER]        = {number,   NULL,    PREC_NONE},
    [TOKEN_AND]           = {NULL,     NULL,    PREC_NONE},
    [TOKEN_CLASS]         = {NULL,     NULL,    PREC_NONE},
    [TOKEN_ELSE]          = {NULL,     NULL,    PREC_NONE},
    [TOKEN_FALSE]         = {literal,  NULL,    PREC_NONE},
    [TOKEN_FOR]           = {NULL,     NULL,    PREC_NONE},
    [TOKEN_FUN]           = {NULL,     NULL,    PREC_NONE},
    [TOKEN_IF]            = {NULL,     NULL,    PREC_NONE},
    [TOKEN_NIL]           = {literal,  NULL,    PREC_NONE},
    [TOKEN_OR]            = {NULL,     NULL,    PREC_NONE},
    [TOKEN_PRINT]         = {NULL,     NULL,    PREC_NONE},
    [TOKEN_RETURN]        = {NULL,     NULL,    PREC_NONE},
    [TOKEN_SUPER]         = {NULL,     NULL,    PREC_NONE},
    [TOKEN_THIS]          = {NULL,     NULL,    PREC_NONE},
    [TOKEN_TRUE]          = {literal,  NULL,    PREC_NONE},
    [TOKEN_VAR]           = {NULL,     NULL,    PREC_NONE},
    [TOKEN_WHILE]         = {NULL,     NULL,    PREC_NONE},
    [TOKEN_ERROR]         = {NULL,     NULL,    PREC_NONE},
    [TOKEN_EOF]           = {NULL,     NULL,    PREC_NONE},
};


bool compile(const char * source, Chunk * chunk, VM * vm)
{
    scanner_init(&scanner, source);
    compiling_chunk = chunk;

    parser.had_error = false;
    parser.panic_mode = false;
    parser.vm = vm;

    advance();
    
    while(!match(TOKEN_EOF)) {
        declaration();
    }

    end_compiler();
    return !parser.had_error;
}

static Chunk * current_chunk()
{
    return compiling_chunk;
}

static void declaration()
{
    if(match(TOKEN_VAR)) {
        var_declaration();
    }
    else {
        statement();
    }

    if(parser.panic_mode) {
        synchronize();
    }
}

static void var_declaration()
{
    uint32_t global = parse_variable("Expect variable name.");

    if(match(TOKEN_EQUAL)) {
        expression();
    } else {
        emit_byte(OP_NIL);
    }

    consume(TOKEN_SEMICOLON, "Expect ';' after variable declaration.");
    define_variable(global);
}

static void statement()
{
    if(match(TOKEN_PRINT)) {
        print_statement();
    } else {
        expression_statement();
    }
}

static void print_statement()
{
    expression();
    consume(TOKEN_SEMICOLON, "Expect ';' after value.");
    emit_byte(OP_PRINT);
}

static void expression_statement()
{
    expression();
    consume(TOKEN_SEMICOLON, "Expect ';' after expression.");
    emit_byte(OP_POP);
}

static void expression()
{
    parse_precedence(PREC_ASSIGNMENT);
}

static void grouping(bool can_assign)
{
    expression();
    consume(TOKEN_RIGHT_PAREN, "Expect ')' after expression.");
}

static void ternary(bool can_assign)
{
    expression();
    consume(TOKEN_COLON, "Expect ':' after then branch of conditional expression.");
    parse_precedence(PREC_TERNARY);
}

static void binary(bool can_assign)
{
    TokenType operator_type = parser.previous.type;
    ParseRule * rule = get_rule(operator_type);
    parse_precedence(rule->precedence + 1);

    switch(operator_type) {
        case TOKEN_BANG_EQUAL:
            emit_bytes(2, OP_EQUAL, OP_NOT);
            break;
        case TOKEN_EQUAL_EQUAL:
            emit_byte(OP_EQUAL);
            break;
        case TOKEN_GREATER:
            emit_byte(OP_GREATER);
            break;
        case TOKEN_GREATER_EQUAL:
            emit_bytes(2, OP_LESS, OP_NOT);
            break;
        case TOKEN_LESS:
            emit_byte(OP_LESS);
            break;
        case TOKEN_LESS_EQUAL:
            emit_bytes(2, OP_GREATER, OP_NOT);
            break;
        case TOKEN_PLUS:
            emit_byte(OP_ADD);
            break;
        case TOKEN_MINUS:
            emit_byte(OP_SUBTRACT);
            break;
        case TOKEN_STAR:
            emit_byte(OP_MULTIPLY);
            break;
        case TOKEN_SLASH:
            emit_byte(OP_DIVIDE);
            break;
        default:
            return; // Unreachable
    }
}

static void unary(bool can_assign)
{
    TokenType operator_type = parser.previous.type;

    // Compile the operand
    parse_precedence(PREC_UNARY);

    // Emit the operator expression
    switch(operator_type) {
        case TOKEN_MINUS:
            emit_byte(OP_NEGATE);
            break;
        case TOKEN_BANG:
            emit_byte(OP_NOT);
            break;
        default:
            return; // Unreachable
    }
}

static void number(bool can_assign)
{
    double value = strtod(parser.previous.start, NULL);
    emit_constant(NUMBER_VAL(value));
}

static void literal(bool can_assign)
{
    switch(parser.previous.type) {
        case TOKEN_NIL:
            emit_byte(OP_NIL);
            break;
        case TOKEN_TRUE:
            emit_byte(OP_TRUE);
            break;
        case TOKEN_FALSE:
            emit_byte(OP_FALSE);
            break;
        default:
            return; // Unreachable
    }
}

static void string(bool can_assign)
{
    // Remove quotes in object_copy_string
    emit_constant(OBJ_VAL((Obj *)object_copy_string(parser.previous.start + 1, parser.previous.length - 2,
        parser.vm)));
}

static void variable(bool can_assign)
{
    named_variable(parser.previous, can_assign);
}

static void named_variable(Token name, bool can_assign)
{
    uint32_t arg = identifier_constant(&name);

    if(can_assign && match(TOKEN_EQUAL)) {
        expression();
        emit_indexed_instruction(OP_SET_GLOBAL, OP_SET_GLOBAL_LONG, arg);
    } else {
        emit_indexed_instruction(OP_GET_GLOBAL, OP_GET_GLOBAL_LONG, arg);
    }
}

static void parse_precedence(Precedence precedence)
{
    advance();
    ParseFn prefix_rule = get_rule(parser.previous.type)->prefix;
    if(prefix_rule == NULL) {
        error("Expect expression.");
        return;
    }

    bool can_assign = precedence <= PREC_ASSIGNMENT;
    prefix_rule(can_assign);

    while(precedence <= get_rule(parser.current.type)->precedence) {
        advance();
        ParseFn infix_rule = get_rule(parser.previous.type)->infix;
        // Will never be NULL if rules[] has PREC_NONE for all non-infix Tokens
        infix_rule(can_assign);
    }

    if(can_assign && match(TOKEN_EQUAL)) {
        error("Invalid assignment target.");
    }
}

static uint32_t parse_variable(const char * error_msg)
{
    consume(TOKEN_IDENTIFIER, error_msg);
    return identifier_constant(&parser.previous);
}

static void define_variable(uint32_t global)
{
    emit_indexed_instruction(OP_DEFINE_GLOBAL, OP_DEFINE_GLOBAL_LONG, global);
}

static ParseRule * get_rule(TokenType type)
{
    return &rules[type];
}

static void advance()
{
    parser.previous = parser.current;

    while(true) {
        parser.current = scan_token(&scanner);
        if(parser.current.type != TOKEN_ERROR) {
            break;
        }

        error_at_current(parser.current.start);
    }
}

static void consume(TokenType type, const char * message)
{
    if(parser.current.type == type) {
        advance();
        return;
    }

    error_at_current(message);
}

static bool check(TokenType type)
{
    return parser.current.type == type;
}

static bool match(TokenType type)
{
    if(!check(type)) {
        return false;
    }

    advance();
    return true;
}

static void emit_byte(uint8_t byte)
{
    chunk_write(current_chunk(), byte, parser.previous.line);
}

static void emit_bytes(size_t count, ...)
{
    va_list args;

    va_start(args, count);
    for(size_t i = 0; i < count; i++) {
        emit_byte((uint8_t)va_arg(args, int));
    }
    va_end(args);
}

static void emit_return()
{
    emit_byte(OP_RETURN);
}

static void emit_constant(Value value)
{
    uint32_t constant = make_constant(value);
    emit_indexed_instruction(OP_CONSTANT, OP_CONSTANT_LONG, constant);
}

static void emit_indexed_instruction(uint8_t short_op, uint8_t long_op, uint32_t constant)
{
    if(constant > (UINT32_MAX >> 8)) {
        error("Too many constants in one chunk.");
        return;
    }

    if(constant > UINT8_MAX) {
        emit_bytes(4, long_op, (constant >> 16) & 0xff, (constant >> 8) & 0xff, constant & 0xff);
    } else {
        emit_bytes(2, short_op, constant);
    }
}

static uint32_t make_constant(Value value)
{
    unsigned int constant = chunk_add_constant(current_chunk(), value);
    return (uint32_t)constant;
}

static uint32_t identifier_constant(Token * name)
{
    return make_constant(OBJ_VAL((Obj *)object_copy_string(name->start, name->length, parser.vm)));
}

static void end_compiler()
{
    emit_return();
#ifdef DEBUG_PRINT_CODE
    if(!parser.had_error) {
        disassemble_chunk(current_chunk(), "code");
    }
#endif /* DEBUG_PRINT_CODE */
}

static void synchronize()
{
    parser.panic_mode = false;

    while(parser.current.type != TOKEN_EOF) {
        if(parser.previous.type == TOKEN_SEMICOLON) {
            return;
        }

        switch(parser.current.type) {
            case TOKEN_CLASS:
            case TOKEN_FUN:
            case TOKEN_VAR:
            case TOKEN_FOR:
            case TOKEN_WHILE:
            case TOKEN_IF:
            case TOKEN_PRINT:
            case TOKEN_RETURN:
                return;
            default:
                ; // Do nothing
        }

        advance();
    }
}

static void error(const char * message)
{
    error_at(&parser.previous, message);
}

static void error_at_current(const char * message)
{
    error_at(&parser.current, message);
}

static void error_at(Token * token, const char * message)
{
    if(parser.panic_mode) {
        return;
    }
    parser.panic_mode = true;
    fprintf(stderr, "[line %u] Error", token->line);

    if(token->type == TOKEN_EOF) {
        fprintf(stderr, " at end");
    } else if(token->type == TOKEN_ERROR) {
        // Nothing
    } else {
        fprintf(stderr, " at '%.*s'", token->length, token->start);
    }

    fprintf(stderr, ": %s\n", message);
    parser.had_error = true;
}