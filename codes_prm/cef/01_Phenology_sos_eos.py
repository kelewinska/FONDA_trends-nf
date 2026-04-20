# +
# :Description: The code identifies SoS and EoS from FORCE Phenology output.
#
# :AUTHOR: Katarzyna Ewa Lewinska
# :DATE: 09 March 2023
# :STATUS:          operational
# :VERSION: 1.0
# :UPDATES:     2023-03-27  pass parameters from the command line; iterate through all tiles in the cube
#                           Linux-Win path compatibility
#               17 Apr 2026: nf revisited changes 
# -

# :ENVIRONMENT: #

import os
import glob
from datetime import datetime
import copy
import rasterio
import numpy as np
import sys
import warnings

startTime = datetime.now()

# :INPUTS: #
if len(sys.argv) < 2:
    cube = r'/data/Dagobah/fonda/grassdata/nf_trend_revisited/level3/gv'  # parent directory
else:
    cube = (sys.argv[1])
    print(cube)

cubedir = list(os.listdir(cube))
tiles = [x for x in cubedir if x.startswith('X')]


# :CODE: #

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=RuntimeWarning)

# iterate through tiles'
for fl in tiles:
    print(fl)

    outtiledir = os.path.join(cube, fl)

    # read in the SoS and EoS data
    sosPath = glob.glob(os.path.join(cube, fl, 'DSS-POL/*SMA_DSS-POL.tif'))
    eosPath = glob.glob(os.path.join(cube, fl, 'DES-POL/*SMA_DES-POL.tif'))

    sosStak = rasterio.open(sosPath[0], "r", tiled=True, BIGTIFF='YES')
    sos = sosStak.read()
    bandNames = sosStak.descriptions

    eosStak = rasterio.open(eosPath[0], "r", tiled=True, BIGTIFF='YES')
    eos = eosStak.read()

    nbands = sos.shape[0]

    for n in range(0, nbands):
        sosT = copy.deepcopy(sos[n])
        sosM = copy.deepcopy(sosT)
        sosT[(sosM > n*365) & (sosM < 365*(n+1))] = sosM[(sosM > n*365) & (sosM < 365*(n+1))] - 365*n
        sosT[(sosM > 365*(n+1))] = sosM[(sosM > 365*(n+1))] - 365*(n)
        if n == 0:
            sosT[(sosM < 0)] = sosM[(sosM < 0)]
        if n >= 1:
            sosT[(sosM < 365 * n)] = (sosM[sosM < 365*n]) - 365*n
        sosT[sosM == -9999] = -9999

        eosT = copy.deepcopy(eos[n])
        eosM = copy.deepcopy(eosT)
        eosT[(eosT > n*365) & (eosT < 365*(n+1))] = eosT[(eosT > n*365) & (eosT < 365*(n+1))] - 365*n
        eosT[(eosT > 365*(n+1))] = eosT[(eosT > 365*(n+1))] - 365*(n)
        if n == 0:
            eosT[(eosM > 365)] = eosM[eosM > 365]
        if n >= 1:
            eosT[(eosM > 365*n)] = eosM[eosM > 365*n] - 365*n
        eosT[eosM == -10000] = -9999

        sos[n] = sosT
        eos[n] = eosT

    sosOut = os.path.splitext((sosPath[0]))[0] + '_DOY.tif'
    with rasterio.open(sosOut, 'w', **sosStak.profile) as dst:
        for ith, bn in enumerate(bandNames):
            dst.set_band_description(ith + 1, bn)
        dst.write(sos)

    eosOut = os.path.splitext((eosPath[0]))[0] + '_DOY.tif'
    with rasterio.open(eosOut, 'w', **eosStak.profile) as dst:
        for ith, bn in enumerate(bandNames):
            dst.set_band_description(ith + 1, bn)
        dst.write(eos)

    # calculate final sos and eos value
    sos = sos.astype(np.float32)
    sos[sos == -9999] = np.nan
    sos25 = np.nanpercentile(sos,25,0)
    sos25[np.isnan(sos25)] = -9999
    sos25 = sos25.astype(int)

    eos = eos.astype(np.float32)
    eos[eos == -9999] = np.nan
    eos75 = np.nanpercentile(eos,75,0)
    eos75[np.isnan(eos75)] = -9999
    eos75 = eos75.astype(int)

    sos25Out = os.path.splitext((sosPath[0]))[0] + '_DOY_25.tif'
    sosProfile = sosStak.profile
    sosProfile.update(count=1)
    with rasterio.open(sos25Out, 'w', **sosProfile) as dst:
        dst.write(sos25,1)

    eos75Out = os.path.splitext((eosPath[0]))[0] + '_DOY_75.tif'
    eosProfile = eosStak.profile
    eosProfile.update(count=1)
    with rasterio.open(eos75Out, 'w', **eosProfile) as dst:
        dst.write(eos75,1)

print('execution took ', datetime.now() - startTime)


# :END OF THE CODE: #
