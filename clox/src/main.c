#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sysexits.h>

#include "chunk.h"
#include "debug.h"
#include "vm.h"

static void repl();
static void run_file(const char * path);
static char * read_file(const char * path);

VM vm;

int main(int argc, char * argv[])
{
    vm_init(&vm);

    if(argc == 1) {
        repl();
    } else if(argc == 2) {
        run_file(argv[1]);
    } else {
        fprintf(stderr, "Usage: clox [path]\n");
        exit(EX_USAGE);
    }
    
    vm_free(&vm);
    return 0;
}

static void repl()
{
    char line[1024];
    while(true) {
        printf("> ");

        if(!fgets(line, sizeof(line), stdin)) {
            printf("\n");
            break;
        }

        vm_interpret(&vm, line);
    }
}

static void run_file(const char * path)
{
    char * source = read_file(path);
    if(source == NULL) {
        exit(EX_IOERR);
    }

    InterpretResult result = vm_interpret(&vm, source);
    free(source);

    if(result == INTERPRET_COMPILE_ERROR) {
        exit(EX_DATAERR);
    }
    if(result == INTERPRET_RUNTIME_ERROR) {
        exit(EX_SOFTWARE);
    }
}

static char * read_file(const char * path)
{
    FILE * file = fopen(path, "rb");
    if(file == NULL) {
        fprintf(stderr, "Could not open file '%s' (%s).\n", path, strerror(errno));
        return NULL;
    }

    fseek(file, 0, SEEK_END);
    size_t file_size = ftell(file);
    rewind(file);

    char * buffer = malloc(file_size + 1);
    if(buffer == NULL) {
        fprintf(stderr, "Not enough memory to read '%s' (%s).\n", path, strerror(errno));
        goto CLEANUP;
    }

    size_t bytes_read = fread(buffer, 1, file_size, file);
    if(bytes_read < file_size) {
        fprintf(stderr, "Failed to read file '%s' (%s).\n", path, strerror(errno));
        free(buffer);
        buffer = NULL;
        goto CLEANUP;
    }
    buffer[bytes_read] = '\0';
CLEANUP:
    fclose(file);
    return buffer;
}