#!/bin/bash 
cd ${PBS_O_WORKDIR}
echo "Running on node: $(hostname)"
echo "Before activate: $(which python)"
source ./venv/bin/activate
echo "After activate: $(which python)"

module unload nvidia
module load gcc/15.2.0
module load cmake/3.31.1

# cmake -G Ninja \
#    -DCMAKE_C_COMPILER=/work/opt/local/aarch64/cores/gcc/15.2.0/bin/gcc \
#    -DCMAKE_CXX_COMPILER=/work/opt/local/aarch64/cores/gcc/15.2.0/bin/g++ \
#    -DCMAKE_TOOLCHAIN_FILE=externals/vcpkg/scripts/buildsystems/vcpkg.cmake \
#    -DCMAKE_EXPORT_COMPILE_COMMANDS=TRUE \
#    -DCMAKE_BUILD_TYPE=Release \
#    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
#    -S . -B build

# cmake --build build --clean-first -j 

#ip addr show


unset PYTHONPATH
export LD_LIBRARY_PATH=$(pwd)/build/Release/lib:$LD_LIBRARY_PATH
export PYTHONPATH="${PWD}/pb_py:${PWD}/server/src:${PYTHONPATH}"
# $(pwd)/build/Release/bin/server --port 33351 --results-dir ./results &
# sleep 3

# 仮想環境を無効化
#deactivate
#qsub -I -l select=1 -W group_list=xg24i001 -q interact-g -l walltime=00:30:00
