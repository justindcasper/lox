#ifndef CLOX_COMPILER_H
#define CLOX_COMPILER_H

#include "chunk.h"
#include "common.h"
#include "vm.h"

bool compile(const char * source, Chunk * chunk, VM * vm);

#endif /* CLOX_COMPILER_H */