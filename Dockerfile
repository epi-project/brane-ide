# DOCKERFILE for brane-ide
#   by Tim Müller
#
# Implements a Dockerfile for the `brane-ide` image.
# 
# There are three layers to this project:
# - The `dev env` layer, which can be used for development and VS Code's in-container mode.
# - The `build` layer, which uses that environment to build the project.
# - The `run` layer, which does not build on the previous layer but provides a fresh, runtime-only environment for the JupyterLab server.
#


##### DEV ENV IMAGE #####
# We build on C++
FROM ubuntu:22.04 AS dev

# Install the dependencies we need
RUN apt-get update && apt-get install -y \
    gcc g++ cmake \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Install mamba
ADD https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh /Mambaforge.sh
RUN chmod +x /Mambaforge.sh \
 && bash /Mambaforge.sh -b -p "${HOME}/conda"

# Install the Xeus dependencies
RUN . "${HOME}/conda/etc/profile.d/conda.sh" && conda activate \
 && mamba install cppzmq xtl nlohmann_json xeus-zmq -c conda-forge

# Prepare the source directory
RUN mkdir -p /source/build





##### BUILD IMAGE #####
# Pickup where we leftoff
FROM dev AS build

# Now copy the source
RUN mkdir -p /source/build
COPY ./src /source/src
COPY ./share /source/share
COPY ./CMakeLists.txt /source/CMakeLists.txt

# Run the build
WORKDIR /source/build
RUN . "${HOME}/conda/etc/profile.d/conda.sh" && conda activate \
 && cmake -D CMAKE_INSTALL_PREFIX=$CONDA_PREFIX ../ \
 && cmake build . \
 && make \
 && make install





##### RUN IMAGE #####
# Start afresh and minimally
FROM jupyter/minimal-notebook:lab-3.0.14 AS run
