import abc
from qiskit import QuantumCircuit
from qiskit.circuit.instruction import Instruction
from qiskit.circuit import library


class Prototype(abc.ABC):
    def __repr__(self) -> str:
        return str(self)

    @property
    @abc.abstractmethod
    def circ(self) -> QuantumCircuit:
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

    @property
    def circ(self) -> QuantumCircuit:
        circ = QuantumCircuit(2, 1, name="MB_RZ")
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


MAPPING: dict[type[Instruction], type[Prototype]] = {
        library.RZGate: RZ,
}
