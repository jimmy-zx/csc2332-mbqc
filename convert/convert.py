import math
from typing import NamedTuple, Any
from qiskit import QuantumCircuit, QuantumRegister
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
        if (prototype := MAPPING.get(type(node.op), None)) is not None:
            proto = prototype(*node.op.params)
            assert len(proto.inputs) == len(proto.outputs)
            assert len(proto.inputs) == len(node.qargs)
        else:
            proto = node.op
        gates.append(GateDesc(proto, node.qargs, node.cargs))
    return gates


def generate(
        descs: list[GateDesc]
        ) -> tuple[QuantumCircuit, dict[QuantumRegister, QuantumRegister]]:
    eff_regs: dict[QuantumRegister, QuantumRegister] = {}
    ancilla_count: int = 0
    for desc in descs:
        for qubit in desc.qargs:
            eff_regs[qubit._register] = qubit._register
        if isinstance(desc.proto, Prototype):
            ancilla_count += len(desc.proto.outputs)
    regs = list(eff_regs) + [
            QuantumRegister(1, f"a{i}") for i in range(ancilla_count)
            ]
    circ = QuantumCircuit(*regs)
    alloc = len(eff_regs)
    for desc in descs:
        if isinstance(desc.proto, Prototype):
            assert len(desc.qargs) == len(desc.proto.inputs)
            mapping = {
                    idx: desc.qargs[idx]._register for idx in desc.proto.inputs
            }
            eff_regs_delta: dict[QuantumRegister, QuantumRegister] = {}
            for i, idx in enumerate(desc.proto.outputs):
                assert idx not in mapping
                mapping[idx] = regs[alloc]
                eff_regs_delta[
                        desc.qargs[desc.proto.inputs[i]]._register
                        ] = regs[alloc]
                alloc += 1
            qargs = [
                    eff_regs.get(mapping[i], mapping[i])[0]
                    for i in range(len(mapping))
                    ]
            circ.compose(desc.proto.circ, qargs, inplace=True)
            eff_regs |= eff_regs_delta
        else:
            circ.append(
                desc.proto,
                [eff_regs[qarg._register] for qarg in desc.qargs],
                desc.cargs
            )
    return circ, eff_regs


if __name__ == "__main__":
    circ = QuantumCircuit(1)
    circ.h(0)
    circ.rz(math.pi / 2, 0)
    circ.h(0)
    gates = serialize(circ)
    print(gates)
    circ, output = generate(gates)
    print(circ.draw())
    print(output)
