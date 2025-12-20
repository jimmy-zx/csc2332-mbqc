#import "@preview/physica:0.9.7": *
#show: super-plus-as-dagger

#set heading(numbering: "I.")
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

= Simulation

In this section, we formally justify the universality of measurement-based quantum computation (MBQC) and describe the methodology used to simulate MBQC on a circuit-based quantum computing platform. All simulations are performed using the Qiskit framework.

== Preliminaries

Measurement-based quantum computation (MBQC) on two-dimensional cluster states
is universal for quantum computation. Specifically, for any $k$-qubit unitary
$U$ and any input state $ket(psi) in (CC^2)^(tensor k)$, there exists an MBQC
pattern consisting solely of single-qubit measurement on a 2D cluster state such
that the resulting transformation on the unmeasured qubits is
$ ket(psi) |-> P(m) U ket(psi) $
where $m in {0,1}^t$ denotes the measurement outcomes string and $P(m)$ is a
Pauli operator efficiently computable from $m$. Hence MBQC is universal can can
implement $U$ exactly by applying $P(m)^+$.

== Notation

Let $G=(V,E)$ be an undirected graph. The associated graph state is defined as
$
  G := (product_((u,v) in E) "CZ"_(u,v)) ket(+)^(tensor abs(V)), #h(1em) ket(+) := (ket(0)+ket(1))/sqrt(2)
$
A cluster state is a graph state where $G$ is a rectangular two-dimensional
lattice.

For $theta in RR$, define the measurement basis
$ ket(plus.minus_theta) := 1/sqrt(2) ( ket(0) plus.minus e^(i theta) ket(1) ) $
and denote by $M(theta)$ the corresponding projective measurement. Measurement
outcomes are labeled by where $m in {0,1}$. An MBQC computation consists of
preparing a cluster state, injecting an input state into designated qubits,
performing a sequence of single-qubit measurements (with measurement angles
allowed to depend on previous outcomes), and interpreting the remaining
unmeasured qubits as the output.

== Teleportation

Teleportation is the fundamental building block of MBQC.
Let qubit 1 be in an arbitrary state $ket(psi)$ and qubit 2 be initialized in
$ket(+)$. After applying CZ, measuring qubit 1 in basis $M(theta)$ with outcome
$m$ leaves qubit 2 in the state up to normalization
$ bypr(m, theta) ket(psi) $ 

This follows from a direct calculation. Writing
$ket(psi) = a ket(0) + b ket(1)$,
$
  "CZ"ket(psi)ket(+) = a ket(0) ket(+) + b ket(1) ket(-)
$
Expanding $ket(0), ket(1)$ in ${ket(plus.minus)_theta}$ basis gives
$
  "CZ"ket(psi)ket(+) &= a (ket(+_theta)+ket(-_theta))/sqrt(2) ket(+) + e^(i theta) b (ket(+_theta)-ket(-_theta))/sqrt(2) ket(-) \
  &= 1/sqrt(2) ( ket(+_theta) (a ket(+) + b e^(i theta) ket(-)) + ket(-_theta) (a ket(+) - b e^(i theta) ket(-)) )
$
Observe that
$a ket(+) + b ket(-) = H( a ket(0) + b ket(1) )$. Also
$rz(-theta) ket(0) = e^(i theta/2) ket(0)$ and
$rz(-theta) ket(1) = e^(-i theta/2) ket(1)$, so up to a global phase
$e^(i theta/2)$,
$rz(-theta) ( a ket(0) + b ket(1) ) prop a ket(0) + b e^(i theta) ket(1)$.

Combining these gives
$
  "CZ"ket(psi)ket(+) &= 1/sqrt(2) ( ket(+_theta) tensor H rz(-theta) ket(psi) + ket(-_theta) tensor bypr(, -theta) ket(psi) )
$
Projecting onto $ket(plus.minus_theta)$ on qubit 1 yields the post-measurement
state $bypr(m, -theta) ket(psi)$ on qubit 2, where $m=0$ if the measurement
outcome is $ket(+_theta)$ and $1$ otherwise.

