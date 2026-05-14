#ifndef CLOX_DEBUG_H
#define CLOX_DEBUG_H

#include "chunk.h"

void disassemble_chunk(Chunk * chunk, const char * name);
unsigned int disassemble_instruction(Chunk * chunk, unsigned int offset);

#endif /* CLOX_DEBUG_H*/