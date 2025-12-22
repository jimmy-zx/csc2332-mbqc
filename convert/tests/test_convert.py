import math
import random
import pytest
import numpy as np
from matplotlib import pyplot as plt
from qiskit import QuantumCircuit, QuantumRegister, transpile
from qiskit.circuit.instruction import Instruction
from qiskit.circuit import library
from qiskit.quantum_info import random_statevector, Statevector, partial_trace
from qiskit_aer import AerSimulator
import networkx as nx
import graphix.pattern
from graphix.visualization import GraphVisualizer
import prototype
import convert


random.seed(42)
rng = np.random.default_rng(seed=42)


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


def visualize_proto(mb_ins: convert.Prototype, show: bool = True) -> GraphVisualizer:
    G = nx.Graph()
    G.add_edges_from(mb_ins.edges)
    gv = GraphVisualizer(
            G,
            v_in=mb_ins.inputs,
            v_out=mb_ins.outputs,
            meas_plane=mb_ins.planes,
            local_clifford=mb_ins.angles,
            )
    if show:
        gv.visualize(
                show_measurement_planes=True,
                show_pauli_measurement=True,
                show_local_clifford=True,
                )
    return gv


@pytest.mark.parametrize(
        "op, proto",
        [
            (library.RZGate, prototype.RZ),
            (library.RXGate, prototype.RX),
        ],
)
def test_unary(op: type[Instruction], proto: type[convert.Prototype], request):
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

    if request.config.getoption("--plot"):
        visualize_proto(mb_ins)
        plt.show()


def test_h(request):
    state = Statevector([1, 0])
    qc_gate = QuantumCircuit(1)
    initialize(state, qc_gate, 0)
    qc_gate.h(0)
    qc_gate.save_statevector(conditional=True)

    mb_ins = prototype.H()
    qc_mb = QuantumCircuit(
            len(mb_ins.inputs + mb_ins.outputs + mb_ins.ancillas[0]),
            len(mb_ins.ancillas[1])
            )
    initialize(state, qc_mb, 0)
    qc_mb.compose(mb_ins.circ, inplace=True)
    qc_mb.save_statevector(conditional=True)

    assert_equiv(qc_gate, qc_mb, [], mb_ins.inputs + mb_ins.ancillas[0])

    if request.config.getoption("--plot"):
        visualize_proto(mb_ins)
        plt.show()


@pytest.mark.parametrize(
        "op, proto",
        [
            (library.CXGate, prototype.CNOT),
            (library.CZGate, prototype.CZ),
        ],
)
def test_binary(op: type[Instruction], proto: type[convert.Prototype], request):
    in0 = random_statevector(2, seed=rng)
    in1 = random_statevector(2, seed=rng)
    qc_gate = QuantumCircuit(2)
    initialize(in0, qc_gate, 0)
    initialize(in1, qc_gate, 1)
    qc_gate.append(op(), [0, 1])
    qc_gate.save_statevector(conditional=True)

    mb_ins = proto()
    qc_mb = QuantumCircuit(
            len(mb_ins.qubits),
            len(mb_ins.clbits)
            )
    initialize(in0, qc_mb, mb_ins.inputs[0])
    initialize(in1, qc_mb, mb_ins.inputs[1])
    qc_mb.compose(mb_ins.circ, inplace=True)
    qc_mb.save_statevector(conditional=True)

    assert_equiv(qc_gate, qc_mb, [], list(mb_ins.non_output_qubits))

    if request.config.getoption("--plot"):
        visualize_proto(mb_ins)
        plt.show()


@pytest.mark.parametrize(
        "op",
        [
            library.RZGate,
            library.RXGate,
        ],
)
@pytest.mark.parametrize("count", range(10))
def test_gen_unary(op: type[Instruction], count):
    _ = count
    theta = random.uniform(0, math.pi * 2)
    q1 = QuantumRegister(1, "q")
    qc_gate = QuantumCircuit(q1)
    state = random_statevector(2)
    initialize(state, qc_gate, q1)
    qc_gate.append(op(theta), q1)

    qc_gen, mapping, _ = convert.generate(convert.serialize(qc_gate))

    qc_gate.save_statevector(conditional=True)
    qc_gen.save_statevector(conditional=True)

    out_idx = qc_gen.find_bit(mapping[q1][0]).index
    assert_equiv(
            qc_gate,
            qc_gen,
            [],
            [i for i in range(len(qc_gen.qubits)) if i != out_idx]
            )


@pytest.mark.parametrize("count", range(10))
def test_gen_h(count):
    _ = count
    q1 = QuantumRegister(1, "q")
    qc_gate = QuantumCircuit(q1)
    state = random_statevector(2)
    initialize(state, qc_gate, q1)
    qc_gate.h(0)

    qc_gen, mapping, _ = convert.generate(convert.serialize(qc_gate))

    qc_gate.save_statevector(conditional=True)
    qc_gen.save_statevector(conditional=True)

    out_idx = qc_gen.find_bit(mapping[q1][0]).index
    assert_equiv(
            qc_gate,
            qc_gen,
            [],
            [i for i in range(len(qc_gen.qubits)) if i != out_idx]
            )


@pytest.mark.parametrize(
        "op",
        [
            library.CXGate,
            library.CZGate,
        ],
)
@pytest.mark.parametrize("count", range(10))
def test_gen_binary(op: type[Instruction], count):
    _ = count
    q1 = QuantumRegister(1, "q1")
    q2 = QuantumRegister(1, "q2")
    qc_gate = QuantumCircuit(q1, q2)
    initialize(random_statevector(2, seed=rng), qc_gate, q1)
    initialize(random_statevector(2, seed=rng), qc_gate, q2)
    qc_gate.append(op(), [q1, q2])

    descs = convert.serialize(qc_gate, skip={prototype.RZ, })
    qc_gen, mapping, _ = convert.generate(descs, diags=[])

    qc_gate.save_statevector(conditional=True)
    qc_gen.save_statevector(conditional=True)

    out_idx = {qc_gen.find_bit(mapping[q][0]).index for q in (q1, q2)}
    assert_equiv(
            qc_gate,
            qc_gen,
            [],
            [i for i in range(len(qc_gen.qubits)) if i not in out_idx]
            )


def test_transpile_qft(request):
    q1 = QuantumRegister(1, "q1")
    q2 = QuantumRegister(1, "q2")
    qc = QuantumCircuit(q1, q2)

    qc.append(library.QFT(2, do_swaps=0), [0, 1])

    qc = transpile(qc, AerSimulator())

    qc.draw("mpl", fold=-1)

    qc_t = transpile(
            qc,
            basis_gates=["rx", "rz", "cz", "h", "cx"],
    )

    qc_t.draw("mpl", fold=-1)

    qc_gen, mapping, G = convert.generate(convert.serialize(qc_t))
    in_idx = [qc_gen.find_bit(q[0]).index for q in (q1, q2)]
    out_idx = [qc_gen.find_bit(mapping[q][0]).index for q in (q1, q2)]

    qc.save_statevector(conditional=True)
    qc_gen.save_statevector(conditional=True)

    qc_gen.draw("mpl", fold=-1)

    assert_equiv(
            qc,
            qc_gen,
            [],
            [i for i in range(len(qc_gen.qubits)) if i not in out_idx]
            )

    gv = GraphVisualizer(G, v_in=in_idx, v_out=out_idx)

    if request.config.getoption("--plot"):
        gv.visualize()
        plt.show()
