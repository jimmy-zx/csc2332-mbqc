#import "@preview/physica:0.9.7": *
#import "@preview/algorithmic:1.0.7"
#import algorithmic: algorithm-figure, style-algorithm
#show: style-algorithm
#show: super-plus-as-dagger

#set heading(numbering: "1.")
#set math.equation(numbering: "(1)")
#show math.equation: it => {
  // only the equation followed by a reference label is numbered
  if it.block and not it.has("label") and it.numbering != none [
    #counter(math.equation).update(v => v - 1)
    #math.equation(it.body, block: true, numbering: none)
  ] else {
    it
  }
}

#let tensor = $times.o$
#let pl = $plus.o$
#set math.mat(delim: "[")
#let rotmat(content) = rot2mat(content, delim: "[")
#let rx = $op(R_x)$
#let ry = $op(R_y)$
#let rz = $op(R_z)$
#let bypr(meas, angle) = $X^(#meas) H R_z (#angle)$

#import "@preview/charged-ieee:0.1.4": ieee
#set page(numbering: "1")
#show: ieee.with(
  title: [Simulation of MBQC and UBQC: A Qiskit-Based MBQC Implementation of the
    Two-Qubit Quantum Fourier Transform],
  abstract: [Measurement-based quantum computation (MBQC) provides an
    alternative model to the circuit-based paradigm by realizing quantum
    algorithms through adaptive single-qubit measurements on highly entangled
    resource states. In this work, we formally justify the universality of MBQC
    and present a systematic methodology for simulating MBQC protocols on a
    circuit-based quantum computing platform using Qiskit. Universal gate
    constructions—including the Hadamard gate, Z-axis rotation, and the CNOT
    gate—are implemented via measurement patterns on cluster states and
    translated into equivalent Qiskit circuits using adaptive measurements and
    classical control. As a concrete demonstration, we implement a two-qubit
    Quantum Fourier Transform (QFT) entirely within the MBQC framework and
    validate its correctness through numerical simulation. Furthermore, we
    extend this implementation to the Universal Blind Quantum Computation (UBQC)
    setting, illustrating how the MBQC-based QFT can be executed in a
    privacy-preserving manner.],
  authors: (
    (name: "Jianjun Zhao", email: "jianjun.zhao@mail.utoronto.ca"),
    (name: "Kaitian Zheng", email: "kaitian.zheng@mail.utoronto.ca"),
  ),
)

= Introduction

For quantum cloud computing to achieve widespread adoption, it must support
mechanisms that protect both data privacy and function privacy. Function privacy
is especially important in the quantum setting, as quantum algorithms frequently
exploit superposition to evaluate a function over many inputs simultaneously,
making leakage of algorithmic structure potentially more damaging than in
classical computation @Childs2005. Ensuring that neither the client’s input nor
the structure of the delegated computation is revealed to the server is
therefore a central challenge in secure quantum computing.

A seminal solution to this challenge was introduced in @broadbent2009universal,
through the Universal Blind Quantum Computation (UBQC) protocol. UBQC enables a
client with limited quantum capabilities to delegate an arbitrary quantum
computation to a remote server while preserving both data and function privacy.
The protocol is fundamentally based on Measurement-Based Quantum Computation
(MBQC) @raussendorf2003measurement, an alternative model of quantum computation
in which computation is driven by adaptive single-qubit measurements performed
on a highly entangled resource state.

MBQC departs from the traditional circuit-based paradigm by separating
entanglement generation from computation. In this model, a fixed entangled
resource state—typically a cluster state—is prepared in advance, and the
computation proceeds through a sequence of single-qubit measurements whose bases
may depend on prior measurement outcomes. As the computation progresses, the
resource state is consumed, and logical operations are realized through
teleportation-like primitives and classical feedforward of measurement results.
MBQC has been shown to be computationally equivalent to the circuit model and is
universal for quantum computation.

The close relationship between MBQC and UBQC makes MBQC a natural framework for
privacy-preserving quantum computation. By randomizing input states and masking
measurement angles, UBQC ensures that the server’s observed operations and
outcomes are information-theoretically independent of the client’s intended
computation @Morimae2013, @Dunjko2014.

