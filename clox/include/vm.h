#ifndef CLOX_VM_H
#define CLOX_VM_H

#include "common.h"
#include "chunk.h"
#include "table.h"
#include "value.h"

#define STACK_MAX 256

typedef struct {
    Chunk * chunk;
    uint8_t * ip;
    Value stack[STACK_MAX];
    Value * stack_top;
    Table strings;
    Obj * objects;
} VM;

typedef enum {
    INTERPRET_OK,
    INTERPRET_COMPILE_ERROR,
    INTERPRET_RUNTIME_ERROR
} InterpretResult;

void vm_init(VM * vm);
void vm_free(VM * vm);
InterpretResult vm_interpret(VM * vm, const char * source);
void vm_push(VM * vm, Value value);
Value vm_pop(VM * vm);

#endif /* CLOX_VM_H*/