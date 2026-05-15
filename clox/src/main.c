#include "chunk.h"
#include "debug.h"

int main(int argc, char * argv[])
{
    Chunk chunk;
    chunk_init(&chunk);

    chunk_write_constant(&chunk, 1.2, 123);

    chunk_write(&chunk, OP_RETURN, 123);

    disassemble_chunk(&chunk, "test chunk");
    chunk_free(&chunk);
    return 0;
}