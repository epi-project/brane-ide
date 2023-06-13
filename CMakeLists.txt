# CMAKE LISTS.txt
#   by Lut99
#
# Created:
#   13 Jun 2023, 16:02:33
# Last edited:
#   13 Jun 2023, 16:06:06
# Auto updated?
#   Yes
#
# Description:
#   CMakeLists file for the BraneScript Xeus kernel.
#   
#   Based on: https://xeus.readthedocs.io/en/latest/kernel_implementation.html
#


### METADATA ###
cmake_minimum_required(VERSION 3.4.3)
project(bscript)

set(EXECUTABLE_NAME bscript)



### CONFIGURATION ###
include(GNUInstallDirs)

# We generate the kernel.json file, given the installation prefix and the executable name
configure_file (
    "${CMAKE_CURRENT_SOURCE_DIR}/share/jupyter/kernels/bscript/kernel.json.in"
    "${CMAKE_CURRENT_SOURCE_DIR}/share/jupyter/kernels/bscript/kernel.json"
)

# Set some Xeus dependencies stuff
option(XEUS_STATIC_DEPENDENCIES "link statically with xeus dependencies" OFF)
if (XEUS_STATIC_DEPENDENCIES)
    set(xeus-zmq_target "xeus-zmq-static")
else ()
    set(xeus-zmq_target "xeus-zmq")
endif ()



### DEPENDENCIES ###
# Be sure to use recent versions
set(xeus-zmq_REQUIRED_VERSION 1.0.2)

find_package(xeus-zmq ${xeus-zmq_REQUIRED_VERSION} REQUIRED)
find_package(Threads)



### FLAGS ###
include(CheckCXXCompilerFlag)

if (CMAKE_CXX_COMPILER_ID MATCHES "Clang" OR CMAKE_CXX_COMPILER_ID MATCHES "GNU" OR CMAKE_CXX_COMPILER_ID MATCHES "Intel")
    CHECK_CXX_COMPILER_FLAG("-std=c++14" HAS_CPP14_FLAG)

    if (HAS_CPP14_FLAG)
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++14")
    else()
        message(FATAL_ERROR "Unsupported compiler -- xeus requires C++14 support!")
    endif()
endif()



### TARGET & LINK ###

# BraneScript source files
set(MY_KERNEL_SRC
    src/custom_interpreter.cpp
    src/custom_interpreter.hpp
)

# My kernel executable
add_executable(${EXECUTABLE_NAME} src/main.cpp ${MY_KERNEL_SRC} )
target_link_libraries(${EXECUTABLE_NAME} PRIVATE ${xeus-zmq_target} Threads::Threads)

set_target_properties(${EXECUTABLE_NAME} PROPERTIES
    INSTALL_RPATH_USE_LINK_PATH TRUE
)



### INSTALLATION ###

# Install the BraneScript kernel
install(TARGETS ${EXECUTABLE_NAME}
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})

# Configuration and data directories for jupyter and my_kernel
set(XJUPYTER_DATA_DIR "share/jupyter" CACHE STRING "Jupyter data directory")

# Install Jupyter kernelspecs
set(MY_KERNELSPEC_DIR ${CMAKE_CURRENT_SOURCE_DIR}/share/jupyter/kernels)
install(DIRECTORY ${MY_KERNELSPEC_DIR}
        DESTINATION ${XJUPYTER_DATA_DIR}
        PATTERN "*.in" EXCLUDE)
