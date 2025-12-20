from graphix import Circuit
from graphix_ibmq.runner import IBMQBackend
from matplotlib import pyplot as plt

circ = Circuit(1)

circ.h(0)

# Transpile to MBQC pattern
pattern = circ.transpile()
pattern.minimize_space()
pattern.standardize()

print(pattern.get_angles())
print(pattern.get_meas_plane())
# pattern.draw_graph()

backend = IBMQBackend(pattern)
backend.to_qiskit()
backend.circ.draw('mpl')
plt.show()
