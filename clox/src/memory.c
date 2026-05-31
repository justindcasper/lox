#include <stdlib.h>

#include "memory.h"

static void free_object(Obj * object);


void * reallocate(void * ptr, size_t old_size, size_t new_size)
{
    if(new_size == 0) {
        free(ptr);
        return NULL;
    }

    void * result = realloc(ptr, new_size);
    return result;
}

void free_objects(VM * vm)
{
    Obj * object = vm->objects;
    while(object != NULL) {
        Obj * next = object->next;
        free_object(object);
        object = next;
    }
}

static void free_object(Obj * object)
{
    switch(object->type) {
        case OBJ_STRING: {
            ObjString * string = (ObjString *)object;
            FREE_ARRAY(char, string->chars, string->length + 1);
            FREE(ObjString, object);
            break;
        }
    }
}