Despite its theoretical appeal, practical implementation of MBQC and UBQC on
current quantum computing platforms is not straightforward @Kashif2022,
@shah2021realizations. Most available quantum hardware and cloud-based
frameworks, such as Qiskit @qiskit2024, are designed around the circuit model
and natively support only computational-basis measurements. MBQC protocols,
however, require adaptive measurements in arbitrary bases and systematic
handling of Pauli byproduct corrections.

This report presents a method for simulating MBQC on a circuit-based quantum
computing platform using Qiskit. We construct MBQC implementations of a
universal gate set and demonstrate how adaptive measurements and Pauli
corrections can be faithfully realized through classical control and
basis-changing unitaries. As a concrete case study, we implement a two-qubit
Quantum Fourier Transform entirely within the MBQC framework and validate its
correctness. Furthermore, we integrate the UBQC protocol with the MBQC-based
Quantum Fourier Transform (QFT) @coppersmith2002qft to demonstrate that the
computation can be executed in a privacy-preserving manner, without revealing
the structure of the algorithm to the server.

The remainder of this report is organized as follows. @simulation provides the
theoretical background of MBQC, including teleportation-based primitives and
correction mechanisms, and the MBQC implementation of a universal gate set. @qft
presents the MBQC implementation of a two-qubit Quantum Fourier Transform and
its simulation in Qiskit. @ubqc introduces the UBQC protocol and applies it to
the MBQC-based QFT to demonstrate blind quantum computation. Finally, the
conclusion summarizes the results and discusses implications for secure quantum
cloud computing.

= Simulation <simulation>

In this section, we formally justify the universality of measurement-based
quantum computation (MBQC) and describe the methodology used to simulate MBQC on
a circuit-based quantum computing platform. All simulations are performed using
the Qiskit framework.

== Preliminaries

Measurement-based quantum computation (MBQC) on two-dimensional cluster states
is universal for quantum computation @raussendorf2003measurement. Specifically,
for any $k$-qubit unitary $U$ and any input state
$ket(psi) in (CC^2)^(tensor k)$, there exists an MBQC pattern consisting solely
of single-qubit measurement on a 2D cluster state such that the resulting
transformation on the unmeasured qubits is
$ ket(psi) |-> P(m) U ket(psi) $
where $m in {0,1}^t$ denotes the measurement outcomes string and $P(m)$ is a
Pauli operator efficiently computable from $m$. Hence MBQC can implement $U$
exactly by applying $P(m)^+$.

== Notation

Let $G=(V,E)$ be an undirected graph. The associated graph state is defined as
$
  G := (product_((u,v) in E) "CZ"_(u,v)) ket(+)^(tensor abs(V)), #h(1em) ket(+) := (ket(0)+ket(1))/sqrt(2)
$
A cluster state is a graph state where $G$ is a rectangular two-dimensional
lattice @shah2021realizations. CZ is the controlled-$Z$ gate
$
  "CZ" = diagonalmatrix(1, 1, 1, -1, fill: 0)
$

For $theta in RR$, define the measurement basis
$ ket(plus.minus_theta) := 1/sqrt(2) ( ket(0) plus.minus e^(i theta) ket(1) ) $
and denote by $M(theta)$ the corresponding projective measurement. Measurement
outcomes are labeled by where $m in {0,1}$. An MBQC computation consists of
preparing a cluster state, injecting an input state into designated qubits,
performing a sequence of single-qubit measurements (with measurement angles
allowed to depend on previous outcomes), and interpreting the remaining
unmeasured qubits as the output.

== Teleportation

Teleportation @Furusawa1998teleportation, @Hermans2022 is the fundamental
building block of MBQC. Let qubit 1 be in an arbitrary state $ket(psi)$ and
qubit 2 be initialized in $ket(+)$. After applying CZ, measuring qubit 1 in
basis $M(theta)$ with outcome $m$ leaves qubit 2 in the state up to
normalization
$ bypr(m, theta) ket(psi) $

This follows from a direct calculation. Writing
$ket(psi) = a ket(0) + b ket(1)$,
$
  "CZ"ket(psi)ket(+) = a ket(0) ket(+) + b ket(1) ket(-)
