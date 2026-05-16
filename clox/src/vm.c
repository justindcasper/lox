#include <stdio.h>

#include "debug.h"
#include "vm.h"

#define BINARY_OP(op) \
    do { \
        double b = vm_pop(vm); \
        double a = vm_pop(vm); \
        vm_push(vm, a op b); \
    } while(false);


static InterpretResult run(VM * vm);
static void reset_stack(VM * vm);
static inline uint8_t read_byte(VM * vm);
static inline uint32_t read_long(VM * vm);
static inline Value read_constant(VM * vm);
static inline Value read_long_constant(VM * vm);


void vm_init(VM * vm)
{
    reset_stack(vm);
}

void vm_free(VM * vm)
{

}

InterpretResult vm_interpret(VM * vm, Chunk * chunk)
{
    vm->chunk = chunk;
    vm->ip = vm->chunk->code;
    return run(vm);
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
            case OP_ADD:
                BINARY_OP(+);
                break;
            case OP_SUBTRACT:
                BINARY_OP(-);
                break;
            case OP_MULTIPLY:
                BINARY_OP(*);
                break;
            case OP_DIVIDE:
                BINARY_OP(/);
                break;
            case OP_NEGATE:
                *(vm->stack_top - 1) *= -1;
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