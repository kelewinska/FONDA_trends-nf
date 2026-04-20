# +
# :Description: The code calculates CEF.
#
# :AUTHOR: Katarzyna Ewa Lewinska
# :DATE: 29 March 2023
# :STATUS:          experimental
# :VERSION: 1.0
# :UPDATES:     17 Apr 2026: nf revisited changes 
# -

# :ENVIRONMENT: #

import os
import copy
import shutil
import numpy as np
import pandas as pd
import rasterio
import sys
import glob
from datetime import datetime, date, timedelta

startTime = datetime.now()

# :INPUTS: #
if len(sys.argv) < 2:
    parentDir = r'/data/Dagobah/fonda/grassdata/nf_trend_revisited/level3/'  # parent directory
else:
    parentDir = (sys.argv[1])
    print(parentDir)


# :CODE: #
#prepare output directory
outDir = os.path.join(os.path.dirname(parentDir),'cef')
if os.path.exists(outDir) is False:
    os.mkdir(outDir)

# get tiles
cubeDir = list(os.listdir(os.path.join(parentDir,'gv')))
tiles = [x for x in cubeDir if x.startswith('X')]

for fl in tiles:
    print(fl)

    # put results for each tile in a separate directory
    outTileDir = os.path.join(outDir, fl)
    if os.path.exists(outTileDir) is False:
        os.mkdir(outTileDir)

    # get data for the tile fl
    SoS = glob.glob(os.path.join(parentDir, 'gv', fl, 'DSS-POL/*DSS-POL_DOY_25.tif'))
    EoS = glob.glob(os.path.join(parentDir, 'gv', fl, 'DES-POL/*DES-POL_DOY_75.tif'))

    FnFgv = glob.glob(os.path.join(parentDir, 'gv', fl, '*TSS_FnF.tif'))
    FnFnpv = glob.glob(os.path.join(parentDir, 'npv', fl, '*TSS_FnF.tif'))
    FnFsoil = glob.glob(os.path.join(parentDir, 'soil', fl, '*TSS_FnF.tif'))
    FnFsh = glob.glob(os.path.join(parentDir, 'shade', fl, '*TSS_FnF.tif'))

    # annual CEF mask
    SoSDataset = rasterio.open(SoS[0])
    sos = SoSDataset.read().astype(np.float32)
    EoSDataset = rasterio.open(EoS[0])
    eos = EoSDataset.read().astype(np.float32)

    sos[sos == -9999] = np.nan
    eos[eos == -9999] = np.nan

    empty = np.ones((sos.shape[1], sos.shape[2])) * (-9999)
    sosMonth = empty.copy()
    eosMonth = empty.copy()

    # sos
    for n in range(0, sos.shape[1]):
        for m in range(0, sos.shape[2]):
            sosdelta = sos[0,n,m]
            if np.isnan(sosdelta):
                continue

            if sosdelta > 0: sosdoy = date(2000, 1, 1) + timedelta(days=int(sosdelta - 1))
            if sosdelta <= 0: sosdoy = date(2000, 1, 1) + timedelta(days=int(sosdelta))


            # round to months
            if (sosdoy.month != 2 and sosdoy.day >= 15): sosmonth = sosdoy + pd.offsets.MonthBegin(0)
            if (sosdoy.month != 2 and sosdoy.day < 15): sosmonth = sosdoy + pd.offsets.MonthEnd(0)
            if (sosdoy.month == 2 and sosdoy.day >= 14): sosmonth = sosdoy + pd.offsets.MonthBegin(0)
            if (sosdoy.month == 2 and sosdoy.day < 14): sosmonth = sosdoy + pd.offsets.MonthEnd(0)

            sosMonth[n,m] = sosmonth.month

    # eos
    for n in range(0,eos.shape[1]):
        for m in range(0, eos.shape[2]):
            eosdelta = eos[0,n,m]
            if np.isnan(eosdelta):
                continue

            if eosdelta > 0: eosdoy = date(2000, 1, 1) + timedelta(days=int(eosdelta - 1))
            if eosdelta < 0: eosdoy = date(2000, 1, 1) + timedelta(days=int(eosdelta))
            if eosdelta == 0: eosdoy = date(2000, 1, 1)

            # round to months
            if (eosdoy.month != 2 and eosdoy.day >= 15): eosmonth = eosdoy + pd.offsets.MonthBegin(0)
            if (eosdoy.month != 2 and eosdoy.day < 15): eosmonth = eosdoy + pd.offsets.MonthEnd(0)
            if (eosdoy.month == 2 and eosdoy.day >= 14): eosmonth = eosdoy + pd.offsets.MonthBegin(0)
            if (eosdoy.month == 2 and eosdoy.day < 14): eosmonth = eosdoy + pd.offsets.MonthEnd(0)

            eosMonth[n,m] = eosmonth.month

    # simplification for uninterrupted growing season
    sosMonth[np.squeeze(np.any([[np.squeeze(abs(sos) - abs(eos) > 365, axis=0)], [np.squeeze(abs(eos) - abs(sos) > 365, axis=0)]], axis=0), axis=0)] = 1
    eosMonth[np.squeeze(np.any([[np.squeeze(abs(sos) - abs(eos) > 365, axis=0)], [np.squeeze(abs(eos) - abs(sos) > 365, axis=0)]], axis=0), axis=0)] = 12

    # annual cef mask
    cefMask = np.ones((12,sos.shape[1], sos.shape[2])) * (-9999)

    # mask1 = np.all([[sosMonth < eosMonth], [sosMonth <= b]],axis=0)
    for b in range(1, 13):
        cefMask[b-1, np.squeeze(np.all([[sosMonth < eosMonth], [sosMonth <= b], [eosMonth >= b]], axis=0), axis=0)] = 1
        # cefMask[b - 1, (np.squeeze(np.all([[sosMonth > eosMonth], [sosMonth > b], [eosMonth < b]], axis=0), axis=0))] = 1
        cefMask[b-1, np.invert(np.squeeze(np.all([[sosMonth > eosMonth], [sosMonth > b], [eosMonth < b]], axis=0), axis=0))] = 1

    # carry over no data
    for b in range(0, 12):
        cefMask[b, sosMonth == -9999] = -9999
        cefMask[b, cefMask[b] == -9999] = np.nan

    # open monthly time series of endmembers
    gvDataset = rasterio.open(FnFgv[0])
    dates = gvDataset.descriptions
    gv = gvDataset.read()
    npvDataset = rasterio.open(FnFnpv[0])
    npv = npvDataset.read()
    soilDataset = rasterio.open(FnFsoil[0])
    soil = soilDataset.read()
    shDataset = rasterio.open(FnFsh[0])
    shade = shDataset.read()

    start = dates[0][0:4]
    end = dates[len(dates)-1][0:4]

    # prepare outputs
    gvLS = np.empty((int(end)-int(start)+1, gvDataset.shape[0], gvDataset.shape[1]), like = gv[0])
    npvLS = gvLS.copy()
    soilLS = gvLS.copy()
    shLS = gvLS.copy()
    bandNames = []

    # cef iterate through years
    for index, y in enumerate(range(int(start), int(end)+1)):
        print(y, index)

        bandNames.append(y)
        bandsubset = [dates.index(d) for d in dates if str(y) in d[0:4]]

        gvSub = gv[bandsubset[0]:bandsubset[11]+1, :, :]
        npvSub = npv[bandsubset[0]:bandsubset[11] + 1, :, :]
        soilSub = soil[bandsubset[0]:bandsubset[11] + 1, :, :]
        shSub = shade[bandsubset[0]:bandsubset[11] + 1, :, :]

        # mask cef
        gvCEF = np.nansum(gvSub.astype('float64') * cefMask, axis=0)
        npvCEF = np.nansum(npvSub.astype('float64') * cefMask, axis=0)
        soilCEF = np.nansum(soilSub.astype('float64') * cefMask, axis=0)
        shCEF = np.nansum(shSub.astype('float64') * cefMask, axis=0)
        # gvCEF = np.sum(np.where(np.isnan(cefMask), np.nan, gvSub),  axis=0)
        # npvCEF = np.sum(np.where(np.isnan(cefMask), np.nan, npvSub), axis=0)
        # soilCEF = np.sum(np.where(np.isnan(cefMask), np.nan, soilSub), axis=0)
        # shCEF = np.sum(np.where(np.isnan(cefMask), np.nan, shSub), axis=0)

        sumCEF = gvCEF + npvCEF + soilCEF + shCEF

        # normalization (rescaling to percentage points)
        gvPP = gvCEF * 100 / sumCEF
        npvPP = npvCEF * 100 / sumCEF
        soilPP = soilCEF * 100 / sumCEF
        shPP = shCEF * 100 / sumCEF

        gvLS[index,:,:] = gvPP
        npvLS[index, :, :] = npvPP
        soilLS[index, :, :] = soilPP
        shLS[index, :, :] = shPP

    # save outputs
    cefProfile = SoSDataset.profile
    cefProfile.update(count=gvLS.shape[0])
    gvcefOut = os.path.join(outTileDir,'gv_cef.tif')
    with rasterio.open(gvcefOut, 'w', **cefProfile) as dst:
        for ith, outbn in enumerate(bandNames):
            dst.set_band_description(ith + 1, str(outbn))
            dst.update_tags(ith + 1, ns='FORCE', Date=str(outbn)[0:4] + '-01-01')
            dst.update_tags(ith + 1, ns='FORCE', Wavelength_unit='decimal year')
            dst.update_tags(ith + 1, ns='FORCE', Domain='SMA_TSA')
        dst.write(gvLS, list(range(1, gvLS.shape[0]+1)))
        dst.close()

    npvcefOut = os.path.join(outTileDir,'npv_cef.tif')
    with rasterio.open(npvcefOut, 'w', **cefProfile) as dst:
        for ith, outbn in enumerate(bandNames):
            dst.set_band_description(ith + 1, str(outbn))
            dst.update_tags(ith + 1, ns='FORCE', Date=str(outbn)[0:4] + '-01-01')
            dst.update_tags(ith + 1, ns='FORCE', Wavelength_unit='decimal year')
            dst.update_tags(ith + 1, ns='FORCE', Domain='SMA_TSA')
        dst.write(npvLS, list(range(1, gvLS.shape[0]+1)))
        dst.close()

    soilcefOut = os.path.join(outTileDir,'soil_cef.tif')
    with rasterio.open(soilcefOut, 'w', **cefProfile) as dst:
        for ith, outbn in enumerate(bandNames):
            dst.set_band_description(ith + 1, str(outbn))
            dst.update_tags(ith + 1, ns='FORCE', Date=str(outbn)[0:4] + '-01-01')
            dst.update_tags(ith + 1, ns='FORCE', Wavelength_unit='decimal year')
            dst.update_tags(ith + 1, ns='FORCE', Domain='SMA_TSA')
        dst.write(soilLS, list(range(1, gvLS.shape[0]+1)))
        dst.close()

    shcefOut = os.path.join(outTileDir,'shade_cef.tif')
    with rasterio.open(shcefOut, 'w', **cefProfile) as dst:
        for ith, outbn in enumerate(bandNames):
            dst.set_band_description(ith + 1, str(outbn))
            dst.update_tags(ith + 1, ns='FORCE', Date=str(outbn)[0:4] + '-01-01')
            dst.update_tags(ith + 1, ns='FORCE', Wavelength_unit='decimal year')
            dst.update_tags(ith + 1, ns='FORCE', Domain='SMA_TSA')
        dst.write(shLS, list(range(1, gvLS.shape[0]+1)))
        dst.close()

print('execution took ', datetime.now() - startTime)

# :END OF THE CODE: #
