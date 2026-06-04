#include <stdio.h>
#include <string.h>

#include "memory.h"
#include "object.h"
#include "table.h"
#include "vm.h"

#define ALLOCATE_OBJ(type, object_type, vm) (type *)allocate_object(sizeof(type), object_type, vm)

static Obj * allocate_object(size_t size, ObjType type, VM * vm);
static ObjString * allocate_string(char * chars, size_t length, uint32_t hash, VM * vm);
static uint32_t hash_string(const char * key, size_t length);


ObjString * object_copy_string(const char * chars, size_t length, void * vm)
{
    uint32_t hash = hash_string(chars, length);
    ObjString * interned = table_find_string(&((VM *)vm)->strings, chars, length, hash);
    if(interned != NULL) {
        return interned;
    }

    char * buf = ALLOCATE(char, length + 1);
    memcpy(buf, chars, length);
    buf[length] = '\0';
    return allocate_string(buf, length, hash, (VM *)vm);
}

ObjString * object_take_string(char * chars, size_t length, void * vm)
{
    uint32_t hash = hash_string(chars, length);
    ObjString * interned = table_find_string(&((VM *)vm)->strings, chars, length, hash);
    if(interned != NULL) {
        FREE_ARRAY(char, chars, length + 1);
        return interned;
    }

    return allocate_string(chars, length, hash, (VM *)vm);
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

static ObjString * allocate_string(char * chars, size_t length, uint32_t hash, VM * vm)
{
    ObjString * string = ALLOCATE_OBJ(ObjString, OBJ_STRING, vm);
    string->length = length;
    string->chars = chars;
    string->hash = hash;
    table_set(&vm->strings, string, NIL_VAL);
    return string;
}

static uint32_t hash_string(const char * key, size_t length)
{
    uint32_t hash = 2166136261u;
    for(size_t i = 0; i < length; i++) {
        hash ^= (uint8_t)key[i];
        hash *= 16777619;
    }
    return hash;
}