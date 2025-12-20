from graphix import Circuit
from circuit_visualizer import *
from typing import Optional
from sys import argv
from numpy import pi

circ_fn_dict = {}

def circ_fn(fn, name: Optional[str] = None):
    if name is None:
        name = fn.__name__
    circ_fn_dict[name] = fn
    return fn

@circ_fn
def h():
    c = Circuit(1)
    c.h(0)
    return c

@circ_fn
def rz():
    c = Circuit(1)
    c.rz(0, pi/4)
    return c

@circ_fn
def cnot():
    c = Circuit(2)
    c.cnot(1, 0)
    return c

if __name__ == '__main__':
    if len(argv) > 1:
        circ_name = argv[1]
        get_circ = circ_fn_dict[circ_name]
        gen_both_circuits(get_circ(), circ_name)
    else:
        for circ_name, get_circ in circ_fn_dict.items():
            gen_both_circuits(get_circ(), circ_name)
    
