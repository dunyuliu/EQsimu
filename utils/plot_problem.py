#! /usr/bin/env python3
"""
plot_problem.py COMPSET_DIR

Draw the problem a compset defines (setup.png in COMPSET_DIR): the fault
plane coloured by a - b with the transfer box, the fault-roughness heights
on the fault grid (utils/roughness.py), and the a, b and initial shear stress at x = 0.

Multi-fault (par.ntotft > 1, par.faultgeom set -- PATHWAY_FORWARD.md board P3):
each fault gets its own (fx, fz) grid from its own par.faultgeom[ift] box and
its own par.fault(par, x, z, ift) call (convert.py's own multi-fault
convention; par.roughness is always None here -- convert.py refuses
roughness + ntotft>1 -- so there is no roughness panel to generalize). The
a - b panel is repeated once per fault, left to right, each at its own
physical extent/aspect; the depth profile (middle-right panels in the
single-fault layout) is drawn for fault 0 only, labelled accordingly.
"""
import inspect
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.dont_write_bytecode = True
import convert
import roughness


def _fault_grid(par, fxmin, fxmax, fzmin, fzmax):
    fx = np.arange(fxmin, fxmax + par.dx/2, par.dx)
    fz = np.arange(fzmin, fzmax + par.dx/2, par.dx)
    return fx, fz


def fault_fields(par, ift=0, box=None):
    """a, b, tstk on fault ift's own grid. box, if given, overrides the
    (fxmin, fxmax, fzmin, fzmax) read off par (used for ntotft > 1, where
    par.fxmin/fxmax/fzmin/fzmax hold only fault 0's box)."""
    if box is None:
        box = (par.fxmin, par.fxmax, par.fzmin, par.fzmax)
    fx, fz = _fault_grid(par, *box)
    keys = ("a", "b", "tstk")
    out = {k: np.zeros((fz.size, fx.size)) for k in keys}
    call_ift = len(inspect.signature(par.fault).parameters) >= 4
    for ix, x in enumerate(fx):
        for iz, z in enumerate(fz):
            v = par.fault(par, x, z, ift) if call_ift else par.fault(par, x, z)
            for k in keys:
                out[k][iz, ix] = v[k]
    return fx, fz, out


def main(compset_dir):
    par, _ = convert.load_problem(compset_dir)
    km = 1e-3
    multi = par.ntotft > 1

    if not multi:
        faults = [fault_fields(par)]
    else:
        faults = [fault_fields(par, ift, box=(xlo, xhi, zlo, zhi))
                  for ift, (xlo, xhi, ycoor, zlo, zhi) in enumerate(par.faultgeom)]

    n_amb_panels = len(faults) if multi else 1
    if multi:
        width_ratios = [1.6]*n_amb_panels + [1]
        figsize = (4.3*n_amb_panels + 3.3, 3.8)
    else:
        width_ratios = [1.6, 1.6, 1]
        figsize = (13, 3.8)
    fig, ax = plt.subplots(1, n_amb_panels + (2 if not multi else 1),
                           figsize=figsize,
                           gridspec_kw=dict(width_ratios=width_ratios),
                           layout="constrained")
    ax = np.atleast_1d(ax)
    amb_ax = ax[:n_amb_panels]
    prof_ax = ax[n_amb_panels] if multi else ax[2]

    for i, (fx, fz, f) in enumerate(faults):
        a = amb_ax[i]
        amb = f["a"] - f["b"]
        lim = np.abs(amb).max()
        im = a.pcolormesh(fx*km, fz*km, amb, cmap="RdBu_r", vmin=-lim,
                          vmax=lim, shading="nearest")
        fig.colorbar(im, ax=a, label="a − b")
        a.set_xlabel("along strike x (km)")
        a.set_ylabel("depth z (km)")
        a.set_aspect("equal")
        a.set_title(f"fault {i}: a − b" if multi else "fault plane: a − b")

    if not multi:
        par0 = par
        a0 = amb_ax[0]
        box = dict(fill=False, lw=1.2)
        a0.add_patch(plt.Rectangle((par0.xmin_trans*km, par0.zmin_trans*km),
                        (par0.xmax_trans - par0.xmin_trans)*km,
                        -par0.zmin_trans*km, ec="k", ls="--", **box))
        a0.plot([], [], "k--", label="transfer box")
        y = roughness.heights(par, compset_dir)
        rough_ax = ax[1]
        if y is not None:
            if par.roughness["kind"] == "file":
                rx, rz, _ = roughness.read(
                    os.path.join(compset_dir, par.roughness["path"]))
                a0.add_patch(plt.Rectangle((rx[0]*km, rz[0]*km),
                                (rx[-1] - rx[0])*km, (rz[-1] - rz[0])*km,
                                ec="tab:green", **box))
                a0.plot([], [], color="tab:green", label="heights file")
            fx, fz, _ = faults[0]
            im = rough_ax.pcolormesh(fx*km, fz*km, y, cmap="viridis",
                                  shading="nearest")
            fig.colorbar(im, ax=rough_ax, label="fault-normal offset y (m)")
            rough_ax.set_title(f"roughness ({par.roughness['kind']})")
        else:
            rough_ax.text(0.5, 0.5, "planar fault", ha="center",
                       transform=rough_ax.transAxes)
        a0.legend(loc="lower left", fontsize=8)
        rough_ax.set_xlabel("along strike x (km)")
        rough_ax.set_ylabel("depth z (km)")
        rough_ax.set_aspect("equal")

    fx0, fz0, f0 = faults[0]
    i0 = np.argmin(np.abs(fx0))
    prof_ax.plot(f0["a"][:, i0], fz0*km, label="a")
    prof_ax.plot(f0["b"][:, i0], fz0*km, label="b")
    prof_ax.set_xlabel("RSF parameter")
    prof_ax.set_ylabel("depth z (km)")
    t = prof_ax.twiny()
    t.plot(f0["tstk"][:, i0]*1e-6, fz0*km, "k:", label="τ₀")
    t.set_xlabel("initial shear stress τ₀ (MPa)")
    lines = prof_ax.get_lines() + t.get_lines()
    prof_ax.legend(lines, [l.get_label() for l in lines], fontsize=8,
                 loc="lower right")
    prof_ax.set_title("fault 0 profile at x = 0" if multi
                       else "profile at x = 0", pad=28)

    out = os.path.join(compset_dir, "setup.png")
    fig.savefig(out, dpi=150)
    print(out)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
