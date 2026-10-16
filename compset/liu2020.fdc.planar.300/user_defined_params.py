"""
Liu et al. (2020): coupled earthquake cycle (EQquasi interseismic + EQdyna
coseismic) on a planar vertical strike-slip fault, 300 m on-fault grid.
See README.md.
"""
from math import *
from problemDefaults import problem

par = problem()

par.mode = 2
par.istart, par.iend = 1, 3

par.fxmin, par.fxmax = -30.0e3, 30.0e3
par.fzmin, par.fzmax = -30.0e3, 0.0e3
par.dx = 300.0e0
par.roughness = None

par.vp, par.vs, par.rou = 6.0e3, 3.464e3, 2.67e3

par.friclaw = 3
par.fric_rsf_a, par.fric_rsf_b, par.fric_rsf_Dc = 0.007, 0.011, 0.011
par.fric_rsf_deltaa = 0.01
par.fric_rsf_r0 = 0.6
par.fric_rsf_v0 = 1e-6
par.init_norm = -50.0e6
par.creep_slip_rate = 1.0e-9

# Neither native source (EQdyna's or EQquasi's) sets a caps switch for this
# planar case, so this stays at the old per-code rule. utils/problemDefaults.py's
# problem class has no default for this field (every other compset sets it
# explicitly to 1), so "leave at default" is written as the concrete -1
# sentinel convert.py's own COMMON comment names for this ("par.eqdyna's -1
# default keeps that rule for any compset that doesn't set this") rather than
# an unset attribute, which load_problem() would reject (missing, not None).
par.C_normal_stress_caps = -1

par.nt_out = 20

par.xmin_trans, par.xmax_trans = -25e3, 25e3
par.zmin_trans = -25e3
par.ymin_trans, par.ymax_trans = -5e3, 5e3
par.dx_trans = 50


def linear1(x, ww, w):
    # EQdyna/EQquasi scripts/lib.py's own taper: 1 inside |x| <= ww, linear
    # down to 0 over the next w, 0 beyond ww + w.
    if abs(x) <= ww:
        res = 1.0
    elif abs(x) > ww and abs(x) < ww + w:
        res = 1. - abs(abs(x) - ww)/w
    else:
        res = 0.0
    return res


def shear_steady_state(p, a, b, v0, r0, load_rate, norm, slip_rate):
    return (-norm*a*asinh(slip_rate/2.0/v0*exp((r0 + b*log(v0/load_rate))/a))
            + p.rou*p.vs/2.0*slip_rate)


def fault(p, x, z):
    # a tapers from fric_rsf_a (|x| <= 20 km and |z + 10 km| <= 7 km) up to
    # fric_rsf_a + fric_rsf_deltaa outside, linearly over 3 km in x and 1 km
    # in z (EQdyna/EQquasi native liu2020 files, both identical).
    tmp1 = linear1(x, 20.e3, 3.e3)
    tmp2 = linear1(-z - 10.0e3, 7.e3, 1.e3)
    a = p.fric_rsf_a + (1. - tmp1*tmp2)*p.fric_rsf_deltaa
    return dict(
        a=a, b=p.fric_rsf_b, Dc=p.fric_rsf_Dc,
        v0=p.fric_rsf_v0, f0=p.fric_rsf_r0,
        vini=p.creep_slip_rate,
        state=p.fric_rsf_Dc/p.creep_slip_rate,
        tnrm=p.init_norm,
        tstk=shear_steady_state(p, a, p.fric_rsf_b, p.fric_rsf_v0,
                                p.fric_rsf_r0, p.creep_slip_rate,
                                p.init_norm, p.creep_slip_rate))


par.fault = fault

par.eqquasi = dict(
    casename="liu2020.fdc.planar.300.quasi",
    bp=1000,
    fymin=-30.0e3, fymax=30.0e3,
    xminc=-25.0e3, xmaxc=25.0e3, zminc=-25.0e3,
    nuni_y_plus=10, nuni_y_minus=10, enlarging_ratio=1.3e0,
    rheology=1,
    solver=1,
    xi=0.02,
    minDc=11e-3,
    far_vel_load=5e-10,
    exit_slip_rate=1.5e-2,
    fric_sw_fs=0, fric_sw_fd=0, fric_sw_D0=0,
    # HPC_nnode/HPC_ncpu/HPC_queue/HPC_time/HPC_account are machine/launch
    # settings, not part of the problem -- utils/convert.py merges them in
    # from utils/machines.py, keyed by create.newcase's --machine flag.
    st_coor_on_fault=[[0.0, -3.0], [0.0, -7.5], [0.0, -12.0], [9.0, -7.5],
                      [12.0, -3.0], [12.0, -12.0], [15.0, -7.5], [18.0, -7.5],
                      [-9.0, -7.5], [-12.0, -3.0], [-12.0, -12.0],
                      [-15.0, -7.5], [-18.0, -7.5]],
    st_coor_off_fault=[[0, 9, 0], [0, -9, 0], [12, 6, 0], [12, -6, 0],
                       [-12, 6, 0], [-12, -6, 0]],
    az_op=2, az_maxiter=2000, az_tol=1.0e-7,
)

par.eqdyna = dict(
    casename="liu2020.fdc.planar.300.dyna",
    tpv=1000,
    xmin=-60.0e3, xmax=60.0e3,
    ymin=-30.0e3, ymax=30.0e3,
    zmin=-60.0e3, zmax=0.0e3,
    fymin=0.0, fymax=0.0,
    xsource=-4.0e3, ysource=0.0, zsource=-7.5e3,
    nuni_y_plus=70, nuni_y_minus=70, enlarging_ratio=1.025e0,
    term=150.,
    dt=0.5*par.dx/par.vp,
    C_elastic=1, C_nuclea=0, C_degen=0,
    nucfault=-999,
    output_plastic=0,
    outputGroundMotion=0,
    nucR=3.e3, nucRuptVel=-9999., nucdtau0=45.0e6,
    # nx/ny/nz (EQdyna's MPI process grid, nx*ny*nz == this code's own
    # HPC_ncpu) and HPC_nnode/HPC_ncpu/HPC_queue/HPC_time/HPC_account are
    # machine/launch settings, not part of the problem -- utils/convert.py
    # merges them in from utils/machines.py, keyed by create.newcase's
    # --machine flag.
    st_coor_on_fault=[[0.0, -3.0], [0.0, -7.5], [0.0, -12.0], [9.0, -7.5],
                      [12.0, -3.0], [12.0, -12.0], [15.0, -7.5], [18.0, -7.5],
                      [-9.0, -7.5], [-12.0, -3.0], [-12.0, -12.0],
                      [-15.0, -7.5], [-18.0, -7.5]],
    st_coor_off_fault=[[0, 9, 0], [0, -9, 0], [12, 6, 0], [12, -6, 0],
                       [-12, 6, 0], [-12, -6, 0]],
)
