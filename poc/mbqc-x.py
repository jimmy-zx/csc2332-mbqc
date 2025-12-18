from graphix import Circuit

circ = Circuit(1)

circ.x(0)

# Transpile to MBQC pattern
pattern = circ.transpile().pattern
pattern.minimize_space()
pattern.standardize()

print(pattern.get_angles())
print(pattern.get_meas_plane())
pattern.draw_graph(flow_from_pattern=False, show_measurement_planes=True)
