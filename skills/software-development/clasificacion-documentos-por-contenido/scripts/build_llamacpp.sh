#!/bin/bash
# build_llamacpp.sh - Compila llama.cpp optimizado para ThinkPad P53
# i7-9850H (6C/12T) + Quadro T1000 4GB
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "==> Verificando dependencias..."
for cmd in cmake git g++; do
    if ! which $cmd &>/dev/null; then
        echo "ERROR: $cmd no instalado. Ejecuta: sudo apt-get install -y cmake build-essential"
        exit 1
    fi
done

if ! nvcc --version &>/dev/null; then
    echo "ERROR: CUDA Toolkit no instalado. Ejecuta: sudo apt-get install -y nvidia-cuda-toolkit"
    exit 1
fi

echo "==> Clonando llama.cpp..."
if [ ! -d "llama.cpp" ]; then
    git clone --depth 1 https://github.com/ggml-org/llama.cpp
fi

cd llama.cpp
echo "==> Compilando con CUDA..."
mkdir -p build && cd build
cmake .. -DGGML_CUDA=ON -DGGML_NATIVE=ON -DGGML_AVX2=ON -DGGML_FMA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release -j$(nproc)
echo "==> COMPILACION COMPLETA"
ls -lh bin/llama-server bin/llama-cli 2>/dev/null
