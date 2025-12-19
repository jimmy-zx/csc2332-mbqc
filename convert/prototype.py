import abc
from qiskit import QuantumCircuit
from qiskit.circuit.instruction import Instruction
from qiskit.circuit import library


class Prototype(abc.ABC):
    def __repr__(self) -> str:
        return str(self)

    @property
    def circ(self) -> QuantumCircuit:
        return self.build(
                len(self.inputs + self.outputs + self.ancillas[0]),
                len(self.ancillas[1]),
        )

    @abc.abstractmethod
    def build(self, qregs, cregs) -> QuantumCircuit:
        ...

    @property
    @abc.abstractmethod
    def inputs(self) -> list[int]:
        ...

    @property
    @abc.abstractmethod
    def outputs(self) -> list[int]:
        ...

    @property
    @abc.abstractmethod
    def ancillas(self) -> tuple[list[int], list[int]]:
        ...


class RZ(Prototype):
    def __init__(self, theta) -> None:
        self.theta = theta

    def __str__(self) -> str:
        return f"RZ({self.theta})"

    def build(self, qregs, cregs) -> QuantumCircuit:
        circ = QuantumCircuit(qregs, cregs, name="MB_RZ")
        circ.barrier()
        circ.h(1)
        circ.cz(0, 1)
        circ.rz(self.theta, 0)
        circ.h(0)
        circ.measure(0, 0)
        with circ.if_test((0, 1)):
            circ.x(1)
        circ.h(1)
        circ.barrier()
        return circ

    @property
    def inputs(self) -> list[int]:
        return [0, ]

    @property
    def outputs(self) -> list[int]:
        return [1, ]

    @property
    def ancillas(self) -> tuple[list[int], list[int]]:
        return ([], [0, ])


class RX(Prototype):
    def __init__(self, theta) -> None:
        self.theta = theta

    def __str__(self) -> str:
        return f"RX({self.theta})"

    def build(self, qregs, cregs) -> QuantumCircuit:
        circ = QuantumCircuit(qregs, cregs, name="MB_RX")
        circ.h(1)
        circ.h(2)
        circ.cz(0, 1)
        circ.cz(1, 2)

        circ.h(0)
        circ.measure(0, 0)

        circ.rz(self.theta, 1)
        with circ.if_test((0, 1)):
            circ.rx(-2 * self.theta, 2)
        circ.h(1)
        circ.measure(1, 1)

        with circ.if_test((1, 1)):
            circ.x(2)
        with circ.if_test((0, 1)):
            circ.z(2)
        return circ

    @property
    def inputs(self) -> list[int]:
        return [0, ]

    @property
    def outputs(self) -> list[int]:
        return [2, ]

    @property
    def ancillas(self) -> tuple[list[int], list[int]]:
        return ([1, ], [0, 1, ])


MAPPING: dict[type[Instruction], type[Prototype]] = {
        library.RZGate: RZ,
        library.RXGate: RX,
}
