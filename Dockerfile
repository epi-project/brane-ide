# DOCKERFILE for brane-ide
#   by Tim Müller
#
# Implements a Dockerfile for the `brane-ide` image.
# 
# Note that this project has three targets:
# - `brane-ide-base` provides everything of the image up to the point where we need to add the branec thing
# - `brane-ide-download` provides everything after that point, getting the `branec` by fetching it from the interwebs.
# - `brane-ide-local` also provides everything from `branec` and later, but by getting `branec` from a local source.
#


##### BASE IMAGE #####
# 584f43f06586: JupyterLab 3.0.14
FROM jupyter/minimal-notebook:lab-3.0.14 as brane-ide-base

USER root
WORKDIR /

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    openssl \
 && rm -rf /var/lib/apt/lists/*

# Install kernel dependencies
RUN pip install \
    filetype==1.0.7 \
    grpcio-tools==1.37.0 \
    grpcio==1.37.0

# Prepare the home folder
RUN rmdir "$HOME/work" \
 && mkdir -p "${HOME}/data" \
 && chown jovyan:users "${HOME}/data" \
 && chmod 744 "${HOME}/data" \
 && mkdir -p "${HOME}/notebooks" \
 && chown jovyan:users "${HOME}/notebooks" \
 && chmod 744 "${HOME}/notebooks"

# Write an entrypoint script to mount the DFS and add the anaconda bin to PATH
RUN printf '%s\n' "#!/usr/bin/env bash" >> /entrypoint.sh \
 && printf '%s\n' "cd \"${HOME}\"" >> /entrypoint.sh \
 && printf '%s\n' "su jovyan<<'EOF'" >> /entrypoint.sh \
 && printf '%s\n' "export PATH=\"/opt/conda/bin:\$PATH\"" >> /entrypoint.sh \
 && printf '%s\n' "if [[ \"\$DEBUG\" -eq 1 ]]; then DEBUG_FLAG=' --debug'; else DEBUG_FLAG=''; fi" >> /entrypoint.sh \
 && printf '%s\n' "tini -g -- start-notebook.sh\$DEBUG_FLAG" >> /entrypoint.sh \
 && printf '%s\n' "EOF" >> /entrypoint.sh \
 && chmod +x /entrypoint.sh



##### DOWNLOAD IMAGE #####
FROM brane-ide-base AS brane-ide-download

# Define the arguments for downloading it
ARG VERSION=1.0.0
ARG ARCH=x86_64

# Download branec
RUN curl -o /branec "https://github.com/epi-project/brane/releases/download/v${VERSION}/branec-linux-${ARCH}" \
 && chmod +x /branec

# Copy the source over
COPY ./kernels /kernels
COPY ./extensions /extensions

# Install the kernel
WORKDIR /kernels/bscript
RUN python setup.py install \
 && python install.py

WORKDIR /

# Finally, mark the entrypoint as run
ENTRYPOINT [ "/entrypoint.sh" ]



##### COPY IMAGE #####
FROM brane-ide-base AS brane-ide-local

# Define the arguments for where to download it from
ARG SOURCE
COPY ${SOURCE} /branec
RUN chmod +x /branec

# Copy the source over
COPY ./kernels /kernels
COPY ./extensions /extensions

# Install the kernel
WORKDIR /kernels/bscript
RUN python setup.py install \
 && python install.py

WORKDIR /

# Finally, mark the entrypoint as run
ENTRYPOINT [ "/entrypoint.sh" ]
