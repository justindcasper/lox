#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#include "compiler.h"
#include "debug.h"
#include "memory.h"
#include "object.h"
#include "vm.h"

#define BINARY_OP(type, op) \
    do { \
        if(!IS_NUMBER(peek(vm, 0)) || !IS_NUMBER(peek(vm, 1))) { \
            runtime_error(vm, "Operands must be numbers."); \
        } \
        double b = AS_NUMBER(vm_pop(vm)); \
        double a = AS_NUMBER(vm_pop(vm)); \
        vm_push(vm, type(a op b)); \
    } while(false)


static InterpretResult run(VM * vm);
static void reset_stack(VM * vm);
static Value peek(VM * vm, int distance);
static void concatenate(VM * vm);
static void runtime_error(VM* vm, const char * format, ...);
static bool is_falsey(Value value);
static inline uint8_t read_byte(VM * vm);
static inline uint32_t read_long(VM * vm);
static inline Value read_constant(VM * vm);
static inline Value read_long_constant(VM * vm);


void vm_init(VM * vm)
{
    reset_stack(vm);
    vm->objects = NULL;
}

void vm_free(VM * vm)
{
    free_objects(vm);
}

InterpretResult vm_interpret(VM * vm, const char * source)
{
    InterpretResult result = INTERPRET_OK;
    Chunk chunk;
    chunk_init(&chunk);

    if(!compile(source, &chunk, vm)) {
        result = INTERPRET_COMPILE_ERROR;
        goto CLEANUP;
    }

    vm->chunk = &chunk;
    vm->ip = vm->chunk->code;

    result = run(vm);

CLEANUP:
    chunk_free(&chunk);
    return result;
}

void vm_push(VM * vm, Value value)
{
    *vm->stack_top = value;
    vm->stack_top++;
}

Value vm_pop(VM * vm)
{
    vm->stack_top--;
    return *vm->stack_top;
}

static InterpretResult run(VM * vm)
{
    while(true) {
#ifdef DEBUG_TRACE_EXECUTION
        printf("          ");
        for(Value * slot = vm->stack; slot < vm->stack_top; slot++) {
            printf("[ ");
            value_print(*slot);
            printf(" ]");
        }
        printf("\n");
        disassemble_instruction(vm->chunk, (unsigned int)(vm->ip - vm->chunk->code));
#endif /* DEBUG_TRACE_EXECUTION */

        uint8_t instruction = read_byte(vm);
        switch(instruction) {
            case OP_CONSTANT: {
                Value constant = read_constant(vm);
                vm_push(vm, constant);
                break;
            }
            case OP_CONSTANT_LONG: {
                Value constant = read_long_constant(vm);
                vm_push(vm, constant);
                break;
            }
            case OP_NIL:
                vm_push(vm, NIL_VAL);
                break;
            case OP_TRUE:
                vm_push(vm, BOOL_VAL(true));
                break;
            case OP_FALSE:
                vm_push(vm, BOOL_VAL(false));
                break;
            case OP_EQUAL: {
                Value b = vm_pop(vm);
                Value a = vm_pop(vm);
                vm_push(vm, BOOL_VAL(value_equality(a, b)));
                break;
            }
            case OP_GREATER:
                BINARY_OP(BOOL_VAL, >);
                break;
            case OP_LESS:
                BINARY_OP(BOOL_VAL, <);
                break;
            case OP_ADD: {
                if(IS_STRING(peek(vm, 0)) && IS_STRING(peek(vm, 1))) {
                    concatenate(vm);
                } else if(IS_NUMBER(peek(vm, 0)) && IS_NUMBER(peek(vm, 1))) {
                    double b = AS_NUMBER(vm_pop(vm));
                    double a = AS_NUMBER(vm_pop(vm));
                    vm_push(vm, NUMBER_VAL(a + b));
                } else {
                    runtime_error(vm, "Operands must be two numbers or two strings.");
                    return INTERPRET_RUNTIME_ERROR;
                }
                break;
            }
            case OP_SUBTRACT:
                BINARY_OP(NUMBER_VAL, -);
                break;
            case OP_MULTIPLY:
                BINARY_OP(NUMBER_VAL, *);
                break;
            case OP_DIVIDE:
                BINARY_OP(NUMBER_VAL, /);
                break;
            case OP_NEGATE:
                if (!IS_NUMBER(peek(vm, 0))) {
                    runtime_error(vm, "Operand must be a number.");
                    return INTERPRET_RUNTIME_ERROR;
                }
                AS_NUMBER(*(vm->stack_top - 1)) *= -1;
                break;
            case OP_NOT:
                vm_push(vm, BOOL_VAL(is_falsey(vm_pop(vm))));
                break;
            case OP_RETURN:
                value_print(vm_pop(vm));
                printf("\n");
                return INTERPRET_OK;
        }
    }
}

static void reset_stack(VM * vm)
{
    vm->stack_top = vm->stack;
}

static Value peek(VM * vm, int distance)
{
    return vm->stack_top[-1 - distance];
}

static void concatenate(VM * vm)
{
    ObjString * b = AS_STRING(vm_pop(vm));
    ObjString * a = AS_STRING(vm_pop(vm));

    size_t length = a->length + b->length;
    char * chars = ALLOCATE(char, length + 1);
    memcpy(chars, a->chars, a->length);
    memcpy(chars + a->length, b->chars, b->length);
    chars[length] = '\0';

    ObjString * result = object_take_string(chars, length, vm);
    vm_push(vm, OBJ_VAL((Obj *)result));
}

static void runtime_error(VM * vm, const char * format, ...)
{
    va_list args;
    va_start(args, format);
    vfprintf(stderr, format, args);
    va_end(args);
    fputs("\n", stderr);

    size_t instruction = vm->ip - vm->chunk->code - 1;
    uint32_t line = line_array_get_line((const LineArray *)&vm->chunk->lines, instruction);
    fprintf(stderr, "[line %d] in script\n", line);
    reset_stack(vm);
}

static bool is_falsey(Value value)
{
    return IS_NIL(value) || (IS_BOOL(value) && !AS_BOOL(value));
}

static inline uint8_t read_byte(VM * vm)
{
    return *vm->ip++;
}

static inline uint32_t read_long(VM * vm)
{
    return (uint32_t)(*vm->ip++ << 16) | (uint32_t)(*vm->ip++ << 8) | (uint32_t)*vm->ip++;
}

static inline Value read_constant(VM * vm)
{
    return vm->chunk->constants.values[read_byte(vm)];
}

static inline Value read_long_constant(VM * vm)
{
    return vm->chunk->constants.values[read_long(vm)];
}