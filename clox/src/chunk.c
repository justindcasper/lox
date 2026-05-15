#include <stdlib.h>

#include "chunk.h"
#include "memory.h"

void chunk_init(Chunk * chunk)
{
    chunk->count = 0;
    chunk->capacity = 0;
    chunk->code = NULL;
    line_array_init(&chunk->lines);
    value_array_init(&chunk->constants);
}

void chunk_write(Chunk * chunk, uint8_t byte, uint32_t line)
{
    if(chunk->capacity < chunk->count + 1) {
        unsigned int old_capacity = chunk->capacity;
        chunk->capacity = GROW_CAPACITY(old_capacity);
        chunk->code = GROW_ARRAY(uint8_t, chunk->code, old_capacity, chunk->capacity);
    }

    chunk->code[chunk->count] = byte;
    line_array_write(&chunk->lines, line);
    chunk->count++;
}

unsigned int chunk_add_constant(Chunk * chunk, Value value)
{
    value_array_write(&chunk->constants, value);
    return chunk->constants.count - 1;
}

void chunk_free(Chunk * chunk)
{
    FREE_ARRAY(uint8_t, chunk->code, chunk->capacity);
    line_array_free(&chunk->lines);
    value_array_free(&chunk->constants);
    chunk_init(chunk);
}
