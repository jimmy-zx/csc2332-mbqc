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


def serialize(circ: QuantumCircuit, skip: set[type[Prototype]] | None = None) -> list[GateDesc]:
    gates: list[GateDesc] = []
    dag = circuit_to_dag(circ)
    skip = skip or set()
    for node in dag.topological_op_nodes():
        proto: Prototype | Instruction
        for type_, prototype in MAPPING.items():
            if prototype in skip:
                continue
            if not isinstance(node.op, type_):
                continue
            proto = prototype(*node.op.params)
            assert len(proto.inputs) == len(proto.outputs)
            assert len(proto.inputs) == len(node.qargs)
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
                nx.Graph
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

    for desc in descs:
        log(f"processing desc {desc}")
        if isinstance(desc.proto, Prototype):
            eff_qregs_delta: dict[QuantumRegister, QuantumRegister] = {}
            eff_cregs_delta: dict[ClassicalRegister, ClassicalRegister] = {}
            qmap: dict[int, QuantumRegister] = {
                    i: desc.qargs[idx]._register for i, idx in enumerate(desc.proto.inputs)
            }
            cmap: dict[int, ClassicalRegister] = {}
            log(f"\tinput qmap: {qmap}")
            log("\tredirect and allocate output pass")
            for i, idx in enumerate(desc.proto.outputs):
                if idx in desc.proto.inputs:
                    log(f"\t\toutputs[{i}] = {idx} overlaps with input, omitting")
                    continue
                reg = QuantumRegister(1, f"aq{qalloc}")
                qalloc += 1
                circ.add_register(reg)
                qmap[idx] = reg
                eff_qregs_delta[qmap[desc.proto.inputs[i]]] = reg
                log(f"\t\tallocating register {reg} for outputs[{i}] = {idx}. "
                    f"Input {qmap[desc.proto.inputs[i]]} redirected to {reg}")
            log("\tallocate quantum ancilla pass")
            for idx in desc.proto.ancillas[0]:
                if idx in desc.proto.outputs:
                    log(f"\t\tancilla {idx} overlaps with output, omitting")
                    continue
                reg = QuantumRegister(1, f"aq{qalloc}")
                qalloc += 1
                circ.add_register(reg)
                qmap[idx] = reg
                log(f"\t\tallocating register {reg} for ancilla {idx}.")
            log("\tallocate classical ancilla pass")
            for idx in desc.proto.ancillas[1]:
                reg = ClassicalRegister(1, f"ac{calloc}")
                if calloc not in added_cregs:
                    added_cregs.add(calloc)
                    circ.add_register(reg)
                calloc += 1
                cmap[idx] = reg
                log(f"\t\tallocating register {reg} for ancilla {idx}.")
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
                    log(f"\t\tqarg {i}: Input {desc.proto.inputs.index(i)} -> {qubit}")
                if i in desc.proto.outputs:
                    log(f"\t\tqarg {i}: Output {desc.proto.outputs.index(i)} -> {qubit}")

            edges = [
                    (
                        circ.find_bit(qubits[i]).index,
                        circ.find_bit(qubits[j]).index,
                        )
                    for i, j in desc.proto.edges
                    ]
            G.add_edges_from(edges)

            subcirc = desc.proto.build(qubits, clbits)

            circ.compose(subcirc, qubits, clbits, inplace=True)

            log(circ.draw())

            eff_qregs |= eff_qregs_delta
            eff_cregs |= eff_cregs_delta
        else:
            circ.append(
                desc.proto,
                [eff_qregs[qarg._register] for qarg in desc.qargs],
                [eff_cregs[carg._register] for carg in desc.cargs],
            )
        circ.barrier()
    return circ, eff_qregs, G