This provides a method to "teleport" the state of qubit 1 to qubit 2, with a
"byproduct" $bypr(m, -theta)$. @universal-gate-mbqc describes methods that use this byproduct to build a universal gate set. @correction-in-mbqc desribes methods to correct this byproduct.

== Correction in MBQC <correction-in-mbqc>

The Pauli byproducts generated during teleportation can be corrected either by applying explicit Pauli gates $X$ and $Z$ or, more efficiently, by modifying subsequent measurement bases. The key identities are
$
  M(theta)X = M(-theta) quad M(theta)Z = M(theta+pi)
$
Thus, in the MBQC process, corrections using $X$ and $Z$ gates can be implemented by adjusting
the measurement angle instead of applying the gates directly to the qubits.

Specifically, for qubit $i$, let $m_X (i)$ and $m_Z (i)$ denote the sets of previous measurement outcomes that contribute to $X$- and $Z$-type corrections, respectively. Additionally, the measurement outcomes are from qubits connected to qubit $i$ via a path. Then the adapted measurement angle is then given by
$
  theta'_i = (-1)^(norm(m_X (i))) theta_i + norm(m_Z (i)) pi
$
Here $theta_i$ is the planned measurement angle and $theta'_i$ is the
measurement angle that incorporats all necessary corrections.

== MBQC Measurement in Qiskit

Circuit-based platforms such as Qiskit natively support only computational-basis measurement, i.e., $Z$-axis measurement, denoted by $M_Z$. To simulate measurement in basis
${ket(plus.minus_theta)}$, denoted by $M(theta)$, we apply the unitary
$
U := H rz(-theta)
$
followed by a $Z$-basis measurement. Formally,
$
  M(theta) = M_Z U
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

To demonstrate universality, we construct a universal gate set ${H, rz, "CNOT"}$ using MBQC primitives. Also, we provide corresponding Qiskit circuits that simulate these gates.

Throughout this subsections, all qubits are prepared in cluster state initially unless stated otherwise.
That is, they are prepared in $ket(+)$ state, and any two qubits connected by an edge in the graph are entangled via a CZ gate.
We also denote the measurement outcome on qubit $i$ by $m_i$.

=== Hadamard gate

Prepare two qubits 0, 1 in clustor state as shown in @h-gate, with the input state $ket(psi)$ injected into qubit 0. Measuring qubit 0 in $M(0)$ teleports the state to the second qubit while applying a Hadamard gate, yielding
$
  ket(psi) ket(+) & |-> ket(m_0) tensor bypr(m_0, 0) ket(psi) \
                  & = ket(m_0) tensor X^(m_0) H ket(psi)
$
The Pauli byproduct $X^(m_0)$ can be corrected using the measurement outcome $m_0$ from qubit 0, by conditionally applying an $X$ gate, or as desribed in @correction-in-mbqc.

#figure(
  grid(columns: (auto, auto), align: center + horizon, gutter: 1em)[
    #image("asset/h-mbqc.svg")
  ][
    #image("asset/h-qiskit.svg")
  ],
  caption: []
)<h-gate>

=== Arbitrary $Z$-Rotation

To implement an arbitrary $rz(theta)$ rotation, three qubits $0,1,2$ are arranged in a linear cluster. The input state $ket(psi)$ is injected into the first qubit $0$. Measuring the qubit $0$ in $M(-theta)$ and qubit $1$ in $M(0)$ teleports the input $ket(psi)$ to the last qubit while applying an $rz(theta)$, which yields
$
  ket(psi) ket(+) ket(+) &|-> ket(m_0) ket(m_1) tensor bypr(m_1, 0) bypr(m_0, theta) ket(psi) \
  &= ket(m_0) ket(m_1) tensor X^(m_1) Z^(m_0) rz(theta) ket(psi) \
$
Again, the byproduct operators are corrected using the classical measurement outcomes $m_1, m_0$ as described in @correction-in-mbqc.

@rz-gate shows only an example for $rz(-pi/4)$. Note the Qiskit circuit in the figure only uses two qubits instead
of three. This is because qubit 0 is reset after first measurement then acts as the last qubit.

