cmake_minimum_required(VERSION 3.0)
project(TerminalRecorder)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_library(UTIL_LIBRARY util)

add_executable(terminal_recorder terminal_recorder.cpp)
target_link_libraries(terminal_recorder ${UTIL_LIBRARY})