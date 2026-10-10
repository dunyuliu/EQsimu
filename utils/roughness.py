"""
Fault roughness for EQsimu problems: one surface y(x, z) on the problem's
fault grid, written as bFault_Rough_Geometry.txt, the file both EQquasi
(rough_fault = 1) and EQdyna (insertFaultType = 3) read.

A problem sets par.roughness to one of
    dict(kind="file", path="heights.txt")    heights from a file in the compset
    dict(kind="resample", path="heights.txt", from_dx=250.0, cutoff=2000.0)
                                             a file at a finer from_dx,
                                             low-passed and decimated to
                                             par.dx at problem-conversion
                                             time (no coarse file is kept)
    dict(kind="fractal", hurst=1.0, alpha=0.005, seed=1)
                                             EQdyna's synthetic surface
and leaves it None for a planar fault.

File format: "nnx nnz", "dx fxmin fzmin", then nnx*nnz rows "y dy/dx dy/dz"
with z varying fastest. The slopes are always np.gradient of the heights, the
form EQdyna's case.setup validates.
"""
import os

import numpy as np
from scipy.ndimage import gaussian_filter

FILENAME = "bFault_Rough_Geometry.txt"


def fault_grid(p):
    nfx = round((p.fxmax - p.fxmin)/p.dx) + 1
    nfz = round((p.fzmax - p.fzmin)/p.dx) + 1
    return (p.fxmin + p.dx*np.arange(nfx), p.fzmin + p.dx*np.arange(nfz))


def read(path):
    """(x, z, y) from a bFault_Rough_Geometry.txt-format file; y is [iz, ix]."""
    with open(path) as f:
        nnx, nnz = (int(float(s)) for s in f.readline().split()[:2])
        h, x0, z0 = (float(s) for s in f.readline().split()[:3])
    y = np.loadtxt(path, skiprows=2)[:, 0].reshape(nnx, nnz).T
    return x0 + h*np.arange(nnx), z0 + h*np.arange(nnz), y


def _place(p, x, z, y, label):
    """Place y [iz, ix] (on grid x, z, spaced at p.dx) onto the problem's
    full fault grid. Outside the box the edge values repeat, as EQquasi
    does. label names the source for error messages."""
    fx, fz = fault_grid(p)
    if not np.isclose(x[1] - x[0], p.dx):
        raise ValueError(f"{label}: spacing {x[1] - x[0]} != problem dx {p.dx}")
    ix, iz = round((x[0] - fx[0])/p.dx), round((z[0] - fz[0])/p.dx)
    if not (np.isclose(x[0], fx[0] + ix*p.dx) and np.isclose(z[0], fz[0] + iz*p.dx)):
        raise ValueError(f"{label}: origin is not on the fault grid")
    if ix < 0 or iz < 0 or ix + x.size > fx.size or iz + z.size > fz.size:
        raise ValueError(f"{label}: box is not inside the fault grid")
    return np.pad(y, ((iz, fz.size - iz - z.size), (ix, fx.size - ix - x.size)),
                  mode="edge")


def from_file(p, path):
    """Heights on the fault grid from a file sampled at p.dx on the same
    nodes. Outside the file's box the edge values repeat, as EQquasi does."""
    x, z, y = read(path)
    return _place(p, x, z, y, path)


def resample(x, z, y, from_dx, to_dx, cutoff=2000.0):
    """Low-pass y [iz, ix] at a cutoff wavelength (m, default 2 km) and
    decimate from from_dx to to_dx, a whole multiple of from_dx. Returns the
    new x, z, y on the coarser grid, same origin as the input.

    The low-pass is the real-space Gaussian equivalent to a Gaussian filter
    exp(-(k/kc)**2) in wavenumber space, applied with reflect (mirror)
    boundary handling before decimation, so wavelengths below the cutoff are
    attenuated rather than aliased by point-picking, and edges are not mixed
    with the opposite edge (an FFT convolution instead treats y as
    periodic, which corrupts the boundary rows/columns -- see
    PATHWAY_FORWARD.md). Slopes are never taken from this grid directly --
    recompute them with roughness.write()'s np.gradient on the returned y.

    Note: this Gaussian still passes ~37% amplitude at the 2 km Nyquist
    wavelength of a 1 km output grid (cutoff=2000.0 default); that is a
    known, separate gap, not fixed here.
    """
    step = to_dx/from_dx
    if not np.isclose(step, round(step)) or round(step) < 1:
        raise ValueError(f"resample: to_dx {to_dx} is not a whole multiple "
                          f"of from_dx {from_dx}")
    step = round(step)
    kc = 2*np.pi/cutoff
    sigma = np.sqrt(2)/kc/from_dx
    y_lp = gaussian_filter(y, sigma=sigma, mode="reflect")
    return x[::step], z[::step], y_lp[::step, ::step]


def fractal_surface(lx, hurst, seed):
    """EQdyna scripts/generateFaultInterface:generateFractalSurface, vectorized;
    identical output for the same lx, hurst and seed."""
    rng = np.random.RandomState(seed)
    transf = 0.5*np.sqrt(2.0)*(rng.normal(size=(lx, lx))
                               + 1j*rng.normal(size=(lx, lx)))
    k = np.arange(lx)
    k = np.where(k > lx//2, k - lx, k)
    ksq = (k[:, None]**2 + k[None, :]**2).astype(float)
    with np.errstate(divide="ignore"):
        pspec = np.where(ksq == 0, 0.0, 1.0/ksq**(hurst + 1.0))
    filt = 1.0/(1.0 + (ksq/(lx/4)**2)**4)
    transf[ksq <= 2] = 0.0
    return 0.25*np.real(np.fft.ifft2(np.sqrt(pspec*filt)*transf))


def fractal(p, hurst=1.0, alpha=0.005, seed=1):
    """EQdyna's insertFaultType 2 surface: rms height alpha*nfx*dx, cut from
    an nfx-by-nfx field."""
    fx, fz = fault_grid(p)
    if fz.size > fx.size:
        raise ValueError("fractal: the fault must be at least as long as deep")
    w = fractal_surface(fx.size, hurst, seed)
    return (w*alpha/(np.std(w)/fx.size/p.dx))[:fz.size, :fx.size]


def heights(p, compset_dir):
    """The problem's surface on its fault grid, or None for a planar fault."""
    r = p.roughness
    if r is None:
        return None
    r = dict(r)
    kind = r.pop("kind")
    if kind == "file":
        return from_file(p, os.path.join(compset_dir, r.pop("path")))
    if kind == "resample":
        path = os.path.join(compset_dir, r.pop("path"))
        from_dx = r.pop("from_dx")
        cutoff = r.pop("cutoff", 2000.0)
        x, z, y = read(path)
        x, z, y = resample(x, z, y, from_dx, p.dx, cutoff=cutoff)
        return _place(p, x, z, y, path)
    if kind == "fractal":
        return fractal(p, **r)
    raise ValueError(f"par.roughness: unknown kind {kind!r}")


def write(p, y, path):
    """Write y [iz, ix] and its np.gradient slopes in the shared format."""
    dydx = np.gradient(y, p.dx, axis=1)
    dydz = np.gradient(y, p.dx, axis=0)
    rows = np.stack([a.T.ravel() for a in (y, dydx, dydz)], axis=1)
    with open(path, "w") as f:
        f.write(f"{y.shape[1]}\t{y.shape[0]}\n"
                f"{p.dx:.6f}\t{p.fxmin:.6f}\t{p.fzmin:.6f}\n")
        np.savetxt(f, rows, fmt="%.7e", delimiter="\t")
