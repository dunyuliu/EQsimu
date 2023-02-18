# /usr/bin/bash 

# check out EQquasi as the interseis component
export ESCIROOT=$(pwd)
echo   $ESCIROOT

rm -rf components bin

mkdir components
mkdir bin

cd components 

# download and install EQquasi
git clone https://github.com/dunyuliu/EQquasi.git eqquasi
cd eqquasi 
source install-eqquasi.sh
cp bin/eqquasi ../../bin/
cd .. # back to components


# download and install EQdyna
git clone https://github.com/dunyuliu/EQdyna.git eqdyna
cd eqdyna
source install-eqdyna.sh
cp bin/eqdyna ../../bin/
cd .. # back to components

# download and install SORD
git clone https://github.com/wangyf/sordw3 sord
cd sord
cd src
cp makefile_mpi makefile
make
cp sord-mO ../../../bin/
cd ../../.. # back to components
