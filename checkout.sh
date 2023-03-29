# /bin/bash 

# The shell script is to check out components contained in ESCI.
# Currently, it has EQdyna, EQquasi, and SORD.

echo "    Welcome to ESCI                                                 "
echo "                                                                    "
echo "    ESCI supports EQdyna, EQquasi, and SORD                         "
echo "       on ls6 and ubuntu                                            " 
echo "                                                                    "
echo "    To checkout ESCI on a specific machine, please tpye             "
echo "       git https://github.com/dunyuliu/ESCI.git                     "
echo "       chmod 755 checkout.sh                                        "
echo "       ./checkout -h                                                "

# It will create folders /components that host src of different tools
# and /bin to host executables.

# Currently, the machines supported are:
#	ls6:	Lonestar6 at TACC
#	ubuntu: Ubuntu 22.04

# setting up environment variables 
#echo " =                                                           ="
#echo " =    To set up environment variables                        ="
#echo " =        ESCIROOT, EQQUASIROOT, EQDYNAROOT                  ="
#echo " =    and adding executables to PATH                         ="
#echo " =    Please 'source checkout.sh'                            ="

export ESCIROOT=$(pwd)
export EQDYNAROOT=$(pwd)/components/eqdyna
export EQQYASIROOT=$(pwd)/components/eqquasi
export PATH=$(pwd)/bin:$PATH
echo ESCIROOT
echo PATH

while getopts "hi:u:" OPTION; do
    case $OPTION in
        i)
            MACH=$OPTARG
            UPDATE="False"
            ;;
        u)
            MACH=$OPTARG
            UPDATE="True"
            ;;
        h)
            echo "Usage: ./checkout.sh [-h] [-i Machine_name] [-u Machine_name]        "
            echo "                                                                     "
            echo "Examples:                                                            "
            echo "                                                                     "
            echo "./checkout.sh -h                                                     "
            echo " -----Display this help message                                      "
            echo "                                                                     "
            echo "./checkout.sh -i ls6                                                 "
            echo " -----Install ESCI on Lonestar6 at TACC                              "
            echo "                                                                     "
            echo "./checkout.sh -u ubuntu                                              "
            echo " -----Update all components with git pull                            "
            echo " -----on ubuntu                                                      "
            echo "                                                                     "
            echo "source checkout.sh                                            "
            echo " -----Activate ENV VAR EQQUASIROOT and add exes to PATH              "
            echo "                                                                     "
            echo "Currently supported machines include:                                "
            echo " ls6/ubuntu                                                          "
            ;;
    esac
done 

if [ -n "$MACH" ]; then 
    export MACHINE=$MACH
    
    echo "Installing ESCI on " $MACHINE " ... ..."
    
    if [ $UPDATE = "False" ]; then 
        rm -rf components bin
        mkdir components
        mkdir bin
    fi
    
    cd components 
    #1 download/update and install EQquasi
    if [ $UPDATE = "False" ]; then 
        git clone https://github.com/dunyuliu/EQquasi.git eqquasi
        cd eqquasi 
    else
        cd eqquasi 
        git stash
        git pull
    fi 
    
    chmod 755 install-eqquasi.sh
    ./install-eqquasi.sh -m $MACHINE
    cp bin/eqquasi ../../bin/
    cd .. # back to components
    
    #2 download/update and install EQdyna
    if [ $UPDATE = "False" ]; then 
        git clone https://github.com/dunyuliu/EQdyna.git eqdyna
        cd eqdyna
    else
        cd eqdyna
        git stash
        git pull
    fi 
    
    chmod 755 install-eqdyna.sh
    ./install-eqdyna.sh -m $MACHINE
    cp bin/eqdyna ../../bin/
    cd .. # back to components
    
    # # download and install SORD
    # git clone https://github.com/wangyf/sordw3 sord
    # cd sord
    # cd src
    # cp makefile_mpi makefile
    # make
    # cp sord-mO ../../../bin/
    # cd ../../.. # back to components
fi 
