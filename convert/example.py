import math
import random
import pytest
import argparse
import tqdm
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
        lhs: QuantumCircuit, rhs: QuantumCircuit,
        lindex: list[int] | None = None, rindex: list[int] | None = None,
        ) -> None:
    sim = AerSimulator(method="statevector")
    results_lhs = sim.run(lhs, shots=1024).result()
    results_rhs = sim.run(rhs, shots=1024).result()
    for lk, lv in results_lhs.data(0)["statevector"].items():
        for rk, rv in results_rhs.data(0)["statevector"].items():
            lindex = lindex or list(range(lv.num_qubits))
            rindex = rindex or list(range(rv.num_qubits))
            lqargs = [i for i in range(lv.num_qubits) if i not in lindex]
            rqargs = [i for i in range(rv.num_qubits) if i not in rindex]
            lhs_v = partial_trace(lv, lqargs).to_statevector()
            rhs_v = partial_trace(rv, rqargs).to_statevector()
            lord = np.argsort(lindex)
            rord = np.argsort(rindex)
            assert np.isclose(lhs_v.probabilities(lord), rhs_v.probabilities(rord)).all()


def collect_sv(
        circ: QuantumCircuit,
        index: list[int] | None = None,
        ) -> np.array:
    sim = AerSimulator(method="statevector")
    results = sim.run(circ, shots=1).result()
    lv = results.data(0)["statevector"]
    lindex = index or list(range(lv.num_qubits))
    lqargs = [i for i in range(lv.num_qubits) if i not in lindex]
    lhs_v = partial_trace(lv, lqargs).to_statevector()
    lord = np.argsort(lindex)
    return lhs_v.probabilities(lord)


def visualize_proto(mb_ins: convert.Prototype, show: bool = True, **kwargs) -> GraphVisualizer:
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
                **kwargs,
                )
    return gv


def plot_rz():
    state = Statevector([1, 0])
    theta = math.pi / 2
    qc_gate = QuantumCircuit(1)
    initialize(state, qc_gate, 0)
    qc_gate.rz(theta, 0)
    qc_gate.save_statevector(conditional=True)

    mb_ins = prototype.RZ(theta)
    mb_ins.ubqc = False
    qc_mb = QuantumCircuit(
            len(mb_ins.inputs + mb_ins.outputs + mb_ins.ancillas[0]),
            len(mb_ins.ancillas[1])
            )
    initialize(state, qc_mb, 0)
    qc_mb.compose(mb_ins.circ, inplace=True)
    qc_mb.save_statevector(conditional=True)

    assert_equiv(qc_gate, qc_mb, [], mb_ins.outputs)

    fig1 = mb_ins.circ.draw("mpl")
    fig1.savefig(f"gen/rz-qiskit.svg")
    visualize_proto(mb_ins, filename="gen/rz-mbqc.svg")


def plot_h(testenv: bool = False):
    state = Statevector([1, 0])
    qc_gate = QuantumCircuit(1)
    initialize(state, qc_gate, 0)
    qc_gate.h(0)
    qc_gate.save_statevector(conditional=True)

    mb_ins = prototype.H(ubqc=False)
    qc_mb = QuantumCircuit(
            len(mb_ins.inputs + mb_ins.outputs + mb_ins.ancillas[0]),
            len(mb_ins.ancillas[1])
            )
    initialize(state, qc_mb, 0)
    qc_mb.compose(mb_ins.circ, inplace=True)
    qc_mb.save_statevector(conditional=True)

    assert_equiv(qc_gate, qc_mb, [], mb_ins.outputs)

    if not testenv:
        fig1 = mb_ins.circ.draw("mpl")
        fig1.savefig("gen/h-qiskit.svg")
        visualize_proto(mb_ins, show=True, filename="gen/h-mbqc.svg")


