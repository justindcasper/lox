add_executable(clox)

target_sources(clox PRIVATE main.c chunk.c debug.c line.c memory.c value.c)

target_include_directories(clox PRIVATE ../include)

target_compile_features(clox PRIVATE c_std_99)