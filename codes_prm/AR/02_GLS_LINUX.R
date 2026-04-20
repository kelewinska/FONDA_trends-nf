#+
# :Description: runs remotePARTS GLS for test sites according to AOI location
#
# :AUTHOR: Katarzyna Ewa Lewinska
# :DATE: 3 May 2023
# :STATUS:          experimental
# :UPDATES:         11.05.2023:   Linux implementation without ncore
# :VERSION: 1.1
# :UPDATES:         2026-04-17  nf revisited changes: new RBF input with >3 sigmas
#-

#!/usr/bin/env Rscript
args = commandArgs(trailingOnly=TRUE)

# :ENVIRONMENT: #
suppressPackageStartupMessages(library(raster))
suppressPackageStartupMessages(library(rgdal))
suppressPackageStartupMessages(library(remotePARTS))
suppressPackageStartupMessages(library(snow))
suppressPackageStartupMessages(library(parallel))
suppressPackageStartupMessages(library(doParallel))


# :INPUTS: #
inDir <- args[1]
AOI <- args[2]
outDir <- args[3]

# test if there is at least one argument: if not, return an error
if (length(args)==0) {
  stop("Missing arguments. Execution aborted. \nRequired arguments: <path> <AOI>", call.=FALSE)
}

# inDir <- 'J:/fonda/grassdata/force/trends'
# AOI = 'BX'

# :LUT: #
if(AOI=='DE') {tiles <- c('X0067_Y0042')}


if (!dir.exists(outDir)){
  dir.create(outDir)
}


# :CODE: #

# prepare big df for data from all the tiles in AOI
GV.df <- data.frame()
NPV.df <- data.frame()
SOIL.df <- data.frame()
SH.df <- data.frame()

# aggregate data across tiles
for(i in tiles){
  print(i)

  # gv
  in_gv <- list.files(file.path(inDir, i), 'gv_ARres.tif$', full.names=TRUE)
  GVar <- stack(in_gv)

  gv.df <- data.frame('Row'=rowFromCell(object=GVar, cell=1:ncell(GVar)),
                      'Col'=colFromCell(object=GVar, cell=1:ncell(GVar)),
                      'lng'=coordinates(GVar)[,1],
                      'lat'=coordinates(GVar)[,2],
                      'Est'=values(GVar[[1]]))
  # extract residuals
  resNames <- c()
  if(i=="X0087_Y0038"){
      for (n in c(6:nlayers(GVar))){
        resNames <- c(resNames,paste0('res_',n-5))
        gv.df <- cbind(gv.df, values(GVar[[n]]))
      }
    } else {
      for (n in c(5:nlayers(GVar))){
        resNames <- c(resNames,paste0('res_',n-4))
        gv.df <- cbind(gv.df, values(GVar[[n]])) }
    }
  colnames(gv.df)[6:length(colnames(gv.df))] <- resNames

  GV.df <- rbind.data.frame(GV.df, gv.df)

  # npv
  in_npv <- list.files(file.path(inDir, i), 'npv_ARres.tif$', full.names=TRUE)
  NPVar <- stack(in_npv)

  npv.df <- data.frame('Row'=rowFromCell(object=NPVar, cell=1:ncell(NPVar)),
                      'Col'=colFromCell(object=NPVar, cell=1:ncell(NPVar)),
                      'lng'=coordinates(NPVar)[,1],
                      'lat'=coordinates(NPVar)[,2],
                      'Est'=values(NPVar[[1]]))
  # extract residuals
  resNames <- c()
  if(i=="X0087_Y0038"){
    for (n in c(6:nlayers(NPVar))){
      resNames <- c(resNames,paste0('res_',n-5))
      npv.df <- cbind(npv.df, values(NPVar[[n]]))
    }
  } else {
    for (n in c(5:nlayers(NPVar))){
      resNames <- c(resNames,paste0('res_',n-4))
      npv.df <- cbind(npv.df, values(NPVar[[n]])) }
  }
  colnames(npv.df)[6:length(colnames(npv.df))] <- resNames

  NPV.df <- rbind.data.frame(NPV.df, npv.df)

  # soil
  in_soil <- list.files(file.path(inDir, i), 'soil_ARres.tif$', full.names=TRUE)
  SOILar <- stack(in_soil)

  soil.df <- data.frame('Row'=rowFromCell(object=SOILar, cell=1:ncell(SOILar)),
                        'Col'=colFromCell(object=SOILar, cell=1:ncell(SOILar)),
                        'lng'=coordinates(SOILar)[,1],
                        'lat'=coordinates(SOILar)[,2],
                        'Est'=values(SOILar[[1]]))
  # extract residuals
  resNames <- c()
  if(i=="X0087_Y0038"){
    for (n in c(6:nlayers(SOILar))){
      resNames <- c(resNames,paste0('res_',n-5))
      soil.df <- cbind(soil.df, values(SOILar[[n]]))
    }
  } else {
    for (n in c(5:nlayers(GVar))){
      resNames <- c(resNames,paste0('res_',n-4))
      soil.df <- cbind(soil.df, values(SOILar[[n]])) }
  }
  colnames(soil.df)[6:length(colnames(soil.df))] <- resNames

  SOIL.df <- rbind.data.frame(SOIL.df, soil.df)

  # shade
  in_sh <- list.files(file.path(inDir, i), 'shade_ARres.tif$', full.names=TRUE)
  SHar <- stack(in_sh)

  sh.df <- data.frame('Row'=rowFromCell(object=SHar, cell=1:ncell(SHar)),
                      'Col'=colFromCell(object=SHar, cell=1:ncell(SHar)),
                      'lng'=coordinates(SHar)[,1],
                      'lat'=coordinates(SHar)[,2],
                      'Est'=values(SHar[[1]]))
  # extract residuals
  resNames <- c()
  if(i=="X0087_Y0038"){
  for (n in c(6:nlayers(SHar))){
    resNames <- c(resNames,paste0('res_',n-5))
    sh.df <- cbind(sh.df, values(SHar[[n]]))
  }
} else {
  for (n in c(5:nlayers(SHar))){
    resNames <- c(resNames,paste0('res_',n-4))
    sh.df <- cbind(sh.df, values(SHar[[n]])) }
}
  colnames(sh.df)[6:length(colnames(sh.df))] <- resNames

  SH.df <- rbind.data.frame(SH.df, sh.df)

}
# take every 3rd pixel
#
GV.df5 <- GV.df[order(GV.df$Row),]
GV.df5 <- GV.df5[seq(1,nrow(GV.df5),5),]
GV.df5 <- GV.df5[order(GV.df5$Col),]
GV.df5 <- GV.df5[seq(1,nrow(GV.df5),5),]
GV.df5 <- GV.df5[order(GV.df5$Row),]

