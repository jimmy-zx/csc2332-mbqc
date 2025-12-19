import math
import random
import pytest
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister
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


def test_rz():
    state = Statevector([1, 0])
    theta = math.pi / 2
    qc_gate = QuantumCircuit(1)
    initialize(state, qc_gate, 0)
    qc_gate.rz(theta, 0)
    qc_gate.save_statevector(conditional=True)

    qc_mb = QuantumCircuit(2, 1)
    initialize(state, qc_mb, 0)
    qc_mb.compose(prototype.RZ(theta).circ, [0, 1], [0], inplace=True)
    qc_mb.save_statevector(conditional=True)

    assert_equiv(qc_gate, qc_mb, [], [0])


def test_rz_gen():
    theta = random.uniform(0, math.pi * 2)
    q1 = QuantumRegister(1, "q")
    qc_gate = QuantumCircuit(q1)
    state = random_statevector(2)
    initialize(state, qc_gate, q1)
    qc_gate.rz(theta, q1)

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
