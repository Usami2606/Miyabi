import time
from enum import Enum
import json

import qiskit
from qiskit import qasm2
from qiskit import qasm3

import warnings

warnings.filterwarnings("ignore")

import pyscf
import pyscf.cc
import pyscf.mcscf

import ffsim
from qiskit import QuantumCircuit, QuantumRegister

import argparse
from enum import Enum
import grpc
import json
import qc_simulator_pb2
import qc_simulator_pb2_grpc

SERVER_ADDRESS = "172.16.1.10"
SERVER_PORT = 33351
TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJRUGNIdThPdkg5MjJhcVZkLWlhWWwzTDVyc192SGkxaldwbHFKSkhIUjBRIn0.eyJleHAiOjE3MzcwMDc3MjYsImlhdCI6MTczNzAwNzQyNiwiYXV0aF90aW1lIjoxNzM3MDA3NDI2LCJqdGkiOiJkNDBmZWI2Zi1jN2UyLTQxMmMtOTc5Mi0zMWU2YWM5MjEwN2YiLCJpc3MiOiJodHRwczovL2lkcC5xYy5yLWNjcy5yaWtlbi5qcC9yZWFsbXMvamhwYy1xdWFudHVtIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6ImRlYjI5ZjNmLTA2ODYtNDFmOC05NzVlLTA4NWVlMGIyMjg5OCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImpocGNxLXJlZG1pbmUiLCJzaWQiOiJiZmIyYjc1Ny1hYTEzLTQyMWEtYTJjZi1jOWI5M2IwODg2ZmQiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsLnFjLnItY2NzLnJpa2VuLmpwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsImRlZmF1bHQtcm9sZXMtamhwYy1xdWFudHVtIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm5hbWUiOiJ0YWthc2hpIHVjaGlkYSIsInByZWZlcnJlZF91c2VybmFtZSI6InRha2FzaGkudWNoaWRhIiwiZ2l2ZW5fbmFtZSI6InRha2FzaGkiLCJmYW1pbHlfbmFtZSI6InVjaGlkYSIsImVtYWlsIjoidGFrYXNoaS51Y2hpZGFAcmlrZW4uanAifQ.ezdji9V2W8trNXTr7aaLa9vNbUR98kn49tIj88KaBTZi2lcE9I9zjkNxLN07q0sESP-8ziLkiLfpBavCDc0B8Q"

class ResponseStatus(Enum):
    UNKNOWN = 0
    QUEUED = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4

def submit_job(
    circuit_language: str, language_version: str, circuit: str, n_shots: int
):
    request = qc_simulator_pb2.SubmitJobRequest(
        token=TOKEN,
        circuit_language=circuit_language,
        language_version=language_version,
        circuit=circuit,
        n_shots=n_shots,
    )

    response = stub.SubmitJob(request)   # ← ここがRPC呼び出し

    return response.job_id


def get_result(stub, job_id):
    response = stub.GetResult(
        qc_simulator_pb2.GetResultRequest(
            token=TOKEN,
            job_id=job_id,
        )
    )
    status = ResponseStatus(response.status)
    result = json.loads(response.result_json) if response.result_json else None
    print(status)
    return status, result



# Specify molecule properties
open_shell = False
spin_sq = 0

# Build N2 molecule
mol = pyscf.gto.Mole()
mol.build(
    atom=[["N", (0, 0, 0)], ["N", (1.0, 0, 0)]],
    basis="6-31g",
    symmetry="Dooh",
)

# Define active space
n_frozen = 2
active_space = range(n_frozen, mol.nao_nr())

# Get molecular integrals
scf = pyscf.scf.RHF(mol).run()
num_orbitals = len(active_space)
n_electrons = int(sum(scf.mo_occ[active_space]))
num_elec_a = (n_electrons + mol.spin) // 2
num_elec_b = (n_electrons - mol.spin) // 2
cas = pyscf.mcscf.CASCI(scf, num_orbitals, (num_elec_a, num_elec_b))
mo = cas.sort_mo(active_space, base=0)
hcore, nuclear_repulsion_energy = cas.get_h1cas(mo)
eri = pyscf.ao2mo.restore(1, cas.get_h2cas(mo), num_orbitals)

# Compute exact energy
exact_energy = cas.run().e_tot

# Get CCSD t2 amplitudes for initializing the ansatz
ccsd = pyscf.cc.CCSD(scf, frozen=[i for i in range(mol.nao_nr()) if i not in active_space]).run()
t1 = ccsd.t1
t2 = ccsd.t2


n_reps = 1
alpha_alpha_indices = [(p, p + 1) for p in range(num_orbitals - 1)]
alpha_beta_indices = [(p, p) for p in range(0, num_orbitals, 4)]

ucj_op = ffsim.UCJOpSpinBalanced.from_t_amplitudes(
    t2=t2,
    t1=t1,
    n_reps=n_reps,
    interaction_pairs=(alpha_alpha_indices, alpha_beta_indices),
)

nelec = (num_elec_a, num_elec_b)