NPV.df5 <- NPV.df[order(NPV.df$Row),]
NPV.df5 <- NPV.df5[seq(1,nrow(NPV.df5),5),]
NPV.df5 <- NPV.df5[order(NPV.df5$Col),]
NPV.df5 <- NPV.df5[seq(1,nrow(NPV.df5),5),]
NPV.df5 <- NPV.df5[order(NPV.df5$Row),]

SOIL.df5 <- SOIL.df[order(SOIL.df$Row),]
SOIL.df5 <- SOIL.df5[seq(1,nrow(SOIL.df5),5),]
SOIL.df5 <- SOIL.df5[order(SOIL.df5$Col),]
SOIL.df5 <- SOIL.df5[seq(1,nrow(SOIL.df5),5),]
SOIL.df5 <- SOIL.df5[order(SOIL.df5$Row),]

SH.df5 <- SH.df[order(SH.df$Row),]
SH.df5 <- SH.df5[seq(1,nrow(SH.df5),5),]
SH.df5 <- SH.df5[order(SH.df5$Col),]
SH.df5 <- SH.df5[seq(1,nrow(SH.df5),5),]
SH.df5 <- SH.df5[order(SH.df5$Row),]

# drop NAs
GV.df5 <- GV.df5[complete.cases(GV.df5),]
NPV.df5 <- NPV.df5[complete.cases(NPV.df5),]
SOIL.df5 <- SOIL.df5[complete.cases(SOIL.df5),]
SH.df5 <- SH.df5[complete.cases(SH.df5),]

# clean memory
rm(GV.df) ;  rm(NPV.df) ;  rm(SOIL.df) ;   rm(SH.df)
rm(gv.df) ;  rm(npv.df) ;  rm(soil.df) ;   rm(sh.df)

