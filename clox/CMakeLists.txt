cmake_minimum_required(VERSION 3.22.1)

project(clox
    VERSION 0.1.0
    LANGUAGES C
)

add_executable(clox)

target_sources(clox PRIVATE src/main.c)

target_include_directories(clox PRIVATE include)

target_compile_features(clox PRIVATE c_std_99)