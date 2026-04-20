# `revisited` branch of the trends repo

With the updates in FORCE and also advancement in the general remote-sensing knowledge, some data processing steps and approaches featured in the original version of this workflow (`main` branch) are outdated, or inaccurate. Therefore, the `revisited` branch offers some updates, though as of April 2026 they are neither implemented in a form of a nf-workflow, nor provide a complete 'bullet-proof' implementations of updates for all the processing steps. 

The `revisited` solution has been updated to FORCE 3.10.04 and consequently uses the respective structure of the prm files and functionality available in this FORCE distribution. The codes and parameters are not backward-compatible. 

The main changes include, but are not limited to:
- updated approach to RBF interpolation 
- Phenology based on PCT (the LSP approach has been deprecated in FORCE)

The workflow/scripts still assumes the input time series to be normalized across sensors (workflow_v1.jpg). This is a major limitation, since such assumption means the complete data pool should be reprocessed, doubling the space requirements (not all applications require normalization and many data users do not wish to work on cross-sensor normalized data). Consequently, the future development should enable sensor-specific unmixing step (workflow_v2.jpg) followed by data aggregation before the LSP and RBF modules. 

The revisited FONDA_trends-nf workflow comprises the following steps:
- Running `force-higher-level` FORCE module with TSA prm files (four, one run for each endmember) to perform Spectral Mixture Analyses (SMA), Land Surface Phenology and Radial Basis Function filtering performed simultaneously   
- derivation of Start of Season and End of Season Dates based on the POL sub-module executed on gv (py script)
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
