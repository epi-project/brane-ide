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


##### RUST BUILD IMAGE #####
FROM ubuntu:22.04 AS build-rust

# Define the build args
ARG UID=1000
ARG GID=1000
ARG BRANE_VERSION=develop

# Setup a user to run as
RUN groupadd -g $GID bob \
 && useradd -m -u $UID -g $GID bob

# Install additional dependencies
RUN apt-get update && apt-get install -y \
    curl git g++ cmake \
 && rm -rf /var/lib/apt/lists/*

# Install rust
USER bob
ADD --chown=bob:bob https://sh.rustup.rs /home/bob/rustup.sh
RUN sh /home/bob/rustup.sh -y --profile minimal

# Download Rust
RUN git clone https://github.com/epi-project/brane /home/bob/brane \
 && cd /home/bob/brane && git checkout $BRANE_VERSION

# Compile the binary
RUN --mount=type=cache,uid=$UID,id=cargoidx,target=/home/bob/.cargo/registry \
    --mount=type=cache,uid=$UID,id=libbraneclicache,target=/home/bob/brane/target \
    . /home/bob/.cargo/env && cd /home/bob/brane \
 && cargo build --release --package brane-cli-c \
 && mv target/release/libbrane_cli.so /home/bob/libbrane_cli.so





##### C++ BUILD IMAGE #####
FROM ubuntu:22.04 AS build-cpp

# Define the build args
ARG UID=1000
ARG GID=1000
ARG XEUS_VERSION=3.2.0

# Now setup a user to run as
RUN groupadd -g $GID bob \
 && useradd -m -u $UID -g $GID bob

# Install the dependencies we need
RUN apt-get update && apt-get install -y \
    gcc g++ cmake git \
    uuid-dev \
 && rm -rf /var/lib/apt/lists/*

# Install mamba
USER bob
ADD --chown=bob:bob https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh /home/bob/Mambaforge.sh
RUN bash /home/bob/Mambaforge.sh -b -p "${HOME}/conda"
#  && ln -s "${HOME}/conda/etc/profile.d/conda.sh" "/etc/profile.d/conda.sh"


# Install the Xeus dependencies
# RUN . "${HOME}/conda/etc/profile.d/conda.sh" \
#  && mamba install cppzmq xtl nlohmann_json xeus-zmq libuuid -c conda-forge
RUN . "${HOME}/conda/etc/profile.d/conda.sh" \
 && mamba install xtl nlohmann_json -c conda-forge

# Build the libxeus library
RUN . "${HOME}/conda/etc/profile.d/conda.sh" && conda activate \
 && git clone https://github.com/jupyter-xeus/xeus /home/bob/xeus \
 && cd /home/bob/xeus && git checkout $XEUS_VERSION \
 && mkdir build && cd build \
 && cmake -D CMAKE_BUILD_TYPE=Release .. \
 && make \
 && mv $(readlink -e libxeus.so) /home/bob/libxeus.so.9 \
 && cd .. && rm -rf build


# Install our lib's dependencies
RUN . "${HOME}/conda/etc/profile.d/conda.sh" \
 && mamba install cppzmq xeus-zmq -c conda-forge

# Now copy the source
RUN mkdir -p /home/bob/source/build
COPY --chown=bob:bob ./CMakeLists.txt /home/bob/source/CMakeLists.txt
COPY --chown=bob:bob ./share /home/bob/source/share
COPY --chown=bob:bob ./src /home/bob/source/src

# Run the build
WORKDIR /home/bob/source/build
RUN . "${HOME}/conda/etc/profile.d/conda.sh" && conda activate \
 && cmake -D CMAKE_INSTALL_PREFIX=$CONDA_PREFIX ../ \
 && cmake build . \
 && make





##### RUN IMAGE #####
# Start afresh
FROM ubuntu:22.04 AS run

# Define the user build args
ARG UID=1000
ARG GID=1000

# Create the jupyter user
RUN groupadd -g $GID brane \
 && useradd -m -u $UID -g $GID brane

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    libzmq5 \
 && rm -rf /var/lib/apt/lists/*

# Install jupyter
USER brane
RUN pip3 install --no-cache-dir --user jupyterlab
USER root

# # Install mamba
# ADD https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh /Mambaforge.sh
# RUN chmod +x /Mambaforge.sh \
#  && bash /Mambaforge.sh -b -p "${HOME}/conda" \
#  && ln -s "${HOME}/conda/etc/profile.d/conda.sh" "/etc/profile.d/conda.sh"

# # Install the Xeus dependencies
# RUN . "${HOME}/conda/etc/profile.d/conda.sh" \
#  && mamba install cppzmq xtl nlohmann_json xeus-zmq -c conda-forge

# Prepare the home folder
USER brane
RUN mkdir -p "${HOME}/notebooks"
USER root

# Write the entrypoint script
RUN printf '%s\n' "#!/usr/bin/env bash" >> /entrypoint.sh \
 && printf '%s\n' "su brane<<'EOF'" >> /entrypoint.sh \
 && printf '%s\n' "export PATH=\"/home/brane/.local/bin:$$PATH\"" >> /entrypoint.sh \
 && printf '%s\n' "export LIBBRANE_PATH=\"/libbrane_cli.so\"" >> /entrypoint.sh \
 && printf '%s\n' "cd \"/home/brane/notebooks\"" >> /entrypoint.sh \
 && printf '%s\n' "if [[ \"\$DEBUG\" -eq 1 ]]; then DEBUG_FLAG=' --debug'; else DEBUG_FLAG=''; fi" >> /entrypoint.sh \
 && printf '%s\n' "jupyter-lab\$DEBUG_FLAG --ip 0.0.0.0 --no-browser --KernelSpecManager.ensure_native_kernel=False" >> /entrypoint.sh \
 && printf '%s\n' "EOF" >> /entrypoint.sh \
 && chmod ugo+x /entrypoint.sh

# Copy libxeus
COPY --from=build-cpp /home/bob/libxeus.so.9 /usr/local/lib/libxeus.so.9
RUN ldconfig

# Copy the kernel
COPY --from=build-cpp --chown=brane:brane /home/bob/source/share/jupyter/kernels/bscript/kernel.json /home/brane/.local/share/jupyter/kernels/bscript/kernel.json
COPY --from=build-cpp --chown=brane:brane /home/bob/source/share/jupyter/kernels/bscript/logo-32x32.png /home/brane/.local/share/jupyter/kernels/bscript/logo-32x32.png
COPY --from=build-cpp --chown=brane:brane /home/bob/source/share/jupyter/kernels/bscript/logo-64x64.png /home/brane/.local/share/jupyter/kernels/bscript/logo-64x64.png
COPY --from=build-cpp /home/bob/source/build/bscript /usr/local/bin/bscript
RUN chmod ugo+x /usr/local/bin/bscript

# Copy-in the brane compiler code
COPY --from=build-rust /home/bob/libbrane_cli.so /libbrane_cli.so

# Set the entrypoint and done
WORKDIR /
ENTRYPOINT [ "/entrypoint.sh" ]

# # Start afresh and minimally
# FROM jupyter/minimal-notebook:lab-4.0.3 AS run

# # Set the startup user & path
# USER root
# WORKDIR /

# # Install dependencies
# RUN apt-get update && apt-get install -y \
#     curl \
#     openssl \
#  && rm -rf /var/lib/apt/lists/*

# # Install mamba
# ADD https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh /Mambaforge.sh
# RUN chmod +x /Mambaforge.sh \
#  && bash /Mambaforge.sh -b -p "${HOME}/conda" \
#  && ln -s "${HOME}/conda/etc/profile.d/conda.sh" "/etc/profile.d/conda.sh"

# # Install the Xeus dependencies
# RUN . "${HOME}/conda/etc/profile.d/conda.sh" \
#  && mamba install cppzmq xtl nlohmann_json xeus-zmq -c conda-forge

# # Prepare the home folder
# RUN rmdir "$HOME/work" \
#  && mkdir -p "${HOME}/data" \
#  && chown jovyan:users "${HOME}/data" \
#  && chmod 744 "${HOME}/data" \
#  && mkdir -p "${HOME}/notebooks" \
#  && chown jovyan:users "${HOME}/notebooks" \
#  && chmod 744 "${HOME}/notebooks"

# # Write an entrypoint script to mount the DFS and add the anaconda bin to PATH
# RUN printf '%s\n' "#!/usr/bin/env bash" >> /entrypoint.sh \
#  && printf '%s\n' "cd \"${HOME}\"" >> /entrypoint.sh \
#  && printf '%s\n' "su jovyan<<'EOF'" >> /entrypoint.sh \
#  && printf '%s\n' "export PATH=\"/opt/conda/bin:\$PATH\"" >> /entrypoint.sh \
#  && printf '%s\n' "if [[ \"\$DEBUG\" -eq 1 ]]; then DEBUG_FLAG=' --debug'; else DEBUG_FLAG=''; fi" >> /entrypoint.sh \
#  && printf '%s\n' "tini -g -- start-notebook.sh\$DEBUG_FLAG" >> /entrypoint.sh \
#  && printf '%s\n' "EOF" >> /entrypoint.sh \
#  && chmod +x /entrypoint.sh

# # Copy the kernel
# COPY --from=build /source/share/jupyter/kernels/bscript/kernel.json /opt/conda/share/jupyter/kernels/bscript/kernel.json
# COPY --from=build /source/share/jupyter/kernels/bscript/logo-32x32.png /opt/conda/share/jupyter/kernels/bscript/logo-32x32.png
# COPY --from=build /source/share/jupyter/kernels/bscript/logo-64x64.png /opt/conda/share/jupyter/kernels/bscript/logo-64x64.png
# COPY --from=build /source/build/bscript /opt/conda/bin/bscript

# # Copy-in the brane compiler code
# COPY .tmp/libbrane_cli.so /libbrane_cli.so

# # Set permissions
# RUN chown -R jovyan:users /opt/conda \
#  && chmod +x /opt/conda/bin/bscript

# # Set the entrypoint and done
# WORKDIR /
# ENTRYPOINT [ "/entrypoint.sh" ]
