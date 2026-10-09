"""
SEAS BP1001: coupled earthquake cycle (EQquasi interseismic + EQdyna
coseismic) on a rough vertical strike-slip fault, 250 m on-fault grid.
See README.md.
"""
from math import *
from problemDefaults import problem

par = problem()

par.mode = 2
par.istart, par.iend = 1, 1

par.fxmin, par.fxmax = -40.0e3, 40.0e3
par.fzmin, par.fzmax = -40.0e3, 0.0e3
par.dx = 250.0e0
par.roughness = dict(kind="file", path="rough_heights.250.txt")

par.vp, par.vs, par.rou = 6.0e3, 3.464e3, 2.67e3

par.friclaw = 3
par.fric_rsf_a, par.fric_rsf_b, par.fric_rsf_Dc = 0.004, 0.03, 0.14
par.fric_rsf_deltaa = 0.036
par.fric_rsf_r0 = 0.6
par.fric_rsf_v0 = 1e-6
par.init_norm = -25.0e6
par.creep_slip_rate = 1.0e-9

par.nt_out = 20

par.xmin_trans, par.xmax_trans = -25e3, 25e3
par.zmin_trans = -25e3
par.ymin_trans, par.ymax_trans = -5e3, 5e3
par.dx_trans = 50


def shear_steady_state(p, a, b, v0, r0, load_rate, norm, slip_rate):
    return (-norm*a*asinh(slip_rate/2.0/v0*exp((r0 + b*log(v0/load_rate))/a))
            + p.rou*p.vs/2.0*slip_rate)


def fault(p, x, z):
    # Velocity-weakening patch |x| <= 18 km, 4 <= |z| <= 16 km, tapering to
    # velocity-strengthening a + deltaa over 2 km.
    if abs(z) >= 18e3 or abs(x) >= 20e3 or abs(z) <= 2e3:
        a = p.fric_rsf_a + p.fric_rsf_deltaa
    elif abs(z) <= 16e3 and abs(z) >= 4e3 and abs(x) <= 18e3:
        a = p.fric_rsf_a
    else:
        tmp1 = (abs(abs(z) - 10e3) - 6e3)/2e3
        tmp2 = (abs(x) - 18e3)/2e3
        a = p.fric_rsf_a + max(tmp1, tmp2)*p.fric_rsf_deltaa
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
    casename="bp1001.fdc.qd",
    bp=1001,
    fymin=-10.0e3, fymax=10.0e3,
    xminc=-35.0e3, xmaxc=35.0e3, zminc=-35.0e3,
    nuni_y_plus=5, nuni_y_minus=5, enlarging_ratio=1.3e0,
    rheology=1,
    solver=1,
    xi=0.005,
    minDc=0.13,
    far_vel_load=4e-10,
    exit_slip_rate=0.2,
    fric_sw_fs=0, fric_sw_fd=0, fric_sw_D0=0,
    HPC_nnode=1, HPC_ncpu=30, HPC_queue="normal", HPC_time="20:00:00",
    HPC_account="EAR22012",
    st_coor_on_fault=[[-36.0, 0.0], [-16.0, 0.0], [0.0, 0.0], [16.0, 0.0],
                      [36.0, 0.0], [-24.0, 0.0], [-16.0, 0.0], [0.0, -10.0],
                      [16.0, -10.0], [0.0, -22.0]],
    st_coor_off_fault=[[0, 8, 0], [0, 8, -10], [0, 16, 0], [0, 16, -10],
                       [0, 32, 0], [0, 32, -10], [0, 48, 0], [16, 8, 0],
                       [-16, 8, 0]],
    az_op=2, az_maxiter=2000, az_tol=1.0e-7,
    C_normal_stress_caps=1,
)

par.eqdyna = dict(
    casename="bp1001.fdc.rough.250.dyna",
    tpv=1000,
    xmin=-60.0e3, xmax=60.0e3,
    ymin=-30.0e3, ymax=30.0e3,
    zmin=-60.0e3, zmax=0.0e3,
    fymin=0.0, fymax=0.0,
    xsource=-4.0e3, ysource=0.0, zsource=-7.5e3,
    nuni_y_plus=70, nuni_y_minus=70, enlarging_ratio=1.025e0,
    term=150.,
    dt=0.25*par.dx/par.vp,
    C_elastic=1, C_nuclea=0, C_degen=0,
    nucfault=-999,
    output_plastic=0,
    outputGroundMotion=1,
    nucR=3.e3, nucRuptVel=-9999., nucdtau0=45.0e6,
    nx=8, ny=4, nz=4,
    HPC_ncpu=128, HPC_nnode=2, HPC_queue="normal", HPC_time="02:00:00",
    HPC_account="EAR22012",
    st_coor_on_fault=[[0.0, -3.0], [0.0, -7.5], [0.0, -12.0], [9.0, -7.5],
                      [12.0, -3.0], [12.0, -12.0], [15.0, -7.5], [18.0, -7.5],
                      [-9.0, -7.5], [-12.0, -3.0], [-12.0, -12.0],
                      [-15.0, -7.5], [-18.0, -7.5]],
    st_coor_off_fault=[[0, 9, 0], [0, -9, 0], [12, 6, 0], [12, -6, 0],
                       [-12, 6, 0], [-12, -6, 0]],
)