$
Expanding $ket(0), ket(1)$ in ${ket(plus.minus)_theta}$ basis gives
$
  & "CZ"ket(psi)ket(+) \ =& a (ket(+_theta)+ket(-_theta))/sqrt(2) ket(+) + e^(i theta) b (ket(+_theta)-ket(-_theta))/sqrt(2) ket(-) \
  =& 1/sqrt(2) ( ket(+_theta) (a ket(+) + b e^(i theta) ket(-)) + ket(-_theta) (a ket(+) - b e^(i theta) ket(-)) )
$
Observe that $a ket(+) + b ket(-) = H( a ket(0) + b ket(1) )$. Also
$rz(-theta) ket(0) = e^(i theta/2) ket(0)$ and
$rz(-theta) ket(1) = e^(-i theta/2) ket(1)$, so up to a global phase
$e^(i theta/2)$,
$rz(-theta) ( a ket(0) + b ket(1) ) prop a ket(0) + b e^(i theta) ket(1)$.

Combining these gives
$
  & "CZ"ket(psi)ket(+) \ =& 1/sqrt(2) ( ket(+_theta) tensor H rz(-theta) ket(psi) + ket(-_theta) tensor bypr(, -theta) ket(psi) )
$
Projecting onto $ket(plus.minus_theta)$ on qubit 1 yields the post-measurement
state $bypr(m, -theta) ket(psi)$ on qubit 2, where $m=0$ if the measurement
outcome is $ket(+_theta)$ and $m=1$ otherwise.

This provides a method to _teleport_ the state of qubit 1 to qubit 2, with a
_byproduct_ $bypr(m, -theta)$. @universal-gate-mbqc describes methods that use
this byproduct to build a universal gate set. @correction-in-mbqc desribes
methods to correct this byproduct.

== Correction in MBQC <correction-in-mbqc>

The Pauli byproducts generated during teleportation can be corrected either by
applying explicit Pauli gates $X$ and $Z$ or, more efficiently, by modifying
subsequent measurement bases. The key identities are
$
  M(theta)X = M(-theta) quad M(theta)Z = M(theta+pi)
$
Thus, in the MBQC process, corrections using $X$ and $Z$ gates can be
implemented by adjusting the measurement angle instead of applying the gates
directly to the qubits.

Specifically, for qubit $i$, let $m_X (i)$ and $m_Z (i)$ denote the sets of
previous measurement outcomes that contribute to $X$- and $Z$-type corrections,
respectively @Danos2006. Additionally, the measurement outcomes are from qubits
connected via some paths with $i$. The adaptive measurement angle is then given
by
$
  theta'_i = (-1)^(norm(m_X (i))) theta_i + norm(m_Z (i)) pi
$
Here $theta_i$ is the planned measurement angle and $theta'_i$ is the
measurement angle that incorporats all necessary corrections.

== MBQC Measurement in Qiskit

Circuit-based platforms such as Qiskit natively support only computational-basis
measurement, i.e., $Z$-axis measurement, denoted by $M_Z$. To simulate
measurement in basis ${ket(plus.minus_theta)}$, denoted by $M(theta)$, we apply
the unitary
$
  U := H rz(-theta)
$
followed by a $Z$-basis measurement. Formally,
$
  M(theta) equiv M_Z U
$
This equivalence follows from the relations
$
  U^+ ket(0) = e^(-i theta/2) ket(+_theta), quad U^+ ket(1) = e^(-i theta/2) ket(-_theta)
$
and hence
$
  U^+ ketbra(0) U = (e^(-i theta/2) ket(+_theta)) (e^(i theta/2) bra(+_theta)) = ketbra(+_theta) \
  U^+ ketbra(1) U = (e^(-i theta/2) ket(-_theta)) (e^(i theta/2) bra(-_theta)) = ketbra(-_theta)
$

== Implementing universal gate set in MBQC <universal-gate-mbqc>

To demonstrate universality, we construct a universal gate set ${H, rz, "CNOT"}$
using MBQC primitives. Also, we provide corresponding Qiskit circuits that
simulate these gates.

