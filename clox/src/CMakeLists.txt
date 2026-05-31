add_executable(clox)

target_sources(clox PRIVATE main.c chunk.c compiler.c debug.c line.c memory.c object.c scanner.c value.c vm.c)

target_include_directories(clox PRIVATE ../include)

target_compile_features(clox PRIVATE c_std_99)