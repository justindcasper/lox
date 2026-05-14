#ifndef CLOX_MEMORY_H
#define CLOX_MEMORY_H

#include "common.h"

#define MIN_CAPACITY_START 8

#define GROW_CAPACITY(capacity) ((capacity) < MIN_CAPACITY_START ? MIN_CAPACITY_START : (capacity) * 2)
#define GROW_ARRAY(type, pointer, old_count, new_count) (type *)reallocate(pointer, sizeof(type) * (old_count), \
    sizeof(type) * (new_count))
#define FREE_ARRAY(type, pointer, old_count) reallocate(pointer, sizeof(type) * old_count, 0)

void * reallocate(void * ptr, size_t old_size, size_t new_size);

#endif /* CLOX_MEMORY_H */