Throughout this subsections, all qubits are prepared in cluster state initially
unless stated otherwise. That is, they are prepared in $ket(+)$ state, and any
two qubits connected by an edge in the graph are entangled via a CZ gate. We
also denote the measurement outcome on qubit $i$ by $m_i$.

=== Hadamard gate

Prepare two qubits 0, 1 in clustor state as shown in @h-gate, with the input
state $ket(psi)$ injected into qubit 0. Measuring qubit 0 in $M(0)$ teleports
the state to the second qubit while applying a Hadamard gate, yielding
$
  ket(psi) ket(+) & |-> ket(m_0) tensor bypr(m_0, 0) ket(psi) \
                  & = ket(m_0) tensor X^(m_0) H ket(psi)
$
The Pauli byproduct $X^(m_0)$ can be corrected using the measurement outcome
$m_0$ from qubit 0, by conditionally applying an $X$ gate, or as desribed in
@correction-in-mbqc.

#figure(
  grid(columns: (auto, auto), align: center + horizon)[
    #image("gen/h-mbqc.svg")
  ][
    #image("gen/h-qiskit.svg")
  ][(a)][(b)],
  caption: [(a) MBQC implementation of the Hadamard gate. Qubit 0 is the input
    and qubit 1 is the output. Arrow indicates the measurement flow.
    The `XY` in the figture indicates the measurement happens on the XY plane,
    and the $0.0$ above the arrow indicates the measuremtn angle.
    (b) Qiskit implementation of (a).],
)<h-gate>

=== Arbitrary $Z$-Rotation

To implement an arbitrary $rz(theta)$ rotation, three qubits $0,1,2$ are
arranged in a linear cluster. The input state $ket(psi)$ is injected into the
first qubit $0$. Measuring the qubit $0$ in $M(-theta)$ and qubit $1$ in $M(0)$
teleports the input $ket(psi)$ to the last qubit while applying an $rz(theta)$,
which yields
$
  ket(psi) ket(+) ket(+) &|-> ket(m_0) ket(m_1) tensor bypr(m_1, 0) bypr(m_0, theta) ket(psi) \
  &= ket(m_0) ket(m_1) tensor X^(m_1) Z^(m_0) rz(theta) ket(psi) \
$
Again, the byproduct operators are corrected using the classical measurement
outcomes $m_1, m_0$ as described in @correction-in-mbqc. @rz-gate shows an
example for $rz(pi/4)$.

#figure(
  grid(columns: (auto, auto), align: center + horizon)[
    #image("gen/rz-mbqc.svg")
  ][
    #image("gen/rz-qiskit.svg")
  ][(a)][(b)],
  caption: [(a) MBQC implementation of $rz(theta)$ with $theta=pi/4$ as an
    example. Qubit 0 is the input and qubit 2 is the output. Arrow indicates the
    measurement flow.
    The `XY` in the figure indicates the measurement happens on the XY plane.
    The 0.25 above the arrow indicates the measurement angle $-pi/4$.
    (b) Qiskit implementation of (a).],
)<rz-gate>

=== Entangling Gate

The CNOT gate is implemented using a four-qubit $0,...,3$ cluster state as shown
in @cnot-gate, with edges $(0,2), (2,1), (2,3)$. Let qubit $0$ encode the target
state $ket(psi)$ and qubit $1$ encode the control state $ket(phi)$. Measuring
qubit 0 in $M(0)$ followed by measuring qubit 2 in $M(0)$. The remaining qubits
$1,3$ are left in the (unormalized) state
$
  (Z^(m_0) tensor X^(m_2) Z^(m_0)) "CNOT"_(1->3) (ket(phi)_1 tensor ket(psi)_3)
$
The proof can be found in appendix @cnot-proof.

Applying the appropriate Pauli corrections yields an exact implementation of the
CNOT gate.

#figure(
  grid(columns: (auto, auto), align: center + horizon)[
    #image("gen/cnot-mbqc.svg")
  ][
    #image("gen/cnot-qiskit.svg")
  ][(a)][(b)],
  caption: [(a) MBQC implementation of CNOT with 4 qubits. Qubit 0 is the target
    bit and qubit 1 is the control bit. Arrow indicates the measurement flow.
    `XY` indicates the measurement happens on the XY plane, and the $0.0$ above
    the arrows indicates measurement angle 0.
    (b) Qiskit implementation of (a).],
)<cnot-gate>

