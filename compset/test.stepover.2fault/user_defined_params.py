"""
test.stepover.2fault: a planar 2-fault (ntotft=2) stepover, EQsimu-side.

Not a physical benchmark -- it exists to exercise utils/convert.py's
multi-fault path end to end:
par.faultgeom (one 5-tuple per fault) and a per-fault fault(p, x, z, ift)
feed both codes' own conventions --

  EQquasi : par.faultgeom 5-tuples unchanged, par.fxmin/fxmax/fzmin/fzmax
            overridden to the union, on_fault_vars (ntotft, nfzMax, nfxMax,
            100) zero-padded per fault, one combined st_coor_on_fault list.
  EQdyna  : par.faultgeom 6-tuples (ycoor duplicated into fymin/fymax),
            par.fxmin/fxmax/fzmin/fzmax left as fault 1's own box (legacy
            single-fault fields), par.onFaultVarsPerFault /
            par.st_coor_on_fault_per_fault as the real per-fault arrays.

Geometry (m), right-lateral, releasing step-over:
  fault 0: x in [-20e3,   0e3], y =     0,  z in [-10e3, 0]   (20 km long)
  fault 1: x in [ -5e3,  20e3], y = -2.0e3, z in [-10e3, 0]   (25 km long,
           so nfxMax > fault 0's own nfx -- exercises the zero-padding)
dx = 1000 m: every fault bound and the 2 km stepover offset is a whole
multiple of dx from the union origin (-20e3, -10e3), as both codes'
mesh generators require.
"""
from math import *
from problemDefaults import problem

par = problem()

par.mode = 1  # quasi-dynamic only; this compset is qdc/dr-equivalent, not
              # fdc (the restart bridge is a separate, blocked board row)
par.istart, par.iend = 1, 1

par.ntotft = 2
FAULT_A = (-20.0e3, 0.0e3, 0.0, -10.0e3, 0.0e3)
FAULT_B = (-5.0e3, 20.0e3, -2.0e3, -10.0e3, 0.0e3)
par.faultgeom = [FAULT_A, FAULT_B]
par.dx = 1000.0e0
par.roughness = None  # must be planar: EQdyna refuses rough + ntotft>1

par.vp, par.vs, par.rou = 6.0e3, 3.464e3, 2.67e3

par.friclaw = 3
par.fric_rsf_a, par.fric_rsf_b, par.fric_rsf_Dc = 0.004, 0.03, 0.14
par.fric_rsf_deltaa = 0.036
par.fric_rsf_r0 = 0.6
par.fric_rsf_v0 = 1e-6
par.init_norm = -25.0e6
par.creep_slip_rate = 1.0e-9

par.nt_out = 20

par.xmin_trans, par.xmax_trans = -15e3, 15e3
par.zmin_trans = -10e3
par.ymin_trans, par.ymax_trans = -5e3, 5e3
par.dx_trans = 50


def shear_steady_state(p, a, b, v0, r0, load_rate, norm, slip_rate):
    return (-norm*a*asinh(slip_rate/2.0/v0*exp((r0 + b*log(v0/load_rate))/a))
            + p.rou*p.vs/2.0*slip_rate)


def fault(p, x, z, ift):
    # Simple velocity-weakening core, |z| <= 8 km, else velocity-strengthening.
    # init_norm differs by 2 MPa per fault so a convert.py bug that aliases
    # fault 0's array onto fault 1 (or vice versa) shows up as the wrong
    # constant on the wrong fault's nodes (same check test.stepover.qdc.1000
    # uses upstream).
    a = p.fric_rsf_a if abs(z) <= 8e3 else p.fric_rsf_a + p.fric_rsf_deltaa
    tnrm = p.init_norm - ift*2.0e6
    return dict(
        a=a, b=p.fric_rsf_b, Dc=p.fric_rsf_Dc,
        v0=p.fric_rsf_v0, f0=p.fric_rsf_r0,
        vini=p.creep_slip_rate,
        state=p.fric_rsf_Dc/p.creep_slip_rate,
        tnrm=tnrm,
        tstk=shear_steady_state(p, a, p.fric_rsf_b, p.fric_rsf_v0,
                                p.fric_rsf_r0, p.creep_slip_rate,
                                tnrm, p.creep_slip_rate))


par.fault = fault

par.eqquasi = dict(
    casename="test.stepover.2fault.qd",
    bp=0,
    fymin=-15.0e3, fymax=15.0e3,
    xminc=-20.0e3, xmaxc=20.0e3, zminc=-10.0e3,
    nuni_y_plus=5, nuni_y_minus=5, enlarging_ratio=1.3e0,
    rheology=1,
    solver=1,
    xi=0.015,
    minDc=0.13,
    far_vel_load=4e-10,
    exit_slip_rate=1.0e-3,
    fric_sw_fs=0, fric_sw_fd=0, fric_sw_D0=0,
    HPC_nnode=1, HPC_ncpu=2, HPC_queue="normal", HPC_time="00:30:00",
    HPC_account="EAR22013",
    st_coor_on_fault=[[-10.0, -2.0], [0.0, -2.0], [5.0, -2.0]],
    st_coor_off_fault=[[0, 5, 0], [0, 5, -5]],
    az_op=2, az_maxiter=2000, az_tol=1.0e-7,
)

par.eqdyna = dict(
    casename="test.stepover.2fault.dyna",
    tpv=1000,
    xmin=-30.0e3, xmax=30.0e3,
    ymin=-15.0e3, ymax=15.0e3,
    zmin=-20.0e3, zmax=0.0e3,
    xsource=-10.0e3, ysource=0.0, zsource=-5.0e3,
    nuni_y_plus=10, nuni_y_minus=10, enlarging_ratio=1.025e0,
    term=5.,
    dt=0.5*par.dx/par.vp,
    C_elastic=1, C_nuclea=0, C_degen=0,
    nucfault=1,
    output_plastic=0,
    outputGroundMotion=0,
    nucR=3.e3, nucRuptVel=-9999., nucdtau0=45.0e6,
    nx=2, ny=2, nz=1,
    HPC_ncpu=4, HPC_nnode=1, HPC_queue="normal", HPC_time="00:10:00",
    HPC_account="EAR22013",
    st_coor_on_fault_per_fault=[
        [[-10.0, -2.0], [0.0, -2.0]],
        [[0.0, -2.0], [10.0, -2.0], [15.0, -2.0]],
    ],
    st_coor_off_fault=[[0, 5, 0], [0, -5, 0]],
)
