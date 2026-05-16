#ifndef CLOX_CHUNK_H
#define CLOX_CHUNK_H

#include "common.h"
#include "line.h"
#include "value.h"

typedef enum {
    OP_CONSTANT,
    OP_CONSTANT_LONG,
    OP_ADD,
    OP_SUBTRACT,
    OP_MULTIPLY,
    OP_DIVIDE,
    OP_NEGATE,
    OP_RETURN
} OpCode;

typedef struct {
    unsigned int count;
    unsigned int capacity;
    uint8_t * code;
    LineArray lines;
    ValueArray constants;
} Chunk;

void chunk_init(Chunk * chunk);
void chunk_write(Chunk * chunk, uint8_t byte, uint32_t line);
unsigned int chunk_add_constant(Chunk * chunk, Value value);
void chunk_write_constant(Chunk * chunk, Value value, uint32_t line);
void chunk_free(Chunk * chunk);

#endif /* CLOX_CHUNK_H */