== Automatic Transpilation

We implemented a library that enables automatic transpilation of gate-based
Qiskit circuits into measurement-based quantum computing (MBQC) circuits. The
source code and proof-of-concepts can be found in @csc2332-mbqc. The library
supports a superset of the required gates, including arbitrary-angle X and Z
rotations, the Hadamard gate, and controlled-X (CNOT) and controlled-Z gates.
The transpilation process proceeds as follows: first, a given circuit is passed
to qiskit.transpile to restrict it to the supported gate set; second, the
resulting circuit is serialized using a topological sort; and finally, each
supported gate is replaced with its corresponding MBQC prototype, with inputs
redirected to outputs of preceding MBQC components as necessary.

= Two-Qubit Quantum Fourier Transform <qft>

In this section, we implement a two-qubit Quantum Fourier Transform (QFT) in
MBQC using the universal gate constructions above. The QFT is a central
subroutine in quantum algorithms such as Shor’s factoring algorithm and quantum
phase estimation. Demonstrating the QFT within the MBQC framework further
validates the universality of the proposed simulation methodology.

#figure(
  grid(rows: (auto, auto), align: center + horizon)[
    #import "@preview/quill:0.7.2": *
    #quantum-circuit(
      lstick($ket(x_0)$), $H$, $R_2$, 1, swap(1), rstick($ket(0) + e^(2pi i [0.x_0]) ket(1)$), [\ ],
      lstick($ket(x_1)$), 1, ctrl(-1), $H$, swap(-1), rstick($ket(0) + e^(2pi i [0.x_0x_1]) ket(1)$),
    )][(a)][
    #import "@preview/quill:0.7.2": *
    #quantum-circuit(
      lstick($ket(x_0)$), 1,   $rz(pi/4)$, targ(),   $rz(-pi/4)$, targ(),   $H$, 1, [\ ],
      lstick($ket(x_1)$), $H$, $rz(pi/4)$, ctrl(-1), 1,           ctrl(-1),
    )][(b)],
  caption: [(a) QFT circuit implementation with 2 qubits. $ket(x_0)$ encodes LSB
    and $ket(x_1)$ encodes MSB. (b) QFT implemented with ${H, rz, "CNOT"}$
    without swap.],
)<qft-circuit>

The two-qubit QFT has a circuit based implementation as shown in @qft-circuit
(a) that consists of Hadamard gates, swap operation, and a controlled phase
rotation
$
  R_k = mat(1, 0; 0, e^(i 2pi \/ 2^k)),
$
which can be implemented using ${H, rz, "CNOT"}$ as shown in @qft-circuit (b).
We also omit the swap operation at the end and interpret the output qubits
accordingly, which can be implemented using three CNOT gates if desired.

== Implementation

#figure(
  image("gen/qft-mbqc.svg"),
  caption: [MBQC implementation of QFT with 2 qubits. Qubit 1 (LSB), 0 (MSB) are
    the input and qubit 3, 13 are the output. Arrow indicates the measurement
    flow. The indices of the nodes are the order of qubits in the circuit in @qft-circuit.
    Hence,
    node $1$ represents $q_0$ while node $0$ represents $q_1$.
    The remaining ancilla qubits matches the indices in this graph.
  ],
)<qft-mbqc>

To implement QFT in MBQC, we prepare 14 qubits $0, ..., 13$ in cluster state as
shown in @qft-mbqc. Let qubit 1 encode the least significant bit $ket(x_0)$
and qubit 0 enocde the most significant bit $ket(x_1)$. The computation is
realized as a composition of MBQC implementations of $H$, $rz(plus.minus pi/4)$,
and CNOT gates. The corresponding Qiskit circuit is constructed using adaptive
measurements and classical control. In the following, we map each gate in
@qft-circuit (b) to a group of nodes and their measurements shown in @qft-mbqc:
- 0-2: $H$ on $ket(x_1)$
- 5-8-7: $rz(pi/4)$ on $ket(x_0)$
- 2-4-3: $rz(pi/4)$ on $ket(x_1)$
- 1-6-3, 5-6: CNOT on control $ket(x_1)$ and target $ket(x_0)$
- 9-12-11: $rz(-pi/4)$ on $ket(x_0)$
- 3-10-7, 10-9: CNOT on control $ket(x_1)$ and target $ket(x_0)$ (here we
  reused qubit 4 because 4 is not measured so it keeps the result from before)
