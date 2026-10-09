#! /usr/bin/env python3
"""
plot_problem.py COMPSET_DIR

Draw the problem a compset defines (setup.png in COMPSET_DIR): the fault
plane coloured by a - b with the transfer box, the fault-roughness heights
on the fault grid (utils/roughness.py), and the a, b and initial shear stress at x = 0.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.dont_write_bytecode = True
import convert
import roughness


def fault_fields(par):
    fx = np.arange(par.fxmin, par.fxmax + par.dx/2, par.dx)
    fz = np.arange(par.fzmin, par.fzmax + par.dx/2, par.dx)
    keys = ("a", "b", "tstk")
    out = {k: np.zeros((fz.size, fx.size)) for k in keys}
    for ix, x in enumerate(fx):
        for iz, z in enumerate(fz):
            v = par.fault(par, x, z)
            for k in keys:
                out[k][iz, ix] = v[k]
    return fx, fz, out


def main(compset_dir):
    par, _ = convert.load_problem(compset_dir)
    fx, fz, f = fault_fields(par)
    km = 1e-3
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.8),
                           gridspec_kw=dict(width_ratios=[1.6, 1.6, 1]),
                           layout="constrained")

    amb = f["a"] - f["b"]
    lim = np.abs(amb).max()
    im = ax[0].pcolormesh(fx*km, fz*km, amb, cmap="RdBu_r", vmin=-lim,
                          vmax=lim, shading="nearest")
    fig.colorbar(im, ax=ax[0], label="a − b")
    box = dict(fill=False, lw=1.2)
    ax[0].add_patch(plt.Rectangle((par.xmin_trans*km, par.zmin_trans*km),
                    (par.xmax_trans - par.xmin_trans)*km, -par.zmin_trans*km,
                    ec="k", ls="--", **box))
    ax[0].plot([], [], "k--", label="transfer box")
    y = roughness.heights(par, compset_dir)
    if y is not None:
        if par.roughness["kind"] == "file":
            rx, rz, _ = roughness.read(
                os.path.join(compset_dir, par.roughness["path"]))
            ax[0].add_patch(plt.Rectangle((rx[0]*km, rz[0]*km),
                            (rx[-1] - rx[0])*km, (rz[-1] - rz[0])*km,
                            ec="tab:green", **box))
            ax[0].plot([], [], color="tab:green", label="heights file")
        im = ax[1].pcolormesh(fx*km, fz*km, y, cmap="viridis",
                              shading="nearest")
        fig.colorbar(im, ax=ax[1], label="fault-normal offset y (m)")
        ax[1].set_title(f"roughness ({par.roughness['kind']})")
    else:
        ax[1].text(0.5, 0.5, "planar fault", ha="center",
                   transform=ax[1].transAxes)
    ax[0].legend(loc="lower left", fontsize=8)
    ax[0].set_title("fault plane: a − b")
    for a in ax[:2]:
        a.set_xlabel("along strike x (km)")
        a.set_ylabel("depth z (km)")
        a.set_aspect("equal")

    i0 = np.argmin(np.abs(fx))
    ax[2].plot(f["a"][:, i0], fz*km, label="a")
    ax[2].plot(f["b"][:, i0], fz*km, label="b")
    ax[2].set_xlabel("RSF parameter")
    ax[2].set_ylabel("depth z (km)")
    t = ax[2].twiny()
    t.plot(f["tstk"][:, i0]*1e-6, fz*km, "k:", label="τ₀")
    t.set_xlabel("initial shear stress τ₀ (MPa)")
    lines = ax[2].get_lines() + t.get_lines()
    ax[2].legend(lines, [l.get_label() for l in lines], fontsize=8,
                 loc="lower right")
    ax[2].set_title("profile at x = 0", pad=28)

    out = os.path.join(compset_dir, "setup.png")
    fig.savefig(out, dpi=150)
    print(out)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
