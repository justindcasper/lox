#include <stdio.h>
#include <string.h>

#include "memory.h"
#include "object.h"
#include "vm.h"

#define ALLOCATE_OBJ(type, object_type, extra, vm) (type *)allocate_object(sizeof(type) + extra, object_type, vm)

static Obj * allocate_object(size_t size, ObjType type, VM * vm);
static ObjString * allocate_string(size_t length, VM * vm);


ObjString * object_copy_string(const char * chars, size_t length, void * vm)
{
    ObjString * string = allocate_string(length, vm);
    memcpy(string->chars, chars, length);
    string->chars[length] = '\0';
    return string;
}

void object_print(Value value)
{
    switch(OBJ_TYPE(value)) {
        case OBJ_STRING:
            printf("%s", AS_CSTRING(value));
            break;
    }
}

static Obj * allocate_object(size_t size, ObjType type, VM * vm)
{
    Obj * object = (Obj *)reallocate(NULL, 0, size);
    object->type = type;

    object->next = vm->objects;
    vm->objects = object;
    return object;
}

static ObjString * allocate_string(size_t length, VM * vm)
{
    ObjString * string = ALLOCATE_OBJ(ObjString, OBJ_STRING, length + 1, vm);
    string->length = length;
    return string;
}