- 11-13: $H$ on $ket(x_0)$

@qft-qiskit gives the the total circuit implemented in Qiskit.

#place(auto, float: true, scope: "parent")[
  #figure(
    image("gen/qft-qiskit.svg"),
    caption: [Qiskit circuit of the two-qubit QFT in MBQC implementation.
    $q_0$ encodes the least significant bit $ket(x_0)$.
    and $q_1$ encodes the most significant bit $ket(x_1)$.
    ],
  )<qft-qiskit>
]

Simulation results, as shown in @qft-result, obtained from the Qiskit simulator
with input
$
  ket(psi_"in") = 1/2 sum_(x=0)^2 e^(-(2pi)/3 i x) ket(x)
$
confirms that the output probability distribution matches the theoretical QFT
output for representative input states, thereby validating both the correctness
of the MBQC construction and the effectiveness of the simulation methodology.

#figure(
  image("asset/qft-mbqc-result.svg"),
  caption: [Simulation results (ignoring bit swap) comparing the theoretical
    output probability distribution of the two-qubit QFT with results
    (frequency) obtained from the MBQC-based Qiskit simulation for 20000 shots,
    demonstrating close agreement.],
) <qft-result>

= Blind Quantum Fourier Transformation <ubqc>

In this section, we apply the Universal Blind Quantum Computation (UBQC)
protocol to the measurement-based implementation of the two-qubit QFT described
in the previous section. The objective is to demonstrate that the MBQC-based QFT
can be executed in a privacy-preserving manner, such that the quantum server
learns neither the client’s input state nor the structure of the delegated
computation beyond an agreed-upon resource graph.

== Overview

The UBQC protocol, introduced by Broadbent et al @broadbent2009universal enables
a client (Alice) with limited quantum capabilities to delegate a universal
quantum computation to a remote quantum server (Bob) while preserving both data
and function privacy. The protocol is built on MBQC and relies on three key
ideas:

+ Randomized input states prepared by Alice,
+ Masked measurement angles sent to Bob, and
+ Classical post-processing of measurement outcomes by Alice.

In the UBQC setting, Bob prepares a fixed entangled resource state and performs
single-qubit measurements according to angles provided by Alice. Due to Alice’s
randomization, Bob cannot infer the actual computation, even though it carries
out all quantum operations.

== UBQC Setting for the MBQC-Based QFT

In the UBQC protocol, instead of preparing each qubit in $ket(+)$, Alice
prepares each qubit in a randomly rotated state
$
  ket(+_alpha_i) = 1/sqrt(2) (ket(0) + e^(i alpha_i) ket(1)), quad alpha_i in "Random"{0, pi/4, ..., (7pi)/4}
$
In our simulation, instead of Alice physically sending these qubits to Bob, we
generate them directly within the simulator as simulating quantum communication
is not our focus here. Each qubit is initialized in the $ket(+)$ state, followed
by a random rotation $rz(alpha_i)$. Bob then entangles the qubits according to
the cluster-state geometry required for the MBQC-based QFT.

In this implementation, we directly construct the specific cluster state
corresponding to the QFT, and therefore Bob is provided with the QFT graph
pattern. In a fully blind or device-independent setting, this assumption can be
removed by having Bob prepare a universal two-dimensional cluster state, while
Alice uses adaptive measurements to effectively delete unneeded qubits and carve
out the required computation graph.

Let $theta_i$ denote the planned measurement angle for qubit $i$ in the original
MBQC implementation of the two-qubit QFT, and let $theta'_i$ denote the
corrected angle that incorporates Pauli byproducts from prior measurements, as
defined in @correction-in-mbqc. In the UBQC protocol, Alice further masks the
measurement angle by selecting a random bit $r_i in "Random"{0,1}$ and sending
Bob the angle
$
  phi.alt_i = theta'_i + alpha_i + pi r_i