## GV ##

# coordinates & time
coords <- data.frame(GV.df5[,c('lng', 'lat')])
# recalculate LAEA(3035) to WGS84(4326)
coordinates(coords) <- c('lng', 'lat')
proj4string(coords) <- CRS("+init=epsg:3035")
coordsLL <- spTransform(coords, CRS("+init=epsg:4326"))

xmin <- coordsLL@coords[coordsLL@coords[,'lng']== min(coordsLL@coords[,'lng'])]
xmax <- coordsLL@coords[coordsLL@coords[,'lng']== max(coordsLL@coords[,'lng'])]
ymin <- coordsLL@coords[coordsLL@coords[,'lat']== min(coordsLL@coords[,'lat'])]
ymax <- coordsLL@coords[coordsLL@coords[,'lat']== max(coordsLL@coords[,'lat'])]

d.mat <- rbind(c(xmin),c(xmax),c(ymin),c(ymax))

max.dist <- max(distm_km(d.mat))

coordsLL <- coordsLL@coords

coordsLL_temp <- coordsLL
colnames(coordsLL_temp) <- c('LON', 'LAT')

GV.df5 <- cbind(GV.df5,coordsLL_temp)

# save(GV.df5, file = paste0(outDir,'/',AOI,'_gv5.RData'))
# load(paste0(outDir,'/',AOI,'_gv5.RData'))
# GV.df3 = GV.df5

# time scale
time.int = 1:(nlayers(GVar)-4) # time points as standard integers
time.scaled = scale(time.int)
# residuals
GV.residuals = GV.df5[,6:ncol(GV.df5)]

# calculate range from residuals
fitno = 3000
range = 0.5


# initial range
GV.corfit <- try(fitCor(resids = GV.residuals, coords = coordsLL,
                        covar_FUN="covar_exp",  # "covar_exppow"
                        distm_FUN="distm_km",
                        # start = list(range = 3, shape=.01),
                        start = list(range = range),
                        fit.n = fitno))

# look for the solution incrementally until the max.dist is reached
repeat {
  if (typeof(GV.corfit)=='list') break
  if (range >= max.dist) break
  range = range + .3
  print(range)
  GV.corfit <- try(fitCor(resids = GV.residuals, coords = coordsLL,
                          covar_FUN="covar_exp",  # "covar_exppow"
                          distm_FUN="distm_km",
                          # start = list(range = 3, shape=.01),
                          start = list(range = range),
                          fit.n = fitno),
                   silent = TRUE)
}

gv.range <- GV.corfit$spcor
saveRDS(gv.range, file = paste0(outDir,'/', AOI, '_gv_range.RDS'))


# partition into 3000-chunks
GV.pm <- sample_partitions(npix = nrow(GV.df5), partsize = 3000, npart = NA)


# gvDM <- data.frame(cbind(GV.df3[,'Est'],GV.df3[,'LON'], GV.df3[,'LAT']))
gvDM <- data.frame(cbind(GV.df5[,'Est'], coordsLL))
names(gvDM) <- c('Est', 'lng', 'lat')

form = "Est ~ 1" # general model
mod.mat <- model.matrix(object = formula(form), data = gvDM)



GV.GLS <- fitGLS_partition(formula = form,
                           # formula0 = form0,
                           data = gvDM,
                           part_FUN = "part_data",
                           distm_FUN = "distm_km",
                           partmat = GV.pm,
                           covar_FUN = "covar_exp",
                           covar.pars = list(range = GV.corfit$spcor),
                           ncross = 6,
                           nugget = NA,
                          #  debug = TRUE, #FALSE,
                           ## multicore arguments:
                           # ncores = 20,
                           # parallel = TRUE
                          #  progressbar = TRUE
)
GV.t.test <- t.test(GV.GLS)
saveRDS(GV.t.test, file = paste0(outDir,'/',AOI,'_gv5_ttest.RDS'))


## NPV ##


# coordinates & time
coords <- data.frame(NPV.df5[,c('lng', 'lat')])
# recalculate LAEA(3035) to WGS84(4326)
coordinates(coords) <- c('lng', 'lat')
proj4string(coords) <- CRS("+init=epsg:3035")
coordsLL <- spTransform(coords, CRS("+init=epsg:4326"))

coordsLL <- coordsLL@coords