def plot_cnot():
    in0 = random_statevector(2, seed=rng)
    in1 = random_statevector(2, seed=rng)
    qc_gate = QuantumCircuit(2)
    initialize(in0, qc_gate, 0)
    initialize(in1, qc_gate, 1)
    qc_gate.cx(0, 1)
    qc_gate.save_statevector(conditional=True)

    mb_ins = prototype.CNOT(ubqc=False)
    qc_mb = QuantumCircuit(
            len(mb_ins.qubits),
            len(mb_ins.clbits)
            )
    initialize(in0, qc_mb, mb_ins.inputs[0])
    initialize(in1, qc_mb, mb_ins.inputs[1])
    qc_mb.compose(mb_ins.circ, inplace=True)
    qc_mb.save_statevector(conditional=True)

    assert_equiv(qc_gate, qc_mb, [], rindex=mb_ins.outputs)

    fig1 = mb_ins.circ.draw("mpl")
    fig1.savefig("gen/cnot-qiskit.svg")
    visualize_proto(mb_ins, show=True, filename="gen/cnot-mbqc.svg")


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
            rindex=[out_idx],
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
            rindex=[out_idx],
            )


@pytest.mark.parametrize(
        "op",
        [
            library.CXGate,
            library.CZGate,
        ],
)
@pytest.mark.parametrize("count", range(10))
@pytest.mark.parametrize("rev", [True, False])
def test_gen_binary(op: type[Instruction], count: int, rev: bool):
    _ = count
    q1 = QuantumRegister(1, "q1")
    q2 = QuantumRegister(1, "q2")
    qc_gate = QuantumCircuit(q1, q2)
    initialize(random_statevector(2, seed=rng), qc_gate, q1)
    initialize(random_statevector(2, seed=rng), qc_gate, q2)
    if rev:
        qc_gate.append(op(), [q2, q1])
    else:
        qc_gate.append(op(), [q1, q2])

    descs = convert.serialize(qc_gate, skip={prototype.RZ, })
    qc_gen, mapping, _ = convert.generate(descs, diags=[])

    qc_gate.save_statevector(conditional=True)
    qc_gen.save_statevector(conditional=True)

    out_idx = [qc_gen.find_bit(mapping[q][0]).index for q in (q1, q2)]
    assert_equiv(
            qc_gate,
            qc_gen,
            rindex=out_idx,
            )


def qft_circuit(plot: bool = True):
    # generate the QFT circuit
    q1 = QuantumRegister(1, "q0")
    q2 = QuantumRegister(1, "q1")
    qc = QuantumCircuit(q1, q2)
    qc.append(library.QFT(2, do_swaps=0), [0, 1])
    qc = transpile(qc, AerSimulator())
    if plot:
        qc.draw("mpl", fold=-1)

    # transpile to basis gate set
    qc_t = transpile(
            qc,
            basis_gates=["rx", "rz", "cz", "h", "cx"],
            optimization_level=3,
    )
    if plot:
        qc_t.draw("mpl", fold=-1)

    return qc, qc_t, [q1, q2]


def test_transpile_qft(request):
    qc, qc_t, (q1, q2) = qft_circuit()

    # convert to mbqc
    descs = convert.serialize(
            qc_t,
            )
    qc_gen, mapping, G = convert.generate(descs, diags=[])
    qc_gen.draw("mpl", fold=-1)

    in_idx = [qc_gen.find_bit(q[0]).index for q in (q1, q2)]
    out_idx = [qc_gen.find_bit(mapping[q][0]).index for q in (q1, q2)]

    amps = np.array([
        1/2,
        np.exp(-2j * np.pi / 3) / 2,
        np.exp(-4j * np.pi / 3) / 2,
        1/2
    ], dtype=complex)

    # add init for qc
    qc_init = QuantumCircuit(*qc.qregs, *qc.cregs)
    qc_init.initialize(amps, [0, 1])
    qc_init.compose(qc, inplace=True)
    qc_init.save_statevector(conditional=True)

    # add init for mbqc
    # qc_gen might have different bit ordering than qc
    qc_gen_init = QuantumCircuit(*qc_gen.qregs, *qc_gen.cregs)
    qc_gen_init.initialize(amps, in_idx)
    qc_gen_init.compose(qc_gen, inplace=True)
    qc_gen_init.save_statevector(conditional=True)

    gv = GraphVisualizer(G, v_in=in_idx, v_out=out_idx)

    if request.config.getoption("--plot"):
        gv.visualize()
        plt.show()

    assert_equiv(
            qc_init,
            qc_gen_init,
            rindex=out_idx,
            )