#figure(
  grid(columns: (auto, auto), align: center + horizon, gutter: 1em)[
    #image("asset/rz-mbqc.svg")
  ][
    #image("asset/rz-qiskit.svg")
  ],
  caption: [],
)<rz-gate>

== Entangling Gate

The CNOT gate is implemented using a four-qubit $0,...,3$ cluster state as shown in @cnot-gate, with edges $(0,2), (2,1), (2,3)$. Let qubit $0$ encode the target state $ket(psi)$ and qubit $1$ encode the control state $ket(phi)$.
Measuring qubit 0 in $M(0)$ followed by measuring qubit 2 in $M(0)$. The remaining qubits $1,3$ are left in the (unormalized) state
$
(Z^(m_0) tensor X^(m_2) Z^(m_0)) "CNOT"_(1->3) (ket(phi)_1 tensor ket(psi)_3)
$
The proof can be found in appendix.

Applying the appropriate Pauli corrections yields an exact implementation of the CNOT gate. In the Qiskit simulation, qubits 0 are reused by resetting measured qubits, reducing the total qubit count.

#figure(
  grid(columns: (auto, auto), align: center + horizon, gutter: 1em)[
    #image("asset/cnot-mbqc.svg")
  ][
    #image("asset/cnot-qiskit.svg")
  ],
)<cnot-gate>

= Two-Qubit Quantum Fourier Transform

In this section, we implement a two-qubit Quantum Fourier Transform (QFT) in
MBQC using the universal gate constructions above. The QFT is a central subroutine in quantum algorithms such as Shor’s factoring algorithm and quantum phase estimation. Demonstrating the QFT within the MBQC framework further validates the universality of the proposed simulation methodology.

#figure(
  grid(rows: (auto, auto), align: center + horizon)[
    #import "@preview/quill:0.7.2": *
    #quantum-circuit(
      lstick($ket(x_0)$), $H$, $R_2$, 1, swap(1), rstick($ket(0) + e^(2pi i [0.x_0]) ket(1)$), [\ ],
      lstick($ket(x_1)$), 1, ctrl(-1), $H$, swap(-1), rstick($ket(0) + e^(2pi i [0.x_0x_1]) ket(1)$),
    )][
    #import "@preview/quill:0.7.2": *
    #grid(columns: (auto,auto, auto))[
      #quantum-circuit(
        1, $R_2$, 1, [\ ],
        1, ctrl(-1), 1,
      )][$equiv$][
      #quantum-circuit(
        1, $rz(pi/4)$, targ(), $rz(-pi/4)$, targ(), 1, [\ ],
        1, $rz(pi/4)$, ctrl(-1), 1, ctrl(-1), 1,
      )
    ]
  ],
  caption: [QFT with 2 qubit],
)<qft>

The two-qubit QFT has a circuit based implementation as shown in @qft that consists of Hadamard gates, swap operation, and a controlled phase rotation
$
  R_k = mat(1, 0; 0, e^(i 2pi \/ 2^k))
$
which can be decomposed into a sequence of $rz$ and CNOT gates. We
also omit the swap operation at the end and interpret the output qubits
accordingly, which can be implemented using three CNOT gates if desired.

Thus the whole implementation uses $H$, $rz$, and CNOT gates.

== Implementation

#figure(
  image("asset/qft-mbqc.svg"),
)<qft-mbqc>

To implement QFT in mbqc, we prepare 14 qubits $0, ..., 13$ in cluster state as
shown in @qft-mbqc. Let qubit $0$ encode the least significant bit $ket(x_0)$ and qubit 1 enocde the most significant bit $ket(x_1)$.
The computation is realized as a composition of MBQC implementations of $H$, $rz(plus.minus pi/4)$, and CNOT gates. The corresponding Qiskit circuit is constructed using adaptive measurements and classical control:
- 0-2: $H$ on $ket(x_1)$
- 2-5-6: $rz(pi/4)$ on $ket(x_1)$
- 1-3-4: $rz(pi/4)$ on $ket(x_0)$
- 6-7-8, 7-4: CNOT on control $ket(x_1)$ and target $ket(x_0)$
- 8-9-10: $rz(-pi/4)$ on $ket(x_0)$
- 10-11-12, 11-4: CNOT on control $ket(x_1)$ and target $ket(x_0)$ (here we
  reused qubit 4 because 4 is not measured so it keeps the result from before)
