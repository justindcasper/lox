#include "chunk.h"
#include "debug.h"
#include "vm.h"

int main(int argc, char * argv[])
{
    VM vm;
    vm_init(&vm);

    Chunk chunk;
    chunk_init(&chunk);

    chunk_write_constant(&chunk, 1.2, 123);

    chunk_write_constant(&chunk, 3.4, 123);
    chunk_write(&chunk, OP_ADD, 123);
    chunk_write_constant(&chunk, 5.6, 123);
    chunk_write(&chunk, OP_DIVIDE, 123);

    chunk_write(&chunk, OP_NEGATE, 123);

    chunk_write(&chunk, OP_RETURN, 123);

    disassemble_chunk(&chunk, "test chunk");
    vm_interpret(&vm, &chunk);

    chunk_free(&chunk);
    vm_free(&vm);

    return 0;
}