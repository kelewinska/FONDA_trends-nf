# `revisited` branch of the trends repo

With the updates of FORCE and also advancement in the general remote-sensing knowledge, some data processing steps and approaches featured in the original version of this workflow (`main` branch) are outdated, or inaccurate. Therefore, the `revisited` branch offers some improvements, though as of April 2026 they are neither implemented in a form of a complete nf-workflow, nor provide a complete 'bullet-proof' implementations of all necessary updates for all the processing steps. 

The `revisited` pool of codes and parameters has been updated to work with FORCE 3.10.04 and consequently uses the respective structure of the prm files, product names, and functionality available in this FORCE distribution. The codes and parameters are not backward-compatible. 

The main changes, as compared with the `main` version, include, but are not limited to:
- updated approach to RBF interpolation 
- Phenology based on PCT (the LSP approach has been deprecated in FORCE)

The workflow/scripts still assumes the input time series to be normalized across sensors. This is a major limitation, since such assumption requires the complete data pool to be reprocessed, doubling the space requirements. Since not all downstream applications require normalization and many data users do not wish to work on cross-sensor normalized data, such requirement is impractical. Consequently, the future development should enable sensor-specific [unmixing step](https://github.com/kelewinska/FONDA_trends-nf/blob/revisited/workflow_v2.jpg) followed by data aggregation before running the LSP-POL and RBF modules. 

The revisited FONDA_trends-nf workflow comprises the following steps:
- Running `force-higher-level` FORCE module with TSA prm files (four, one run for each endmember) to perform Spectral Mixture Analyses (SMA), Land Surface Phenology and Radial Basis Function filtering performed simultaneously   
- derivation of Start of Season and End of Season Dates based on the POL sub-module executed on gv (py script)
- creation of gap-free monthly composites (py script)
- derivation of Cumulative Endmember Fractions (py script)
- AR trend analyses (R script)
- Hypothesis testing using Generalized Lease Square regression (R script)

![alt tex](https://github.com/kelewinska/FONDA_trends-nf/blob/revisited/workflow_v1.jpg)

### General structure:
`R_dockr` - Comprises a Dockerfile for the R environment \
`conda_env` - Comprises a .yml file describing the Python environment \
`endm` - Comprises an example of a txt file with definition of endmembers used for SMA. Order from left to right: gv, npv, soil, shade \
`codes_prm` - Comprises the codes and prm files. The order of execution is as follows: *.prm, cef (order as suggested by numbers), AR (order as suggested by numbers). 

Since the logic and naming convention of codes' outputs has not been changes, it should be fairly straightforward to update the old nf workflow with these new codes. 

The status of this workflow is experimental and as stated requires further refinement to adhere to the highest standards of the current state-of-the-art. 