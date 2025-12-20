#import "@preview/physica:0.9.7": *
#show: super-plus-as-dagger

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

Measurement-based quantum computation (MBQC) on two-dimensional cluster states
is universal for quantum computation. Specifically, for any $k$-qubit unitary
$U$ and any input state $ket(psi) in (CC^2)^(tensor k)$, there exists an MBQC
pattern consisting only of single-qubit measurement on a 2D cluster state such
that the resulting transformation on the unmeasured qubits is
$ ket(psi) |-> P(m) U ket(psi) $
where $m in {0,1}^t$ denotes the measurement outcomes string and $P(m)$ is a
Pauli operator efficiently computable from $m$. Hence MBQC is universal can can
implement $U$ exactly by applying $P(m)^+$.

== Notation

Let $G=(V,E)$ be a graph. The associated graph state is defined as
$
  G = (product_((u,v) in E) "CZ"_(u,v)) ket(+)^(tensor abs(V)), #h(1em) ket(+) := (ket(0)+ket(1))/sqrt(2)
$
A cluster state is a graph state where $G$ is a rectangular two-dimensional
lattice. For $theta in RR$, define the measurement basis
$ ket(plus.minus_theta) := 1/sqrt(2) ( ket(0) plus.minus e^(i theta) ket(1) ) $
and denote by $M(theta)$ the corresponding projective measurement. Measurement
outcomes are labeled by where $m in {0,1}$. An MBQC computation consists of
preparing a cluster state, injecting an input state into designated qubits,
performing a sequence of single-qubit measurements (with measurement angles
allowed to depend on previous outcomes), and interpreting the remaining
unmeasured qubits as the output.

== Teleportation

Let qubit 1 be in an arbitrary state $ket(psi)$ and qubit 2 be initialized in
$ket(+)$. After applying $"CZ"_(1,2)$, measuring qubit 1 in basis $M(theta)$
with outcome $s$ leaves qubit 2 in the state
$
  X^s H R_z (theta) ket(psi)
$
up to normalization.

This follows from a direct calculation. Writing
$ket(psi) = a ket(0) + b ket(1)$,
$
  "CZ"ket(psi)ket(+) = a ket(0) ket(+) + b ket(1) ket(-)
$
Expanding $ket(0), ket(1)$ in ${ket(plus.minus)_theta}$ basis gives
$
  "CZ"ket(psi)ket(+) &= a (ket(+_theta)+ket(-_theta))/sqrt(2) + e^(i theta) b (ket(+_theta)-ket(-_theta))/sqrt(2) \
  &= 1/sqrt(2) ( ket(+_theta) (a ket(+) + b e^(i theta) ket(-)) + ket(-_theta) (a ket(+) - b e^(i theta) ket(-)) )
$
It remains to identify the single-qubit operators mapping $ket(psi)$ to the
bracketed states on qubit 2. Observe that
$a ket(+) + b ket(-) = H( a ket(0) + b ket(1) )$. Also
$R_z (-theta) ket(0) = e^(i theta/2) ket(0)$ and
$R_z (-theta) ket(1) = e^(-i theta/2) ket(1)$, so up to a global phase
$e^(i theta/2)$,
$R_z (-theta) ( a ket(0) + b ket(1) ) prop a ket(0) + b e^(i theta) ket(1)$.

Combining these gives
$
  "CZ"ket(psi)ket(+) &= 1/sqrt(2) ( ket(+_theta) tensor H R_z (-theta) ket(psi) + ket(-_theta) tensor X H R_z (-theta) ket(psi) )
$
Projecting onto $ket(plus.minus_theta)$ on qubit 1 yields the post-measurement
state $X^m H R_z (theta) ket(psi)$ on qubit 2, where $m=0$ if the measurement
outcome is $ket(+_theta)$ and $1$ otherwise.

This gives us a method to "teleport" the state of qubit 1 to qubit 2, with a
"byproduct" $X H R_z (-theta)$. Later we will see we can use this to build a
universal gate set, enabling universal computation in MBQC.

== Single-Qubit Rotation

Any single-qubit gate $U in "SU"(2)$ can be represented as a composition of
three rotations along two different axes, for example
$U(alpha,beta,gamma)=R_x (gamma) R_z (beta) R_x (alpha)$ where $R_x$ and $R_z$
represent rotations around the $X$ and $Z$ axis, respectively. This gate can be
implemented in MBQC using a linear path of 5 qubits $q_0, ..., q_4$ in a cluster
state, with an input $ket(psi)$ injected at $q_0$ and $q_4$ left unmeasured as
output. Measuring the qubits $q_0, ..., q_3$ in bases
$M(theta_0), ..., M(theta_3)$ respectively implements
$
  ket(psi) ket(+)ket(+)ket(+)ket(+) |-> ket(m_0)ket(m_1)ket(m_2)ket(m_3) tensor (X^(m_1+m_3)Z^(m_0+m_2)R_x (gamma) R_z (beta) R_x (alpha) ket(psi))
$
where
$
  theta_0 = 0, quad theta_1 = (-1)^(m_0+1)alpha, quad theta_2 = (-1)^(m_1)beta, quad theta_3=(-1)^(m_0+m_2)gamma
$
and $m_0, ..., m_3$ are the measurement results from $q_0, ..., q_3$. This
follows a direct computation using the relations $H R_z (theta) H = R_x (theta)$
and Pauli identities $X R_z (theta) = R_z (-theta) X$ and
$Z R_x (theta) = R_x (-theta) Z$.

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

