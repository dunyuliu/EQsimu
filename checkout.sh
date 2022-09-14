# /usr/bin/bash 

# check out EQquasi as the interseis component
mkdir components
mkdir bin

cd components 
git clone https://github.com/dunyuliu/EQquasi.git eqquasi
cd eqquasi 
source install-eqquasi.sh
cp bin/eqquasi ../../bin/
cd .. # back to components

git clone https://github.com/wangyf/sordw3 sord
cd sord
cd src
cp makefile_mpi makefile
make
cp sord-mO ../../../bin/
cd ../../.. # back to components
