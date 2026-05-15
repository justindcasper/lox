#include "line.h"
#include "memory.h"

void line_array_init(LineArray * array)
{
    array->count = 0;
    array->capacity = 0;
    array->lines = NULL;
}

void line_array_write(LineArray * array, uint32_t line_num)
{
    if(array->count > 0 && array->lines[array->count - 1].line == line_num) {
        array->lines[array->count - 1].count++;
        return;
    }

    if(array->capacity < array->count + 1) {
        unsigned int old_capacity = array->capacity;
        array->capacity = GROW_CAPACITY(old_capacity);
        array->lines = GROW_ARRAY(PackedLine, array->lines, old_capacity, array->capacity);
    }
    
    array->lines[array->count].count = 1;
    array->lines[array->count].line = line_num;
    array->count++;
}

void line_array_free(LineArray * array)
{
    FREE_ARRAY(PackedLine, array->lines, array->capacity);
    line_array_init(array);
}

uint32_t line_array_get_line(const LineArray * array, unsigned int offset)
{
    uint32_t line_num = 0;
    unsigned int off_counter = 0;

    for(unsigned int i = 0; i < array->count && off_counter <= offset; i++) {
        if(array->lines[i].count + off_counter > offset) {
            line_num = array->lines[i].line;
            break;
        }
        off_counter += array->lines[i].count;
    }

    return line_num;
}
