import math
import random
import pytest
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.instruction import Instruction
from qiskit.circuit import library
from qiskit.quantum_info import random_statevector, Statevector, partial_trace
from qiskit_aer import AerSimulator
import prototype
import convert


def initialize(state: Statevector, qc: QuantumCircuit, idx) -> None:
    alpha, beta = state.data
    theta = 2 * np.arccos(np.abs(alpha))
    phi = np.angle(beta) - np.angle(alpha)
    qc.ry(theta, idx)
    qc.rz(phi, idx)


def assert_equiv(
        lhs: QuantumCircuit, rhs: QuantumCircuit, lqargs, rqargs
        ) -> None:
    sim = AerSimulator(method="statevector")
    results_lhs = sim.run(lhs, shots=1024).result()
    results_rhs = sim.run(rhs, shots=1024).result()
    for lk, lv in results_lhs.data(0)["statevector"].items():
        for rk, rv in results_rhs.data(0)["statevector"].items():
            lhs_v = partial_trace(lv, lqargs).to_statevector()
            rhs_v = partial_trace(rv, rqargs).to_statevector()
            assert lhs_v.equiv(rhs_v)


@pytest.mark.parametrize(
        "op, proto",
        [
            (library.RZGate, prototype.RZ),
            (library.RXGate, prototype.RX),
        ],
)
def test_unary(op: type[Instruction], proto: type[convert.Prototype]):
    state = Statevector([1, 0])
    theta = math.pi / 2
    qc_gate = QuantumCircuit(1)
    initialize(state, qc_gate, 0)
    qc_gate.append(op(theta), [0])
    qc_gate.save_statevector(conditional=True)

    mb_ins = proto(theta)
    qc_mb = QuantumCircuit(
            len(mb_ins.inputs + mb_ins.outputs + mb_ins.ancillas[0]),
            len(mb_ins.ancillas[1])
            )
    initialize(state, qc_mb, 0)
    qc_mb.compose(mb_ins.circ, inplace=True)
    qc_mb.save_statevector(conditional=True)

    assert_equiv(qc_gate, qc_mb, [], mb_ins.inputs + mb_ins.ancillas[0])


@pytest.mark.parametrize(
        "op",
        [
            library.RZGate,
            library.RXGate,
        ],
)
def test_gen_unary(op: type[Instruction]):
    theta = random.uniform(0, math.pi * 2)
    q1 = QuantumRegister(1, "q")
    qc_gate = QuantumCircuit(q1)
    state = random_statevector(2)
    initialize(state, qc_gate, q1)
    qc_gate.append(op(theta), q1)

    qc_gen, mapping = convert.generate(convert.serialize(qc_gate))

    qc_gate.save_statevector(conditional=True)
    qc_gen.save_statevector(conditional=True)

    out_idx = qc_gen.find_bit(mapping[q1][0]).index
    assert_equiv(
            qc_gate,
            qc_gen,
            [],
            [i for i in range(len(qc_gen.qubits)) if i != out_idx]
            )
