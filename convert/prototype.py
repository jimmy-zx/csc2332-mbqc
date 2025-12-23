import abc
import math
import random
from qiskit import QuantumCircuit
from qiskit.circuit.instruction import Instruction
from qiskit.circuit import library

from graphix.fundamentals import Plane


class Prototype(abc.ABC):
    def __str__(self) -> str:
        return "Prototype"

    def __repr__(self) -> str:
        return str(self)

    @property
    def circ(self) -> QuantumCircuit:
        return self.build(
                len(self.qubits),
                len(self.clbits),
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

    @property
    @abc.abstractmethod
    def edges(self) -> list[tuple[int, int]]:
        ...

    @property
    def angles(self) -> dict[int, float]:
        return {}

    @property
    def planes(self) -> dict[int, Plane]:
        return {}

    @property
    def qubits(self) -> set[int]:
        return set(self.inputs + self.outputs + self.ancillas[0])

    @property
    def clbits(self) -> set[int]:
        return set(self.ancillas[1])

    @property
    def non_output_qubits(self) -> set[int]:
        return self.qubits - set(self.outputs)

    @property
    def additional_qubits(self) -> set[int]:
        return (set(self.ancillas[0]) | set(self.outputs)) - set(self.inputs)

    def initialize(self, circ: QuantumCircuit) -> None:
        for node in self.additional_qubits:
            circ.h(node)

    def entangle(self, circ: QuantumCircuit) -> None:
        for u, v in self.edges:
            circ.cz(u, v)

    def measure(self, circ: QuantumCircuit, qubit: int, clbit: int) -> int:
        plane = self.planes[qubit]
        angle = self.angles[qubit]
        if angle != 0.:
            circ.rz(angle * math.pi, qubit)
        if plane == Plane.XY:
            circ.h(qubit)
        else:
            raise NotImplementedError()
        circ.measure(qubit, clbit)
        return 1

    def cleanup(self, circ: QuantumCircuit) -> None:
        pass


class UBPrototype(Prototype, abc.ABC):
    def __init__(
            self,
            ubqc: bool = True,
            cleanup: bool = True,
            correction: bool = True,
            alphas: dict[int, float] | None = None,
            masks: dict[int, int] | None = None,
            ) -> None:
        self.ubqc = ubqc
        self.enable_cleanup = cleanup
        self.correction = correction
        self.ubqc_angles: dict[int, float] | None = None
        self.ubqc_masks: dict[int, int] | None = None
        self.alphas = alphas or {}
        self.masks = masks or {}

    def generate_angles(self) -> dict[int, float]:
        if not self.ubqc:
            return {node: 0 for node in self.additional_qubits}
        angles = [k * math.pi / 4 for k in range(8)]
        return {
                node : self.alphas.get(node, random.choice(angles))
                for node in self.additional_qubits
                }

    def initialize(self, circ: QuantumCircuit) -> None:
        self.ubqc_angles = self.generate_angles()
        self.ubqc_masks = {}
        for node in self.additional_qubits:
            circ.h(node)
            if self.ubqc:
                circ.rz(self.ubqc_angles[node], node)

    def measure(self, circ: QuantumCircuit, qubit: int, clbit: int) -> int:
        assert self.ubqc_angles is not None
        angle = self.ubqc_angles.get(qubit, None)
        if qubit in self.inputs:
            angle = 0
        if self.ubqc:
            circ.rz(-angle, qubit)
        mask: int = 1  # 1 -> no flip, 0 -> flip
        if self.ubqc:
            mask = self.masks.get(qubit, random.choice([0, 1]))
            if mask == 0:
                circ.rz(math.pi, qubit)
        super().measure(circ, qubit, clbit)
        if not self.correction:
            mask = 1
        self.ubqc_masks[qubit] = mask
        return mask

    def cleanup(self, circ: QuantumCircuit) -> None:
        if not self.enable_cleanup or not self.ubqc:
            return
        assert self.ubqc_angles is not None
        for node in set(self.outputs) - set(self.inputs):
            circ.rz(-self.ubqc_angles[node], node)
        #for node, mask in self.ubqc_masks.items():
        #    if mask == 0:
        #        circ.rz(math.pi, node)
        self.ubqc_masks = None


class RZ(UBPrototype):
    def __init__(self, theta, **kwargs) -> None:
        super().__init__(**kwargs)
        self.theta = theta

    def __str__(self) -> str:
        return f"RZ({self.theta})"

    def build(self, qregs, cregs) -> QuantumCircuit:
        circ = QuantumCircuit(qregs, cregs)
        self.initialize(circ)
        self.entangle(circ)
        m0 = self.measure(circ, 0, 0)
        self.cleanup(circ)
        with circ.if_test((0, m0)):
            circ.x(1)
        circ.h(1)
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

    @property
    def edges(self) -> list[tuple[int, int]]:
        return [(0, 1)]

    @property
    def angles(self) -> dict[int, float]:
        return {0: self.theta / math.pi}

    @property
    def planes(self) -> dict[int, Plane]:
        return {0: Plane.XY}


class RX(UBPrototype):
    def __init__(self, theta, **kwargs) -> None:
        super().__init__(**kwargs)
        self.theta = theta

    def __str__(self) -> str:
        return f"RX({self.theta})"

    def build(self, qregs, cregs) -> QuantumCircuit:
        circ = QuantumCircuit(qregs, cregs)
        self.initialize(circ)
        self.entangle(circ)
        m0 = self.measure(circ, 0, 0)
        m1 = self.measure(circ, 1, 1)
        self.cleanup(circ)

        with circ.if_test((0, m0)):
            circ.rx(-2 * self.theta, 2)
        with circ.if_test((1, m1)):
            circ.x(2)
        with circ.if_test((0, m0)):
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

    @property
    def edges(self) -> list[tuple[int, int]]:
        return [(0, 1), (1, 2)]

    @property
    def angles(self) -> dict[int, float]:
        return {0: 0., 1: self.theta / math.pi}

    @property
    def planes(self) -> dict[int, Plane]:
        return {0: Plane.XY, 1: Plane.XY}


class H(UBPrototype):
    def __str__(self) -> str:
        return "H"

    def build(self, qregs, cregs):
        circ = QuantumCircuit(qregs, cregs)
        self.initialize(circ)
        self.entangle(circ)
        m0 = self.measure(circ, 0, 0)
        self.cleanup(circ)
        with circ.if_test((0, m0)):
            circ.x(1)
        return circ

    @property
    def inputs(self) -> list[int]:
        return [0, ]

    @property
    def outputs(self) -> list[int]:
        return [1, ]

    @property
    def ancillas(self) -> tuple[list[int], list[int]]:
        return [], [0, ]

    @property
    def edges(self) -> list[tuple[int, int]]:
        return [(0, 1)]

    @property
    def planes(self) -> dict[int, Plane]:
        return {0: Plane.XY}

    @property
    def angles(self) -> dict[int, float]:
        return {0: 0.}


class CZ(UBPrototype):
    def __str__(self) -> str:
        return "CZ"

    def build(self, qregs, cregs):
        """
        0-2-4
            |
        1-3-5
        """
        circ = QuantumCircuit(qregs, cregs)
        self.initialize(circ)
        self.entangle(circ)
        m: dict[int, int] = {}
        for c, i in enumerate([0, 2, 1, 3]):
            m[c] = self.measure(circ, i, c)
        self.cleanup(circ)

        with circ.if_test((1, m[1])):
            circ.x(4)
        with circ.if_test((0, m[0])):
            circ.z(4)
        with circ.if_test((3, m[3])):
            circ.z(4)

        with circ.if_test((3, m[3])):
            circ.x(5)
        with circ.if_test((2, m[2])):
            circ.z(5)
        with circ.if_test((1, m[1])):
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

    @property
    def edges(self) -> list[tuple[int, int]]:
        return [
                (0, 2),
                (2, 4),
                (1, 3),
                (3, 5),
                (4, 5)
                ]

    @property
    def planes(self) -> dict[int, Plane]:
        return {q: Plane.XY for q in [0, 1, 2, 3]}

    @property
    def angles(self) -> dict[int, float]:
        return {q: 0. for q in [0, 1, 2, 3]}


class CNOT(UBPrototype):
    def __str__(self) -> str:
        return "CNOT"

    def build(self, qregs, cregs) -> QuantumCircuit:
        """
        0-2-3
          |
          1-4
        """
        circ = QuantumCircuit(qregs, cregs)

        self.initialize(circ)
        self.entangle(circ)
        m: dict[int, int] = {}
        for c, i in enumerate([0, 2]):
            m[c] = self.measure(circ, i, c)
        self.cleanup(circ)

        with circ.if_test((1, m[1])):
            circ.x(3)
        with circ.if_test((0, m[0])):
            circ.z(3)
        with circ.if_test((0, m[0])):
            circ.z(1)

        return circ

    @property
    def inputs(self) -> list[int]:
        return [1, 0]

    @property
    def outputs(self) -> list[int]:
        return [1, 3]

    @property
    def ancillas(self) -> tuple[list[int], list[int]]:
        return [1, 2], [0, 1]

    @property
    def edges(self) -> list[tuple[int, int]]:
        return [
                (0, 2),
                (2, 1),
                (2, 3),
                ]

    @property
    def planes(self) -> dict[int, Plane]:
        return {0: Plane.XY, 2: Plane.XY}

    @property
    def angles(self) -> dict[int, float]:
        return {0: 0., 2: 0.,}


MAPPING: dict[type[Instruction], type[Prototype]] = {
        library.RZGate: RZ,
        library.RXGate: RX,
        library.HGate: H,
        library.CZGate: CZ,
        library.CXGate: CNOT,
}
