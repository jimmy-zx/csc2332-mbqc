from typing import NamedTuple, Any
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.converters import circuit_to_dag
from qiskit.circuit.instruction import Instruction
import networkx as nx
from prototype import Prototype, MAPPING


class GateDesc(NamedTuple):
    proto: Prototype | Instruction
    qargs: list[Any]
    cargs: list[Any]


def serialize(
        circ: QuantumCircuit,
        skip: set[type[Prototype]] | None = None,
        count: int = -1,
        ubqc: bool = True,
        ) -> list[GateDesc]:
    gates: list[GateDesc] = []
    dag = circuit_to_dag(circ)
    skip = skip or set()
    for node in dag.topological_op_nodes():
        proto: Prototype | Instruction
        for type_, prototype in MAPPING.items():
            if count == 0:
                continue
            if prototype in skip:
                continue
            if not isinstance(node.op, type_):
                continue
            proto = prototype(*node.op.params, ubqc=ubqc)
            assert len(proto.inputs) == len(proto.outputs)
            assert len(proto.inputs) == len(node.qargs)
            count -= 1
            break
        else:
            proto = node.op
        gates.append(GateDesc(proto, node.qargs, node.cargs))
    return gates


def generate(
        descs: list[GateDesc],
        diags: list[str] | None = None,
        ) -> tuple[
                QuantumCircuit,
                dict[QuantumRegister, QuantumRegister],
                tuple[nx.Graph, dict[int, float]],
                ]:
    def log(msg: str) -> None:
        if diags is not None:
            diags.append(msg)
            print(msg)

    eff_qregs: dict[QuantumRegister, QuantumRegister] = {}
    eff_cregs: dict[ClassicalRegister, ClassicalRegister] = {}

    for desc in descs:
        for qubit in desc.qargs:
            qreg = qubit._register
            eff_qregs[qreg] = qreg
        for clbit in desc.cargs:
            creg = clbit._register
            eff_cregs[creg] = creg

    log(f"initial qregs: {eff_qregs}")
    log(f"initial cregs: {eff_cregs}")

    regs = list(eff_qregs) + list(eff_cregs)
    circ = QuantumCircuit(*regs)

    qalloc_init = len(eff_qregs)
    calloc_init = len(eff_cregs)
    qalloc = qalloc_init
    calloc = calloc_init
    added_cregs: set[int] = set()

    G = nx.Graph()
    angles: dict[int, float] = {}

    for desc in descs:
        log(f"processing desc {desc}")
        if isinstance(desc.proto, Prototype):
            eff_qregs_delta: dict[QuantumRegister, QuantumRegister] = {}
            eff_cregs_delta: dict[ClassicalRegister, ClassicalRegister] = {}
            qmap: dict[int, QuantumRegister] = {
                    sub: desc.qargs[main]._register for main, sub in enumerate(desc.proto.inputs)
            }
            cmap: dict[int, ClassicalRegister] = {}
            log(f"\tinput qmap: {qmap}")
            log("\tredirect and allocate output pass")
            for main, sub in enumerate(desc.proto.outputs):
                if sub in desc.proto.inputs:
                    log(f"\t\toutputs[{main}] = {sub} overlaps with input, omitting")
                    continue
                reg = QuantumRegister(1, f"aq{qalloc}")
                qalloc += 1
                circ.add_register(reg)
                qmap[sub] = reg
                eff_qregs_delta[qmap[desc.proto.inputs[main]]] = reg
                log(f"\t\tallocating register {reg} for outputs[{main}] = {sub}. "
                    f"Input {qmap[desc.proto.inputs[main]]} redirected to {reg}")
            log("\tallocate quantum ancilla pass")
            for sub in desc.proto.ancillas[0]:
                if sub in desc.proto.outputs:
                    log(f"\t\tancilla {sub} overlaps with output, omitting")
                    continue
                reg = QuantumRegister(1, f"aq{qalloc}")
                qalloc += 1
                circ.add_register(reg)
                qmap[sub] = reg
                log(f"\t\tallocating register {reg} for ancilla {sub}.")
            log("\tallocate classical ancilla pass")
            for sub in desc.proto.ancillas[1]:
                reg = ClassicalRegister(1, f"ac{calloc}")
                if calloc not in added_cregs:
                    added_cregs.add(calloc)
                    circ.add_register(reg)
                calloc += 1
                cmap[sub] = reg
                log(f"\t\tallocating register {reg} for ancilla {sub}.")
            calloc = calloc_init

            qubits = [
                    eff_qregs.get(qmap[i], qmap[i])[0]
                    for i in range(len(qmap))
                    ]
            clbits = [
                    eff_cregs.get(cmap[i], cmap[i])[0]
                    for i in range(len(cmap))
                    ]
            log("\tSummary")
            for i, qubit in enumerate(qubits):
                if i in desc.proto.inputs:
                    log(f"\t\tqarg {i}: -> {qubit}")
                if i in desc.proto.outputs:
                    log(f"\t\tqarg {i}: -> {qubit}")

            def qubit_ord(qubit) -> int:
                return int("".join(ch for ch in qubit._register.name if ch.isdigit()))

            edges = [
                    (
                        qubit_ord(qubits[i]),
                        qubit_ord(qubits[j]),
                        )
                    for i, j in desc.proto.edges
                    ]
            log("\t\t" + str(edges))
            G.add_edges_from(edges)

            angles |= {
                    qubit_ord(qubits[i]) : angle for i, angle in desc.proto.angles.items()
                    }

            subcirc = desc.proto.build(qubits, clbits)

            circ.compose(subcirc, qubits, clbits, inplace=True)

            eff_qregs |= eff_qregs_delta
            eff_cregs |= eff_cregs_delta
        else:
            circ.append(
                desc.proto,
                [eff_qregs[qarg._register] for qarg in desc.qargs],
                [eff_cregs[carg._register] for carg in desc.cargs],
            )
        circ.barrier()
    return circ, eff_qregs, (G, angles)
