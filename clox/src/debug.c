#include <stdio.h>

#include "debug.h"
#include "value.h"

static unsigned int simple_instruction(const char * name, unsigned int offset);
static unsigned int constant_instruction(const char * name, Chunk * chunk, unsigned int offset);


void disassemble_chunk(Chunk * chunk, const char * name)
{
    printf("== %s ==\n", name);

    for(int offset = 0; offset < chunk->count;) {
        offset = disassemble_instruction(chunk, offset);
    }
}

unsigned int disassemble_instruction(Chunk * chunk, unsigned int offset)
{
    printf("%04u ", offset);
    if(offset > 0 && chunk->lines[offset] == chunk->lines[offset - 1]) {
        printf("   | ");
    } else {
        printf("%4u ", chunk->lines[offset]);
    }

    uint8_t instruction = chunk->code[offset];
    switch(instruction) {
        case OP_CONSTANT:
            return constant_instruction("OP_CONSTANT", chunk, offset);
        case OP_RETURN:
            return simple_instruction("OP_RETURN", offset);
        default:
            printf("Unknown opcode %u\n", instruction);
            return offset + 1;
    }
}


static unsigned int simple_instruction(const char * name, unsigned int offset)
{
    printf("%s\n", name);
    return offset + 1;
}

static unsigned int constant_instruction(const char * name, Chunk * chunk, unsigned int offset)
{
    uint8_t constant = chunk->code[offset + 1];
    printf("%-16s %4u '", name, constant);
    value_print(chunk->constants.values[constant]);
    printf("'\n");
    return offset + 2;
}