$

Bob then measures qubit $i$ in the basis ${ket(plus.minus_(phi.alt_i))}$ and
returns the measurement outcome $m_i in {0,1}$ to Alice. If $r_i = 1$, Alice
flips the received outcome; otherwise keeps it unchanged. This classical
post-processing ensures that Alice recovers the correct logical measurement
result while Bob only observes uniformly random data.

Because the masking $alpha_i$ and $r_i$ are chosen independently and uniformly
at random, Bob cannot infer the actual computation, or the computation result.

== Simulation

We extended our automatic transpilation library to support simulations of UBQC.
1. When preparing a state, introduces a random angle $alpha$ via a Z-rotation.
2. When measuring a state, reverts the corresponding random angle $alpha$ and
  randomly adds $pi$ to the measurement angle.
3. When performing Pauli-corrections, flips the classical results depending
  on the mask.

To preserve gate independence, the random angle $alpha$ is reverted
for the output qubits of each gate.
An example of a UBQC $Z$-rotation
gate is shown in @ubqc-rz.

#figure(
  image("gen/ubqc_rz.svg"),
  caption: [
    UBQC version of $R_z (pi / 4)$, with $alpha_1 = pi / 2, alpha_2 = 3/4 pi$ and a mask of $pi$ on $q_0$.
    The random angle $alpha$ is reverted before the Pauli corrections,
    and the Pauli corrections results are flipped based on the mask.
  ]
)<ubqc-rz>

== Results

Correctness follows from the fact that Alice exactly recovers the same effective
measurement outcomes as in the non-blind MBQC-based QFT as shown in @qft-ubqc-result
after applying the classical flips determined by ${r_i}$. Conversely, Bob only
observes a uniformly distributed measurement outcome.
This implies Bob can gain no information from the measurements.

#figure(
  image("gen/ubqc_res.svg"),
  caption: [Measurement results in Alice and Bob's view of the UBQC-based two-qubit QFT
    with frequency obtained from the Qiskit simulation for 100 experiments, showing
    that Alice gets the correct distribution while Bob gets
    a universal distribution.
  ],
) <qft-ubqc-result>

= Conclusion

In this project, we presented a comprehensive simulation framework for
measurement-based quantum computation using a circuit-based quantum computing
platform. By explicitly constructing MBQC implementations of a universal gate
set and translating them into Qiskit-compatible circuits, we demonstrated that
MBQC protocols can be accurately simulated using adaptive measurements and
classical feedforward.

The successful implementation of a two-qubit Quantum Fourier Transform validated
both the universality of the MBQC constructions and the correctness of the
simulation methodology. Extending this implementation to the Universal Blind
Quantum Computation setting further demonstrated that privacy-preserving quantum
computation can be achieved without modifying the underlying MBQC logic.

Overall, this work illustrates that MBQC is not only a theoretical model of
quantum computation but also a practical framework for secure, delegated quantum
algorithms. The simulation techniques developed here provide a foundation for
exploring larger MBQC-based algorithms, fault-tolerant constructions, and
advanced cryptographic protocols within existing quantum software ecosystems.

#bibliography("refs.bib")

#pagebreak()

= Appendix

== Single-Qubit Rotation

For completeness, we provide an MBQC implementation of arbitrary single qubit
gate @shah2021realizations.

Any single-qubit gate $U in "SU"(2)$ can be represented as a composition of
three rotations along two different axes, for example
$U(alpha,beta,gamma)=rx(gamma) rz(beta) rx(alpha)$ where $rx$ and $rz$ represent
rotations around the $X$ and $Z$ axis, respectively. This gate can be
implemented in MBQC using a linear path of 5 qubits $q_0, ..., q_4$ in a cluster
state, with an input $ket(psi)$ injected at $q_0$ and $q_4$ left unmeasured as
output. Measuring the qubits $q_0, ..., q_3$ in bases
$M(theta_0), ..., M(theta_3)$ respectively transforms
$ket(psi) ket(+)ket(+)ket(+)ket(+)$ into
$
  ket(m_0)ket(m_1)ket(m_2)ket(m_3) \ tensor \ (X^(m_1+m_3)Z^(m_0+m_2)rx(gamma) rz(beta) rx(alpha) ket(psi))
