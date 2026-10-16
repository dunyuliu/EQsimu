"""
Liu et al. (2020): coupled earthquake cycle (EQquasi interseismic + EQdyna
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
par.fric_rsf_a, par.fric_rsf_b, par.fric_rsf_Dc = 0.007, 0.011, 0.011
par.fric_rsf_deltaa = 0.01
par.fric_rsf_r0 = 0.6
par.fric_rsf_v0 = 1e-6
# EQdyna's native liu2020.fdc.rough.250/user_defined_params.py sets
# init_norm = -50.0e6, same as EQdyna's native bp1001.fdc.rough.250 file --
# the same sigma_n drift PROJECT_RULES.md rule 7 documents (bp1001:
# -25 vs -50 MPa). EQquasi's own native liu2020.fdc.rough.250 file already
# uses -25.0e6, same as it does for bp1001. Following the bp1001.fdc.rough.250
# precedent already established in this repo, this compset uses EQquasi's
# value (-25.0e6) as the single canonical input for both codes.
par.init_norm = -25.0e6
par.creep_slip_rate = 1.0e-9

# EQdyna's native file sets nt_out = 20, EQquasi's native file sets 100;
# nt_out is in convert.py's COMMON (both codes read the same value), so one
# canonical value must be picked. bp1001.fdc.rough.250 picked EQdyna's
# value (20, the output/restart cadence EQdyna actually ran the paper with);
# followed here for the same reason -- not reconciled further.
par.nt_out = 20

par.xmin_trans, par.xmax_trans = -25e3, 25e3
par.zmin_trans = -25e3
par.ymin_trans, par.ymax_trans = -5e3, 5e3
par.dx_trans = 50

# Both codes read this identically (EQdyna pin >= 29774c3). EQquasi's own
# native liu2020.fdc.rough.250 file already carries this explicit switch at
# its tail (caps historically implied by rough_fault); EQdyna's native file
# has rough_fault/insertFaultType = 3 with no separate switch. Carried
# through explicitly on the shared par, same as bp1001.fdc.rough.250.
par.C_normal_stress_caps = 1


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
    casename="liu2020.fdc.rough.250.quasi",
    bp=1000,
    fymin=-10.0e3, fymax=10.0e3,
    xminc=-35.0e3, xmaxc=35.0e3, zminc=-35.0e3,
    nuni_y_plus=5, nuni_y_minus=5, enlarging_ratio=1.3e0,
    rheology=1,
    solver=1,
    xi=0.005,
    minDc=11e-3,
    far_vel_load=5e-10,
    exit_slip_rate=1.5e-2,
    fric_sw_fs=0, fric_sw_fd=0, fric_sw_D0=0,
    # HPC_nnode/HPC_ncpu/HPC_queue/HPC_time/HPC_account are machine/launch
    # settings, not part of the problem -- utils/convert.py merges them in
    # from utils/machines.py, keyed by create.newcase's --machine flag.
    # HPC_email: no personal emails in this repo (CLAUDE.md); EQquasi's
    # native file carried one, left unset here, same as bp1001.fdc.rough.250.
    st_coor_on_fault=[[0.0, -3.0], [0.0, -7.5], [0.0, -12.0], [9.0, -7.5],
                      [12.0, -3.0], [12.0, -12.0], [15.0, -7.5], [18.0, -7.5],
                      [-9.0, -7.5], [-12.0, -3.0], [-12.0, -12.0],
                      [-15.0, -7.5], [-18.0, -7.5]],
    st_coor_off_fault=[[0, 9, 0], [0, -9, 0], [12, 6, 0], [12, -6, 0],
                       [-12, 6, 0], [-12, -6, 0]],
    az_op=2, az_maxiter=2000, az_tol=1.0e-7,
)

par.eqdyna = dict(
    casename="liu2020.fdc.rough.250.dyna",
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
    outputGroundMotion=1,
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
