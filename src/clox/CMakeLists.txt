cmake_minimum_required(VERSION 3.22.1)

project(clox C)

add_executable(clox src/main.c)

target_include_directories(clox PRIVATE include)