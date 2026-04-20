# +
# :Description:
#
# :AUTHOR: Katarzyna Ewa Lewinska
# :DATE: 17 March 2022
# :STATUS:          operational
# :VERSION: 1.0     based on Fold2Days
# :UPDATES:         2023-03-17  Monthly composites
#                   2023-03-20  Filling in from RBF output 16 days
#                   2023-03-22  Filling in from RBF output 24 days for wider gaps signa 16, 48, 96
#                   2023-10-30  QA bits: 4-NAN, 3-RBF32, 2-RBF-16, 1-monthly/original, 0-noData
#                   2026-04-17  nf revisited changes: new RBF input with >3 sigmas
# :TO-DOs:          improve speed - it is painfully slow... -> xarray?
#                   clean to free ram
# -


# :ENVIRONMENT: #

from osgeo import gdal
import os
import pandas as pd
import numpy as np
import glob
import rasterio
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import warnings

startTime = datetime.now()
# :INPUTS: #
os.chdir(r'/data/Dagobah/fonda/grassdata/nf_trend_revisited/level3/')
cdir = os.getcwd()

gvdir = 'gv'
npvdir = 'npv'
soildir = 'soil'
shadedir = 'shade'

cubedir = list(os.listdir(os.path.join(cdir, 'gv')))
tiles = [x for x in cubedir if x.startswith('X')]

foldMonths = 1      # number of months to base the composite on


# :CODE: #

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=RuntimeWarning)


nos = len(tiles)
# tiles = tiles[1:1+nos]

print(tiles)
print(nos)

