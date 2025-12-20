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
                len(set(self.inputs + self.outputs + self.ancillas[0])),
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


class CZ(Prototype):
    def __str__(self) -> str:
        return "CZ"

    def build(self, qregs, cregs):
        """
        0-2-4
            |
        1-3-5
        """
        circ = QuantumCircuit(qregs, cregs)
        for i in [2, 3, 4, 5]:
            circ.h(i)
        for a, b in [
                (0, 2),
                (2, 4),
                (1, 3),
                (3, 5),
                (4, 5)
                ]:
            circ.cz(a, b)

        for i in [0, 2, 1, 3]:
            circ.h(i)

        for c, i in enumerate([0, 2, 1, 3]):
            circ.measure(i, c)

        with circ.if_test((1, 1)):
            circ.x(4)
        with circ.if_test((0, 1)):
            circ.z(4)
        with circ.if_test((3, 1)):
            circ.z(4)

        with circ.if_test((3, 1)):
            circ.x(5)
        with circ.if_test((2, 1)):
            circ.z(5)
        with circ.if_test((1, 1)):
            circ.z(5)

        return circ

    @property
    def inputs(self) -> list[int]:
        return [0, 1]

    @property
    def outputs(self) -> list[int]:
        return [4, 5]

    @property
    def ancillas(self) -> tuple[list[int], list[int]]:
        return ([2, 3], [0, 1, 2, 3])


MAPPING: dict[type[Instruction], type[Prototype]] = {
        library.RZGate: RZ,
        library.RXGate: RX,
        library.CZGate: CZ,
}
