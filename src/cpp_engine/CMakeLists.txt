cmake_minimum_required(VERSION 3.16)
project(VeloRAG LANGUAGES CXX)

# Use C++20 for advanced concurrency features
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add our source directory
include_directories(include)

# 2. Hardcode the exact Apple Silicon include paths directly
include_directories("/opt/homebrew/include")

# Define the executable
add_executable(velorag src/main.cpp)

# Link standard threading libraries
find_package(Threads REQUIRED)
target_link_libraries(velorag PRIVATE
    Threads::Threads
    "/opt/homebrew/lib/libzmq.dylib")
