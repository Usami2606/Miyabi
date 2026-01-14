FROM ubuntu:24.04 AS builder

RUN apt update && \
    apt upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential \
    clang \
    cmake \
    curl \
    git \
    ninja-build \
    pkg-config \
    python3.12-dev \
    python3-venv \
    tar \
    unzip \
    zip

COPY cmake/ /app/cmake/
COPY proto/ /app/proto/
COPY server/ /app/server/
COPY \
    CMakeLists.txt \
    requirements.txt \
    vcpkg.json \
    /app/

WORKDIR /app

# vcpkg
ENV VCPKG_ROOT="/app/externals/vcpkg"
ENV PATH="${VCPKG_ROOT}:${PATH}"
RUN git clone https://github.com/microsoft/vcpkg.git "${VCPKG_ROOT}" && \
    "${VCPKG_ROOT}/bootstrap-vcpkg.sh"

RUN python3.12 -m venv .venv && \
    . .venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

RUN . .venv/bin/activate && \
    cmake -DCMAKE_TOOLCHAIN_FILE="${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake" -DCMAKE_EXPORT_COMPILE_COMMANDS=TRUE -DCMAKE_BUILD_TYPE=Release -S . -B build -G Ninja && \
    cmake --build build

FROM ubuntu:24.04
COPY --from=builder /app/build/Release/bin/server /app/bin/
COPY \
    server/src/quantum_simulator.py \
    requirements.txt \
    /app/
ENV PYTHONPATH="/app:${PYTHONPATH}"

RUN apt-get update && \
    apt-get upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3.12-dev \
    python3-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN python3.12 -m venv .venv && \
    . .venv/bin/activate && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["/bin/sh", "-c", ". .venv/bin/activate && /app/bin/server --port 33351 --results-dir /app/results"]