coordsLL_temp <- coordsLL
colnames(coordsLL_temp) <- c('LON', 'LAT')

NPV.df5 <- cbind(NPV.df5,coordsLL_temp)


# time scale
time.int = 1:(nlayers(NPVar)-4) # time points as standard integers
time.scaled = scale(time.int)
# residuals
NPV.residuals = NPV.df5[,6:ncol(NPV.df5)]

# calculate range from residuals
fitno = 3000
range = 0.5


# initial range
NPV.corfit <- try(fitCor(resids = NPV.residuals, coords = coordsLL,
                        covar_FUN="covar_exp",  # "covar_exppow"
                        distm_FUN="distm_km",
                        # start = list(range = 3, shape=.01),
                        start = list(range = range),
                        fit.n = fitno))

# look for the solution incrementally until the max.dist is reached
repeat {
  if (typeof(NPV.corfit)=='list') break
  if (range >= max.dist) break
  range = range + .3
  print(range)
  NPV.corfit <- try(fitCor(resids = NPV.residuals, coords = coordsLL,
                          covar_FUN="covar_exp",  # "covar_exppow"
                          distm_FUN="distm_km",
                          # start = list(range = 3, shape=.01),
                          start = list(range = range),
                          fit.n = fitno),
                          silent = TRUE)
}

npv.range <- NPV.corfit$spcor
saveRDS(npv.range, file = paste0(outDir,'/', AOI, '_npv_range.RDS'))


# partition into 3000-chunks
NPV.pm <- sample_partitions(npix = nrow(NPV.df5), partsize = 3000, npart = NA)

npvDM <- data.frame(cbind(NPV.df5[,'Est'], coordsLL))
names(npvDM) <- c('Est', 'lng', 'lat')

form = "Est ~ 1" # general model
mod.mat <- model.matrix(object = formula(form), data = npvDM)



NPV.GLS <- fitGLS_partition(formula = form,
                           # formula0 = form0,
                           data = npvDM,
                           part_FUN = "part_data",
                           distm_FUN = "distm_km",
                           partmat = NPV.pm,
                           covar_FUN = "covar_exp",
                           covar.pars = list(range = NPV.corfit$spcor),
                           ncross = 6,
                           nugget = NA
                          #  debug = FALSE, #FALSE,
                           ## multicore arguments:
                           # ncores = 20,
                           # parallel = TRUE
                          #  progressbar = TRUE
)

NPV.t.test <- t.test(NPV.GLS)

saveRDS(NPV.t.test, file = paste0(outDir,'/',AOI,'_npv5_ttest.RDS'))


## SOIL ##


# coordinates & time
coords <- data.frame(SOIL.df5[,c('lng', 'lat')])
# recalculate LAEA(3035) to WGS84(4326)
coordinates(coords) <- c('lng', 'lat')
proj4string(coords) <- CRS("+init=epsg:3035")
coordsLL <- spTransform(coords, CRS("+init=epsg:4326"))

coordsLL <- coordsLL@coords

coordsLL_temp <- coordsLL
colnames(coordsLL_temp) <- c('LON', 'LAT')

SOIL.df5 <- cbind(SOIL.df5,coordsLL_temp)


# time scale
time.int = 1:(nlayers(SOILar)-4) # time points as standard integers
time.scaled = scale(time.int)
# residuals
SOIL.residuals = SOIL.df5[,6:ncol(SOIL.df5)]

# calculate range from residuals
fitno = 3000
range = 0.5


# initial range
SOIL.corfit <- try(fitCor(resids = SOIL.residuals, coords = coordsLL,
                          covar_FUN="covar_exp",  # "covar_exppow"
                          distm_FUN="distm_km",
                          # start = list(range = 3, shape=.01),
                          start = list(range = range),
                          fit.n = fitno))

# look for the solution incrementally until the max.dist is reached
repeat {
  if (typeof(SOIL.corfit)=='list') break
  if (range >= max.dist) break
  range = range + .3
  print(range)
  SOIL.corfit <- try(fitCor(resids = SOIL.residuals, coords = coordsLL,
                            covar_FUN="covar_exp",  # "covar_exppow"
                            distm_FUN="distm_km",
                            # start = list(range = 3, shape=.01),
                            start = list(range = range),
                            fit.n = fitno),
                     silent = TRUE)
}

