# +
# :Description: Combines grasslands+pastures and cropland productivity maps from doi:10.1186/2192-1709-2-32.
#
# :AUTHOR: Katarzyna Ewa Lewinska
# :DATE: 11 April 2023
# :VERSION: 1.0
# :UPDATES:
# -

# :ENVIRONMENT: #

import os
import shutil
import copy
import numpy as np
import pandas as pd
import rasterio
import sys
import glob
from datetime import datetime, date, timedelta

startTime = datetime.now()

# :INPUTS: #
grasslandPath = r'P:\Fonda\data\esdac_biomass_production_geotiff\sqi_fig4_grass1.tif'
croplandPath = r'P:\Fonda\data\esdac_biomass_production_geotiff\sqi_fig5_crop1.tif'

# :CODE: #

GrassDataset = rasterio.open(grasslandPath)
CropDataset = rasterio.open(croplandPath)

grass = GrassDataset.read()
crop = CropDataset.read()

grass[0,grass[0,]<0] = 0
crop[0,crop[0,]<0] = 0

sum = grass + crop


# save outputs
Profile = GrassDataset.profile
Out = r'P:\Fonda\data\esdac_biomass_production_geotiff\grass_crop_productivity.tif'
with rasterio.open(Out, 'w', **Profile) as dst:
    dst.write(sum)
    dst.close()

print('execution took ', datetime.now() - startTime)

# :END OF THE CODE: #

