#!/bin/bash
# EQsimu: check out EQquasi and EQdyna at the commits pinned in
# components.txt, build them with their own install scripts, and set the
# environment.
#
#   ./checkout.sh -i <mach>   clone + build into components/   (ls6, local, ...)
#   ./checkout.sh -u <mach>   move existing checkouts to the pins + rebuild
#   source checkout.sh        set EQSIMUROOT, EQQUASIROOT, EQDYNAROOT, PATH
#
# <mach> is passed straight to each component's install script (-m <mach>),
# except local: a workstation building both codes from the conda env at
# $CONDA_PREFIX (set it, no activation needed). EQquasi builds as conda-linux;
# EQdyna's installer has no conda target, so its makefile is run directly.
# local also makes components/venv (the env's python plus scipy, which only
# EQsimu's utils/roughness.py needs), so the shared env is left untouched.

EQSIMUROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export EQSIMUROOT
export EQQUASIROOT=$EQSIMUROOT/components/eqquasi
export EQDYNAROOT=$EQSIMUROOT/components/eqdyna
export PATH=$EQSIMUROOT/utils:$EQQUASIROOT/bin:$EQQUASIROOT/scripts:$EQDYNAROOT/bin:$PATH
[ -x "$EQSIMUROOT/components/venv/bin/python3" ] && export PATH=$EQSIMUROOT/components/venv/bin:$PATH

usage() {
    sed -n '2,15p' "$EQSIMUROOT/checkout.sh" | sed 's/^# \{0,1\}//'
}

MACH=""
MODE=""
OPTIND=1
while getopts "hi:u:" OPTION; do
    case $OPTION in
        i) MACH=$OPTARG; MODE=install ;;
        u) MACH=$OPTARG; MODE=update ;;
        h) usage ;;
        *) usage; return 1 2>/dev/null || exit 1 ;;
    esac
done

# Sourced with no flags: environment only.
[ -z "$MODE" ] && { return 0 2>/dev/null || exit 0; }

set -e
cd "$EQSIMUROOT"
[ "$MODE" = install ] && rm -rf components
mkdir -p components

grep -v '^#' components.txt | while read -r name repo commit; do
    [ -z "$name" ] && continue
    dir=components/$name
    if [ "$MODE" = install ]; then
        git clone "$repo" "$dir"
    elif [ ! -d "$dir/.git" ]; then
        echo "checkout.sh: $dir missing; run ./checkout.sh -i $MACH" >&2
        exit 1
    else
        git -C "$dir" fetch origin
    fi
    git -C "$dir" checkout --detach "$commit"
    echo "$name at $(git -C "$dir" rev-parse HEAD)"
done

if [ "$MACH" = local ]; then
    CP=${CONDA_PREFIX:?checkout.sh: local needs CONDA_PREFIX, the conda env to build from}
    export PATH=$CP/bin:$PATH
    (cd components/eqquasi && bash install.eqquasi.sh -m conda-linux)
    (cd components/eqdyna/src/fortran && MACHINE=ubuntu make LIB="$CP/lib" INC="$CP/include" \
        NETCDF_INC="-I$CP/include" NETCDF_LIB="-L$CP/lib -Wl,-rpath,$CP/lib -lnetcdf -lnetcdff")
    mkdir -p components/eqdyna/bin
    mv components/eqdyna/src/fortran/eqdyna components/eqdyna/bin/
    "$CP/bin/python3" -m venv --system-site-packages components/venv
    components/venv/bin/pip install -q scipy
else
    (cd components/eqquasi && bash install.eqquasi.sh -m "$MACH")
    (cd components/eqdyna  && bash install-eqdyna.sh  -m "$MACH")
fi
echo "EQsimu ready. Run: source checkout.sh"
