from typing import NamedTuple, Any
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.converters import circuit_to_dag
from qiskit.circuit.instruction import Instruction
from prototype import Prototype, MAPPING


class GateDesc(NamedTuple):
    proto: Prototype | Instruction
    qargs: list[Any]
    cargs: list[Any]


def serialize(circ: QuantumCircuit) -> list[GateDesc]:
    gates: list[GateDesc] = []
    dag = circuit_to_dag(circ)
    for node in dag.topological_op_nodes():
        proto: Prototype | Instruction
        for type_, prototype in MAPPING.items():
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
        descs: list[GateDesc]
        ) -> tuple[QuantumCircuit, dict[QuantumRegister, QuantumRegister]]:
    eff_qregs: dict[QuantumRegister, QuantumRegister] = {}
    eff_cregs: dict[ClassicalRegister, ClassicalRegister] = {}

    for desc in descs:
        for qubit in desc.qargs:
            qreg = qubit._register
            eff_qregs[qreg] = qreg
        for clbit in desc.cargs:
            creg = clbit._register
            eff_cregs[creg] = creg

    regs = list(eff_qregs) + list(eff_cregs)
    circ = QuantumCircuit(*regs)

    qalloc = 0
    calloc = 0

    for desc in descs:
        if isinstance(desc.proto, Prototype):
            eff_qregs_delta: dict[QuantumRegister, QuantumRegister] = {}
            eff_cregs_delta: dict[ClassicalRegister, ClassicalRegister] = {}
            qmap: dict[int, QuantumRegister] = {
                    idx: desc.qargs[idx]._register for idx in desc.proto.inputs
            }
            cmap: dict[int, ClassicalRegister] = {}
            for i, idx in enumerate(desc.proto.outputs):
                reg = QuantumRegister(1, f"aq{qalloc}")
                qalloc += 1
                circ.add_register(reg)
                qmap[idx] = reg
                eff_qregs_delta[qmap[desc.proto.inputs[i]]] = reg
            for idx in desc.proto.ancillas[0]:
                if idx in desc.proto.outputs:
                    continue
                reg = QuantumRegister(1, f"aq{qalloc}")
                qalloc += 1
                circ.add_register(reg)
                qmap[idx] = reg
            for idx in desc.proto.ancillas[1]:
                reg = ClassicalRegister(1, f"ac{calloc}")
                calloc += 1
                circ.add_register(reg)
                cmap[idx] = reg

            qubits = [
                    eff_qregs.get(qmap[i], qmap[i])[0]
                    for i in range(len(qmap))
                    ]
            clbits = [
                    eff_cregs.get(cmap[i], cmap[i])[0]
                    for i in range(len(cmap))
                    ]

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
    return circ, eff_qregs
