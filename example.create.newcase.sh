rm -rf qdc-bp7 fdc-liu2020-planar dr-tpv104
# creating a quasi dynamic cycle with EQquasi,
# setting the run case directory as qdc-bp7,
# and choose the compset bp7-qd-10-a.
python utils/create.newcase qdc qdc-bp7 bp7-qd-a-10

# creating a fully dynamic cycle with EQquasi+EQdyna
# setting the run case directory as fdc-liu2020-planar,
# and choose the compset liu2020-planar

python utils/create.newcase fdc fdc-liu2020-planar liu2020-planar

# creating a dynamic rupture with EQdyna
# setting the run case directory as dr-tpv104,
# and choose the compset liu2020-planar

python utils/create.newcase dr dr-tpv104 tpv104


