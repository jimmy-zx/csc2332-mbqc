from graphix import Pattern, Circuit
from graphix_ibmq.runner import IBMQBackend
from matplotlib import pyplot as plt

def gen_pattern(circ: Circuit):
    pattern = circ.transpile()
    pattern.standardize()
    pattern.shift_signals()
    # pattern.minimize_space()
    return pattern

def gen_mbqc(pattern: Pattern, filename):
    # use with modified graphix.visualization.visualize_w_flow
    pattern.draw_graph(filename=filename, save=True)

def gen_qiskit(pattern: Pattern, filename):
    backend = IBMQBackend(pattern)
    backend.to_qiskit()

    # remove initial reset and H gate of input qubit
    h_removed = {}
    reset_removed = {}
    new_data = []
    for instr, qbit, cbit in backend.circ.data:
        print(instr, qbit, cbit)
        q = qbit[0]
        if instr.name == 'h' and q._index == 0 and not h_removed.get(q, False):
            h_removed[q] = True
            continue
        if instr.name == 'reset' and q._index == 0 and not reset_removed.get(q, False):
            reset_removed[q] = True
            continue
        new_data.append((instr, qbit, cbit))

    backend.circ.data = new_data

    backend.circ.draw('mpl', filename=filename, initial_state=False, fold=50)
    plt.show()

def gen_both_circuits(circuit: Circuit, prefix: str):
    pattern = gen_pattern(circuit)
    gen_mbqc(pattern, f'{prefix}-mbqc.svg')
    gen_qiskit(pattern, f'{prefix}-qiskit.svg')
