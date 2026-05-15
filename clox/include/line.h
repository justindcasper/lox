#ifndef CLOX_LINE_H
#define CLOX_LINE_H

#include "common.h"

typedef struct {
    uint32_t count;
    uint32_t line;
} PackedLine;

typedef struct {
    unsigned int count;
    unsigned int capacity;
    PackedLine * lines;
} LineArray;

void line_array_init(LineArray * array);
void line_array_write(LineArray * array, uint32_t line_num);
void line_array_free(LineArray * array);
uint32_t line_array_get_line(const LineArray * array, unsigned int offset);


#endif /* CLOX_LINE_H */