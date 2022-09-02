# /usr/bin/bash 

# check out EQquasi as the interseis component
mkdir components
cd components 
git clone https://github.com/dunyuliu/EQquasi.git eqquasi
cd eqquasi 
source install-eqquasi.sh
cd .. # back to components

git clone https://github.com/wangyf/SORDlatest.git sord
cd .. # back to components