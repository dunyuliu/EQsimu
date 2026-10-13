#!/bin/bash
# EQsimu: check out EQquasi and EQdyna at the commits pinned in
# components.txt, build them with their own install scripts, and set the
# environment.
#
#   ./checkout.sh -i <mach>   clone + build into components/   (ls6, ubuntu, ...)
#   ./checkout.sh -u <mach>   move existing checkouts to the pins + rebuild
#   source checkout.sh        set EQSIMUROOT, EQQUASIROOT, EQDYNAROOT, PATH
#
# <mach> is passed straight to each component's install script (-m <mach>).

EQSIMUROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export EQSIMUROOT
export EQQUASIROOT=$EQSIMUROOT/components/eqquasi
export EQDYNAROOT=$EQSIMUROOT/components/eqdyna
export PATH=$EQSIMUROOT/utils:$EQQUASIROOT/bin:$EQQUASIROOT/scripts:$EQDYNAROOT/bin:$PATH

usage() {
    sed -n '2,10p' "$EQSIMUROOT/checkout.sh" | sed 's/^# \{0,1\}//'
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

(cd components/eqquasi && bash install.eqquasi.sh -m "$MACH")
(cd components/eqdyna  && bash install-eqdyna.sh  -m "$MACH")
echo "EQsimu ready. Run: source checkout.sh"
