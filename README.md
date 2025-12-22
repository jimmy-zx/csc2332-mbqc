# Simulation of MBQC and UBQC
A Qiskit-Based MBQC Implementation of the Two-Qubit Quantum Fourier Transform

## Report

Report in [report.typ](report/report.typ),
compiled versions can be found in [releases](https://github.com/jimmy-zx/csc2332-mbqc/releases).

## MBQC Transpiler

See [convert](convert) for source code and [test_convert.py](convert/tests/test_convert.py)
for examples.

Interfaces in [convert.py](convert/convert.py):
- `serialize` converts a quantum circuit to a list of descriptors.
- `generate` converts descriptors to a MBQC-based circuit, a mapping of outputs, and a graph for MBQC cluster states.