# iterate through tiles
for i in range(0, nos):
    # itile = tiles.iat[i, 0]
    itile = tiles[i]
    print(itile)

    # get paths to endmembers
    gvtile = os.path.join(cdir, gvdir, itile)
    npvtile = os.path.join(cdir, npvdir, itile)
    soiltile = os.path.join(cdir, soildir, itile)
    shtile = os.path.join(cdir, shadedir, itile)

   # unmixing data
    rmse = glob.glob(gvtile+'/RMS/*SMA_RMS.tif')
    gvtss = glob.glob(gvtile+'/TSS/*TSS.tif')
    npvtss = glob.glob(npvtile+'/TSS/*TSS.tif')
    soiltss = glob.glob(soiltile + '/TSS/*TSS.tif')
    shtss = glob.glob(shtile + '/TSS/*TSS.tif')

    # 16-day RBF interpolation
    gvrbfp = glob.glob(gvtile+'/TSI/*TSI.tif')
    npvrbfp = glob.glob(npvtile + '/TSI/*TSI.tif')
    soilrbfp = glob.glob(soiltile + '/TSI/*TSI.tif')
    shrbfp = glob.glob(shtile + '/TSI/*TSI.tif')


    rms = gdal.Open(rmse[0])
    gv = gdal.Open(gvtss[0])
    npv = gdal.Open(npvtss[0])
    soil = gdal.Open(soiltss[0])
    sh = gdal.Open(shtss[0])

    gvrbf = gdal.Open(gvrbfp[0])
    npvrbf = gdal.Open(npvrbfp[0])
    soilrbf = gdal.Open(soilrbfp[0])
    shrbf = gdal.Open(shrbfp[0])


    # get time info from Band information in the stack
    datDes = []
    for b in range(1, gv.RasterCount+1):
        bt = gv.GetRasterBand(b)
        dest = bt.GetDescription()
        datDes.append(dest)

    datDesRBF = []
    for b2 in range(1, gvrbf.RasterCount+1):
        bt2 = gvrbf.GetRasterBand(b2)
        dest2 = bt2.GetDescription()
        datDesRBF.append(dest2)

    # dates = []
    datesYmd = []
    for n in range(0, len(datDes)):
        # dates.append(datDes[n][0:8])
        datesYmd.append(datetime.strptime(datDes[n][0:8], "%Y%m%d"))

    # get dates from RBF layerstack
    datesYmdRBF = []
    for n2 in range(0, len(datDesRBF)):
        datesYmdRBF.append(datetime.strptime(datDesRBF[n2][0:8], "%Y%m%d"))


    firstYear = int(datesYmd[0].strftime('%Y'))
    lastYear = int(datesYmd[-1].strftime('%Y'))

    gvLS = np.empty((rms.GetRasterBand(1).ReadAsArray().shape[0],
                    rms.GetRasterBand(1).ReadAsArray().shape[1],1),
                    like = rms.GetRasterBand(1).ReadAsArray())
    npvLS = gvLS.copy()
    soilLS = gvLS.copy()
    shLS = gvLS.copy()
    qaLS = np.empty((rms.GetRasterBand(1).ReadAsArray().shape[0],
                           rms.GetRasterBand(1).ReadAsArray().shape[1],1),
                    dtype=np.int8)*4
    bandNames = []
    for y in range(firstYear, lastYear+1):

        # iterate through composites in a single year
        for mm in range(0, 12):                # m is not used in the for loop
            fday = datetime(year=y, month=mm+1, day=1)  # the first day in the time series
            lday = (fday + relativedelta(months=foldMonths)) - timedelta(days=1)

            bname = fday.strftime('%Y%m%d')
            bandNames.append(bname)
            # ind = [index for index, adate in enumerate(datesYmd) if fday <= adate <= lday]
            ind = [index for index in range(len(datesYmd)) if fday <= datesYmd[index] <= lday]

            # prepare fill in values
            indRBF = [index for index in range(len(datesYmdRBF)) if fday <= datesYmdRBF[index] <= lday]
            # indRBFW = [index for index in range(len(datesYmdRBFW)) if fday <= datesYmdRBFW[index] <= lday]

            empty = np.ones((rms.RasterXSize, rms.RasterYSize, len(indRBF))) * (-9999)
            gvRBFarr = empty.copy()
            npvRBFarr = empty.copy()
            soilRBFarr = empty.copy()
            shRBFarr = empty.copy()
            qaRBFarr = np.ones((rms.RasterXSize, rms.RasterYSize, 1), dtype=np.int8) * (2)

         
            for bR, bandR in enumerate(indRBF):  # will use the value passed by ind
                # print('b is:', bR, 'band is: ', bandR)
                gvRBFarr[:, :, bR] = gvrbf.GetRasterBand(bandR + 1).ReadAsArray()
                npvRBFarr[:, :, bR] = npvrbf.GetRasterBand(bandR + 1).ReadAsArray()
                soilRBFarr[:, :, bR] = soilrbf.GetRasterBand(bandR + 1).ReadAsArray()
                shRBFarr[:, :, bR] = shrbf.GetRasterBand(bandR + 1).ReadAsArray()


            gvRBFarr[gvRBFarr == -9999] = np.nan
            npvRBFarr[npvRBFarr == -9999] = np.nan
            soilRBFarr[soilRBFarr == -9999] = np.nan
            shRBFarr[shRBFarr == -9999] = np.nan
            # qaRBFarr[gvRBFarr == -9999] = np.nan

            gvRBFComp = np.nanmean(gvRBFarr[:, :, :], axis=2)
            npvRBFComp = np.nanmean(npvRBFarr[:, :, :], axis=2)
            soilRBFComp = np.nanmean(soilRBFarr[:, :, :], axis=2)
            shRBFComp = np.nanmean(shRBFarr[:, :, :], axis=2)
            qaRBFarr[np.isnan(gvRBFComp)] = 4
            qaRBFarr[gvRBFComp == 0] = 0


            # # fill in the 0s and nan in 8-day RBF with 16-day RBF
            # gvMa = np.squeeze(np.any([[gvRBFComp == 0], [np.isnan(gvRBFComp)]], axis=0), axis=(0))
            # npvMa = np.squeeze(np.any([[npvRBFComp == 0], [np.isnan(npvRBFComp)]], axis=0), axis=(0))
            # soilMa = np.squeeze(np.any([[soilRBFComp == 0], [np.isnan(soilRBFComp)]], axis=0), axis=(0))
            # shMa = np.squeeze(np.any([[shRBFComp == 0], [np.isnan(shRBFComp)]], axis=0), axis=(0))

            # gvRBFComp[gvMa] = gvRBFWmean[gvMa]
            # # gvRBFComp[gvRBFComp == 0 | np.isnan(gvRBFComp)] = gvRBFWmean[gvRBFComp == 0 | np.isnan(gvRBFComp)]
            # npvRBFComp[npvMa] = npvRBFWmean[npvMa]
            # soilRBFComp[soilMa] = soilRBFWmean[soilMa]
            # shRBFComp[shMa] = shRBFWmean[shMa]
            # qaRBFarr[gvMa] = qaRBFWarr[gvMa]
            # # qaarr = np.zeros((rms.RasterXSize, rms.RasterYSize, 1), dtype=np.int8)

            if len(ind) > 0:

                qaComp = np.ones((rms.RasterXSize, rms.RasterYSize, 1), dtype=np.int8)

                if len(ind) > 1:    # exclusive False for len([1])
                    print(y, mm, ': multiple images: look for lowest RMSE')
                    empty = np.ones((rms.RasterXSize, rms.RasterYSize, len(ind))) * (-9999)
                    rmsearr = empty.copy()
                    rmsearrM = empty.copy()
                    gvarr = empty.copy()
                    npvarr = empty.copy()
                    soilarr = empty.copy()
                    sharr = empty.copy()
                    # qaarr = np.zeros((rms.RasterXSize, rms.RasterYSize, 1), dtype=np.int8)

                    for b, band in enumerate(ind):          # will use the value passed by ind
                        # print('b is:', b, 'band is: ', band)
                        rmsearr[:, :, b] = rms.GetRasterBand(band + 1).ReadAsArray()
                        gvarr[:, :, b] = gv.GetRasterBand(band + 1).ReadAsArray()
                        npvarr[:, :, b] = npv.GetRasterBand(band + 1).ReadAsArray()
                        soilarr[:, :, b] = soil.GetRasterBand(band + 1).ReadAsArray()
                        sharr[:, :, b] = sh.GetRasterBand(band + 1).ReadAsArray()

                    rmsearr[gvarr == -9999] = np.nan
                    rmsearr[rmsearr == -9999] = np.nan
                    minrmse = np.nanmin(rmsearr[:, :, :], axis=2)
                    # minrmse = rmsearr[:, :, :].min(axis=2)

                    for m in range(0, len(ind)):  # 1 change to b
                        rmsearrM[:, :, m] = np.where(rmsearr[:, :, m] == minrmse, 1, 0)

                    gvM = empty.copy()
                    npvM = empty.copy()
                    soilM = empty.copy()
                    shM = empty.copy()
                    for m1 in range(0, len(ind)):  # 1 change to b
                        gvM[:, :, m1] = np.where(rmsearrM[:, :, m1] == 1, gvarr[:, :, m1], -9999)
                        npvM[:, :, m1] = np.where(rmsearrM[:, :, m1] == 1, npvarr[:, :, m1], -9999)
                        soilM[:, :, m1] = np.where(rmsearrM[:, :, m1] == 1, soilarr[:, :, m1], -9999)
                        shM[:, :, m1] = np.where(rmsearrM[:, :, m1] == 1, sharr[:, :, m1], -9999)

                    gvM[gvM == -9999] = np.nan
                    npvM[npvM == -9999] = np.nan
                    soilM[soilM == -9999] = np.nan
                    shM[shM == -9999] = np.nan

                    gvComp = np.nanmean(gvM, axis=2)
                    npvComp = np.nanmean(npvM, axis=2)
                    soilComp = np.nanmean(soilM, axis=2)
                    shComp = np.nanmean(shM, axis=2)

                else:
                    print(y, mm, ': single image in the time window: copy as is')

                    gvComp = gv.GetRasterBand(ind[0]+1).ReadAsArray()
                    npvComp = npv.GetRasterBand(ind[0]+1).ReadAsArray()
                    soilComp = soil.GetRasterBand(ind[0]+1).ReadAsArray()
                    shComp = sh.GetRasterBand(ind[0]+1).ReadAsArray()

                # fill in all nan with RBD and RBFW
                # first identify the masks
                gvMs = np.squeeze(np.any([[gvComp == 0], [np.isnan(gvComp)], [gvComp == -9999]], axis = 0),axis=(0))
                npvMs = np.squeeze(np.any([[npvComp == 0], [np.isnan(npvComp)], [npvComp == -9999]], axis=0), axis=(0))
                soilMs = np.squeeze(np.any([[soilComp == 0], [np.isnan(soilComp)], [soilComp == -9999]], axis=0), axis=(0))
                shMs = np.squeeze(np.any([[shComp == 0], [np.isnan(shComp)], [shComp == -9999]], axis=0), axis=(0))
                # and apply them
                gvComp[gvMs] = gvRBFComp[gvMs]
                npvComp[npvMs] = npvRBFComp[npvMs]
                soilComp[soilMs] = soilRBFComp[soilMs]
                shComp[shMs] = shRBFComp[shMs]
                qaComp[gvMs] = qaRBFarr[gvMs]


            if len(ind) == 0:
            # else:
                print(y, mm, ': empty range, take RBF')

                gvComp = gvRBFComp
                npvComp = npvRBFComp
                soilComp = soilRBFComp
                shComp = shRBFComp
                qaComp = qaRBFarr

            qaComp[gvRBFComp == np.nan] = 4
            qaComp[gvRBFComp == 0] = 0

            # add band to the out LS
            gvLS = np.append(gvLS, np.atleast_3d(gvComp), axis=2)
            npvLS = np.append(npvLS, np.atleast_3d(npvComp), axis=2)
            soilLS = np.append(soilLS, np.atleast_3d(soilComp), axis=2)
            shLS = np.append(shLS, np.atleast_3d(shComp), axis=2)
            qaLS = np.append(qaLS, np.atleast_3d(qaComp), axis=2)

    # create the output filename
    nOut = os.path.basename(os.path.splitext((npvtss[0]))[0])

    # output paths
    gvOutP = os.path.join(gvtile, nOut + '_FnFX.tif')
    npvOutP = os.path.join(npvtile, nOut + '_FnFX.tif')
    soilOutP = os.path.join(soiltile, nOut + '_FnFX.tif')
    shOutP = os.path.join(shtile, nOut + '_FnFX.tif')
    qaOutP = os.path.join(gvtile, nOut + '_FnFX_QA.tif')

    # get rid of the first empty array at axis 2
    gvLS = gvLS[:,:,1:gvLS.shape[2]]
    npvLS = npvLS[:, :, 1:npvLS.shape[2]]
    soilLS = soilLS[:, :, 1:soilLS.shape[2]]
    shLS = shLS[:, :, 1:shLS.shape[2]]
    qaLS = qaLS[:, :, 1:qaLS.shape[2]]

    gvStak = rasterio.open(gvrbfp[0], "r", tiled=True, BIGTIFF='YES')

    gvProfile = gvStak.profile
    gvProfile.update(count=gvLS.shape[2])
    with rasterio.open(gvOutP, 'w', **gvProfile) as dst:
        for ith, outbn in enumerate(bandNames):
            dst.set_band_description(ith+1, outbn)
            # dst.update_tags(ith, ns='TIMESERIES', dates=outbn[0:4]+'-'+outbn[4:6]+'-'+outbn[6:8]+'T00:00:00')
            # dst.update_tags(ith, ns='TIMESERIES',dates=outbnDate[ith])
            # dst.update_tags(ith, ns='FORCE', Date=datetime.strptime(outbn, '%Y%m%d' ) )
            # dst.update_tags(ith+1, ns='FORCE', Date=outbnDate[ith])
            dst.update_tags(ith+1, ns='FORCE', Date=outbn[0:4]+'-'+outbn[4:6]+'-'+outbn[6:8])
            dst.update_tags(ith+1, ns='FORCE', Wavelength_unit='decimal year')
            dst.update_tags(ith+1, ns='FORCE', Domain='SMA_TSA')
            # dst.update_tags(ith+1, start_time=outbnDate[ith]+'T00:00:00')
            # dst.update_tags(ith, DATE_TIME=outbn[0:4] + '-' + outbn[4:6] + '-' + outbn[6:8]+'T12:00')
            # dst.update_tags(ith, dates=outbn[0:4] + '-' + outbn[4:6] + '-' + outbn[6:8])
        # rasterio needs the band axis first.
        dst.write(np.moveaxis(gvLS,-1,0), list(range(1,gvLS.shape[2]+1)))
        dst.close()

    with rasterio.open(npvOutP, 'w', **gvProfile) as dst:
        for ith, outbn in enumerate(bandNames):
            dst.set_band_description(ith+1, outbn)
            dst.update_tags(ith + 1, ns='FORCE', Date=outbn[0:4] + '-' + outbn[4:6] + '-' + outbn[6:8])
            dst.update_tags(ith + 1, ns='FORCE', Wavelength_unit='decimal year')
            dst.update_tags(ith + 1, ns='FORCE', Domain='SMA_TSA')
        # rasterio needs the band axis first.
        dst.write(np.moveaxis(npvLS,-1,0), list(range(1,npvLS.shape[2]+1)))
        dst.close()

    with rasterio.open(soilOutP, 'w', **gvProfile) as dst:
        for ith, outbn in enumerate(bandNames):
            dst.set_band_description(ith+1, outbn)
            dst.update_tags(ith + 1, ns='FORCE', Date=outbn[0:4] + '-' + outbn[4:6] + '-' + outbn[6:8])
            dst.update_tags(ith + 1, ns='FORCE', Wavelength_unit='decimal year')
            dst.update_tags(ith + 1, ns='FORCE', Domain='SMA_TSA')
        # rasterio needs the band axis first.
        dst.write(np.moveaxis(soilLS,-1,0), list(range(1,soilLS.shape[2]+1)))
        dst.close()

    with rasterio.open(shOutP, 'w', **gvProfile) as dst:
        for ith, outbn in enumerate(bandNames):
            dst.set_band_description(ith+1, outbn)
            dst.update_tags(ith + 1, ns='FORCE', Date=outbn[0:4] + '-' + outbn[4:6] + '-' + outbn[6:8])
            dst.update_tags(ith + 1, ns='FORCE', Wavelength_unit='decimal year')
            dst.update_tags(ith + 1, ns='FORCE', Domain='SMA_TSA')
        # rasterio needs the band axis first.
        dst.write(np.moveaxis(shLS,-1,0), list(range(1,shLS.shape[2]+1)))
        dst.close()


    gvProfile.update(dtype='uint8')
    gvProfile.update(nodata='255')
    with rasterio.open(qaOutP, 'w', **gvProfile) as dst:
        for ith, outbn in enumerate(bandNames):
            dst.set_band_description(ith+1, outbn)
            dst.update_tags(ith + 1, ns='FORCE', Date=outbn[0:4] + '-' + outbn[4:6] + '-' + outbn[6:8])
            dst.update_tags(ith + 1, ns='FORCE', Wavelength_unit='decimal year')
            dst.update_tags(ith + 1, ns='FORCE', Domain='SMA_TSA')
        # rasterio needs the band axis first.
        dst.write(np.moveaxis(qaLS,-1,0), list(range(1,qaLS.shape[2]+1)))
        dst.close()

print('execution took ', datetime.now() - startTime)

# :END OF THE CODE: #
