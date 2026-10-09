#!/bin/bash
# Fully dynamic cycle (EQquasi + EQdyna) for SEAS BP1001 on a rough fault.
source checkout.sh
create.newcase fdc fdc-bp1001 bp1001.fdc.rough.250 --machine ls6
cd fdc-bp1001 && ./case.setup && ./case.submit