soil.range <- SOIL.corfit$spcor
saveRDS(soil.range, file = paste0(outDir,'/', AOI, '_soil_range.RDS'))

# partition into 3000-chunks
SOIL.pm <- sample_partitions(npix = nrow(SOIL.df5), partsize = 3000, npart = NA)

soilDM <- data.frame(cbind(SOIL.df5[,'Est'], coordsLL))
names(soilDM) <- c('Est', 'lng', 'lat')

form = "Est ~ 1" # general model
mod.mat <- model.matrix(object = formula(form), data = soilDM)



SOIL.GLS <- fitGLS_partition(formula = form,
                             # formula0 = form0,
                             data = soilDM,
                             part_FUN = "part_data",
                             distm_FUN = "distm_km",
                             partmat = SOIL.pm,
                             covar_FUN = "covar_exp",
                             covar.pars = list(range = SOIL.corfit$spcor),
                             ncross = 6,
                             nugget = NA,
                            #  debug = FALSE, #FALSE,
                             ## multicore arguments:
                             # ncores = 20,
                             # parallel = TRUE
                            #  progressbar = FALSE
)

SOIL.t.test <- t.test(SOIL.GLS)

saveRDS(SOIL.t.test, file = paste0(outDir,'/',AOI,'_soil5_ttest.RDS'))


## SH ##


# coordinates & time
coords <- data.frame(SH.df5[,c('lng', 'lat')])
# recalculate LAEA(3035) to WGS84(4326)
coordinates(coords) <- c('lng', 'lat')
proj4string(coords) <- CRS("+init=epsg:3035")
coordsLL <- spTransform(coords, CRS("+init=epsg:4326"))

coordsLL <- coordsLL@coords

coordsLL_temp <- coordsLL
colnames(coordsLL_temp) <- c('LON', 'LAT')

SH.df5 <- cbind(SH.df5,coordsLL_temp)


# time scale
time.int = 1:(nlayers(SHar)-4) # time points as standard integers
time.scaled = scale(time.int)
# residuals
SH.residuals = SH.df5[,6:ncol(SH.df5)]

# calculate range from residuals
fitno = 3000
range = 0.5


# initial range
SH.corfit <- try(fitCor(resids = SH.residuals, coords = coordsLL,
                        covar_FUN="covar_exp",  # "covar_exppow"
                        distm_FUN="distm_km",
                        # start = list(range = 3, shape=.01),
                        start = list(range = range),
                        fit.n = fitno))

# look for the solution incrementally until the max.dist is reached
repeat {
  if (typeof(SH.corfit)=='list') break
  if (range >= max.dist) break
  range = range + .3
  print(range)
  SH.corfit <- try(fitCor(resids = SH.residuals, coords = coordsLL,
                          covar_FUN="covar_exp",  # "covar_exppow"
                          distm_FUN="distm_km",
                          # start = list(range = 3, shape=.01),
                          start = list(range = range),
                          fit.n = fitno),
                   silent = TRUE)
}

sh.range <- SH.corfit$spcor
saveRDS(sh.range, file = paste0(outDir,'/', AOI, '_sh_range.RDS'))

# partition into 3000-chunks
SH.pm <- sample_partitions(npix = nrow(SH.df5), partsize = 3000, npart = NA)

shDM <- data.frame(cbind(SH.df5[,'Est'], coordsLL))
names(shDM) <- c('Est', 'lng', 'lat')

form = "Est ~ 1" # general model
mod.mat <- model.matrix(object = formula(form), data = shDM)



SH.GLS <- fitGLS_partition(formula = form,
                           # formula0 = form0,
                           data = shDM,
                           part_FUN = "part_data",
                           distm_FUN = "distm_km",
                           partmat = SH.pm,
                           covar_FUN = "covar_exp",
                           covar.pars = list(range = SH.corfit$spcor),
                           ncross = 6,
                           nugget = NA,
                          #  debug = FALSE, #FALSE,
                           ## multicore arguments:
                           # ncores = 20,
                           # parallel = TRUE
                          #  progressbar = TRUE
)

SH.t.test <- t.test(SH.GLS)

saveRDS(SH.t.test, file = paste0(outDir,'/',AOI,'_sh5_ttest.RDS'))

# :END OF THE CODE: #