$
where
$
  theta_0 = 0, quad theta_1 = (-1)^(m_0+1)alpha, \ theta_2 = (-1)^(m_1)beta, quad theta_3=(-1)^(m_0+m_2)gamma
$
and $m_0, ..., m_3$ are the measurement results from $q_0, ..., q_3$. This
follows a direct computation using the relations $H rz(theta) H = rx(theta)$ and
Pauli identities $X rz(theta) = rz(-theta) X$ and $Z rx(theta) = rx(-theta) Z$.

For the byproduct $X^(m_1+m_3) Z^(m_0+m_2)$, we can correct for these additional
Pauli gates by choosing the measurement basis of the output qubit $q_4$
appropriately or correcting for them classically after the quantum computation.

== CNOT Gate <cnot-proof>

Consider the four-qubit cluster geometry in @cnot-gate with edges $(0,2)$,
$(1,2)$, and $(2,3)$. Let qubit $0$ (target input) be initialized in $ket(psi)$,
qubit $1$ (control input) in $ket(phi.alt)$, and qubits $2$ and $3$ in $ket(+)$.
Prepare the cluster state by applying $"CZ"_{0,2}\, "CZ"_{1,2}\, "CZ"_{2,3}$.
Measure qubit $0$ in $M(0)$ (the $X$-basis) with outcome $m_0$, then measure
qubit $2$ in $M(0)$ with outcome $m_2$ @shah2021realizations.

Since controlled-$Z$ gates commute, the joint preparation can be written as

$
  ket(Psi) = "CZ"_(1,2) "CZ"_(2,3) ("CZ"_(0,2) (ket(psi)_0 ket(+)_2)) tensor ket(phi.alt)_1 ket(+)_3
$

By the teleportation lemma with $theta = 0$, the post-measurement state of
qubits $(1,2,3)$ is

$
  ket(Psi_(m_0)) = "CZ"_(1,2) "CZ"_(2,3) (ket(phi.alt)_1 tensor X^(m_0) H ket(psi)_2 tensor ket(+)_3)
$

Next, applying the teleportation lemma again on the pair $(2,3)$ with
$theta = 0$ yields

$ X^(m_2) H X^(m_0) H ket(psi)_3 = X^(m_2) Z_3^(m_0) ket(psi)_3 $

using $H X H = Z$.

It remains to account for the interaction with the control qubit via
$"CZ"_(1,2)$. Under teleportation from qubit $2$ to qubit $3$, the entangling
operation $"CZ"_(1,2)$ is mapped to $"CNOT"_(1→3)$ because conjugation by $H$ on
the target transforms controlled-$Z$ into controlled-$X$:

$ "CNOT"_(1->3) = (I_1 tensor H_3) "CZ"_(1,3) (I_1 tensor H_3). $

The measurement outcome $m_0$ additionally induces a $Z^(m_0)$ byproduct on the
control line, leading to the stated overall byproduct
$(Z_1^(m_0) tensor X_3^(m_2) Z_3^(m_0))$.

// We can also implement a CZ gate in MBQC.
//
// Measuring the first row gives
// $
//   ket(psi)ket(+)ket(+) |-> ket(m_0)ket(m_1) tensor X^(m_1) H X^(m_0) H ket(psi) = ket(m_0)ket(m_1) tensor X^(m_1) Z^(m_0) ket(psi) \
// $
// The second row gives a similar result and hence the state before measuring $q_4$
// can be written as
// $
//   "CZ" ( X^(m_1) Z^(m_0) ket(psi) X^(m_4) Z^(m_3) ket(phi) )
// $ <CZ1>
// Using the following identities and the fact that CZ is symmetric
// $
//   "CZ"(X tensor I) = (X tensor Z)"CZ" quad "CZ"(Z tensor I) = (Z tensor I)"CZ"
// $
// we can transform @CZ1 into
// $
//   ( X^(m_1)Z^(m_4) Z^(m_0) tensor X^(m_4) Z^(m_1) Z^(m_3) ) "CZ" (ket(psi) tensor ket(phi))
// $
// As mentioned before, we can correct the above result using previous measurement
// results.

