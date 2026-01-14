import json

print("quantum_simulator module loaded", flush=True) 
import qiskit
from qiskit import qasm2
from qiskit import qasm3
from qiskit_aer import AerSimulator


def simulate_quantum_circuit(
    circuit_language: str,
    language_version: str,
    circuit: str,
    n_shots: int,
    timeout_seconds: int,
    result_file_path: str,
) -> tuple[bool, str]:
    print("called simulate_quantum_circuit3", flush=True)

    try:

        print("loading circuit", flush=True)

        if circuit_language == "QASM":
            print("circuit language is QASM", flush=True)
            if language_version == "2":
                qiskit_circuit = qasm2.loads(circuit)
                print("language version is 2", flush=True)
            elif language_version == "3":
                print("language version is 3", flush=True)
                qiskit_circuit = qasm3.loads(circuit)
            else:
                raise ValueError(
                    f'invalid version for "{circuit_language}": "{language_version}"'
                )
        else:
            print("invalid circuit language", flush=True)
            raise ValueError(
                f'invalid circuit language: "{circuit_language}"'
            )

        print("circuit loaded", flush=True)
        simulator = AerSimulator()
        print("simulator created", flush=True)
        job = simulator.run(circuits=qiskit_circuit, shots=n_shots, memory=True)
        print("job submitted")
        dict_result = job.result(timeout=timeout_seconds*3).to_dict()
        print("simulation completed", flush=True)

        with open(result_file_path, "w", encoding="utf-8") as f:
            json.dump(dict_result, f)

        return True, ""

    except Exception as e:
        return False, f"error: {repr(e)}"

# # def simulate_quantum_circuit(*args):
# #     print("called simulate_quantum_circuit", flush=True)
# #     return True, "ok"

