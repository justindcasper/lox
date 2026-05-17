#include <stdio.h>

#include "compiler.h"
#include "scanner.h"

Scanner scanner;

void compile(const char * source)
{
    scanner_init(&scanner, source);
    unsigned int line = 0;
    while(true) {
        Token token = scan_token(&scanner);
        if(token.line != line) {
            printf("%4u ", token.line);
            line = token.line;
        } else {
            printf("   | ");
        }
        printf("%2d '%.*s'\n", token.type, token.length, token.start);

        if(token.type == TOKEN_EOF) {
            break;
        }
    }
}