def plot_ubqc_qft(testenv: bool = False):
    qc, qc_t, (q1, q2) = qft_circuit(plot=False)

    sv_alice: list[np.array] = []
    sv_bob: list[np.array] = []

    for i in tqdm.tqdm(range(100)):
        # convert to mbqc
        descs = convert.serialize(
                qc_t,
                )
        qc_gen, mapping, G = convert.generate(descs)

        # Bob's circuit
        qc_bob, mapping_bob, G_bob = convert.generate(descs)
        if random.choice([0, 1]) == 0:
            qc_bob.x(mapping_bob[q1])
        if random.choice([0, 1]) == 0:
            qc_bob.x(mapping_bob[q2])

        in_idx = [qc_gen.find_bit(q[0]).index for q in (q1, q2)]
        out_idx = [qc_gen.find_bit(mapping[q][0]).index for q in (q1, q2)]

        amps = np.array([
            1/2,
            np.exp(-2j * np.pi / 3) / 2,
            np.exp(-4j * np.pi / 3) / 2,
            1/2
        ], dtype=complex)

        # add init for qc
        qc_init = QuantumCircuit(*qc.qregs, *qc.cregs)
        qc_init.initialize(amps, [0, 1])
        qc_init.compose(qc, inplace=True)
        qc_init.save_statevector(conditional=True)

        # add init for mbqc
        # qc_gen might have different bit ordering than qc
        qc_gen_init = QuantumCircuit(*qc_gen.qregs, *qc_gen.cregs)
        qc_gen_init.initialize(amps, in_idx)
        qc_gen_init.compose(qc_gen, inplace=True)
        qc_gen_init.save_statevector()

        # add init for bob
        qc_bob_init = QuantumCircuit(*qc_bob.qregs, *qc_bob.cregs)
        qc_bob_init.initialize(amps, in_idx)
        qc_bob_init.compose(qc_bob, inplace=True)
        qc_bob_init.save_statevector()

        gv = GraphVisualizer(G, v_in=in_idx, v_out=out_idx)

        sv_alice.append(collect_sv(qc_gen_init, out_idx))
        sv_bob.append(collect_sv(qc_bob_init, out_idx))

    stats_alice = np.array(sv_alice).mean(axis=0)
    stats_bob = np.array(sv_bob).mean(axis=0)

    w = 0.35
    xs = np.array([0, 1, 2, 3])

    fig, ax = plt.subplots(1, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("outcome")
    ax.set_ylabel("probability")
    ax.bar(xs - w / 2, stats_alice, w, label="Alice")
    ax.bar(xs + w / 2, stats_bob, w, label="Bob")
    ax.set_xticks(xs)
    ax.set_xticklabels(["00", "01", "10", "11"])
    ax.legend()
    if not testenv:
        fig.savefig("gen/ubqc_res.svg")


def plot_ubqc_rz():
    q = QuantumRegister(1, "q0")
    qc = QuantumCircuit(q)
    qc.rz(math.pi / 2, 0)

    descs = convert.serialize(qc)
    descs[0].proto.alphas = {1: math.pi / 4}
    descs[0].proto.masks = {0: 0, 1: 1}
    qc_gen, mapping, G = convert.generate(descs)

    fig = qc_gen.draw("mpl")
    fig.savefig("gen/ubqc_rz.svg")



def main() -> None:
    funcs = [
        plot_ubqc_qft,
        plot_ubqc_rz,
        plot_h,
        plot_rz,
        plot_cnot,
            ]
    parser = argparse.ArgumentParser()
    parser.add_argument("--func", type=str, required=False)
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()
    if args.func:
        for func in funcs:
            if func.__name__ == args.func:
                func()
    if args.plot:
        plt.show()


if __name__ == "__main__":
    main()
