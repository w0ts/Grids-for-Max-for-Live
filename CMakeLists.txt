# Builds the grids external with the Max SDK (max-sdk-base, fetched at a pinned commit):
#   cmake -S . -B build && cmake --build build --config Release
# -> build/package/externals/grids.mxo (macOS, x86_64 + arm64, signed ad hoc) or grids.mxe64 (Windows x64)
cmake_minimum_required(VERSION 3.25)

set(CMAKE_OSX_ARCHITECTURES "x86_64;arm64" CACHE STRING "macOS architectures")
set(MAX_SDK_PACKAGE_OUT_OF_TREE ON CACHE BOOL "externals into build/package, not the source tree")
set(AUTHOR_DOMAIN "io.github.w0ts" CACHE STRING "bundle identifier prefix")
set(GIT_VERSION_TAG "1.1.0" CACHE STRING "the version in the macOS bundle")

include(FetchContent)
FetchContent_Declare(
  max-sdk-base
  GIT_REPOSITORY https://github.com/Cycling74/max-sdk-base.git
  GIT_TAG c03a2922a2a8ff149165a1e2ea134e9321d6e202   # main, 2026-06-17
)
FetchContent_MakeAvailable(max-sdk-base)

# The external: max-sdk-base's project() hook makes the target from these directory properties (no glob: the fetched
# SDK lives under build/, the one source is named)
set_property(DIRECTORY PROPERTY max::external YES)
project(grids C CXX)
target_sources(grids PRIVATE grids.c)
