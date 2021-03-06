# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 10:37:36 2017

@author: witte
"""

from tespy import con, cmp, nwk
import numpy as np
from matplotlib import pyplot as plt
import pandas as pd

# %% network

fluid_list = ['H2O']
nw = nwk.network(fluids=fluid_list, p_unit='bar', T_unit='C')

# %% components

# sinks & sources
back = cmp.source('to collector')
feed = cmp.sink('from collector')

# collector
coll = cmp.solar_collector(label='solar thermal collector')

# %% connections

b_c = con.connection(back, 'out1', coll, 'in1')
c_f = con.connection(coll, 'out1', feed, 'in1')

nw.add_conns(b_c, c_f)

# %% component parameters

# set pressure ratio and heat flow, as well as dimensional parameters of
# the collector. E is missing, thus energy balance for radiation is not
# performed at this point
coll.set_attr(pr=0.99, Q=8e3, lkf_lin=1, lkf_quad=0.005, A=10, Tamb=10)

# %% connection parameters

b_c.set_attr(p=5, T=20, fluid={'H2O': 1})
c_f.set_attr(p0=2, T=120)

# %% solving

# going through several parametrisation possibilities
mode = 'design'
nw.solve(mode=mode)
nw.print_results()

# set absorption instead of outlet temperature
coll.set_attr(E=9e2)
c_f.set_attr(T=np.nan)

nw.solve(mode=mode)
nw.print_results()

# set outlet temperature and mass flow instead of heat flow and radiation
coll.set_attr(Q=np.nan, E=np.nan)
c_f.set_attr(T=100, m=1e-1)

nw.solve(mode=mode)
nw.print_results()
nw.save('SC')

# looping over different ambient temperatures and levels of absorption
# (of the inclined surface) assuming constant mass flow

# set print_level to none
nw.set_printoptions(print_level='none')
mode = 'offdesign'
c_f.set_attr(T=np.nan)

gridnum = 10
T_amb = np.linspace(-10, 30, gridnum, dtype=float)
E_glob = np.linspace(100, 1000, gridnum, dtype=float)

df = pd.DataFrame(columns=T_amb)

for E in E_glob:
    eta = []
    coll.set_attr(E=E)
    for T in T_amb:
        coll.set_attr(Tamb=T)
        nw.solve(mode=mode, design_path='SC')
        eta += [coll.Q.val / (coll.E.val * coll.A.val)]
        # cut out efficiencies smaller than zero
        if eta[-1] < 0:
            eta[-1] = np.nan

    df.loc[E] = eta

E, T = np.meshgrid(T_amb, E_glob)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot_wireframe(E, T, df.as_matrix())
# temperature difference -> mean collector temperature to ambient temperature
ax.set_xlabel('ambient temperature t_a in °C')
# absorption on the inclined surface
ax.set_ylabel('absorption E in $\mathrm{\\frac{W}{m^2}}$')
# thermal efficiency (no optical losses)
ax.set_zlabel('efficiency $\eta$')
plt.show()