- 4-13: $H$ on $ket(x_1)$

@qft-qiskit gives the the circuit implemented in Qiskit.

#figure(
  image("asset/qft-qiskit.svg"),
)<qft-qiskit>

Simulation results @qft-result obtained from the Qiskit simulator with input 
$
  ket(psi_"in") = 1/2 sum_(x=0)^2 e^(-(2pi)/3 i x) ket(x)
$
confirm that the output probability distribution matches the theoretical QFT output for representative input states, thereby validating both the correctness of the MBQC construction and the effectiveness of the simulation methodology.

#figure(
  image("asset/qft-cmp1.svg"),
) <qft-result>

= UBQC

In this section, we discuss the application of UBQC protocol to the MBQC-based
two-qubit QFT, as implemented in the previous section, and present the results
of our experiment.

= Appendix

== Single-Qubit Rotation

Any single-qubit gate $U in "SU"(2)$ can be represented as a composition of
three rotations along two different axes, for example
$U(alpha,beta,gamma)=rx(gamma) rz(beta) rx(alpha)$ where $rx$ and $rz$ represent
rotations around the $X$ and $Z$ axis, respectively. This gate can be
implemented in MBQC using a linear path of 5 qubits $q_0, ..., q_4$ in a cluster
state, with an input $ket(psi)$ injected at $q_0$ and $q_4$ left unmeasured as
output. Measuring the qubits $q_0, ..., q_3$ in bases
$M(theta_0), ..., M(theta_3)$ respectively implements
$
  ket(psi) ket(+)ket(+)ket(+)ket(+) |-> ket(m_0)ket(m_1)ket(m_2)ket(m_3) tensor (X^(m_1+m_3)Z^(m_0+m_2)rx(gamma) rz(beta) rx(alpha) ket(psi))
$
where
$
  theta_0 = 0, quad theta_1 = (-1)^(m_0+1)alpha, quad theta_2 = (-1)^(m_1)beta, quad theta_3=(-1)^(m_0+m_2)gamma
$
and $m_0, ..., m_3$ are the measurement results from $q_0, ..., q_3$. This
follows a direct computation using the relations $H rz(theta) H = rx(theta)$ and
Pauli identities $X rz(theta) = rz(-theta) X$ and $Z rx(theta) = rx(-theta) Z$.

For the byproduct $X^(m_1+m_3) Z^(m_0+m_2)$, we can correct for these additional
Pauli gates by choosing the measurement basis of the output qubit $q_4$
appropriately or correcting for them classically after the quantum computation.

== Entangling Gate

We can also implement a CZ gate in MBQC.

Measuring the first row gives
$
  ket(psi)ket(+)ket(+) |-> ket(m_0)ket(m_1) tensor X^(m_1) H X^(m_0) H ket(psi) = ket(m_0)ket(m_1) tensor X^(m_1) Z^(m_0) ket(psi) \
$
The second row gives a similar result and hence the state before measuring $q_4$
can be written as
$
  "CZ" ( X^(m_1) Z^(m_0) ket(psi) X^(m_4) Z^(m_3) ket(phi) )
$ <CZ1>
Using the following identities and the fact that CZ is symmetric
$
  "CZ"(X tensor I) = (X tensor Z)"CZ" quad "CZ"(Z tensor I) = (Z tensor I)"CZ"
$
we can transform @CZ1 into
$
  ( X^(m_1)Z^(m_4) Z^(m_0) tensor X^(m_4) Z^(m_1) Z^(m_3) ) "CZ" (ket(psi) tensor ket(phi))
$
As mentioned before, we can correct the above result using previous measurement
results.

