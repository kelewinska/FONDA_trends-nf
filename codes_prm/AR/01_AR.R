#+
# :Description: runs remotePARTS ARfit for all tiles in a folder structure
#
# :AUTHOR: Katarzyna Ewa Lewinska
# :DATE: 26 April 2023
# :VERSION: 1.0
#-

#!/usr/bin/env Rscript
args = commandArgs(trailingOnly=TRUE)

# :ENVIRONMENT: #
suppressPackageStartupMessages(library(snow))
library(remotePARTS)
library(doParallel)
library(foreach)
library(raster)
library(graphics)


# :INPUTS: #

inDir <- args[1]
outDir <- args[2]

# test if there is at least one argument: if not, return an error
if (length(args)==0) {
  stop("Missing input directory. Execution aborted", call.=FALSE)
}

# inDir <- 'J:/fonda/grassdata/force/cef'
# outDir <- 'J:/fonda/grassdata/force/trends'

tiles <- list.dirs(inDir, full.names = FALSE)
tiles <- grep('^X', tiles, value = TRUE)

# :SETUP: #
ncores = 10 # cores
maxmem_GB = 100 #max to use memory for calculations ## 20
maxmem_Bytes = maxmem_GB * 1e9 #in bytes
chunk_size = 1e6 # maximum size (in bytes) of individual data chunks to read/write at a time

if (!dir.exists(outDir)){
  dir.create(outDir)
}


## :FUNCTIONALITY: ##

# AR  fit function
# AR output with residuals
raster_ARres <- function(x, na.rm = FALSE, time = 1:length(x)){
  if(na.rm){ # na handling
    if(any(is.na(x))){return(c(timetrend = NA, pval = NA, b = NA, intercept=NA, resids=rep(NA,length(x)) ))} # exclude pixel if there is missing data (trend is NA)
    if(sd(x, na.rm = TRUE) == 0){return(c(timetrend = 0, pval = 1, b = NA, intercept=NA, resids=rep(NA,length(x)) ))} # trend = 0 for a pixel pixel if there is no variance
  }
  ar = remotePARTS::fitAR(x ~ time) # full CLS
  timetrend = ar$coefficients["time"] # extract time trend only
  intercept = ar$coefficient[[1]]
  pval = ar$pval['time'] # extract pval
  B = ar$rho ## get AR coefficient
  return(c("timetrend" = unname(timetrend),
           'intercept' = unname(intercept),
           "pval" = pval,
           "b" = as.vector(B),
           resids = ar$residuals) )
}
# AR output without residuals
raster_AR <- function(x, na.rm = FALSE, time = 1:length(x)){
  if(na.rm){ # na handling
    if(any(is.na(x))){return(c(timetrend = NA, pval = NA, b = NA, intercept=NA ))} # exclude pixel if there is missing data (trend is NA)
    if(sd(x, na.rm = TRUE) == 0){return(c(timetrend = 0, pval = 1, b = NA, intercept=NA ))} # trend = 0 for a pixel pixel if there is no variance
  }
  ar = remotePARTS::fitAR(x ~ time) # full CLS
  timetrend = ar$coefficients["time"] # extract time trend only
  intercept = ar$coefficient[[1]]
  pval = ar$pval['time'] # extract pval
  B = ar$rho ## get AR coefficient
  return(c("timetrend" = unname(timetrend),
           'intercept' = unname(intercept),
           "pval" = pval,
           "b" = as.vector(B)) )
}

# :CODE: #

for(i in tiles){
  print(i)
  #prepare output dir
  if (!dir.exists(file.path(outDir, i))){
    dir.create(file.path(outDir, i))
  }

  # gv
  in_gv = list.files(file.path(inDir, i), 'gv_cef.tif', full.names=TRUE)
  GVstk <- brick(in_gv)
  NANmask <- calc(GVstk, sum)
  GVstk[NANmask==0] = NA

    ## SETUP ##
    ## check/change options
    # rasterOptions() # print current options
    rasterOptions(maxmemory = maxmem_Bytes, # increase memory for calculations to 8GB
                  chunksize = chunk_size)
    # rasterOptions() # print new options

    ## check if raster is in memory
    inMemory(GVstk)

    ## check if we can process the stack in memory
    canProcessInMemory(GVstk, verbose = TRUE)

    ## Here's the formula to caclulate approximately how much RAM (GB) is needed to process 4-8 copies of the entire stack:
    # 8 * c(4, 8) * ncell(GVstk) * nlayers(GVstk) / 1e9

  out_gv = file.path(outDir, i, 'gv_ARres.tif')
  print(out_gv)
  beginCluster(ncores)
  stack_AR_mc = clusterR(GVstk,
                         fun = calc,
                         args = list(fun = raster_ARres, na.rm = TRUE),
                         filename = out_gv,
                         overwrite = TRUE)
  endCluster()

  # npv
  in_npv = list.files(file.path(inDir, i), 'npv_cef.tif', full.names=TRUE)
  NPVstk <- brick(in_npv)
  NPVstk[NANmask==0] = NA

  out_npv = file.path(outDir, i, 'npv_ARres.tif')
  print(out_npv)

  beginCluster(ncores)
  stack_AR_mc = clusterR(NPVstk,
                         fun = calc,
                         args = list(fun = raster_ARres, na.rm = TRUE),
                         filename = out_npv,
                         overwrite = TRUE)
  endCluster()


  # soil
  in_soil = list.files(file.path(inDir, i), 'soil_cef.tif', full.names=TRUE)
  SOILstk <- brick(in_soil)
  SOILstk[NANmask==0] = NA

  out_soil = file.path(outDir, i, 'soil_ARres.tif')
  print(out_soil)

  beginCluster(ncores)
  stack_AR_mc = clusterR(SOILstk,
                         fun = calc,
                         args = list(fun = raster_ARres, na.rm = TRUE),
                         filename = out_soil,
                         overwrite = TRUE)
  endCluster()

  # shade
  in_shade = list.files(file.path(inDir, i), 'shade_cef.tif', full.names=TRUE)
  SHADEstk <- brick(in_shade)
  SHADEstk[NANmask==0] = NA

  out_shade = file.path(outDir, i, 'shade_ARres.tif')
  print(out_shade)

  beginCluster(ncores)
  stack_AR_mc = clusterR(SHADEstk,
                         fun = calc,
                         args = list(fun = raster_ARres, na.rm = TRUE),
                         filename = out_shade,
                         overwrite = TRUE)
  endCluster()
}

# :END OF THE CODE: #
