# Sensitivity of long-term trends in European grasslands to endmembers definition.

The aim of the FONDA_trends-nf workflow was to automatize repetitive post-processing steps marked in the workflow diagram below. The overarching goal of the study was to compare long-term trends calculated for a selection of test sites using a wide selection of input parameters.  
The input data of this workflow were 1984-2022 time series of BOA Landsat and Sentinel-2 scenes acquired over 13 sides located across Europe. The Level 1 data used to derive the BOA time series were downloaded from USGS and ESA-Copernicus data repositories and subsequently processed to Level 2 BOA with FORCE. Finally, the data were cross-normalized between sensors to assure consistency of time series. The aforementioned preprocessing, presented in the left portion of the workflow graph, was performed beforehand and was not a part of the FONDA_trends-nf workflow.

The FONDA_trends-nf workflow comprises the following steps:
- Spectral Mixture Analyses (SMA), Land Surface Phenology and Radial Basis Function filtering performed simultaneously by the means of [FORCE](https://github.com/davidfrantz/force) `force-higher-level` module.  
- derivation of Start of Season and End of Season Dates (py script)
- creation of gap-free monthly composites (py script)
- derivation of Cumulative Endmember Fractions (py script)
- AR trend analyses (R script)
- Hypothesis testing using Generalized Lease Square regression (R script)

![alt text](https://github.com/erfea/FONDA_trends-nf/blob/main/2023_08_22_Workflow_Git.jpg)

### General structure:
`R_dockr` - Comprises a Dockerfile for the R environment \
`conda_env` - Comprises a .yml file describing the Python environment \
`endm` - Comprises an example of a txt file with definition of endmembers used for SMA. Order from left to right: gv, npv, soil, shade \
`nf` - Comprises the Nextflow workflow 

### Notes on the Nextflow implementation:
The workflow was written and executed on local Linux server, hence many variables are hardcoded. Furthermore, the workflow uses local FORCE and R-specific Docker containers available in the local environment. \
`/ mainPRM.nf` defines the execution of the postprocessing workflow (to be called to execute the workflow) \
`/ local.config` defines the local environment \
`/ AR|CEF|FNF|GLS|SMA_RBF|SOS_EOS|TSA_SMA_RBF_parameters.nf`  - definitions of processes 

`nextflow run -c nextflow.config -profile bb8 mainPRM.nf -resume `

## Notes
The FONDA_trends-nf workflow is a part of the ongoing research with a related research paper in preparation. 


### Related publications:
* Frantz, D., 2019. *FORCE—Landsat + Sentinel-2 Analysis Ready Data and Beyond*. Remote Sensing 11, 1124. https://doi.org/10.3390/rs11091124
* Lewińska, K.E., Hostert, P., Buchner, J., Bleyhl, B., Radeloff, V.C., 2020. *Short-term vegetation loss versus decadal degradation of grasslands in the Caucasus based on Cumulative Endmember Fractions*. Remote Sens. Environ. 248. https://doi.org/10.1016/j.rse.2020.111969
* Ives, A.R., Zhu, L., Wang, F., Zhu, J., Morrow, C.J., Radeloff, V.C., 2021. *Statistical inference for trends in spatiotemporal data*. Remote Sensing of Environment 266, 112678. https://doi.org/10.1016/j.rse.2021.112678
* Lewińska K.E., Okujeni A., Kowalski K., Lehnamm F., Radeloff V.C., Leser U., Hostert P. (2025). Impact of data density and endmember definitions on long-term trends in ground cover fractions across European grasslands Remote Sensing of Environment https://doi.org/10.1016/j.rse.2025.114736
