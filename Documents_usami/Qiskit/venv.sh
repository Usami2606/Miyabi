#!/bin/bash
#PBS -q debug-g
#PBS -l select=1
#PBS -W group_list=xg24i001
#PBS -j oe
cd ${PBS_O_WORKDIR}
echo "Running on node: $(hostname)"
# 仮想環境作成
#python3 -m venv ./venv
# 仮想環境確認
echo "Before activate: $(which python)"
source ./venv/bin/activate
echo "After activate: $(which python)"

module unload nvidia
module load gcc/15.2.0
module load cmake/3.31.1

#pip install --upgrade pip
#pip install -r requirements.txt
#pip install grpcio
#pip install pytest
#pip install grpcio-tools
#pip install qiskit-aer

#chemistry

# pip install pyscf
# pip install ffsim
# pip install qiskit-ibm-runtime
# pip install qiskit-addon-sqd
# pip install numpy



# cmake -G Ninja \
#    -DCMAKE_C_COMPILER=/work/opt/local/aarch64/cores/gcc/15.2.0/bin/gcc \
#    -DCMAKE_CXX_COMPILER=/work/opt/local/aarch64/cores/gcc/15.2.0/bin/g++ \
#    -DCMAKE_TOOLCHAIN_FILE=externals/vcpkg/scripts/buildsystems/vcpkg.cmake \
#    -DCMAKE_EXPORT_COMPILE_COMMANDS=TRUE \
#    -DCMAKE_BUILD_TYPE=Release \
#    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
#    -S . -B build


# cmake --build build --clean-first -j 

unset PYTHONPATH
export LD_LIBRARY_PATH=$(pwd)/build/Release/lib:$LD_LIBRARY_PATH
export PYTHONPATH="${PWD}/pb_py:${PWD}/server/src:${PYTHONPATH}"
# $(pwd)/build/Release/bin/server --port 33351 --results-dir ./results &
# sleep 3
# python -m pytest test
# python ${PWD}/examples/submit_job.py
# python ${PWD}/examples/submit_job.py
# python ${PWD}/examples/submit_job.py
# python ${PWD}/examples/call.py 
# python ${PWD}/async/latency.py
python ${PWD}/Chemistry/chem_server.py
# kill $!



#pip install -r examples/requirements.txt
#export PYTHONPATH="${PWD}/pb_py"
#ushd pb_py
#make
#popd


# 仮想環境を無効化
deactivate
    