# create an empty quantum circuit
qubits = QuantumRegister(2 * num_orbitals, name="q")
print(f"Qubits={qubits}, Orbitals={num_orbitals}")
circuit = QuantumCircuit(qubits)

# prepare Hartree-Fock state as the reference state and append it to the quantum circuit
circuit.append(ffsim.qiskit.PrepareHartreeFockJW(num_orbitals, nelec), qubits)

# apply the UCJ operator to the reference state
circuit.append(ffsim.qiskit.UCJOpSpinBalancedJW(ucj_op), qubits)
circuit.measure_all()

#from qiskit_ibm_runtime.fake_provider import FakeBrisbane
#backend = FakeBrisbane()

from qiskit_aer import AerSimulator
from qiskit.compiler import transpile
backend = AerSimulator()

isa_circuit = transpile(circuit, backend=backend, optimization_level=1)

print("ready simlator")

print(type(circuit))
qasm_str = qasm3.dumps(isa_circuit)
with open("circuit.qasm", "w") as f:
    f.write(qasm_str)

channel = grpc.insecure_channel(f"{SERVER_ADDRESS}:{SERVER_PORT}")
stub = qc_simulator_pb2_grpc.SimulatorServiceStub(channel)
job_id = submit_job("QASM", "3", qasm_str, 30000) 

while True:
            status, result = get_result(stub, job_id)
            if status == ResponseStatus.COMPLETED:
                break
            elif status == ResponseStatus.FAILED:
                raise RuntimeError(f"Job {job_id} failed")
            else:
                  print("caluculating...")
            time.sleep(10)

channel.close()


import numpy as np
from qiskit_addon_sqd.counts import BitArray

counts = result["results"][0]["data"]["counts"]

bit_array = BitArray.from_counts(
    counts=counts,
    num_bits=2 * num_orbitals,
)



# from qiskit_aer import AerSimulator
# from qiskit.compiler import transpile

# backend = AerSimulator()

# isa_circuit = transpile(circuit, backend=backend, optimization_level=1)

#from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
#spin_a_layout = [0, 14, 18, 19, 20, 33, 39, 40, 41, 53, 60, 61, 62, 72, 81, 82]
#spin_b_layout = [2, 3, 4, 15, 22, 23, 24, 34, 43, 44, 45, 54, 64, 65, 66, 73]
#initial_layout = spin_a_layout + spin_b_layout
#pass_manager = generate_preset_pass_manager(
#    optimization_level=3, backend=backend, initial_layout=initial_layout
#)


# with PRE_INIT passes
# We will use the circuit generated by this pass manager for hardware execution
#pass_manager.pre_init = ffsim.qiskit.PRE_INIT
#isa_circuit = pass_manager.run(circuit)
#print(f"Gate counts (w/ pre-init passes): {isa_circuit.count_ops()}")

# from qiskit_addon_sqd.counts import generate_bit_array_uniform

# from qiskit_ibm_runtime import SamplerV2 as Sampler

# sampler = Sampler(mode=backend)
# print("job start")
# job = sampler.run([isa_circuit], shots=100)
# primitive_result = job.result()
# pub_result = primitive_result[0]
# bit_array = pub_result.data.meas
# from qiskit_addon_sqd.counts import generate_bit_array_uniform
# bit_array = generate_bit_array_uniform(10_000, num_orbitals * 2, rand_seed=rng)

rng = np.random.default_rng(12345)

from functools import partial

from qiskit_addon_sqd.fermion import SCIResult, diagonalize_fermionic_hamiltonian, solve_sci_batch

# SQD options
energy_tol = 1e-3
occupancies_tol = 1e-3
max_iterations = 5

# Eigenstate solver options
num_batches = 1
samples_per_batch = 10000
symmetrize_spin = True
carryover_threshold = 1e-5
max_cycle = 200

# Pass options to the built-in eigensolver. If you just want to use the defaults,
# you can omit this step, in which case you would not specify the sci_solver argument
# in the call to diagonalize_fermionic_hamiltonian below.
sci_solver = partial(solve_sci_batch, spin_sq=0.0, max_cycle=max_cycle)

# List to capture intermediate results
result_history = []


def callback(results: list[SCIResult]):
    result_history.append(results)
    iteration = len(result_history)
    print(f"Iteration {iteration}")
    for i, result in enumerate(results):
        print(f"\tSubsample {i}")
        print(f"\t\tEnergy: {result.energy + nuclear_repulsion_energy}")
        print(f"\t\tSubspace dimension: {np.prod(result.sci_state.amplitudes.shape)}")


result = diagonalize_fermionic_hamiltonian(
    hcore,
    eri,
    bit_array,
    samples_per_batch=samples_per_batch,
    norb=num_orbitals,
    nelec=nelec,
    num_batches=num_batches,
    energy_tol=energy_tol,
    occupancies_tol=occupancies_tol,
    max_iterations=max_iterations,
    sci_solver=sci_solver,
    symmetrize_spin=symmetrize_spin,
    carryover_threshold=carryover_threshold,
    callback=callback,
    seed=rng
)

